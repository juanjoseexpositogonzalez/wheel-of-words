"""The annotation write path — design §P3/P5, spec §2.5 R2/R3.

Writes automatic `pos`/`lemma` values and provenance **unconditionally**,
without ever reading, importing, or otherwise referencing `ManualCorrection`
(R2/R3). Splitting read from write into two separate modules is what makes
that guarantee checkable by a static, structural guard rather than only a
runtime assertion that could pass by chance:
`test_annotation_write_repository_isolation.py` asserts, via AST inspection,
that this module's source never names `ManualCorrection` — not in an import,
not as a bare name, not as an attribute, not as an exact or substring string
literal, and not as a `+`-concatenated chain of split literals. The write
path cannot corrupt a correction through any of THOSE construction patterns,
because it cannot see the correction table through them at all.

**Not an exhaustive proof (R3, Judgment Day round 2).** The guard above is
bounded to the string-construction patterns it explicitly recognises. An
f-string interpolation, `str.join`, or `%`-formatted string that assembled
`"manual_correction"` at runtime would currently evade it — "structurally
provable" overstated what a finite AST pattern-matcher can guarantee against
arbitrary string construction. Closing every such route is future work, not
a claim this module makes today.

**Atomicity (REQ-003-014, AC-003-15).** `write()` is one transaction: DELETE
the occurrences' existing provenance, UPDATE each occurrence's `pos`/`lemma`,
INSERT the new provenance rows, COMMIT. A failure at any point — including
after some `UPDATE` statements have already been issued but not yet committed
— leaves every row exactly as it was before the call: the session context
manager closes without committing, which rolls back the whole transaction.
Validation of the annotations themselves (length, order, UPOS membership,
confidence range) is the caller's responsibility (`AnnotateImport`, Phase 4)
and happens entirely before this method is ever called — this repository
trusts its input and only guarantees that a *write* either lands completely
or not at all.

REQ-003-011, REQ-003-014, AC-003-15.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import delete, insert, update

from wheel_vocabulary.infrastructure.persistence.models import AnnotationProvenance, Occurrence

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from sqlalchemy.orm import Session, sessionmaker

    from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity, AnnotationRecord

__all__ = ["OccurrenceAnnotation", "SqlAlchemyAnnotationWriteRepository"]

# SQLite's compile-time SQLITE_LIMIT_VARIABLE_NUMBER is 32766 host parameters
# per statement. The provenance `DELETE`'s `IN (?, ...)` clause binds one
# parameter per occurrence id, so a run covering more occurrences than that
# would overflow it unchunked. Mirrors `book_repository.py::_INSERT_BATCH` —
# same fixed-size chunking mechanism, applied to a `DELETE ... WHERE ... IN`
# clause instead of an `INSERT` (C3).
_IN_CLAUSE_BATCH = 10_000


@dataclass(frozen=True, slots=True)
class OccurrenceAnnotation:
    """One occurrence's validated automatic annotation, ready to persist.

    The caller (Phase 4's `AnnotateImport`) has already validated every field
    against `domain.annotation` (UPOS membership, confidence range) before
    constructing one of these — this repository performs no validation of
    its own, only the write.
    """

    occurrence_id: int
    pos: str | None
    lemma: str | None
    pos_confidence: float | None
    lemma_confidence: float | None


class SqlAlchemyAnnotationWriteRepository:
    """Implements the write half of design §P3's two-repository split."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def write(
        self,
        *,
        annotations: Sequence[AnnotationRecord],
        identity: AnalyzerIdentity,
        language: str,
        processed_at: datetime,
    ) -> None:
        """Persist every annotation in one transaction — R2, AC-003-15.

        DELETE the covered occurrences' existing provenance, UPDATE each
        occurrence's `pos`/`lemma`, INSERT the new provenance rows, in that
        order, all inside one `Session` transaction. An empty `annotations`
        sequence is a no-op — no transaction is opened.

        Typed against the `AnnotationRecord` PORT (`application/annotation/
        ports.py`), not the concrete `OccurrenceAnnotation` below — this is
        what lets `api/dependencies.py` assemble `AnnotateImport` with this
        repository typed as `AnnotationWriter` (SPEC-003 task 5.5):
        `OccurrenceAnnotation` instances (still constructed throughout the
        Phase 3/4 test suite) satisfy `AnnotationRecord` structurally, so
        every existing call site keeps working unchanged.
        """
        if not annotations:
            return

        occurrence_ids = [annotation.occurrence_id for annotation in annotations]
        with self._session_factory() as session:
            self._delete_provenance(session, occurrence_ids)
            self._update_occurrences(session, annotations)
            self._insert_provenance(
                session,
                annotations=annotations,
                identity=identity,
                language=language,
                processed_at=processed_at,
            )
            session.commit()

    def _delete_provenance(self, session: Session, occurrence_ids: Sequence[int]) -> None:
        """DELETE existing provenance in fixed-size batches (C3).

        Chunked the same way `book_repository.py::_insert_occurrences` chunks
        its `INSERT`: a `_IN_CLAUSE_BATCH`-sized slice per statement, so no
        single `IN (?, ...)` clause can exceed SQLite's host-parameter limit
        regardless of how many occurrences one run covers.
        """
        for start in range(0, len(occurrence_ids), _IN_CLAUSE_BATCH):
            batch = occurrence_ids[start : start + _IN_CLAUSE_BATCH]
            session.execute(
                delete(AnnotationProvenance).where(AnnotationProvenance.occurrence_id.in_(batch))
            )

    def _update_occurrences(
        self, session: Session, annotations: Sequence[AnnotationRecord]
    ) -> None:
        """One `UPDATE` per occurrence, all inside the caller's transaction.

        Not batched via `executemany`: every statement must be individually
        observable so a mid-run failure (`AC-003-15`) can be injected and
        proven to roll back every prior, not-yet-committed `UPDATE` in the
        same call — the exact scenario `test_a_failure_mid_transaction_
        leaves_zero_rows_touched` exercises.
        """
        for annotation in annotations:
            session.execute(
                update(Occurrence)
                .where(Occurrence.id == annotation.occurrence_id)
                .values(pos=annotation.pos, lemma=annotation.lemma)
            )

    def _insert_provenance(
        self,
        session: Session,
        *,
        annotations: Sequence[AnnotationRecord],
        identity: AnalyzerIdentity,
        language: str,
        processed_at: datetime,
    ) -> None:
        session.execute(
            insert(AnnotationProvenance),
            [
                {
                    "occurrence_id": annotation.occurrence_id,
                    "source": identity.source,
                    "model_name": identity.model_name,
                    "model_version": identity.model_version,
                    "language": language,
                    "processed_at": processed_at,
                    "pos_confidence": annotation.pos_confidence,
                    "lemma_confidence": annotation.lemma_confidence,
                }
                for annotation in annotations
            ],
        )
