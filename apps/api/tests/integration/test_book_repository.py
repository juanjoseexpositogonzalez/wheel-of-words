"""Integration tests for `SqlAlchemyBookRepository` — design §7.3 (T204, T206, T207, T213).

Every test here opens a real SQLite database through the file-backed
`book_repository` fixture (`tests/integration/conftest.py`), never `:memory:`,
so a second engine — as production dependency injection creates per request —
sees the same data.

REQ-002-008, REQ-002-009, REQ-002-012, REQ-002-013.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from wheel_vocabulary.api.dependencies import (
    get_book_repository,
    get_import_text,
    get_read_import,
)
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.application.imports.use_cases import ImportText
from wheel_vocabulary.infrastructure.clock import SystemClock
from wheel_vocabulary.infrastructure.persistence.book_repository import (
    SqlAlchemyBookRepository,
)
from wheel_vocabulary.infrastructure.settings import Settings
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor

if TYPE_CHECKING:
    from sqlalchemy import Engine

_NOW = datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC)


class _ExplodingRepository:
    """Satisfies `BookRepository` but `create()` always raises — for T213."""

    def create(self, **kwargs: object) -> int:
        del kwargs
        message = "simulated persistence-layer failure"
        raise RuntimeError(message)

    def frequency_pairs(self, book_id: int) -> list[tuple[str, str, int]] | None:
        del book_id
        return None


# --------------------------------------------------------------------------
# T204 — create() batches the occurrence write with a Core insert()
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_create_batches_occurrence_inserts_at_the_configured_size(
    monkeypatch: pytest.MonkeyPatch,
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """Never `Session.add_all()`: batching is observable at the SQL layer.

    The batch size is monkeypatched down to 3 so the assertion stays fast and
    exact — 7 rows must produce 3 INSERT statements (3 + 3 + 1), which can only
    happen if the write loop actually slices at `_INSERT_BATCH`.
    """
    monkeypatch.setattr(SqlAlchemyBookRepository, "_INSERT_BATCH", 3)
    engine: Engine = book_repository._session_factory.kw["bind"]  # noqa: SLF001 - test-only introspection
    statements: list[str] = []

    def _capture(
        _conn: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,  # noqa: FBT001
    ) -> None:
        if "INSERT INTO occurrence" in statement:
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", _capture)
    try:
        occurrences = [(f"w{i}", f"w{i}", i) for i in range(7)]
        book_repository.create(
            content_hash="0" * 64,
            token_count=7,
            created_at=_NOW,
            occurrences=occurrences,
        )
    finally:
        event.remove(engine, "before_cursor_execute", _capture)

    assert len(statements) == 3


# --------------------------------------------------------------------------
# T206 — content_hash, computed before decoding, round-trips exactly
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_content_hash_matches_an_independently_computed_sha256(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """AC-002-13: two identical uploads store the same, independently-verifiable hash."""
    body = b"the same synthetic bytes, twice"
    expected = hashlib.sha256(body).hexdigest()

    first_id = book_repository.create(
        content_hash=expected, token_count=0, created_at=_NOW, occurrences=()
    )
    second_id = book_repository.create(
        content_hash=expected, token_count=0, created_at=_NOW, occurrences=()
    )

    with book_repository._session_factory() as session:  # noqa: SLF001 - test-only introspection
        from wheel_vocabulary.infrastructure.persistence.models import Book

        first_hash = session.get(Book, first_id).content_hash
        second_hash = session.get(Book, second_id).content_hash

    assert first_hash == expected
    assert second_hash == expected


@pytest.mark.integration
def test_a_one_byte_difference_changes_the_hash(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """AC-002-13: two files differing by one byte must never collide."""
    hash_a = hashlib.sha256(b"synthetic content a").hexdigest()
    hash_b = hashlib.sha256(b"synthetic content b").hexdigest()

    assert hash_a != hash_b

    id_a = book_repository.create(
        content_hash=hash_a, token_count=0, created_at=_NOW, occurrences=()
    )
    id_b = book_repository.create(
        content_hash=hash_b, token_count=0, created_at=_NOW, occurrences=()
    )

    with book_repository._session_factory() as session:  # noqa: SLF001 - test-only introspection
        from wheel_vocabulary.infrastructure.persistence.models import Book

        assert session.get(Book, id_a).content_hash != session.get(Book, id_b).content_hash


# --------------------------------------------------------------------------
# T207 — frequency_pairs() distinguishes unknown from empty, survives a new
# session against the same database
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_frequency_pairs_returns_none_for_an_unknown_id(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """AC-002-12 design §7.2: unknown id is None (404), never an empty list."""
    assert book_repository.frequency_pairs(999_999) is None


@pytest.mark.integration
def test_frequency_pairs_returns_an_empty_list_for_an_empty_import(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """REQ-002-012: an existing import with zero occurrences is `[]`, not `None`."""
    book_id = book_repository.create(
        content_hash="0" * 64, token_count=0, created_at=_NOW, occurrences=()
    )

    assert book_repository.frequency_pairs(book_id) == []


@pytest.mark.integration
def test_frequency_pairs_survives_a_new_session_against_the_same_database(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """AC-002-12: a new repository instance reads the identical list back."""
    occurrences = [("Stra\u00dfe", "strasse", 0), ("stra\u00dfe", "strasse", 1)]
    book_id = book_repository.create(
        content_hash="0" * 64, token_count=2, created_at=_NOW, occurrences=occurrences
    )

    engine: Engine = book_repository._session_factory.kw["bind"]  # noqa: SLF001
    from wheel_vocabulary.infrastructure.persistence.engine import create_session_factory

    fresh_repository = SqlAlchemyBookRepository(create_session_factory(engine))

    first_read = book_repository.frequency_pairs(book_id)
    second_read = fresh_repository.frequency_pairs(book_id)

    assert first_read is not None
    assert sorted(second_read) == sorted(first_read)
    assert sorted(second_read) == [("Stra\u00dfe", "strasse", 1), ("stra\u00dfe", "strasse", 1)]


# --------------------------------------------------------------------------
# T213 — closing leg of AC-002-18: persistence-failure and 404 logging
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_a_persistence_failure_during_create_logs_code_and_no_raw_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A repository exception during `create()` must be safely logged, never text."""
    caplog.set_level(logging.DEBUG)
    app = create_app()
    app.dependency_overrides[get_import_text] = lambda: ImportText(
        extractor=PlainTextExtractor(),
        max_size_bytes=4_194_304,
        repository=_ExplodingRepository(),
        clock=SystemClock(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/imports",
        files={"file": ("sample.txt", b"zzqxsentinel", "text/plain")},
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "PERSISTENCE_FAILURE"
    messages = [record.getMessage() for record in caplog.records]
    assert any("code=PERSISTENCE_FAILURE" in message for message in messages)
    assert "zzqxsentinel" not in "\n".join(messages)


@pytest.mark.integration
def test_reading_an_unknown_import_logs_the_attempted_id(
    book_repository: SqlAlchemyBookRepository,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-002-18 closing leg: a 404 read identifies itself by code and the id, not text."""
    caplog.set_level(logging.DEBUG)
    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: book_repository
    client = TestClient(app)

    response = client.get("/api/v1/imports/424242")

    assert response.status_code == 404
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "code=IMPORT_NOT_FOUND" in message and "import_id=424242" in message for message in messages
    )


# --------------------------------------------------------------------------
# Remaining Protocol methods and dependency providers (not gated by their own
# task — coverage/DoD completeness, AGENTS.md §10)
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_get_book_repository_builds_a_repository_from_settings(tmp_path) -> None:  # noqa: ANN001
    """The default dependency provider, exercised directly (no app override)."""
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'default.db'}")

    repository = get_book_repository(settings)

    assert isinstance(repository, SqlAlchemyBookRepository)


@pytest.mark.integration
def test_get_read_import_builds_a_read_use_case(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """The GET-side dependency provider, exercised directly."""
    use_case = get_read_import(book_repository)

    assert use_case.execute(999_999) is None
