"""Integration tests for SQLAlchemy engine and session factories.

REQ-001-005, REQ-001-NF-003, design §6.5, TB201.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from sqlalchemy import Engine


@pytest.mark.integration
def test_create_engine_from_url_connects_to_sqlite_database(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """Engine factory creates a local SQLite connection without public network access."""
    database_url = f"sqlite:///{tmp_path / 'app.db'}"

    engine = managed_engine(create_engine_from_url(database_url))

    with engine.connect() as connection:
        assert connection.execute(text("select 1")).scalar_one() == 1


@pytest.mark.integration
def test_create_engine_from_url_uses_wal_for_local_sqlite_files(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """WU2b: file-backed SQLite engines use WAL so readers do not starve writers."""
    engine = managed_engine(create_engine_from_url(f"sqlite:///{tmp_path / 'wal.db'}"))

    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"


@pytest.mark.integration
def test_create_session_factory_returns_working_sessions(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """Session factory binds sessions to the supplied SQLite engine."""
    engine = managed_engine(create_engine_from_url(f"sqlite:///{tmp_path / 'session.db'}"))
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        assert isinstance(session, Session)
        assert session.execute(text("select 42")).scalar_one() == 42
