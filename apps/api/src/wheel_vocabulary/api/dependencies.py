"""FastAPI dependency providers.

Centralises all ``Depends(...)`` factories so routes, tests, and the app
factory can import from a single, circular-import-safe location.

ADR-0002: infrastructure adapters are wired here, not imported directly in routes.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from wheel_vocabulary.application.clock import Clock  # noqa: TC001 – runtime for FastAPI
from wheel_vocabulary.application.imports.ports import (
    BookRepository,  # noqa: TC001 – runtime for FastAPI
    TextExtractor,  # noqa: TC001 – runtime for FastAPI
)
from wheel_vocabulary.application.imports.use_cases import ImportText, ReadImport
from wheel_vocabulary.infrastructure.clock import SystemClock
from wheel_vocabulary.infrastructure.persistence.book_repository import (
    SqlAlchemyBookRepository,
)
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)
from wheel_vocabulary.infrastructure.settings import Settings, get_settings
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor
from wheel_vocabulary.infrastructure.version import get_package_version

__all__ = [
    "Settings",
    "get_app_version",
    "get_book_repository",
    "get_clock",
    "get_import_text",
    "get_read_import",
    "get_settings",
    "get_text_extractor",
]


def get_clock() -> Clock:
    """Dependency provider: returns the production SystemClock.

    Tests override this via ``app.dependency_overrides[get_clock]`` to inject
    a FrozenClock without touching the route implementation.
    """
    return SystemClock()


def get_app_version() -> str:
    """Dependency provider: returns the installed wheel-vocabulary version."""
    return get_package_version()


def get_text_extractor() -> TextExtractor:
    """Dependency provider: returns the strict UTF-8 extractor."""
    return PlainTextExtractor()


def get_book_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> BookRepository:
    """Dependency provider: returns a repository bound to the configured database.

    A fresh engine per resolution — this is a local, single-user desktop app
    (ADR-0005), not a pooled server, so the cost is negligible and there is no
    speculative pool configuration to maintain (Art. VII.6). Tests override
    this via ``app.dependency_overrides[get_book_repository]`` to inject an
    isolated, schema-ready SQLite database instead of the configured one.
    """
    engine = create_engine_from_url(settings.database_url)
    return SqlAlchemyBookRepository(create_session_factory(engine))


def get_import_text(
    extractor: Annotated[TextExtractor, Depends(get_text_extractor)],
    repository: Annotated[BookRepository, Depends(get_book_repository)],
    clock: Annotated[Clock, Depends(get_clock)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ImportText:
    """Dependency provider: assembles the import use case from its ports.

    Tests override this to run the ordered gate against a small size limit
    without touching the environment.
    """
    return ImportText(
        extractor=extractor,
        max_size_bytes=settings.max_import_size_bytes,
        repository=repository,
        clock=clock,
    )


def get_read_import(
    repository: Annotated[BookRepository, Depends(get_book_repository)],
) -> ReadImport:
    """Dependency provider: assembles the read use case from its port."""
    return ReadImport(repository=repository)
