"""The annotation read path — design §P3, spec §2.5.

Issues one query for the occurrences and provenance of an import, plus one
lookup for whatever `ManualCorrection` rows exist over those occurrences,
then resolves the read-time precedence rule (§2.5) in pure Python via
`domain.annotation.resolve_effective` — never in SQL, so the rule stays
testable without a database (design §P3).

**Naming note (REQ-003-023, design §P6).** The read model's *effective*
lemma field is spelled exactly ``lemma`` — not ``effective_lemma`` — because
only the five exact names in `test_no_lemma_naming.py::_ALLOWED_LEMMA_SYMBOLS`
may appear anywhere in this package: ``lemma`` (the effective wire key),
``lemma_confidence``, ``lemma_origin``, ``automatic_lemma`` and
``lemmatizer``. ``effective_lemma`` is not one of them and would fail the
guard. ``pos`` carries no such restriction (only the *bare* two-to-three
letter literal is ISO-639-shaped, and that check is scoped to `domain/`
anyway), so the POS-side fields keep the more descriptive
``effective_pos``/``pos_origin``/``automatic_pos`` spelling design §P3
describes. The two field families are asymmetrically named on purpose — this
is the intended reading of the allow-list's own inline comments, not an
inconsistency.

REQ-003-010 (R1/R4/R5), REQ-003-011 (AC-003-11).
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from wheel_vocabulary.domain.annotation import Origin, resolve_effective
from wheel_vocabulary.infrastructure.persistence.models import (
    AnnotationProvenance,
    Book,
    ManualCorrection,
    Occurrence,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import datetime

    from sqlalchemy import Row
    from sqlalchemy.orm import Session, sessionmaker

__all__ = ["AnnotatedOccurrence", "SqlAlchemyAnnotationReadRepository"]


@dataclass(frozen=True, slots=True)
class AnnotatedOccurrence:
    """One occurrence's precedence-resolved read model — design §P3 R1.

    No field here holds a raw, unresolved manual-correction value: the
    constructor's ``corrections`` argument is an ``InitVar``, consumed by
    `__post_init__` to produce ``effective_pos``/``pos_origin`` and
    ``lemma``/``lemma_origin``, then discarded. Only the resolved value, its
    origin marker, and the retained automatic/audit value (R4) are exposed —
    there is no ambiguous ``pos`` or ``lemma`` attribute a caller could read
    by accident and get an unresolved value back. Constructing this object
    *is* applying precedence (design §P3).
    """

    occurrence_id: int
    position: int
    raw_text: str
    automatic_pos: str | None
    automatic_lemma: str | None
    pos_confidence: float | None
    lemma_confidence: float | None
    source: str | None
    model_name: str | None
    model_version: str | None
    language: str | None
    processed_at: datetime | None
    corrections: InitVar[Mapping[str, str | None]]
    effective_pos: str | None = field(init=False)
    pos_origin: Origin = field(init=False)
    lemma: str | None = field(init=False)
    lemma_origin: Origin = field(init=False)

    def __post_init__(self, corrections: Mapping[str, str | None]) -> None:
        effective_pos, pos_origin = resolve_effective(self.automatic_pos, corrections.get("pos"))
        object.__setattr__(self, "effective_pos", effective_pos)
        object.__setattr__(self, "pos_origin", pos_origin)
        lemma, lemma_origin = resolve_effective(self.automatic_lemma, corrections.get("lemma"))
        object.__setattr__(self, "lemma", lemma)
        object.__setattr__(self, "lemma_origin", lemma_origin)


class SqlAlchemyAnnotationReadRepository:
    """Implements the read half of design §P3's two-repository split."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def read(self, book_id: int) -> list[AnnotatedOccurrence] | None:
        """Return every occurrence of `book_id`, precedence-resolved and
        ordered by `position`, or `None` if `book_id` is unknown."""
        with self._session_factory() as session:
            if session.get(Book, book_id) is None:
                return None

            statement = (
                select(
                    Occurrence.id,
                    Occurrence.position,
                    Occurrence.raw_text,
                    Occurrence.pos,
                    Occurrence.lemma,
                    AnnotationProvenance.source,
                    AnnotationProvenance.model_name,
                    AnnotationProvenance.model_version,
                    AnnotationProvenance.language,
                    AnnotationProvenance.processed_at,
                    AnnotationProvenance.pos_confidence,
                    AnnotationProvenance.lemma_confidence,
                )
                .outerjoin(
                    AnnotationProvenance, AnnotationProvenance.occurrence_id == Occurrence.id
                )
                .where(Occurrence.book_id == book_id)
                .order_by(Occurrence.position)
            )
            rows = list(session.execute(statement))
            corrections = self._read_corrections(session, [row.id for row in rows])
            return [_annotated_occurrence(row, corrections.get(row.id, {})) for row in rows]

    def _read_corrections(
        self, session: Session, occurrence_ids: Sequence[int]
    ) -> dict[int, dict[str, str]]:
        if not occurrence_ids:
            return {}
        statement = select(
            ManualCorrection.occurrence_id,
            ManualCorrection.field,
            ManualCorrection.corrected_value,
        ).where(ManualCorrection.occurrence_id.in_(occurrence_ids))
        corrections: dict[int, dict[str, str]] = {}
        for row in session.execute(statement):
            corrections.setdefault(row.occurrence_id, {})[row.field] = row.corrected_value
        return corrections


def _annotated_occurrence(row: Row[Any], corrections: Mapping[str, str]) -> AnnotatedOccurrence:
    """Build one `AnnotatedOccurrence` from a joined row and its corrections."""
    return AnnotatedOccurrence(
        occurrence_id=row.id,
        position=row.position,
        raw_text=row.raw_text,
        automatic_pos=row.pos,
        automatic_lemma=row.lemma,
        pos_confidence=row.pos_confidence,
        lemma_confidence=row.lemma_confidence,
        source=row.source,
        model_name=row.model_name,
        model_version=row.model_version,
        language=row.language,
        processed_at=row.processed_at,
        corrections=corrections,
    )
