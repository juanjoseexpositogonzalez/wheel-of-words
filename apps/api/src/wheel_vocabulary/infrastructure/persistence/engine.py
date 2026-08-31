"""SQLAlchemy engine and session factory helpers.

REQ-001-005, REQ-001-NF-003, design §6.5, TB202.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

__all__ = ["create_engine_from_url", "create_session_factory"]


def create_engine_from_url(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the configured database URL."""
    engine = create_engine(database_url, future=True)
    if engine.url.get_backend_name() == "sqlite" and engine.url.database not in {
        None,
        "",
        ":memory:",
    }:

        @event.listens_for(engine, "connect")
        def _enable_wal(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
            finally:
                cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a typed session factory bound to ``engine``."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
