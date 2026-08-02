"""Alembic environment for wheel-vocabulary migrations."""

from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import make_url

from wheel_vocabulary.infrastructure.persistence.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def ensure_sqlite_parent_directory(database_url: str) -> None:
    """Create the parent directory for file-backed SQLite URLs."""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or url.database in (None, ":memory:"):
        return

    Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def run_migrations_offline() -> None:
    """Run migrations without opening a DBAPI connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live SQLAlchemy connection."""
    ensure_sqlite_parent_directory(config.get_main_option("sqlalchemy.url"))
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
