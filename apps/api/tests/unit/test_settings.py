"""Unit tests for Settings loader (TB101).

Tests must be RED before infrastructure/settings.py is created.
REQ-001-007, UT-BE-001, UT-BE-002, spec AC-PFB-03.
"""

from pathlib import Path

import pytest

from wheel_vocabulary.infrastructure.settings import Settings, get_settings


def _settings_without_env_file(**overrides: object) -> Settings:
    """Construct Settings without reading a developer-local .env file."""
    return Settings(_env_file=None, **overrides)


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Keep settings-sensitive tests isolated from cached .env reads."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.unit
def test_settings_defaults() -> None:
    """Constructs Settings() in a clean env; asserts sensible defaults."""
    s = _settings_without_env_file()
    assert s.environment == "development"
    assert s.database_url.startswith("sqlite:///")


@pytest.mark.unit
def test_settings_excludes_health_contract_fields() -> None:
    """Health contract fields are not environment-overridable settings."""
    s = _settings_without_env_file()
    assert not hasattr(s, "app_name")
    assert not hasattr(s, "app_version")


@pytest.mark.unit
def test_settings_defaults_ignore_ambient_working_directory_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Direct Settings construction can opt out of ambient .env files."""
    env_file = tmp_path / ".env"
    env_file.write_text("ENVIRONMENT=from-local-env\n")
    monkeypatch.chdir(tmp_path)

    s = _settings_without_env_file()

    assert s.environment == "development"


@pytest.mark.unit
def test_settings_ignores_deprecated_health_contract_env_file_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deprecated APP_NAME/APP_VERSION keys in a local .env do not break Settings."""
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=bad\nAPP_VERSION=9.9.9\nENVIRONMENT=test\n")
    monkeypatch.chdir(tmp_path)

    s = Settings(_env_file=env_file)

    assert s.environment == "test"
    assert not hasattr(s, "app_name")
    assert not hasattr(s, "app_version")


@pytest.mark.unit
def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL env var override is picked up by Settings."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    s = _settings_without_env_file()
    assert s.database_url == "sqlite:///:memory:"


@pytest.mark.unit
def test_settings_log_level_default() -> None:
    """Default log_level is INFO."""
    s = _settings_without_env_file()
    assert s.log_level == "INFO"
