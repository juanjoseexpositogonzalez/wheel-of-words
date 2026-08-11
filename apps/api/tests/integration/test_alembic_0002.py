"""Alembic integration tests for revision 0002 — Book/Occurrence (T201).

AC-002-11, H3. `alembic upgrade head` must create `book` and `occurrence`;
`alembic downgrade -1` must remove both and return to the `0001_baseline`
empty-schema baseline.

REQ-002-008.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import command
from sqlalchemy import create_engine, inspect, text

if TYPE_CHECKING:
    from collections.abc import Callable

    from alembic.config import Config
    from sqlalchemy import Engine


def test_upgrade_and_downgrade_book_occurrence(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """AC-002-11: upgrade creates both tables; downgrade -1 removes them cleanly."""
    command.upgrade(alembic_config, "head")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    inspector = inspect(engine)
    assert "book" in inspector.get_table_names()
    assert "occurrence" in inspector.get_table_names()

    command.downgrade(alembic_config, "-1")

    inspector = inspect(engine)
    assert "book" not in inspector.get_table_names()
    assert "occurrence" not in inspector.get_table_names()
    with engine.connect() as connection:
        version = connection.execute(text("select version_num from alembic_version")).scalar_one()
    assert version == "0001_baseline"
