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

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from sqlalchemy import Engine


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
