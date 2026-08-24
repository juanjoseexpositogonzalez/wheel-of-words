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


@pytest.mark.unit
def test_max_import_size_bytes_defaults_to_four_mebibytes() -> None:
    """AC-002-03: the documented default is 4 MiB, expressed in bytes."""
    s = _settings_without_env_file()

    assert s.max_import_size_bytes == 4194304


@pytest.mark.unit
def test_max_import_size_bytes_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-002-03: MAX_IMPORT_SIZE_BYTES overrides the default."""
    monkeypatch.setenv("MAX_IMPORT_SIZE_BYTES", "64")

    s = _settings_without_env_file()

    assert s.max_import_size_bytes == 64


@pytest.mark.unit
def test_annotation_language_defaults_to_english() -> None:
    """REQ-003-003: the default language is configuration, not a hardcode
    reachable from the port/domain/schema (design §P4) — it lives here."""
    s = _settings_without_env_file()

    assert s.annotation_language == "en"


@pytest.mark.unit
def test_annotation_language_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANNOTATION_LANGUAGE", "fr")

    s = _settings_without_env_file()

    assert s.annotation_language == "fr"


@pytest.mark.unit
def test_analyzer_models_defaults_to_the_installed_english_pipeline() -> None:
    """design §P4: adding a second language is config + adapter, no
    migration — this dict is the one place a language code maps to a
    concrete pipeline name."""
    s = _settings_without_env_file()

    assert s.analyzer_models == {"en": "en_core_web_sm"}


@pytest.mark.unit
def test_analyzer_models_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """`pydantic-settings` parses a dict field from a JSON env value."""
    monkeypatch.setenv("ANALYZER_MODELS", '{"en": "en_core_web_sm", "fr": "fr_core_news_sm"}')

    s = _settings_without_env_file()

    assert s.analyzer_models == {"en": "en_core_web_sm", "fr": "fr_core_news_sm"}
