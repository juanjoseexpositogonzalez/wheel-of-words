"""Occurrence-level synthetic data for the vocabulary response benchmark.

The fixture creates rows directly rather than deriving tokens from text: the
benchmark exercises the grouped read over annotated occurrences and seeded
manual corrections. Values are synthetic identifiers, never imported prose.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import insert, select

from wheel_vocabulary.infrastructure.persistence.models import Book, ManualCorrection, Occurrence

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

__all__ = ["SeededVocabularyBenchmarkCorpus", "seed_vocabulary_benchmark_corpus"]

_VOCABULARY_SIZE = 30_000
_HOMOGRAPH_PERCENT = 12
_UNANNOTATED_PERCENT = 2
_INSERT_BATCH_SIZE = 10_000
_UPOS_TAGS = ("NOUN", "VERB", "ADJ", "ADV", "PROPN", "AUX")
_CREATED_AT = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class SeededVocabularyBenchmarkCorpus:
    """The persisted benchmark corpus and its deterministic composition."""

    book_id: int
    occurrence_count: int
    homograph_lemma_count: int
    unannotated_count: int
    manual_correction_count: int


def seed_vocabulary_benchmark_corpus(
    session_factory: sessionmaker[Session],
    *,
    occurrence_count: int,
    manual_correction_count: int,
    seed: int = 20260830,
) -> SeededVocabularyBenchmarkCorpus:
    """Persist a deterministic Zipfian occurrence corpus and correction rows."""
    if occurrence_count < 1:
        msg = "occurrence_count must be positive"
        raise ValueError(msg)
    if not 0 <= manual_correction_count <= occurrence_count:
        msg = "manual_correction_count must be within the occurrence count"
        raise ValueError(msg)

    rng = random.Random(seed)  # noqa: S311 - deterministic synthetic fixture
    cumulative_weights = list(
        itertools.accumulate(1 / rank for rank in range(1, _VOCABULARY_SIZE + 1))
    )
    unannotated_count = 0

    with session_factory() as session:
        book = Book(
            content_hash="vocabulary-benchmark".ljust(64, "0"),
            import_status="succeeded",
            token_count=occurrence_count,
            created_at=_CREATED_AT,
        )
        session.add(book)
        session.flush()
        book_id = book.id

        for start in range(0, occurrence_count, _INSERT_BATCH_SIZE):
            positions = range(start, min(start + _INSERT_BATCH_SIZE, occurrence_count))
            ranks = rng.choices(
                range(_VOCABULARY_SIZE),
                cum_weights=cumulative_weights,
                k=len(positions),
            )
            rows = []
            for position, rank in zip(positions, ranks, strict=True):
                if position % (100 // _UNANNOTATED_PERCENT) == 0:
                    lemma = None
                    pos = None
                    unannotated_count += 1
                else:
                    lemma = f"l{rank}"
                    primary_pos = _UPOS_TAGS[rank % len(_UPOS_TAGS)]
                    if rank % 100 < _HOMOGRAPH_PERCENT and position % 2:
                        pos = _UPOS_TAGS[(rank + 1) % len(_UPOS_TAGS)]
                    else:
                        pos = primary_pos
                rows.append(
                    {
                        "book_id": book_id,
                        "raw_text": f"t{position}",
                        "normalized_text": f"t{position}",
                        "position": position,
                        "lemma": lemma,
                        "pos": pos,
                    }
                )
            session.execute(insert(Occurrence), rows)

        correction_ids = list(
            session.scalars(
                select(Occurrence.id)
                .where(Occurrence.book_id == book_id)
                .order_by(Occurrence.position)
                .limit(manual_correction_count)
            )
        )
        session.execute(
            insert(ManualCorrection),
            [
                {
                    "occurrence_id": occurrence_id,
                    "field": "lemma",
                    "corrected_value": f"l{(index + 17) % _VOCABULARY_SIZE}",
                    "corrected_at": _CREATED_AT,
                }
                for index, occurrence_id in enumerate(correction_ids)
            ],
        )
        session.commit()

    return SeededVocabularyBenchmarkCorpus(
        book_id=book_id,
        occurrence_count=occurrence_count,
        homograph_lemma_count=_VOCABULARY_SIZE * _HOMOGRAPH_PERCENT // 100,
        unannotated_count=unannotated_count,
        manual_correction_count=manual_correction_count,
    )
