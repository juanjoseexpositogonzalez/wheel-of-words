"""Integration tests for `SqlAlchemyAnnotationWriteRepository` — design §P3/P5.

Written RED before `annotation_write_repository.py` exists: the import below
is the only thing that can fail at collection time.

Every test opens a real SQLite database through the file-backed
`annotation_session_factory` fixture (`tests/integration/conftest.py`), never
`:memory:` — mirroring `test_book_repository.py`'s precedent, so a fresh
repository instance sees what a prior write actually committed.

REQ-003-011 (R2 — writes unconditionally, never checks `ManualCorrection`),
REQ-003-014 / AC-003-15 (atomicity — a mid-run failure touches zero rows).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import event, func, select

from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.infrastructure.persistence.annotation_write_repository import (
    OccurrenceAnnotation,
    SqlAlchemyAnnotationWriteRepository,
)
from wheel_vocabulary.infrastructure.persistence.models import (
    AnnotationProvenance,
    Book,
    ManualCorrection,
    Occurrence,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlalchemy.orm import Session, sessionmaker

_NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)
_IDENTITY = AnalyzerIdentity(source="spacy", model_name="en_core_web_sm", model_version="3.8.0")


def _seed_occurrences(session_factory: sessionmaker[Session], *, count: int) -> list[int]:
    """Persist a `Book` and `count` unannotated `Occurrence` rows; return their ids in order."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=count, created_at=_NOW
        )
        session.add(book)
        session.flush()
        occurrences = [
            Occurrence(
                book_id=book.id,
                raw_text=f"w{position}",
                normalized_text=f"w{position}",
                position=position,
            )
            for position in range(count)
        ]
        session.add_all(occurrences)
        session.commit()
        return [occurrence.id for occurrence in occurrences]


@pytest.mark.integration
def test_write_sets_pos_and_lemma_and_inserts_provenance(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """Every §2.4 field is recoverable, and `pos`/`lemma` land on the occurrence."""
    occurrence_ids = _seed_occurrences(annotation_session_factory, count=2)
    repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)

    repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="VERB",
                lemma="run",
                pos_confidence=0.9,
                lemma_confidence=None,
            ),
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[1],
                pos="NOUN",
                lemma="dog",
                pos_confidence=None,
                lemma_confidence=None,
            ),
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )

    with annotation_session_factory() as session:
        first = session.get(Occurrence, occurrence_ids[0])
        second = session.get(Occurrence, occurrence_ids[1])
        provenance = session.execute(
            select(AnnotationProvenance).where(
                AnnotationProvenance.occurrence_id == occurrence_ids[0]
            )
        ).scalar_one()

    assert first is not None
    assert second is not None
    assert first.pos == "VERB"
    assert first.lemma == "run"
    assert second.pos == "NOUN"
    assert second.lemma == "dog"
    assert provenance.source == "spacy"
    assert provenance.model_name == "en_core_web_sm"
    assert provenance.model_version == "3.8.0"
    assert provenance.language == "en"
    assert provenance.pos_confidence == pytest.approx(0.9)
    assert provenance.lemma_confidence is None


@pytest.mark.integration
def test_write_ignores_an_existing_manual_correction_and_writes_unconditionally(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """R2: the automatic value is written regardless of a seeded correction,
    and the correction itself is left completely untouched."""
    occurrence_ids = _seed_occurrences(annotation_session_factory, count=1)
    with annotation_session_factory() as session:
        session.add(
            ManualCorrection(
                occurrence_id=occurrence_ids[0],
                field="pos",
                corrected_value="VERB",
                corrected_at=_NOW,
            )
        )
        session.commit()
    repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)

    repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="NOUN",
                lemma="dog",
                pos_confidence=None,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )

    with annotation_session_factory() as session:
        occurrence = session.get(Occurrence, occurrence_ids[0])
        correction = session.execute(
            select(ManualCorrection).where(ManualCorrection.occurrence_id == occurrence_ids[0])
        ).scalar_one()

    assert occurrence is not None
    assert occurrence.pos == "NOUN"
    assert correction.corrected_value == "VERB"
    assert correction.field == "pos"


@pytest.mark.integration
def test_a_re_run_replaces_the_previous_provenance_row(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """R2: reprocessing writes provenance unconditionally — one row survives, refreshed."""
    occurrence_ids = _seed_occurrences(annotation_session_factory, count=1)
    repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="NOUN",
                lemma="dog",
                pos_confidence=0.5,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )
    later = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)
    new_identity = AnalyzerIdentity(
        source="spacy", model_name="en_core_web_sm", model_version="3.9.0"
    )

    repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="VERB",
                lemma="run",
                pos_confidence=0.8,
                lemma_confidence=None,
            )
        ],
        identity=new_identity,
        language="en",
        processed_at=later,
    )

    with annotation_session_factory() as session:
        provenance_rows = (
            session.execute(
                select(AnnotationProvenance).where(
                    AnnotationProvenance.occurrence_id == occurrence_ids[0]
                )
            )
            .scalars()
            .all()
        )
        occurrence = session.get(Occurrence, occurrence_ids[0])

    assert len(provenance_rows) == 1
    assert provenance_rows[0].model_version == "3.9.0"
    assert occurrence is not None
    assert occurrence.pos == "VERB"
    assert occurrence.lemma == "run"


@pytest.mark.integration
def test_write_with_an_empty_sequence_is_a_no_op(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """An empty batch opens no transaction and touches nothing."""
    occurrence_ids = _seed_occurrences(annotation_session_factory, count=1)
    repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)

    repository.write(annotations=[], identity=_IDENTITY, language="en", processed_at=_NOW)

    with annotation_session_factory() as session:
        occurrence = session.get(Occurrence, occurrence_ids[0])
        provenance_count = session.execute(
            select(func.count()).select_from(AnnotationProvenance)
        ).scalar_one()

    assert occurrence is not None
    assert occurrence.pos is None
    assert provenance_count == 0


@pytest.mark.integration
def test_a_failure_mid_transaction_leaves_zero_rows_touched(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """AC-003-15: the second `UPDATE occurrence` in the loop fails; the first
    occurrence's update — already issued but not yet committed — must also
    roll back. Nothing SPEC-002 already wrote may end up mixed with the new
    run's values."""
    occurrence_ids = _seed_occurrences(annotation_session_factory, count=2)
    repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    engine: Engine = annotation_session_factory.kw["bind"]  # noqa: SLF001 - test-only introspection
    update_calls = {"count": 0}

    def _fail_on_second_update(
        _conn: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,  # noqa: FBT001
    ) -> None:
        if "UPDATE occurrence" in statement:
            update_calls["count"] += 1
            if update_calls["count"] == 2:
                message = "simulated mid-transaction failure"
                raise RuntimeError(message)

    event.listen(engine, "before_cursor_execute", _fail_on_second_update)
    try:
        with pytest.raises(RuntimeError, match="simulated mid-transaction failure"):
            repository.write(
                annotations=[
                    OccurrenceAnnotation(
                        occurrence_id=occurrence_ids[0],
                        pos="VERB",
                        lemma="run",
                        pos_confidence=None,
                        lemma_confidence=None,
                    ),
                    OccurrenceAnnotation(
                        occurrence_id=occurrence_ids[1],
                        pos="NOUN",
                        lemma="dog",
                        pos_confidence=None,
                        lemma_confidence=None,
                    ),
                ],
                identity=_IDENTITY,
                language="en",
                processed_at=_NOW,
            )
    finally:
        event.remove(engine, "before_cursor_execute", _fail_on_second_update)

    with annotation_session_factory() as session:
        first = session.get(Occurrence, occurrence_ids[0])
        second = session.get(Occurrence, occurrence_ids[1])
        provenance_count = session.execute(
            select(func.count()).select_from(AnnotationProvenance)
        ).scalar_one()

    assert first is not None
    assert second is not None
    assert first.pos is None, "the first occurrence's UPDATE was issued but must not survive"
    assert second.pos is None
    assert provenance_count == 0, "no provenance row may exist without a completed run"
