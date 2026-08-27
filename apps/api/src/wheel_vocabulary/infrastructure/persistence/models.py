"""SQLAlchemy mapped classes for the text-import and annotation capabilities.

`Book`/`Occurrence` map one-to-one onto migration `0002_book_occurrence`;
design §6.1. `raw_text` and `normalized_text` are separate mapped columns and
MUST NOT collapse (Art. V.1, REQ-002-010). Neither table carries a
`deleted_at`, `is_deleted`, or tombstone column — deletion is permanent
(REQ-002-011, H8).

`AnnotationProvenance`/`ManualCorrection` and `Occurrence.lemma` map onto
migration `0003_annotation`; design §P5. `pos`/`lemma` are reserved and always
`None` for every row `002-text-import` writes (ADR-0006, REQ-002-010); this
capability's write repository is the only path that ever sets them, and it
never touches `ManualCorrection` (R2/R3, `test_annotation_write_repository_
isolation.py`). `ManualCorrection` ships with schema only in this capability —
no code path here inserts, updates, or deletes a row in it (R6).

REQ-002-008, REQ-002-009, REQ-002-010, REQ-003-006, REQ-003-007, REQ-003-011,
REQ-003-015.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves `Mapped[datetime]` at runtime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheel_vocabulary.infrastructure.persistence.base import Base

__all__ = ["AnnotationProvenance", "Book", "ManualCorrection", "Occurrence"]


class Book(Base):
    """One imported corpus.

    ``language`` is an ADR-0008 hook, unset in this slice (no detection).
    ``import_status`` is terminal-only: every row here is ``"succeeded"``,
    because a failed import is never persisted (REQ-002-013).
    """

    __tablename__ = "book"
    # Non-unique on purpose: spec §7 excludes re-import dedup by hash (design §6.1).
    __table_args__ = (Index("ix_book_content_hash", "content_hash", unique=False),)

    id: Mapped[int] = mapped_column(primary_key=True)
    language: Mapped[str | None] = mapped_column(default=None)
    content_hash: Mapped[str] = mapped_column(nullable=False)
    import_status: Mapped[str] = mapped_column(nullable=False)
    token_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # No delete cascade configured on the ORM relationship: deletion (cut 3)
    # issues two explicit DELETE statements itself (design §6.2) rather than
    # relying on either this or the FK's `ondelete="CASCADE"`, because SQLite
    # ships with `PRAGMA foreign_keys = OFF` by default.
    occurrences: Mapped[list[Occurrence]] = relationship(back_populates="book")


class Occurrence(Base):
    """One emitted token — the *textual form* and its *normalized form*.

    ``position`` is the zero-based token index (T10), not a byte or character
    offset. ``pos`` is reserved and unpopulated by this capability
    (REQ-002-010); no per-occurrence write here ever sets it.
    """

    __tablename__ = "occurrence"
    # Covering index: serves the whole GET GROUP BY as an ordered index scan, no
    # temp b-tree, no sort (design §6.1). No (book_id, position) unique index —
    # that invariant is proved for free by a pure domain property test instead
    # (design §6.1 rationale).
    __table_args__ = (
        Index("ix_occurrence_book_norm_raw", "book_id", "normalized_text", "raw_text"),
        # Covering index for the vocabulary-browser GROUP BY (design §D1): an
        # ordered index scan over (book_id, lemma, pos), no temp B-tree.
        Index("ix_occurrence_book_lemma_pos", "book_id", "lemma", "pos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # No standalone index here: `ix_occurrence_book_norm_raw` below starts with
    # `book_id`, so it already serves single-column lookups without a second
    # index doubling the write cost at scale (design §6.1).
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id", ondelete="CASCADE"), nullable=False)
    raw_text: Mapped[str] = mapped_column(nullable=False)
    normalized_text: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    pos: Mapped[str | None] = mapped_column(default=None)
    # design §P5, spec §2.1 L1-L6: a third, separately stored value — never
    # derived from `normalized_text`, never collapsed into `pos`. `Text`
    # mirrors `raw_text`/`normalized_text`'s migration column type.
    lemma: Mapped[str | None] = mapped_column(Text(), default=None)

    book: Mapped[Book] = relationship(back_populates="occurrences")


class AnnotationProvenance(Base):
    """Recoverable provenance for one automatically annotated occurrence — spec §2.4.

    One row per occurrence (`occurrence_id` UNIQUE): one analyzer pass
    produces both `pos` and `lemma` under one model identity, so a
    per-`(occurrence, field)` provenance record would duplicate identical
    data and invite the two copies to drift (spec §2.4). The write repository
    deletes and re-inserts this row on every run (R2) — it is never updated
    in place — so `processed_at` always reflects the most recent run.
    """

    __tablename__ = "annotation_provenance"
    __table_args__ = (
        Index("ix_annotation_provenance_occurrence_id", "occurrence_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    occurrence_id: Mapped[int] = mapped_column(
        ForeignKey("occurrence.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    source: Mapped[str] = mapped_column(String(length=64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(length=32), nullable=False)
    # Never a hardcoded default (ADR-0008, REQ-003-003): the language the run
    # was actually invoked with, recorded per annotation, not assumed at read
    # time.
    language: Mapped[str] = mapped_column(String(length=35), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(nullable=False)
    # §2.3 C1-C2: independent, each `NULL` or a float in [0.0, 1.0]. Never
    # fabricated by this layer (C3) — whatever the analyzer reported, verbatim.
    pos_confidence: Mapped[float | None] = mapped_column(default=None)
    lemma_confidence: Mapped[float | None] = mapped_column(default=None)


class ManualCorrection(Base):
    """A user's correction for one `(occurrence, field)` pair — spec §2.5.

    Schema only in this capability (R6): nothing in this codebase inserts,
    updates, or deletes a row here. `annotation_write_repository.py` (task
    3.6-3.8) is proven, structurally, never to import or reference this class
    at all — the write path cannot corrupt what it cannot see.

    `field` holds the bare string `"pos"` or `"lemma"` (spec §2.5) — a plain
    `String` column, not an enum: this table lives in `infrastructure/`, not
    `domain/`, so the ISO-639-shape guard scoped to `domain/annotation.py`
    does not reach it (design §P6).
    """

    __tablename__ = "manual_correction"
    __table_args__ = (
        Index("ix_manual_correction_occurrence_field", "occurrence_id", "field", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    occurrence_id: Mapped[int] = mapped_column(
        ForeignKey("occurrence.id", ondelete="CASCADE"), nullable=False
    )
    field: Mapped[str] = mapped_column(String(length=16), nullable=False)
    corrected_value: Mapped[str] = mapped_column(Text(), nullable=False)
    corrected_at: Mapped[datetime] = mapped_column(nullable=False)
