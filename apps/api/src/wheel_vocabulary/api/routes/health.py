"""Health route — GET /api/v1/health.

Returns a structured JSON response confirming the server is up, along with
its version and a UTC timestamp. Injects Clock and Settings via FastAPI
Depends() so tests can override them without touching this module.

REQ-001-001, REQ-001-002, REQ-PFB-CONTRACT-01, design §6.1, NDD-06.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 – used at runtime in _format_timestamp
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from wheel_vocabulary.api.dependencies import get_clock
from wheel_vocabulary.api.dtos.health import HealthResponse
from wheel_vocabulary.application.clock import Clock  # noqa: TC001 – FastAPI resolves at runtime
from wheel_vocabulary.infrastructure.settings import Settings, get_settings

__all__ = ["router"]

router = APIRouter(prefix="/api/v1")


def _format_timestamp(dt: datetime) -> str:
    """Format a datetime as ISO-8601 UTC with millisecond precision.

    Contract: ``YYYY-MM-DDTHH:MM:SS.sssZ`` per design §6.2.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


@router.get("/health", response_model=HealthResponse)
def health(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> HealthResponse:
    """Return the application health status.

    The route is intentionally thin — no domain logic, no infrastructure I/O
    beyond reading the injected clock and settings. Constitution Art. VII.4.
    """
    response.headers["X-Schema-Version"] = "1"
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=_format_timestamp(clock.now_utc()),
    )
