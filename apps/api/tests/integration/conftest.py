"""Fixtures shared by the integration test modules.

REQ-TESTHYG-001, AC-TESTHYG-001, TH02.

Integration tests open real SQLite engines. SQLAlchemy pools the underlying
``sqlite3.Connection`` objects, so an engine that is never disposed keeps those
connections open until the garbage collector reclaims them. That emits a
``ResourceWarning`` at an arbitrary later point, which is why the leak used to
be reported against unrelated tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.book_repository import (
    SqlAlchemyBookRepository,
)
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from sqlalchemy import Engine
    from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def managed_engine() -> Iterator[Callable[[Engine], Engine]]:
    """Register engines for guaranteed disposal at test teardown.

    Pass any freshly constructed engine through this callable and it is
    returned unchanged, after being scheduled for ``dispose()``. Keeping the
    registrar independent of engine construction lets Alembic tests use
    ``create_engine`` directly while the persistence tests keep exercising the
    production ``create_engine_from_url`` factory.
    """
    engines: list[Engine] = []

    def register(engine: Engine) -> Engine:
        engines.append(engine)
        return engine

    yield register

    for engine in engines:
        engine.dispose()


@pytest.fixture
def book_repository(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> SqlAlchemyBookRepository:
    """A `SqlAlchemyBookRepository` bound to an isolated, schema-ready SQLite file.

    File-backed, not `:memory:` — an in-memory SQLite database is scoped to a
    single connection, so a second engine (as production dependency injection
    creates per request) would see an empty database. `Base.metadata.create_all`
    mirrors the precedent already established in `test_base.py`; the same
    schema is what `0002_book_occurrence` creates, so the two never diverge in
    a test run against this fixture (T203/T202 are one mapping).
    """
    engine = managed_engine(create_engine_from_url(f"sqlite:///{tmp_path / 'book_repository.db'}"))
    Base.metadata.create_all(engine)
    return SqlAlchemyBookRepository(create_session_factory(engine))


@pytest.fixture
def annotation_session_factory(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> sessionmaker[Session]:
    """A schema-ready SQLite session factory shared by the annotation write
    and read repository integration tests — design §P3, §P5.

    File-backed for the same reason `book_repository` is: a second repository
    instance (as `test_annotation_read_repository.py` constructs against the
    same database) must see what a prior write actually committed.
    """
    engine = managed_engine(create_engine_from_url(f"sqlite:///{tmp_path / 'annotation.db'}"))
    Base.metadata.create_all(engine)
    return create_session_factory(engine)
