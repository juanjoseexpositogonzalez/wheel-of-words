"""Shared test fixtures for the wheel_vocabulary test suite.

Fixture placement policy:
- Fixtures scoped to a single test module belong in that module.
- Fixtures shared across two or more modules in the same sub-directory belong
  in a conftest.py within that sub-directory.
- Fixtures shared across sub-directories (smoke/, unit/, api/, integration/)
  belong here at the tests/ root.

Slice A: this file is infrastructure scaffolding only.
Slice B adds: FrozenClock, TestClient factory, tmp_db_url, alembic_config.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic.config import Config


class FrozenClock:
    """Test double that returns a fixed datetime from now_utc().

    Used to inject deterministic timestamps into the health route
    so tests can assert exact timestamp values without wall-clock coupling.

    design §6.2 (test injection), TB104.
    """

    def __init__(self, fixed_dt: datetime | None = None) -> None:
        if fixed_dt is None:
            fixed_dt = datetime(2026, 7, 20, 12, 0, 0, 0, tzinfo=UTC)
        self._fixed_dt = fixed_dt

    def now_utc(self) -> datetime:
        """Return the fixed datetime this instance was constructed with."""
        return self._fixed_dt


@pytest.fixture
def frozen_clock() -> FrozenClock:
    """Provide a FrozenClock with a fixed UTC timestamp for tests."""
    return FrozenClock(datetime(2026, 7, 20, 12, 0, 0, 0, tzinfo=UTC))


@pytest.fixture
def sqlite_database_url(tmp_path: Path) -> str:
    """Return an isolated SQLite database URL for integration tests."""
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def alembic_config(sqlite_database_url: str) -> Config:
    """Build an Alembic config bound to an isolated SQLite database."""
    api_root = Path(__file__).resolve().parents[1]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "migrations"))
    config.set_main_option("sqlalchemy.url", sqlite_database_url)
    return config
