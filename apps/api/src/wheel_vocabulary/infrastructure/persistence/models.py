"""SQLAlchemy mapped classes for the text-import capability — design §6.1.

Maps one-to-one onto migration `0002_book_occurrence`. `raw_text` and
`normalized_text` are separate mapped columns and MUST NOT collapse (Art. V.1,
REQ-002-010). `pos` is reserved and always `None` for every row this capability
writes (ADR-0006, REQ-002-010). Neither table carries a `deleted_at`,
`is_deleted`, or tombstone column — deletion is permanent (REQ-002-011, H8).

REQ-002-008, REQ-002-009, REQ-002-010.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves `Mapped[datetime]` at runtime

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheel_vocabulary.infrastructure.persistence.base import Base

__all__ = ["Book", "Occurrence"]


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

    book: Mapped[Book] = relationship(back_populates="occurrences")
