"""Alembic integration tests for the SPEC-001 empty baseline.

REQ-001-006, REQ-PFB-CONTRACT-002, AC-PFB-11, TB206.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import command
from sqlalchemy import create_engine, inspect, text

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from alembic.config import Config
    from sqlalchemy import Engine


def test_alembic_upgrade_to_the_baseline_revision_creates_only_version_table(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """The SPEC-001 baseline revision alone still creates nothing.

    Pinned against the named revision, not `head`: since `0002_book_occurrence`
    (SPEC-002 cut 2) landed, `head` legitimately creates `book`/`occurrence`
    too. `tests/integration/test_alembic_0002.py` covers that revision.
    """
    command.upgrade(alembic_config, "0001_baseline")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    inspector = inspect(engine)

    assert inspector.get_table_names() == ["alembic_version"]
    with engine.connect() as connection:
        version = connection.execute(text("select version_num from alembic_version")).scalar_one()
    assert version == "0001_baseline"


def test_alembic_downgrade_base_removes_baseline_version(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """The baseline downgrade path succeeds without creating user tables."""
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    inspector = inspect(engine)

    assert inspector.get_table_names() == ["alembic_version"]
    with engine.connect() as connection:
        rows = connection.execute(text("select version_num from alembic_version")).all()
    assert rows == []


def test_alembic_upgrade_creates_missing_sqlite_parent_directory(
    alembic_config: Config,
    tmp_path: Path,
) -> None:
    """The default file-backed SQLite migration works when the data dir is absent."""
    database_path = tmp_path / "missing" / "app.db"
    alembic_config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(alembic_config, "head")

    assert database_path.exists()
