"""Integration tests for `SqlAlchemyAnnotationReadRepository` — design §P3.

Written RED before `annotation_repository.py` exists: the import below is the
only thing that can fail at collection time.

Every test opens a real SQLite database through the file-backed
`annotation_session_factory` fixture, mirroring
`test_annotation_write_repository.py` — the write repository seeds automatic
annotations, direct session inserts seed `ManualCorrection` rows (R6: no
production code path does this), and this module's repository is what is
actually under test.

REQ-003-010 (R1/R4/R5 — read-time precedence, audit value, origin marker),
REQ-003-011 (AC-003-11 — reprocessing leaves a correction byte-identical).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.domain.annotation import UPOS_TAGS
from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
    SqlAlchemyAnnotationReadRepository,
)
from wheel_vocabulary.infrastructure.persistence.annotation_write_repository import (
    OccurrenceAnnotation,
    SqlAlchemyAnnotationWriteRepository,
)
from wheel_vocabulary.infrastructure.persistence.models import Book, ManualCorrection, Occurrence

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

_NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)
_IDENTITY = AnalyzerIdentity(source="spacy", model_name="en_core_web_sm", model_version="3.8.0")


def _seed_book_with_occurrences(
    session_factory: sessionmaker[Session], *, tokens: list[str]
) -> tuple[int, list[int]]:
    """Persist a `Book` and one unannotated `Occurrence` per token.

    Returns `(book_id, occurrence_ids)`.
    """
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64,
            import_status="succeeded",
            token_count=len(tokens),
            created_at=_NOW,
        )
        session.add(book)
        session.flush()
        occurrences = [
            Occurrence(
                book_id=book.id, raw_text=token, normalized_text=token.lower(), position=position
            )
            for position, token in enumerate(tokens)
        ]
        session.add_all(occurrences)
        session.commit()
        return book.id, [occurrence.id for occurrence in occurrences]


def _seed_correction(
    session_factory: sessionmaker[Session],
    *,
    occurrence_id: int,
    field: str,
    corrected_value: str,
    corrected_at: datetime = _NOW,
) -> None:
    with session_factory() as session:
        session.add(
            ManualCorrection(
                occurrence_id=occurrence_id,
                field=field,
                corrected_value=corrected_value,
                corrected_at=corrected_at,
            )
        )
        session.commit()


@pytest.mark.integration
def test_read_returns_none_for_an_unknown_book_id(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """Mirrors `frequency_pairs`'s unknown-vs-empty distinction (design §7.2)."""
    repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    assert repository.read(999_999) is None


@pytest.mark.integration
def test_read_returns_automatic_origin_for_an_unannotated_occurrence(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """No correction, no provenance: everything reads as automatic and null."""
    book_id, _ = _seed_book_with_occurrences(annotation_session_factory, tokens=["run"])
    repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    rows = repository.read(book_id)

    assert rows is not None
    assert len(rows) == 1
    row = rows[0]
    assert row.effective_pos is None
    assert row.pos_origin == "automatic"
    assert row.automatic_pos is None
    assert row.lemma is None
    assert row.lemma_origin == "automatic"
    assert row.automatic_lemma is None


@pytest.mark.integration
def test_read_returns_an_empty_list_for_a_book_with_zero_occurrences(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """Mirrors `frequency_pairs`'s zero-occurrence state (REQ-002-012); the
    corrections lookup must short-circuit rather than issuing an empty
    `IN ()` query."""
    book_id, _ = _seed_book_with_occurrences(annotation_session_factory, tokens=[])
    repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    assert repository.read(book_id) == []


@pytest.mark.integration
def test_a_seeded_correction_wins_on_read(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """AC-003-10: a `VERB` correction over automatic `NOUN` wins, and `NOUN`
    stays recoverable as the audit value."""
    book_id, occurrence_ids = _seed_book_with_occurrences(
        annotation_session_factory, tokens=["saw"]
    )
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="NOUN",
                lemma="saw",
                pos_confidence=0.6,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )
    _seed_correction(
        annotation_session_factory,
        occurrence_id=occurrence_ids[0],
        field="pos",
        corrected_value="VERB",
    )
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    rows = read_repository.read(book_id)

    assert rows is not None
    row = rows[0]
    assert row.effective_pos == "VERB"
    assert row.pos_origin == "manual"
    assert row.automatic_pos == "NOUN"


@pytest.mark.integration
def test_precedence_is_per_field_not_per_occurrence(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """AC-003-10: a correction on `pos` only leaves `lemma` fully automatic."""
    book_id, occurrence_ids = _seed_book_with_occurrences(
        annotation_session_factory, tokens=["saw"]
    )
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="NOUN",
                lemma="saw",
                pos_confidence=None,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )
    _seed_correction(
        annotation_session_factory,
        occurrence_id=occurrence_ids[0],
        field="pos",
        corrected_value="VERB",
    )
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    row = read_repository.read(book_id)[0]  # type: ignore[index]

    assert row.pos_origin == "manual"
    assert row.lemma_origin == "automatic"
    assert row.lemma == "saw"
    assert row.automatic_lemma == "saw"


@pytest.mark.integration
def test_read_exposes_provenance_and_confidence_fields(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """REQ-003-007/008: every §2.4 field and both confidences are recoverable per row."""
    book_id, occurrence_ids = _seed_book_with_occurrences(
        annotation_session_factory, tokens=["run"]
    )
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="VERB",
                lemma="run",
                pos_confidence=0.97,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    row = read_repository.read(book_id)[0]  # type: ignore[index]

    assert row.source == "spacy"
    assert row.model_name == "en_core_web_sm"
    assert row.model_version == "3.8.0"
    assert row.language == "en"
    assert row.processed_at is not None
    assert row.pos_confidence == pytest.approx(0.97)
    assert row.lemma_confidence is None


@pytest.mark.integration
def test_rows_are_ordered_by_position(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """REQ-003-013/AC-003-14: the annotation input is `position`-ordered; the
    read model must preserve that ordering too."""
    book_id, _ = _seed_book_with_occurrences(
        annotation_session_factory, tokens=["one", "two", "three"]
    )
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    rows = read_repository.read(book_id)

    assert rows is not None
    assert [row.position for row in rows] == [0, 1, 2]
    assert [row.raw_text for row in rows] == ["one", "two", "three"]


@pytest.mark.integration
def test_reprocessing_leaves_the_correction_byte_identical(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """AC-003-11: a re-run refreshes the automatic value underneath a
    correction; the correction row itself, and the effective value it
    produces, are untouched."""
    book_id, occurrence_ids = _seed_book_with_occurrences(
        annotation_session_factory, tokens=["saw"]
    )
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="NOUN",
                lemma="saw",
                pos_confidence=0.5,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )
    correction_time = datetime(2026, 8, 24, 13, 0, 0, tzinfo=UTC)
    _seed_correction(
        annotation_session_factory,
        occurrence_id=occurrence_ids[0],
        field="pos",
        corrected_value="VERB",
        corrected_at=correction_time,
    )
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    # A re-run with a different automatic value and a newer model.
    later = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)
    new_identity = AnalyzerIdentity(
        source="spacy", model_name="en_core_web_sm", model_version="3.9.0"
    )
    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="AUX",
                lemma="see",
                pos_confidence=0.8,
                lemma_confidence=None,
            )
        ],
        identity=new_identity,
        language="en",
        processed_at=later,
    )

    with annotation_session_factory() as session:
        correction = session.get(ManualCorrection, _correction_id(session, occurrence_ids[0]))

    after = read_repository.read(book_id)[0]  # type: ignore[index]

    assert after.effective_pos == "VERB", "the corrected value still wins"
    assert after.pos_origin == "manual"
    assert after.automatic_pos == "AUX", "the audit value refreshed underneath the correction"
    assert correction is not None
    assert correction.corrected_value == "VERB"
    assert correction.corrected_at == correction_time.replace(tzinfo=None)


def _correction_id(session: Session, occurrence_id: int) -> int:
    return session.execute(
        select(ManualCorrection.id).where(ManualCorrection.occurrence_id == occurrence_id)
    ).scalar_one()


# --------------------------------------------------------------------------
# Task 3.11 — property: a seeded correction survives an arbitrary re-run.
# --------------------------------------------------------------------------

_re_annotation_values = st.tuples(
    st.sampled_from(sorted(UPOS_TAGS)),
    st.text(alphabet=st.characters(categories=["Ll"]), min_size=1, max_size=12),
    st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
)


@pytest.mark.integration
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(re_annotation=_re_annotation_values)
def test_property_a_seeded_correction_survives_any_generated_reannotation(
    annotation_session_factory: sessionmaker[Session],
    re_annotation: tuple[str, str, float | None],
) -> None:
    """AC-003-11: for ANY generated automatic `pos`/`lemma`/confidence a
    re-run could produce, the seeded correction still wins and the new
    automatic value is still recoverable as the audit value underneath it.

    Each example seeds its own book so examples never interfere with one
    another on the shared `annotation_session_factory` database.
    """
    generated_pos, generated_lemma, generated_confidence = re_annotation
    book_id, occurrence_ids = _seed_book_with_occurrences(
        annotation_session_factory, tokens=["saw"]
    )
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos="NOUN",
                lemma="saw",
                pos_confidence=None,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )
    _seed_correction(
        annotation_session_factory,
        occurrence_id=occurrence_ids[0],
        field="pos",
        corrected_value="VERB",
    )

    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_ids[0],
                pos=generated_pos,
                lemma=generated_lemma,
                pos_confidence=generated_confidence,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )

    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    row = read_repository.read(book_id)[0]  # type: ignore[index]

    assert row.effective_pos == "VERB"
    assert row.pos_origin == "manual"
    assert row.automatic_pos == generated_pos
    assert row.lemma == generated_lemma
    assert row.lemma_origin == "automatic"
