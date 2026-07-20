"""API-layer tests for GET /api/v1/health (TB110).

Uses FastAPI TestClient with dependency override for Clock injection.
Tests must be RED before api/main.py and api/routes/health.py are created.

REQ-001-001, REQ-001-002, REQ-PFB-CONTRACT-01, AC-PFB-10, API-BE-001.
design §6.1, design §6.2.
"""

from __future__ import annotations

import importlib.resources
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import jsonschema
import pytest
from fastapi.testclient import TestClient

from wheel_vocabulary.api.main import create_app, get_clock

# Fixed time used by FrozenClock in all timestamp-sensitive tests
_FIXED_DT = datetime(2026, 7, 20, 14, 32, 0, 123000, tzinfo=UTC)
_FIXED_TIMESTAMP = "2026-07-20T14:32:00.123Z"


class _FrozenClock:
    """Local test double — returns a fixed UTC datetime from now_utc()."""

    def __init__(self, fixed_dt: datetime) -> None:
        self._fixed_dt = fixed_dt

    def now_utc(self) -> datetime:
        return self._fixed_dt


@pytest.fixture
def client() -> TestClient:
    """TestClient with FrozenClock injected via FastAPI dependency override."""
    app = create_app()
    frozen = _FrozenClock(_FIXED_DT)
    app.dependency_overrides[get_clock] = lambda: frozen
    return TestClient(app)


@pytest.mark.unit
def test_health_status_200(client: TestClient) -> None:
    """GET /api/v1/health returns HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.unit
def test_health_response_body(client: TestClient) -> None:
    """Response body contains exactly the required keys."""
    response = client.get("/api/v1/health")
    body = response.json()
    assert "status" in body
    assert "service" in body
    assert "version" in body
    assert "timestamp" in body


@pytest.mark.unit
def test_health_status_ok(client: TestClient) -> None:
    """body['status'] equals 'ok'."""
    response = client.get("/api/v1/health")
    assert response.json()["status"] == "ok"


@pytest.mark.unit
def test_health_service_name(client: TestClient) -> None:
    """body['service'] equals 'wheel-vocabulary-api'."""
    response = client.get("/api/v1/health")
    assert response.json()["service"] == "wheel-vocabulary-api"


@pytest.mark.unit
def test_health_version_matches_package(client: TestClient) -> None:
    """body['version'] matches the version in pyproject.toml."""
    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    expected_version = data["project"]["version"]

    response = client.get("/api/v1/health")
    assert response.json()["version"] == expected_version


@pytest.mark.unit
def test_health_timestamp_frozen(client: TestClient) -> None:
    """With FrozenClock injected, body['timestamp'] equals the fixed ISO-8601 string."""
    response = client.get("/api/v1/health")
    assert response.json()["timestamp"] == _FIXED_TIMESTAMP


@pytest.mark.unit
def test_health_schema_validation(client: TestClient) -> None:
    """Response body validates against health.v1.json (spec §9 Hook 4)."""
    schema_path = importlib.resources.files("wheel_vocabulary.api.schemas").joinpath(
        "health.v1.json"
    )
    schema = json.loads(schema_path.read_text())
    response = client.get("/api/v1/health")
    # Should not raise
    jsonschema.validate(response.json(), schema)


@pytest.mark.unit
def test_health_x_schema_version_header(client: TestClient) -> None:
    """Response carries the X-Schema-Version: 1 header per design §6.3."""
    response = client.get("/api/v1/health")
    assert response.headers.get("x-schema-version") == "1"


@pytest.mark.unit
def test_health_no_extra_fields(client: TestClient) -> None:
    """Response body has exactly the four documented keys — no extras."""
    response = client.get("/api/v1/health")
    assert set(response.json().keys()) == {"status", "service", "version", "timestamp"}
