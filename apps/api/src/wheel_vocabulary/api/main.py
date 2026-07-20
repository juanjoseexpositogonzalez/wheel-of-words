"""FastAPI application factory.

Creates and configures the FastAPI application instance. Exposes ``create_app``
as a factory callable for ``uvicorn --factory`` invocation and for test-client
construction.

REQ-001-001, design §6.1, ADR-0002 (hexagonal wiring).
"""

from __future__ import annotations

from fastapi import FastAPI

from wheel_vocabulary.api.dependencies import get_clock
from wheel_vocabulary.api.routes import health as health_router_module

__all__ = ["create_app", "get_clock"]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Include all routers. Do not store the app at module level so each
    test client gets a fresh instance with clean dependency overrides.
    """
    app = FastAPI(
        title="Wheel Vocabulary API",
        description="Backend for the Wheel of Words vocabulary application.",
        version="0.1.0",
    )
    app.include_router(health_router_module.router)
    return app
