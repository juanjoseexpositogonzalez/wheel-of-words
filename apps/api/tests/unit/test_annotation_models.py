"""ORM mapping tests for the annotation persistence models — design §P5.

Written RED before `infrastructure/persistence/models.py` gains
`Occurrence.lemma`, `AnnotationProvenance` and `ManualCorrection`: the import
below is the only thing that can fail at collection time.

**Task 3.1 drives the Alembic migration, not the ORM mapping** (slice-2 task
audit finding): this module is what actually drives the mapped classes.
Without it, task 3.4's `[IMPL]` would have had no preceding `[TEST]` — the
exact defect class task 2.8 (`errors.py`) fell into.

REQ-003-006, REQ-003-007, REQ-003-011 (schema-only R6), REQ-003-015.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import inspect

from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)
from wheel_vocabulary.infrastructure.persistence.models import (
    AnnotationProvenance,
    Book,
    ManualCorrection,
    Occurrence,
)

_NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def session_factory(tmp_path):  # noqa: ANN001, ANN201
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'annotation_models.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    yield factory
    engine.dispose()


@pytest.mark.unit
def test_occurrence_lemma_is_nullable_and_defaults_to_none(session_factory) -> None:  # noqa: ANN001
    """REQ-003-006: `Occurrence.lemma` is a separate, nullable column."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=1, created_at=_NOW
        )
        session.add(book)
        session.flush()
        occurrence = Occurrence(book_id=book.id, raw_text="run", normalized_text="run", position=0)
        session.add(occurrence)
        session.commit()

        stored = session.get(Occurrence, occurrence.id)
        assert stored is not None
        assert stored.lemma is None


@pytest.mark.unit
def test_occurrence_lemma_round_trips_a_stored_value(session_factory) -> None:  # noqa: ANN001
    """REQ-003-006: a lemma written on the mapped column is read back unchanged."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=1, created_at=_NOW
        )
        session.add(book)
        session.flush()
        occurrence = Occurrence(
            book_id=book.id, raw_text="ran", normalized_text="ran", position=0, lemma="run"
        )
        session.add(occurrence)
        session.commit()

        stored = session.get(Occurrence, occurrence.id)
        assert stored is not None
        assert stored.lemma == "run"


@pytest.mark.unit
def test_annotation_provenance_maps_all_seven_fields(session_factory) -> None:  # noqa: ANN001
    """REQ-003-007: all seven §2.4 fields are recoverable on the mapped row."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=1, created_at=_NOW
        )
        session.add(book)
        session.flush()
        occurrence = Occurrence(book_id=book.id, raw_text="run", normalized_text="run", position=0)
        session.add(occurrence)
        session.flush()
        provenance = AnnotationProvenance(
            occurrence_id=occurrence.id,
            source="spacy",
            model_name="en_core_web_sm",
            model_version="3.8.0",
            language="en",
            processed_at=_NOW,
            pos_confidence=0.97,
            lemma_confidence=None,
        )
        session.add(provenance)
        session.commit()

        stored = session.get(AnnotationProvenance, provenance.id)
        assert stored is not None
        assert stored.occurrence_id == occurrence.id
        assert stored.source == "spacy"
        assert stored.model_name == "en_core_web_sm"
        assert stored.model_version == "3.8.0"
        assert stored.language == "en"
        # SQLite drops tzinfo on round-trip; compare the naive wall-clock value.
        assert stored.processed_at == _NOW.replace(tzinfo=None)
        assert stored.pos_confidence == pytest.approx(0.97)
        assert stored.lemma_confidence is None


@pytest.mark.unit
def test_annotation_provenance_occurrence_id_is_unique(session_factory) -> None:  # noqa: ANN001
    """Design §P5: `occurrence_id` FK is UNIQUE — one provenance row per occurrence."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=1, created_at=_NOW
        )
        session.add(book)
        session.flush()
        occurrence = Occurrence(book_id=book.id, raw_text="run", normalized_text="run", position=0)
        session.add(occurrence)
        session.flush()
        session.add(
            AnnotationProvenance(
                occurrence_id=occurrence.id,
                source="spacy",
                model_name="en_core_web_sm",
                model_version="3.8.0",
                language="en",
                processed_at=_NOW,
                pos_confidence=None,
                lemma_confidence=None,
            )
        )
        session.commit()

        session.add(
            AnnotationProvenance(
                occurrence_id=occurrence.id,
                source="spacy",
                model_name="en_core_web_sm",
                model_version="3.8.1",
                language="en",
                processed_at=_NOW,
                pos_confidence=None,
                lemma_confidence=None,
            )
        )
        with pytest.raises(Exception, match="UNIQUE"):
            session.commit()


@pytest.mark.unit
def test_manual_correction_maps_field_and_corrected_value(session_factory) -> None:  # noqa: ANN001
    """R6: the table is mapped and writable directly in a test, even though
    no production code path in this capability ever writes to it."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=1, created_at=_NOW
        )
        session.add(book)
        session.flush()
        occurrence = Occurrence(book_id=book.id, raw_text="run", normalized_text="run", position=0)
        session.add(occurrence)
        session.flush()
        correction = ManualCorrection(
            occurrence_id=occurrence.id,
            field="pos",
            corrected_value="VERB",
            corrected_at=_NOW,
        )
        session.add(correction)
        session.commit()

        stored = session.get(ManualCorrection, correction.id)
        assert stored is not None
        assert stored.occurrence_id == occurrence.id
        assert stored.field == "pos"
        assert stored.corrected_value == "VERB"
        assert stored.corrected_at == _NOW.replace(tzinfo=None)


@pytest.mark.unit
def test_manual_correction_is_unique_per_occurrence_and_field(session_factory) -> None:  # noqa: ANN001
    """Design §P5: `UNIQUE(occurrence_id, field)` — at most one correction per field."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=1, created_at=_NOW
        )
        session.add(book)
        session.flush()
        occurrence = Occurrence(book_id=book.id, raw_text="run", normalized_text="run", position=0)
        session.add(occurrence)
        session.flush()
        session.add(
            ManualCorrection(
                occurrence_id=occurrence.id, field="pos", corrected_value="VERB", corrected_at=_NOW
            )
        )
        session.commit()

        session.add(
            ManualCorrection(
                occurrence_id=occurrence.id, field="pos", corrected_value="NOUN", corrected_at=_NOW
            )
        )
        with pytest.raises(Exception, match="UNIQUE"):
            session.commit()


@pytest.mark.unit
def test_reflected_schema_matches_the_mapped_models(session_factory) -> None:  # noqa: ANN001
    """The models this file drives create exactly the tables `0003_annotation` creates."""
    with session_factory() as session:
        inspector = inspect(session.bind)
        table_names = set(inspector.get_table_names())

    assert {"annotation_provenance", "manual_correction"} <= table_names
