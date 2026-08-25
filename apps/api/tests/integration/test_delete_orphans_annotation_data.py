"""S1 — deleting an import must not leave ghost `manual_correction`/
`annotation_provenance` rows for a LATER, unrelated import to inherit.

SQLite's `PRAGMA foreign_keys` is OFF by default (`engine.py::create_engine_
from_url` never enables it, confirmed by `test_engine.py`), so the
`ondelete="CASCADE"` declared on `manual_correction.occurrence_id` and
`annotation_provenance.occurrence_id` (`models.py`) does nothing.
`book_repository.py::delete()` already documents this exact hazard and
compensates for `occurrence`/`book` with two explicit `DELETE` statements —
but was never extended to the two annotation child tables.

`Occurrence.id` is a plain SQLAlchemy integer primary key, which SQLite maps
onto its ROWID (no `sqlite_autoincrement` table option is set anywhere in
`models.py`), so a freed id is eligible for reuse by a later INSERT. Combined
with the orphaned child rows above, this reproduces end to end: delete book
A, its `manual_correction`/`annotation_provenance` rows survive keyed to
occurrence id 1, a later unrelated book B reuses id 1 for its own first
occurrence, and the read repository resolves B's occurrence as
`pos_origin="manual"` with a correction the user never made on B at all.

REQ-002-011, REQ-003-011 (R6 — no code path here should ever attribute a
correction to an occurrence the user never corrected).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
    SqlAlchemyAnnotationReadRepository,
)
from wheel_vocabulary.infrastructure.persistence.annotation_write_repository import (
    OccurrenceAnnotation,
    SqlAlchemyAnnotationWriteRepository,
)
from wheel_vocabulary.infrastructure.persistence.book_repository import (
    SqlAlchemyBookRepository,
)
from wheel_vocabulary.infrastructure.persistence.models import (
    AnnotationProvenance,
    ManualCorrection,
    Occurrence,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

_NOW = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)
_IDENTITY = AnalyzerIdentity(source="spacy", model_name="en_core_web_sm", model_version="3.8.0")


@pytest.mark.integration
def test_deleting_a_book_removes_its_manual_corrections_and_provenance(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """The narrow, direct claim: after `delete()`, zero `manual_correction`
    and zero `annotation_provenance` rows remain for the deleted book's
    occurrences — not merely that `occurrence`/`book` are gone.

    RED before S1: both counts were 1, not 0 — `delete()` never touched
    either child table.
    """
    book_repository = SqlAlchemyBookRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    book_id = book_repository.create(
        content_hash="a" * 64, token_count=1, created_at=_NOW, occurrences=[("run", "run", 0)]
    )
    with annotation_session_factory() as session:
        occurrence_id = session.query(Occurrence).filter_by(book_id=book_id).one().id
        session.add(
            ManualCorrection(
                occurrence_id=occurrence_id,
                field="pos",
                corrected_value="VERB",
                corrected_at=_NOW,
            )
        )
        session.commit()
    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_id,
                pos="NOUN",
                lemma="run",
                pos_confidence=0.9,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )

    assert book_repository.delete(book_id) is True

    with annotation_session_factory() as session:
        remaining_corrections = (
            session.query(ManualCorrection).filter_by(occurrence_id=occurrence_id).count()
        )
        remaining_provenance = (
            session.query(AnnotationProvenance).filter_by(occurrence_id=occurrence_id).count()
        )
    assert remaining_corrections == 0
    assert remaining_provenance == 0


@pytest.mark.integration
def test_deleting_a_book_does_not_fabricate_a_manual_correction_on_a_later_reimport(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """End-to-end reproduction of the exact ghost-correction scenario (S1).

    Book A gets a manual correction on its one occurrence. Book A is
    deleted. Book B is imported next, with the SAME occurrence count, so
    SQLite reuses the freed rowid for B's own first occurrence (asserted
    explicitly below, so this test fails loudly rather than silently
    passing if a future SQLAlchemy/SQLite change stops reusing ids). Book B
    is then annotated for real. The read repository must show B's
    occurrence as purely automatic — never inheriting A's correction.

    RED before S1: `read_repository.read(book_b_id)[0].pos_origin` was
    `"manual"` and `.effective_pos` was `"VERB"` — a correction the user
    never made on book B at all.
    """
    book_repository = SqlAlchemyBookRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)

    book_a_id = book_repository.create(
        content_hash="a" * 64, token_count=1, created_at=_NOW, occurrences=[("run", "run", 0)]
    )
    with annotation_session_factory() as session:
        occurrence_a_id = session.query(Occurrence).filter_by(book_id=book_a_id).one().id
        session.add(
            ManualCorrection(
                occurrence_id=occurrence_a_id,
                field="pos",
                corrected_value="VERB",
                corrected_at=_NOW,
            )
        )
        session.commit()

    assert book_repository.delete(book_a_id) is True

    book_b_id = book_repository.create(
        content_hash="b" * 64, token_count=1, created_at=_NOW, occurrences=[("dog", "dog", 0)]
    )
    with annotation_session_factory() as session:
        occurrence_b_id = session.query(Occurrence).filter_by(book_id=book_b_id).one().id
    # Precondition this scenario depends on: SQLite reused the freed rowid.
    # If this ever stops holding, the test must fail loudly here rather than
    # silently proving nothing downstream.
    assert occurrence_b_id == occurrence_a_id

    write_repository.write(
        annotations=[
            OccurrenceAnnotation(
                occurrence_id=occurrence_b_id,
                pos="NOUN",
                lemma="dog",
                pos_confidence=0.95,
                lemma_confidence=None,
            )
        ],
        identity=_IDENTITY,
        language="en",
        processed_at=_NOW,
    )

    rows = read_repository.read(book_b_id)

    assert rows is not None
    assert len(rows) == 1
    assert rows[0].pos_origin == "automatic", "book B's occurrence inherited book A's correction"
    assert rows[0].effective_pos == "NOUN"
    assert rows[0].lemma == "dog"
