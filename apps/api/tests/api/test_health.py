"""API-layer tests for GET /api/v1/health (TB110).

Uses FastAPI TestClient with dependency override for Clock injection.
Tests must be RED before api/main.py and api/routes/health.py are created.

REQ-001-001, REQ-001-002, REQ-PFB-CONTRACT-01, AC-PFB-10, API-BE-001.
design §6.1, design §6.2.
"""

from __future__ import annotations

import importlib.resources
import json
from datetime import UTC, datetime, timedelta, timezone

import jsonschema
import pytest
from fastapi.testclient import TestClient

from wheel_vocabulary.api.dependencies import get_app_version, get_clock, get_settings
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.api.routes.health import _format_timestamp

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
    """TestClient with deterministic dependencies injected via FastAPI overrides."""
    app = create_app()
    frozen = _FrozenClock(_FIXED_DT)
    app.dependency_overrides[get_clock] = lambda: frozen
    app.dependency_overrides[get_app_version] = lambda: "9.8.7"
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
def test_health_version_uses_injected_version_provider(client: TestClient) -> None:
    """body['version'] comes from get_app_version dependency injection."""
    response = client.get("/api/v1/health")
    assert response.json()["version"] == "9.8.7"


@pytest.mark.unit
def test_health_does_not_resolve_settings_dependency() -> None:
    """GET /health does not read settings from environment or .env files."""
    app = create_app()
    app.dependency_overrides[get_clock] = lambda: _FrozenClock(_FIXED_DT)
    app.dependency_overrides[get_app_version] = lambda: "9.8.7"

    def fail_if_resolved() -> None:
        raise AssertionError("Health route must not resolve settings.")

    app.dependency_overrides[get_settings] = fail_if_resolved

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["service"] == "wheel-vocabulary-api"


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


@pytest.mark.unit
def test_format_timestamp_rejects_naive_datetime() -> None:
    """_format_timestamp rejects naive datetimes before appending Z."""
    naive = datetime(2026, 7, 20, 14, 32, 0, 123000)

    with pytest.raises(ValueError, match="UTC-aware"):
        _format_timestamp(naive)


@pytest.mark.unit
def test_format_timestamp_rejects_non_utc_datetime() -> None:
    """_format_timestamp rejects aware datetimes that are not UTC."""
    non_utc = datetime(
        2026,
        7,
        20,
        14,
        32,
        0,
        123000,
        tzinfo=timezone(timedelta(hours=2)),
    )

    with pytest.raises(ValueError, match="UTC-aware"):
        _format_timestamp(non_utc)
