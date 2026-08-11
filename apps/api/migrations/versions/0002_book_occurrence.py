"""Book and Occurrence — persistence for the text-import capability.

Revision ID: 0002_book_occurrence
Revises: 0001_baseline
Create Date: 2026-08-11 00:00:00.000000

Additive only (REQ-002-008). No `(book_id, position)` unique index (design
§6.1 rationale) and no `deleted_at` / `is_deleted` / tombstone column anywhere
(REQ-002-011, hook H8) — a soft delete is forbidden by design, not merely
unshipped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0002_book_occurrence"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create `book` and `occurrence`, plus their two indexes."""
    op.create_table(
        "book",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("language", sa.String(length=35), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("import_status", sa.String(length=16), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_book_content_hash", "book", ["content_hash"], unique=False)

    op.create_table(
        "occurrence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("book.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("pos", sa.String(length=16), nullable=True),
    )
    op.create_index(
        "ix_occurrence_book_norm_raw",
        "occurrence",
        ["book_id", "normalized_text", "raw_text"],
    )


def downgrade() -> None:
    """Drop both tables, returning the schema to the `0001_baseline` state."""
    op.drop_index("ix_occurrence_book_norm_raw", table_name="occurrence")
    op.drop_table("occurrence")
    op.drop_index("ix_book_content_hash", table_name="book")
    op.drop_table("book")
