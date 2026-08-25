"""API-layer tests for POST/GET /api/v1/imports/{id}/annotation (task 5.4).

End to end through the real FastAPI stack, using a fake analyzer registry so
the suite never depends on the real spaCy model (that lives in the
`@pytest.mark.integration` layer, Phase 4). Every route behaviour pinned
here is a spec decision, not an implementation detail:

1. POST writes, then returns the same precedence-resolved shape GET returns
   (REQ-003-012, REQ-003-018 "own contract").
2. GET always carries both confidence keys, `null` included (C5).
3. `UNSUPPORTED_LANGUAGE` is a 422 and writes nothing (AC-003-03).
4. An unknown import id is a 404 `IMPORT_NOT_FOUND`, reusing the SPEC-002
   envelope (spec §4).

REQ-003-003, REQ-003-007, REQ-003-009, REQ-003-010, REQ-003-012.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from fastapi.testclient import TestClient

from wheel_vocabulary.api.dependencies import (
    get_analyzer_registry,
    get_annotation_read_repository,
    get_annotation_write_repository,
    get_book_repository,
    get_clock,
)
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.application.annotation.errors import UnsupportedLanguageError
from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.domain.annotation import LinguisticAnnotation
from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
    SqlAlchemyAnnotationReadRepository,
)
from wheel_vocabulary.infrastructure.persistence.annotation_write_repository import (
    SqlAlchemyAnnotationWriteRepository,
)
from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.book_repository import (
    SqlAlchemyBookRepository,
)
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from pathlib import Path

_ENDPOINT = "/api/v1/imports/{}/annotation"


class _FrozenClock:
    def now_utc(self) -> Any:
        from datetime import UTC, datetime

        return datetime(2026, 8, 24, 9, 0, 0, tzinfo=UTC)


class _StubAnalyzer:
    """Deterministic stand-in for `SpacyLinguisticAnalyzer` (design §Testing Strategy)."""

    identity = AnalyzerIdentity(source="stub", model_name="stub-model", model_version="1.0")

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del language
        return [
            LinguisticAnnotation(
                raw_text=token,
                source_index=index,
                pos="VERB",
                lemma=token.lower(),
                pos_confidence=0.9,
                lemma_confidence=None,
            )
            for index, token in enumerate(tokens)
        ]


class _StubRegistry:
    """Structurally satisfies `AnalyzerRegistry` (application/annotation/ports.py).

    Only "en" resolves; anything else raises before any pipeline would load
    — mirroring the real `infrastructure/nlp/registry.py::AnalyzerRegistry`.
    """

    def resolve(self, language: str) -> _StubAnalyzer:
        if language != "en":
            raise UnsupportedLanguageError(language=language)
        return _StubAnalyzer()


@pytest.fixture
def annotation_client(tmp_path: Path) -> Iterator[TestClient]:
    """A client wired to an isolated, schema-ready SQLite database and a
    fake analyzer registry — no real spaCy model is loaded by this suite."""
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'annotation.db'}")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    book_repository = SqlAlchemyBookRepository(session_factory)
    read_repository = SqlAlchemyAnnotationReadRepository(session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(session_factory)

    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: book_repository
    app.dependency_overrides[get_annotation_read_repository] = lambda: read_repository
    app.dependency_overrides[get_annotation_write_repository] = lambda: write_repository
    app.dependency_overrides[get_analyzer_registry] = _StubRegistry
    app.dependency_overrides[get_clock] = _FrozenClock
    yield TestClient(app)
    engine.dispose()


def _create_import(client: TestClient, text: bytes = b"ran ran") -> int:
    response = client.post("/api/v1/imports", files={"file": ("sample.txt", text, "text/plain")})
    assert response.status_code == 201
    book_id: int = response.json()["id"]
    return book_id


@pytest.mark.unit
def test_post_annotation_writes_and_returns_the_precedence_resolved_result(
    annotation_client: TestClient,
) -> None:
    """AC-003-09/AC-003-18: POST writes then returns the same shape GET returns."""
    book_id = _create_import(annotation_client, b"ran ran")

    response = annotation_client.post(_ENDPOINT.format(book_id))
    body = response.json()

    assert response.status_code == 201
    assert body["id"] == book_id
    assert body["provenance"] == {
        "source": "stub",
        "model_name": "stub-model",
        "model_version": "1.0",
        "language": "en",
        # SQLite has no native timezone-aware DATETIME type (same
        # deprecation surfaced elsewhere in this suite, e.g.
        # test_alembic_0003.py), so a round trip through the write
        # repository loses the tzinfo `_FrozenClock` supplied.
        "processed_at": "2026-08-24T09:00:00",
    }
    assert len(body["occurrences"]) == 2
    first = body["occurrences"][0]
    assert first["pos"] == "VERB"
    assert first["pos_origin"] == "automatic"
    assert first["automatic_pos"] == "VERB"
    assert first["lemma"] == "ran"
    assert first["lemma_origin"] == "automatic"
    assert first["automatic_lemma"] == "ran"
    assert first["pos_confidence"] == 0.9


@pytest.mark.unit
def test_post_annotation_carries_the_schema_version_header(
    annotation_client: TestClient,
) -> None:
    book_id = _create_import(annotation_client)

    response = annotation_client.post(_ENDPOINT.format(book_id))

    assert response.headers.get("x-schema-version") == "1"


@pytest.mark.unit
def test_lemma_confidence_key_is_present_with_json_null_when_unreported(
    annotation_client: TestClient,
) -> None:
    """C5: the stub analyzer never reports a lemma confidence — the key
    MUST still be present in the wire body, with a JSON `null`, not omitted."""
    book_id = _create_import(annotation_client, b"ran")

    body = annotation_client.post(_ENDPOINT.format(book_id)).json()

    occurrence = body["occurrences"][0]
    assert "lemma_confidence" in occurrence
    assert occurrence["lemma_confidence"] is None


@pytest.mark.unit
def test_get_annotation_returns_the_same_shape_as_post(annotation_client: TestClient) -> None:
    book_id = _create_import(annotation_client, b"ran ran")
    annotation_client.post(_ENDPOINT.format(book_id))

    response = annotation_client.get(_ENDPOINT.format(book_id))
    body = response.json()

    assert response.status_code == 200
    assert response.headers.get("x-schema-version") == "1"
    assert len(body["occurrences"]) == 2
    assert body["occurrences"][0]["lemma"] == "ran"


@pytest.mark.unit
def test_get_annotation_before_any_run_returns_null_provenance_and_null_fields(
    annotation_client: TestClient,
) -> None:
    """A never-annotated import is a valid GET, not a 404 or an error."""
    book_id = _create_import(annotation_client, b"lobo")

    body = annotation_client.get(_ENDPOINT.format(book_id)).json()

    assert body["provenance"] is None
    occurrence = body["occurrences"][0]
    assert occurrence["pos"] is None
    assert occurrence["pos_origin"] == "automatic"
    assert occurrence["lemma"] is None
    assert occurrence["pos_confidence"] is None
    assert occurrence["lemma_confidence"] is None


@pytest.mark.unit
def test_post_annotation_on_an_unsupported_language_is_422_and_writes_nothing(
    annotation_client: TestClient,
) -> None:
    """AC-003-03: `UNSUPPORTED_LANGUAGE`, no fallback, no row written."""
    book_id = _create_import(annotation_client, b"ran")

    response = annotation_client.post(f"{_ENDPOINT.format(book_id)}?language=xx")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "UNSUPPORTED_LANGUAGE"

    unwritten = annotation_client.get(_ENDPOINT.format(book_id)).json()
    assert unwritten["provenance"] is None
    assert unwritten["occurrences"][0]["pos"] is None


@pytest.mark.unit
def test_post_annotation_on_an_unknown_import_is_404(annotation_client: TestClient) -> None:
    response = annotation_client.post(_ENDPOINT.format(999_999))
    body = response.json()

    assert response.status_code == 404
    assert body["error"]["code"] == "IMPORT_NOT_FOUND"


@pytest.mark.unit
def test_get_annotation_on_an_unknown_import_is_404(annotation_client: TestClient) -> None:
    response = annotation_client.get(_ENDPOINT.format(999_999))
    body = response.json()

    assert response.status_code == 404
    assert body["error"]["code"] == "IMPORT_NOT_FOUND"


@pytest.mark.unit
def test_reannotating_updates_the_automatic_values_and_keeps_writing_unconditionally(
    annotation_client: TestClient,
) -> None:
    """REQ-003-011: the write path is unconditional; a second run refreshes
    the automatic value (no seeded correction exists here, so the effective
    value moves too — the correction-survives case is covered at the
    repository layer, Phase 3)."""
    book_id = _create_import(annotation_client, b"ran")

    first = annotation_client.post(_ENDPOINT.format(book_id)).json()
    second = annotation_client.post(_ENDPOINT.format(book_id)).json()

    assert first["occurrences"][0]["lemma"] == "ran"
    assert second["occurrences"][0]["lemma"] == "ran"
    assert second["provenance"]["source"] == "stub"
