"""API tests for the read-only vocabulary endpoint."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from wheel_vocabulary.api.dependencies import get_book_repository, get_read_vocabulary
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.application.vocabulary.use_cases import ReadVocabulary
from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)
from wheel_vocabulary.infrastructure.persistence.models import ManualCorrection, Occurrence
from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import (
    SqlAlchemyVocabularyReadRepository,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.orm import Session, sessionmaker


_ENDPOINT = "/api/v1/imports/{}/vocabulary"
_ANNOTATION_SCHEMA_SHA256 = "ab5439de465d768ebaf1be629315b78aef652aa175c2aaf09ab2c35a7d1de309"


@pytest.fixture
def vocabulary_client(tmp_path: Path) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    """Create a client and database for vocabulary route assertions."""
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'vocabulary.db'}")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    book_repository = SqlAlchemyBookRepository(session_factory)
    vocabulary_reader = SqlAlchemyVocabularyReadRepository(session_factory)
    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: book_repository
    app.dependency_overrides[get_read_vocabulary] = lambda: ReadVocabulary(
        repository=vocabulary_reader
    )
    yield TestClient(app), session_factory
    engine.dispose()


def _seed_groups(client: TestClient, session_factory: sessionmaker[Session]) -> int:
    response = client.post(
        "/api/v1/imports",
        files={"file": ("sample.txt", b"red blue green black white gray", "text/plain")},
    )
    assert response.status_code == 201
    book_id: int = response.json()["id"]
    values = [
        ("run", "VERB"),
        ("run", "VERB"),
        ("run", "NOUN"),
        (None, "VERB"),
        ("leaf", None),
        ("moon", "NOUN"),
    ]
    with session_factory() as session:
        for position, (lemma, pos) in enumerate(values):
            session.execute(
                update(Occurrence)
                .where(Occurrence.book_id == book_id, Occurrence.position == position)
                .values(lemma=lemma, pos=pos)
            )
        session.commit()
    return book_id


@pytest.mark.unit
def test_get_vocabulary_returns_the_versioned_ordered_group_contract(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    response = client.get(_ENDPOINT.format(book_id))

    assert response.status_code == 200
    assert response.headers["x-schema-version"] == "1"
    assert response.json() == {
        "id": book_id,
        "group_count": 5,
        "total_occurrence_count": 6,
        "groups": [
            {"lemma": "run", "pos": "VERB", "occurrence_count": 2},
            {"lemma": None, "pos": "VERB", "occurrence_count": 1},
            {"lemma": "leaf", "pos": None, "occurrence_count": 1},
            {"lemma": "moon", "pos": "NOUN", "occurrence_count": 1},
            {"lemma": "run", "pos": "NOUN", "occurrence_count": 1},
        ],
    }


@pytest.mark.unit
def test_identical_vocabulary_requests_preserve_the_entire_body_order(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    first = client.get(_ENDPOINT.format(book_id))
    second = client.get(_ENDPOINT.format(book_id))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.unit
def test_vocabulary_pos_selector_narrows_groups_without_changing_their_counts(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    unfiltered = client.get(_ENDPOINT.format(book_id))
    filtered = client.get(_ENDPOINT.format(book_id), params={"pos": "NOUN"})

    assert unfiltered.status_code == 200
    assert filtered.status_code == 200
    assert filtered.json() == {
        "id": book_id,
        "group_count": 2,
        "total_occurrence_count": 2,
        "groups": [
            {"lemma": "moon", "pos": "NOUN", "occurrence_count": 1},
            {"lemma": "run", "pos": "NOUN", "occurrence_count": 1},
        ],
    }
    unfiltered_counts = {
        (group["lemma"], group["pos"]): group["occurrence_count"]
        for group in unfiltered.json()["groups"]
    }
    assert {
        (group["lemma"], group["pos"]): group["occurrence_count"]
        for group in filtered.json()["groups"]
    } == {key: unfiltered_counts[key] for key in unfiltered_counts if key[1] == "NOUN"}


@pytest.mark.unit
def test_vocabulary_pos_selector_can_select_the_null_pos_bucket(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    response = client.get(_ENDPOINT.format(book_id), params={"pos": "null"})

    assert response.status_code == 200
    assert response.json()["groups"] == [
        {"lemma": "leaf", "pos": None, "occurrence_count": 1},
    ]


@pytest.mark.unit
def test_vocabulary_rejects_an_invalid_pos_selector(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    response = client.get(_ENDPOINT.format(book_id), params={"pos": "not-a-pos"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert "groups" not in response.json()


@pytest.mark.unit
def test_vocabulary_pos_selector_without_matching_groups_is_an_empty_success(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    response = client.get(_ENDPOINT.format(book_id), params={"pos": "ADJ"})

    assert response.status_code == 200
    assert response.json() == {
        "id": book_id,
        "group_count": 0,
        "total_occurrence_count": 0,
        "groups": [],
    }


@pytest.mark.unit
def test_unknown_vocabulary_import_returns_a_content_free_not_found_error(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = vocabulary_client

    response = client.get(_ENDPOINT.format(999_999))
    body: dict[str, Any] = response.json()

    assert response.status_code == 404
    assert body["error"]["code"] == "IMPORT_NOT_FOUND"
    serialized = response.text.lower()
    assert "red" not in serialized
    assert "lemma" not in serialized
    assert "traceback" not in serialized
    assert "/users/" not in serialized


@pytest.mark.unit
def test_deleted_vocabulary_import_returns_import_not_found(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    """AC-005-05: a deleted import is distinguishable from an empty existing import."""
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    deleted = client.delete(f"/api/v1/imports/{book_id}")
    response = client.get(_ENDPOINT.format(book_id))

    assert deleted.status_code == 204
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "IMPORT_NOT_FOUND"


@pytest.mark.unit
def test_vocabulary_read_refreshes_after_a_correction_committed_between_requests(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    """AC-005-09: groups are recomputed after a committed correction, without cache invalidation."""
    client, session_factory = vocabulary_client
    book_id = _seed_groups(client, session_factory)

    first = client.get(_ENDPOINT.format(book_id))
    with session_factory() as session:
        occurrence_id = session.scalar(
            select(Occurrence.id).where(
                Occurrence.book_id == book_id,
                Occurrence.position == 0,
            )
        )
        assert occurrence_id is not None
        session.add(
            ManualCorrection(
                occurrence_id=occurrence_id,
                field="pos",
                corrected_value="NOUN",
                corrected_at=datetime(2026, 8, 31, tzinfo=UTC),
            )
        )
        session.commit()
    second = client.get(_ENDPOINT.format(book_id))

    assert first.status_code == second.status_code == 200
    assert first.json()["groups"] != second.json()["groups"]
    assert {
        (group["lemma"], group["pos"]): group["occurrence_count"]
        for group in second.json()["groups"]
    } == {
        (None, "VERB"): 1,
        ("leaf", None): 1,
        ("moon", "NOUN"): 1,
        ("run", "NOUN"): 2,
        ("run", "VERB"): 1,
    }


@pytest.mark.unit
def test_vocabulary_is_additive_to_the_frozen_annotation_contract(
    vocabulary_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = vocabulary_client
    annotation_schema = (
        Path(__file__).parents[2]
        / "src"
        / "wheel_vocabulary"
        / "api"
        / "schemas"
        / "annotation.v1.json"
    )

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert hashlib.sha256(annotation_schema.read_bytes()).hexdigest() == _ANNOTATION_SCHEMA_SHA256
    paths = response.json()["paths"]
    assert "/api/v1/imports/{import_id}/vocabulary" in paths
    assert set(paths["/api/v1/imports/{import_id}/annotation"]) == {"get", "post"}
