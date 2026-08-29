"""Read scenario — AC-005-08 scenario 2: reading leaves the correction table untouched.

Seeds a `ManualCorrection` row directly via the ORM (no writer exists yet,
per REQ-005-002's "testable now" note), runs `groups()`, and asserts the
`manual_correction` row count and bytes are unchanged afterwards.

REQ-005-008, AC-005-08 scenario 2.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from wheel_vocabulary.infrastructure.persistence.models import (
    Book,
    ManualCorrection,
    Occurrence,
)
from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import (
    SqlAlchemyVocabularyReadRepository,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from sqlalchemy import Engine
    from sqlalchemy.orm import sessionmaker


@pytest.mark.integration
def test_vocabulary_read_leaves_manual_correction_unchanged(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """AC-005-08 scenario 2: given an import with a seeded correction, when the
    vocabulary read runs, the correction rows are byte-identical afterwards and
    the row count is unchanged.

    Seeds one `Book` with two `Occurrence` rows (one `VERB`, one `NOUN`) and
    one `ManualCorrection` moving the first occurrence's `lemma` from `saw`
    to `see`. Runs `groups()`, then re-reads the correction table and asserts
    both the row count and every column value are identical.
    """
    book_id = _seed_corpus_with_correction(annotation_session_factory)

    # Snapshot the correction table BEFORE the read.
    before = _read_all_corrections(annotation_session_factory)

    # Run the vocabulary read.
    repository = SqlAlchemyVocabularyReadRepository(annotation_session_factory)
    groups = repository.groups(book_id)

    assert groups is not None, "groups() returned None for an existing import"

    # Snapshot the correction table AFTER the read.
    after = _read_all_corrections(annotation_session_factory)

    # Row count unchanged.
    assert len(after) == len(before), (
        f"manual_correction row count changed: {len(before)} -> {len(after)}"
    )

    # Every column value byte-identical.
    assert after == before, (
        "manual_correction rows changed during vocabulary read:\n"
        f"before: {before}\n"
        f"after:  {after}"
    )


@pytest.mark.integration
def test_vocabulary_read_does_not_add_corrections_when_none_seeded(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """AC-005-08 scenario 2, zero-correction leg: an import with no seeded
    corrections still has zero `manual_correction` rows after `groups()` runs.

    The read path joins `manual_correction` to resolve effective values; this
    asserts that join is a pure read, never a side-effecting write, even when
    the table is empty.
    """
    book_id = _seed_corpus_without_corrections(annotation_session_factory)

    before = _read_all_corrections(annotation_session_factory)
    assert before == [], "fixture precondition: no corrections seeded"

    repository = SqlAlchemyVocabularyReadRepository(annotation_session_factory)
    groups = repository.groups(book_id)

    assert groups is not None

    after = _read_all_corrections(annotation_session_factory)

    assert after == before
    assert len(after) == 0


def _seed_corpus_with_correction(session_factory: sessionmaker[Session]) -> int:
    """Seed a book with two occurrences and one manual correction, return book_id."""
    with session_factory() as session:
        book = Book(
            content_hash="test-hash-correction-scenario",
            import_status="succeeded",
            token_count=2,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        session.add(book)
        session.flush()
        book_id = book.id

        occ1 = Occurrence(
            book_id=book_id,
            raw_text="saw",
            normalized_text="saw",
            position=0,
            pos="NOUN",
            lemma="saw",
        )
        occ2 = Occurrence(
            book_id=book_id,
            raw_text="run",
            normalized_text="run",
            position=1,
            pos="VERB",
            lemma="run",
        )
        session.add_all([occ1, occ2])
        session.flush()

        correction = ManualCorrection(
            occurrence_id=occ1.id,
            field="lemma",
            corrected_value="see",
            corrected_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
        session.add(correction)
        session.commit()
        return book_id


def _seed_corpus_without_corrections(session_factory: sessionmaker[Session]) -> int:
    """Seed a book with two occurrences and no corrections, return book_id."""
    with session_factory() as session:
        book = Book(
            content_hash="test-hash-no-corrections",
            import_status="succeeded",
            token_count=2,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        session.add(book)
        session.flush()
        book_id = book.id

        occ1 = Occurrence(
            book_id=book_id,
            raw_text="saw",
            normalized_text="saw",
            position=0,
            pos="NOUN",
            lemma="saw",
        )
        occ2 = Occurrence(
            book_id=book_id,
            raw_text="run",
            normalized_text="run",
            position=1,
            pos="VERB",
            lemma="run",
        )
        session.add_all([occ1, occ2])
        session.commit()
        return book_id


def _read_all_corrections(session_factory: sessionmaker[Session]) -> list[tuple[int, str, str, str]]:
    """Read every manual_correction row as a comparable tuple.

    Returns `(occurrence_id, field, corrected_value, corrected_at_iso)` tuples
    so the assertion compares values, not ORM object identity.
    """
    with session_factory() as session:
        rows = session.execute(
            select(
                ManualCorrection.occurrence_id,
                ManualCorrection.field,
                ManualCorrection.corrected_value,
                ManualCorrection.corrected_at,
            ).order_by(ManualCorrection.id)
        ).all()
        return [
            (occurrence_id, field, corrected_value, corrected_at.isoformat())
            for occurrence_id, field, corrected_value, corrected_at in rows
        ]