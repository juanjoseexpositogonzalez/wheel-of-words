"""Integration tests for `DELETE /api/v1/imports/{id}` — design §6.2 (T301-T303).

Every test drives the real FastAPI stack (`TestClient`) against an isolated,
schema-ready SQLite database, mirroring `tests/api/test_imports.py`'s pattern.
Deletion is permanent (REQ-002-011): a soft delete is forbidden by spec, so
these tests assert on actual row removal, not a status flag.

REQ-002-011, AC-002-15.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from wheel_vocabulary.api.dependencies import get_book_repository
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.book_repository import (
    SqlAlchemyBookRepository,
)
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_ENDPOINT = "/api/v1/imports"


@pytest.fixture
def client_and_repository(
    tmp_path: Path,
) -> Iterator[tuple[TestClient, SqlAlchemyBookRepository]]:
    """A `TestClient` and the exact `SqlAlchemyBookRepository` it is wired to.

    Exposing the repository alongside the client lets a test inspect rows
    directly (e.g. counting orphaned `Occurrence` rows) without a second,
    disconnected database. The engine is disposed at teardown, mirroring
    `tests/conftest.py::imports_client` (REQ-TESTHYG-001).
    """
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'delete.db'}")
    Base.metadata.create_all(engine)
    repository = SqlAlchemyBookRepository(create_session_factory(engine))
    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: repository
    yield TestClient(app), repository
    engine.dispose()


def _post(client: TestClient, body: bytes) -> int:
    response = client.post(_ENDPOINT, files={"file": ("sample.txt", body, "text/plain")})
    return int(response.json()["id"])


# --------------------------------------------------------------------------
# T301 — DELETE removes the book and its occurrences; a subsequent GET 404s
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_delete_removes_book_and_occurrences_with_zero_orphans(
    client_and_repository: tuple[TestClient, SqlAlchemyBookRepository],
) -> None:
    """AC-002-15: 204, a subsequent GET 404s with the domain envelope, zero rows remain."""
    client, repository = client_and_repository
    book_id = _post(client, b"uno dos dos")

    response = client.delete(f"{_ENDPOINT}/{book_id}")

    assert response.status_code == 204
    follow_up = client.get(f"{_ENDPOINT}/{book_id}")
    follow_up_body = follow_up.json()
    assert follow_up.status_code == 404
    assert follow_up_body["error"]["code"] == "IMPORT_NOT_FOUND"
    with repository._session_factory() as session:  # noqa: SLF001 - test-only introspection
        from wheel_vocabulary.infrastructure.persistence.models import Occurrence

        remaining = session.query(Occurrence).filter_by(book_id=book_id).count()
    assert remaining == 0


@pytest.mark.integration
def test_delete_response_carries_no_body(
    client_and_repository: tuple[TestClient, SqlAlchemyBookRepository],
) -> None:
    """204 No Content: nothing to parse, mirroring the HTTP semantics of the status."""
    client, _ = client_and_repository
    book_id = _post(client, b"hola")

    response = client.delete(f"{_ENDPOINT}/{book_id}")

    assert response.status_code == 204
    assert response.content == b""


# --------------------------------------------------------------------------
# T302 — explicit two-statement delete, never ON DELETE CASCADE
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_delete_removes_occurrences_without_relying_on_a_cascade(
    client_and_repository: tuple[TestClient, SqlAlchemyBookRepository],
) -> None:
    """design §6.2: SQLite's `PRAGMA foreign_keys` is OFF by default in this suite.

    An implementation leaning on the FK's `ondelete="CASCADE"` declaration
    alone would leave every `Occurrence` row behind here, because the engine
    (`infrastructure/persistence/engine.py`) never turns the pragma on. Zero
    orphans is only reachable by two explicit `DELETE` statements in one
    transaction (`occurrence` then `book`).
    """
    client, repository = client_and_repository
    book_id = _post(client, b"uno dos dos tres tres tres")

    response = client.delete(f"{_ENDPOINT}/{book_id}")

    assert response.status_code == 204
    with repository._session_factory() as session:  # noqa: SLF001 - test-only introspection
        from wheel_vocabulary.infrastructure.persistence.models import Occurrence

        orphan_count = session.query(Occurrence).filter_by(book_id=book_id).count()
    assert orphan_count == 0


# --------------------------------------------------------------------------
# T303 — unknown or already-deleted id is a clean 404, body-shape asserted
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_deleting_an_unknown_id_returns_the_domain_404_envelope(
    client_and_repository: tuple[TestClient, SqlAlchemyBookRepository],
) -> None:
    """AC-002-15: status-only would be a false green here.

    **Observed RED, corrected from the task's prediction.** Before T304, this
    was NOT a bare Starlette 404 — `GET /api/v1/imports/{id}` already occupies
    this exact path since cut 2 (T212), so Starlette's router recognises the
    path and answers an unregistered `DELETE` on it with `405 Method Not
    Allowed` and body `{"detail": "Method Not Allowed"}`, not `404`. That is
    still a genuine RED attributable to the missing DELETE handler — 405
    unambiguously means "this path exists, this method does not" — just a
    different status than tasks.md predicted (a path-unregistered 404 would
    only occur if no route at all matched `/api/v1/imports/{id}`). The body
    shape assertion below is what distinguishes "route absent for this
    method" (`{"detail": ...}`) from "route present, id unknown"
    (`{"error": {"code": "IMPORT_NOT_FOUND"}}"`), regardless of which of the
    two absent-route statuses fires.
    """
    client, _ = client_and_repository

    response = client.delete(f"{_ENDPOINT}/999999")
    body = response.json()

    assert response.status_code == 404
    assert "detail" not in body
    assert body["error"]["code"] == "IMPORT_NOT_FOUND"


@pytest.mark.integration
def test_deleting_an_already_deleted_id_returns_404(
    client_and_repository: tuple[TestClient, SqlAlchemyBookRepository],
) -> None:
    """REQ-002-011: a second delete of the same id is also a clean 404, not a 204."""
    client, _ = client_and_repository
    book_id = _post(client, b"uno")
    first = client.delete(f"{_ENDPOINT}/{book_id}")
    assert first.status_code == 204

    second = client.delete(f"{_ENDPOINT}/{book_id}")

    assert second.status_code == 404
    assert second.json()["error"]["code"] == "IMPORT_NOT_FOUND"
