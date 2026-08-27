"""Covering index for the vocabulary group query — design §Migration/Rollout.

Revision ID: 0004_vocabulary_group_index
Revises: 0003_annotation
Create Date: 2026-08-27 00:00:00.000000

Additive only: adds `ix_occurrence_book_lemma_pos` on
`occurrence(book_id, lemma, pos)` so the vocabulary-browser `GROUP BY` runs as
an ordered index scan (design §D1). No column or table is created, altered,
or dropped; `downgrade()` removes only the index, returning the schema to the
`0003_annotation` baseline exactly (REQ-005-009).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0004_vocabulary_group_index"
down_revision: str | None = "0003_annotation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the `(book_id, lemma, pos)` covering index on `occurrence`."""
    op.create_index(
        "ix_occurrence_book_lemma_pos",
        "occurrence",
        ["book_id", "lemma", "pos"],
    )


def downgrade() -> None:
    """Drop the index, returning the schema to `0003_annotation`."""
    op.drop_index("ix_occurrence_book_lemma_pos", table_name="occurrence")
