"""Unit tests for HealthResponse DTO (TB108).

Tests must be RED before api/dtos/health.py is created.
REQ-001-002, REQ-PFB-CONTRACT-01, design §6.3, UT-BE-003.
"""

from __future__ import annotations

import importlib.resources
import json

import jsonschema
import pytest
from pydantic import ValidationError

from wheel_vocabulary.api.dtos.health import HealthResponse


@pytest.mark.unit
def test_health_response_valid_construction() -> None:
    """HealthResponse constructs successfully with all required fields."""
    dto = HealthResponse(
        status="ok",
        service="wheel-vocabulary-api",
        version="0.1.0",
        timestamp="2026-07-20T00:00:00.000Z",
    )
    assert dto.status == "ok"
    assert dto.service == "wheel-vocabulary-api"
    assert dto.version == "0.1.0"
    assert dto.timestamp == "2026-07-20T00:00:00.000Z"


@pytest.mark.unit
def test_health_response_schema_validation() -> None:
    """HealthResponse.model_dump() validates against health.v1.json schema."""
    dto = HealthResponse(
        status="ok",
        service="wheel-vocabulary-api",
        version="0.1.0",
        timestamp="2026-07-20T00:00:00.000Z",
    )
    schema_path = importlib.resources.files("wheel_vocabulary.api.schemas").joinpath(
        "health.v1.json"
    )
    schema = json.loads(schema_path.read_text())
    # Should not raise
    jsonschema.validate(dto.model_dump(), schema)


@pytest.mark.unit
def test_health_response_rejects_extra_fields() -> None:
    """HealthResponse raises ValidationError when constructed with extra fields."""
    with pytest.raises(ValidationError, match="extra_field"):
        HealthResponse(  # type: ignore[call-arg]
            status="ok",
            service="wheel-vocabulary-api",
            version="0.1.0",
            timestamp="2026-07-20T00:00:00.000Z",
            extra_field="should-fail",
        )
