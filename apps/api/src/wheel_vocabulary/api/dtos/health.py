"""HealthResponse DTO for GET /api/v1/health.

A strict Pydantic model that corresponds one-to-one with the JSON schema
health.v1.json. Extra fields are forbidden to guarantee schema conformance.

REQ-001-002, REQ-PFB-CONTRACT-01, design §6.3.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

__all__ = ["HealthResponse"]


class HealthResponse(BaseModel):
    """Response body for GET /api/v1/health.

    Fields match CONTRACT-1 exactly:
    - ``status``: literal "ok"
    - ``service``: service name string
    - ``version``: semver string from package metadata
    - ``timestamp``: ISO-8601 UTC ms string
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
    version: str
    timestamp: str
