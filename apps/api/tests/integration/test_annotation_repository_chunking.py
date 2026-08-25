"""C3 — SQLite `IN (?, ...)` parameter-count boundary for the annotation paths.

`SqlAlchemyAnnotationReadRepository._read_corrections` and
`SqlAlchemyAnnotationWriteRepository.write`'s provenance `DELETE` both build one
unchunked `IN (?, ...)` clause over every occurrence id involved. SQLite's
compile-time `SQLITE_LIMIT_VARIABLE_NUMBER` is 32766 host parameters per
statement; a book with more occurrences than that overflows the clause.

REPRODUCED (RED, before the fix): a book with 32767 occurrences —
one over the limit — made `AnnotationReadRepository.read()` raise::

    sqlite3.OperationalError: too many SQL variables

and `AnnotationWriteRepository.write()` raise the same error from its
provenance `DELETE`. 32766 occurrences (exactly at the limit) always worked,
which is why the off-by-one only shows up at scale — this is what makes it a
genuine corpus-size defect and not a hypothetical one.

Both repositories are seeded through bulk Core `insert()` (mirroring
`book_repository.py::_insert_occurrences`), not `Session.add_all()`, so the
32767-row setup itself stays fast enough for a normal test run.

REQ-003-011, REQ-003-014.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import insert

from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
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

_NOW = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)
_IDENTITY = AnalyzerIdentity(source="spacy", model_name="en_core_web_sm", model_version="3.8.0")

# One over SQLite's compile-time SQLITE_LIMIT_VARIABLE_NUMBER (32766).
_OVER_THE_LIMIT = 32_767


def _seed_book_with_many_occurrences(
    session_factory: sessionmaker[Session], *, count: int
) -> tuple[int, list[int]]:
    """Bulk-insert `count` occurrences for one book; return `(book_id, occurrence_ids)`."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=count, created_at=_NOW
        )
        session.add(book)
        session.flush()
        book_id = book.id
        batch_size = 10_000
        for start in range(0, count, batch_size):
            end = min(start + batch_size, count)
            session.execute(
                insert(Occurrence),
                [
                    {
                        "book_id": book_id,
                        "raw_text": f"w{position}",
                        "normalized_text": f"w{position}",
                        "position": position,
                        "pos": None,
                    }
                    for position in range(start, end)
                ],
            )
        session.commit()

    with session_factory() as session:
        occurrence_ids = [
            row.id
            for row in session.execute(
                Occurrence.__table__.select()
                .with_only_columns(Occurrence.id)
                .where(Occurrence.book_id == book_id)
                .order_by(Occurrence.position)
            )
        ]
    return book_id, occurrence_ids


@pytest.mark.integration
def test_read_succeeds_for_a_book_with_more_occurrences_than_the_sqlite_variable_limit(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """C3: `read()` must chunk `_read_corrections`'s `IN (?, ...)` clause.

    RED (before the fix): raised
    ``sqlite3.OperationalError: too many SQL variables`` from inside
    `_read_corrections`, because `ManualCorrection.occurrence_id.in_(occurrence_ids)`
    put all 32767 ids in one clause.
    """
    book_id, occurrence_ids = _seed_book_with_many_occurrences(
        annotation_session_factory, count=_OVER_THE_LIMIT
    )
    # A correction on the very last occurrence proves chunked results are
    # still merged correctly, not just that no exception was raised.
    with annotation_session_factory() as session:
        session.add(
            ManualCorrection(
                occurrence_id=occurrence_ids[-1],
                field="pos",
                corrected_value="VERB",
                corrected_at=_NOW,
            )
        )
        session.commit()
    repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    result = repository.read(book_id)

    assert result is not None
    assert len(result) == _OVER_THE_LIMIT
    assert result[-1].pos_origin == "manual"
    assert result[-1].effective_pos == "VERB"
    assert result[0].pos_origin == "automatic"


@pytest.mark.integration
def test_write_succeeds_for_more_annotations_than_the_sqlite_variable_limit(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """C3: `write()` must chunk the provenance `DELETE`'s `IN (?, ...)` clause.

    RED (before the fix): raised
    ``sqlite3.OperationalError: too many SQL variables`` from the
    `delete(AnnotationProvenance).where(AnnotationProvenance.occurrence_id.in_(occurrence_ids))`
    statement, because all 32767 ids were bound in one clause.
    """
    book_id, occurrence_ids = _seed_book_with_many_occurrences(
        annotation_session_factory, count=_OVER_THE_LIMIT
    )
    del book_id
    repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)

    repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_id,
                pos="NOUN",
                lemma=f"w{index}",
                pos_confidence=None,
                lemma_confidence=None,
            )
            for index, occurrence_id in enumerate(occurrence_ids)
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )

    with annotation_session_factory() as session:
        first = session.get(Occurrence, occurrence_ids[0])
        last = session.get(Occurrence, occurrence_ids[-1])

    assert first is not None
    assert first.pos == "NOUN"
    assert last is not None
    assert last.pos == "NOUN"
    assert last.lemma == f"w{_OVER_THE_LIMIT - 1}"
