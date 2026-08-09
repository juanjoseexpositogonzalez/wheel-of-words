"""Security regression tests for the public health contract (TD08)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from wheel_vocabulary.api.main import create_app


def test_health_response_exposes_only_the_public_contract_fields() -> None:
    response = TestClient(create_app()).get("/api/v1/health")

    assert response.status_code == 200
    assert set(response.json()) == {"status", "service", "version", "timestamp"}


def test_health_response_does_not_leak_configuration_names_or_values(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///private.db")
    monkeypatch.setenv("WHEEL_TEST_SECRET", "do-not-expose")

    response = TestClient(create_app()).get("/api/v1/health")
    body = response.text.lower()

    assert "database_url" not in body
    assert "private.db" not in body
    assert "do-not-expose" not in body
