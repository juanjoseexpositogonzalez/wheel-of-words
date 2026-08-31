"""Vocabulary aggregation read path — design §D1, §D2, §D5; spec §2.1-§2.5.

Groups occurrences by their precedence-resolved effective `(lemma, POS)`
pair. Two legs run inside one explicit SQLite read transaction, so they
observe one snapshot while WAL lets unrelated writers commit concurrently:

* **leg A** (`_raw_group_counts`): `GROUP BY` over the RAW `Occurrence`
  columns — an index-ordered scan served by `ix_occurrence_book_lemma_pos`,
  no temp B-tree (design D2). Counts every occurrence under its raw pair,
  corrected ones included.
* **leg B** (`_corrected_deltas`): one `(raw pair, effective pair)` per
  occurrence carrying at least one `ManualCorrection` row. Bounded by the
  correction count, never by the occurrence count.

`_merge` moves each occurrence leg B names out of its raw group and into
its effective group by calling `domain.annotation.resolve_effective` — the
ONE place spec §2.5's precedence rule runs (design D1). A SQL `COALESCE`
over `manual_correction` would be a second, divergent definition of that
rule and is explicitly forbidden (spec §2.2 E3). Work is
O(groups + corrections), never O(occurrences).

The query joins `occurrence` and `manual_correction` only. It never joins
the provenance table, so confidence cannot reach this module at all (design
D4, spec §2.4 K1).

REQ-005-001, REQ-005-002, REQ-005-003, REQ-005-005, REQ-005-009.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from wheel_vocabulary.domain.annotation import resolve_effective
from wheel_vocabulary.infrastructure.persistence.models import Book, ManualCorrection, Occurrence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from sqlalchemy.orm import Session, sessionmaker

__all__ = ["SqlAlchemyVocabularyReadRepository", "VocabularyGroup"]

# Mirrors `annotation_repository.py::_IN_CLAUSE_BATCH` — the same SQLite
# host-parameter ceiling (32766 per statement), applied here to the
# corrected-occurrence lookup instead of the correction-row lookup there.
_IN_CLAUSE_BATCH = 10_000

_Pair = tuple[str | None, str | None]


@dataclass(frozen=True, slots=True)
class VocabularyGroup:
    """One `(effective lemma, effective POS)` pair and its occurrence count.

    Never a stored row (§2.5 P1) — computed at query time on every request.
    Carries no aggregate provenance, confidence, or origin marker (§2.1 G6).
    """

    lemma: str | None
    pos: str | None
    occurrence_count: int


class SqlAlchemyVocabularyReadRepository:
    """Implements design §D1's V3 hybrid: `GROUP BY` plus a correction delta."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def groups(self, book_id: int) -> Sequence[VocabularyGroup] | None:
        """Return every `(lemma, POS)` group for `book_id`, or `None`.

        `None` means `book_id` is unknown, mirroring
        `annotation_repository.py::read`'s existence check — established
        with its own query, independent of whether the aggregation returns
        a row. An import with zero occurrences returns `[]`, never `None`
        (§2.3, AC-005-05). The returned sequence carries design D5's total
        order, applied after the leg-A/leg-B merge below. File-backed SQLite
        engines use WAL by default; the explicit read transaction below keeps
        both query legs on one snapshot without blocking a concurrent writer's
        commit.
        """
        with self._session_factory() as session:
            session.connection().exec_driver_sql("BEGIN")
            if session.get(Book, book_id) is None:
                return None

            counts = self._raw_group_counts(session, book_id)
            deltas = self._corrected_deltas(session, book_id)
            merged = _merge(counts, deltas)
            return _ordered(merged)

    def _raw_group_counts(self, session: Session, book_id: int) -> dict[_Pair, int]:
        """Leg A: an index-ordered `GROUP BY` scan (design D2), no temp B-tree."""
        statement = (
            select(Occurrence.lemma, Occurrence.pos, func.count().label("occurrence_count"))
            .where(Occurrence.book_id == book_id)
            .group_by(Occurrence.lemma, Occurrence.pos)
        )
        return {(lemma, pos): count for lemma, pos, count in session.execute(statement)}

    def _corrected_deltas(self, session: Session, book_id: int) -> list[tuple[_Pair, _Pair]]:
        """Leg B: `(raw pair, effective pair)` for every corrected occurrence.

        Bounded by the correction count (design D1): only occurrences that
        appear in `manual_correction` are ever fetched here.
        """
        corrected_ids = select(ManualCorrection.occurrence_id).distinct().subquery()
        statement = (
            select(Occurrence.id, Occurrence.lemma, Occurrence.pos)
            .where(Occurrence.book_id == book_id)
            .where(Occurrence.id.in_(select(corrected_ids)))
        )
        raw_by_id = {row_id: (word, tag) for row_id, word, tag in session.execute(statement)}
        if not raw_by_id:
            return []

        corrections = self._read_corrections(session, list(raw_by_id))
        deltas: list[tuple[_Pair, _Pair]] = []
        for occurrence_id, raw in raw_by_id.items():
            fields = corrections.get(occurrence_id, {})
            effective = (
                resolve_effective(raw[0], fields.get("lemma"))[0],
                resolve_effective(raw[1], fields.get("pos"))[0],
            )
            deltas.append((raw, effective))
        return deltas

    def _read_corrections(
        self, session: Session, occurrence_ids: Sequence[int]
    ) -> dict[int, dict[str, str]]:
        """Batched lookup, mirroring
        `annotation_repository.py::_read_corrections` — a fixed-size `IN
        (?, ...)` chunk per query so no single clause overflows SQLite's
        host-parameter limit regardless of correction count."""
        corrections: dict[int, dict[str, str]] = {}
        for start in range(0, len(occurrence_ids), _IN_CLAUSE_BATCH):
            batch = occurrence_ids[start : start + _IN_CLAUSE_BATCH]
            statement = select(
                ManualCorrection.occurrence_id,
                ManualCorrection.field,
                ManualCorrection.corrected_value,
            ).where(ManualCorrection.occurrence_id.in_(batch))
            for occurrence_id, field, value in session.execute(statement):
                corrections.setdefault(occurrence_id, {})[field] = value
        return corrections


def _merge(counts: dict[_Pair, int], deltas: list[tuple[_Pair, _Pair]]) -> dict[_Pair, int]:
    """Move each corrected occurrence from its raw group to its effective
    one (design D1). A group whose count reaches zero is dropped — a pair
    with zero occurrences MUST NOT appear as a group (§2.1 G3)."""
    merged = dict(counts)
    for raw, effective in deltas:
        if raw == effective:
            continue
        merged[raw] = merged.get(raw, 0) - 1
        merged[effective] = merged.get(effective, 0) + 1
    return {key: count for key, count in merged.items() if count > 0}


def _sort_key(item: tuple[_Pair, int]) -> tuple[int, bool, str, bool, str]:
    """Design D5's total order: `occurrence_count DESC`, then the key
    itself, `NULL` sorting before any string in both halves.

    Comparing `None` against `str` raises `TypeError` under Python's
    default ordering, so each key half is split into a presence flag
    (`False` sorts before `True`) plus a filler string used ONLY to break
    ties among present values — the filler is never returned to a caller,
    so an empty-string value and a `NULL` value stay distinguishable on the
    wire (§2.3 N3); this key only decides ORDER, never identity.
    """
    key, count = item
    first, second = key
    return (-count, first is not None, first or "", second is not None, second or "")


def _ordered(merged: dict[_Pair, int]) -> list[VocabularyGroup]:
    return [
        VocabularyGroup(lemma=key[0], pos=key[1], occurrence_count=count)
        for key, count in sorted(merged.items(), key=_sort_key)
    ]
