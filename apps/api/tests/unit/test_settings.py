"""Unit tests for Settings loader (TB101).

Tests must be RED before infrastructure/settings.py is created.
REQ-001-007, UT-BE-001, UT-BE-002, spec AC-PFB-03.
"""

import pytest

from wheel_vocabulary.infrastructure.settings import Settings


@pytest.mark.unit
def test_settings_defaults() -> None:
    """Constructs Settings() in a clean env; asserts sensible defaults."""
    s = Settings()
    assert s.app_name == "wheel-vocabulary-api"
    assert s.environment == "development"
    assert s.database_url.startswith("sqlite:///")


@pytest.mark.unit
def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL env var override is picked up by Settings."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    s = Settings()
    assert s.database_url == "sqlite:///:memory:"


@pytest.mark.unit
def test_settings_log_level_default() -> None:
    """Default log_level is INFO."""
    s = Settings()
    assert s.log_level == "INFO"
