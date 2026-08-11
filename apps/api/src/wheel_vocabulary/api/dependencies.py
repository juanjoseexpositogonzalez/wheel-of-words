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
    TextExtractor,  # noqa: TC001 – runtime for FastAPI
)
from wheel_vocabulary.application.imports.use_cases import ImportText
from wheel_vocabulary.infrastructure.clock import SystemClock
from wheel_vocabulary.infrastructure.settings import Settings, get_settings
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor
from wheel_vocabulary.infrastructure.version import get_package_version

__all__ = [
    "Settings",
    "get_app_version",
    "get_clock",
    "get_import_text",
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


def get_import_text(
    extractor: Annotated[TextExtractor, Depends(get_text_extractor)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ImportText:
    """Dependency provider: assembles the import use case from its ports.

    Tests override this to run the ordered gate against a small size limit
    without touching the environment.
    """
    return ImportText(extractor=extractor, max_size_bytes=settings.max_import_size_bytes)
