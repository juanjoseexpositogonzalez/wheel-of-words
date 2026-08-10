"""Empty-schema baseline.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-01 00:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create no user tables; Alembic records only its version table."""
    pass


def downgrade() -> None:
    """Remove no user tables because the baseline creates none."""
    pass
