"""FastAPI dependency providers.

Centralises all ``Depends(...)`` factories so routes, tests, and the app
factory can import from a single, circular-import-safe location.

ADR-0002: infrastructure adapters are wired here, not imported directly in routes.
"""

from __future__ import annotations

from wheel_vocabulary.application.clock import Clock  # noqa: TC001 – runtime for FastAPI
from wheel_vocabulary.infrastructure.clock import SystemClock

__all__ = ["get_clock"]


def get_clock() -> Clock:
    """Dependency provider: returns the production SystemClock.

    Tests override this via ``app.dependency_overrides[get_clock]`` to inject
    a FrozenClock without touching the route implementation.
    """
    return SystemClock()
