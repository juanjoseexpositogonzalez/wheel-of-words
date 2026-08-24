"""Lemma, annotation provenance and manual correction — design §P5.

Revision ID: 0003_annotation
Revises: 0002_book_occurrence
Create Date: 2026-08-24 00:00:00.000000

Additive only (REQ-003-015): adds `occurrence.lemma`, `annotation_provenance`
and `manual_correction`. Nothing `002-text-import` created is dropped,
renamed, retyped, or made non-nullable. `manual_correction` ships with
schema only — no code path in this capability writes a row into it (R6).

Both `op.batch_alter_table` for the column add and the column drop: a bare
`ALTER TABLE ... DROP COLUMN` needs SQLite >= 3.35, and `downgrade()` must
work unconditionally (AC-003-16).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0003_annotation"
down_revision: str | None = "0002_book_occurrence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add `occurrence.lemma`, `annotation_provenance` and `manual_correction`."""
    with op.batch_alter_table("occurrence") as batch_op:
        batch_op.add_column(sa.Column("lemma", sa.Text(), nullable=True))

    op.create_table(
        "annotation_provenance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "occurrence_id",
            sa.Integer(),
            sa.ForeignKey("occurrence.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=35), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.Column("pos_confidence", sa.Float(), nullable=True),
        sa.Column("lemma_confidence", sa.Float(), nullable=True),
    )
    op.create_index(
        "ix_annotation_provenance_occurrence_id",
        "annotation_provenance",
        ["occurrence_id"],
        unique=True,
    )

    op.create_table(
        "manual_correction",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "occurrence_id",
            sa.Integer(),
            sa.ForeignKey("occurrence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field", sa.String(length=16), nullable=False),
        sa.Column("corrected_value", sa.Text(), nullable=False),
        sa.Column("corrected_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_manual_correction_occurrence_field",
        "manual_correction",
        ["occurrence_id", "field"],
        unique=True,
    )


def downgrade() -> None:
    """Drop all three additions, returning the schema to `0002_book_occurrence`."""
    op.drop_index("ix_manual_correction_occurrence_field", table_name="manual_correction")
    op.drop_table("manual_correction")

    op.drop_index("ix_annotation_provenance_occurrence_id", table_name="annotation_provenance")
    op.drop_table("annotation_provenance")

    with op.batch_alter_table("occurrence") as batch_op:
        batch_op.drop_column("lemma")
