"""FastAPI application factory.

Creates and configures the FastAPI application instance. Exposes ``create_app``
as a factory callable for ``uvicorn --factory`` invocation and for test-client
construction.

REQ-001-001, design §6.1, ADR-0002 (hexagonal wiring).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wheel_vocabulary.api.dependencies import get_clock
from wheel_vocabulary.api.errors import register_error_handlers
from wheel_vocabulary.api.routes import health as health_router_module
from wheel_vocabulary.api.routes import imports as imports_router_module
from wheel_vocabulary.infrastructure.version import get_package_version

__all__ = ["create_app", "get_clock"]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Include all routers. Do not store the app at module level so each
    test client gets a fresh instance with clean dependency overrides.
    """
    app = FastAPI(
        title="Wheel Vocabulary API",
        description="Backend for the Wheel of Words vocabulary application.",
        version=get_package_version(),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        # POST is added by the cut that first exposes it (design §14.1). A
        # browser preflight for a method outside this list is answered with 400,
        # so the list has to grow with the surface, not ahead of it.
        allow_methods=["GET", "POST"],
        # Intentionally empty. A multipart upload sends `Content-Type`, which is
        # already in Starlette's SAFELISTED_HEADERS, so the preflight passes
        # without listing it. Do not "fix" this speculatively (Art. VII.6).
        allow_headers=[],
    )
    register_error_handlers(app)
    app.include_router(health_router_module.router)
    app.include_router(imports_router_module.router)
    return app
