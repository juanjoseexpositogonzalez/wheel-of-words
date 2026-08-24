"""Application settings loaded from environment variables.

Uses pydantic-settings to read configuration from environment and .env files.
REQ-001-007, REQ-001-NF-006, design §6.4, NDD-07.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "get_settings"]


class Settings(BaseSettings):
    """Centralised application configuration.

    Environment-specific fields can be overridden by environment variables
    (case-insensitive). Public health contract fields are intentionally not
    settings because they must not drift from the JSON schema contract.
    """

    environment: str = "development"
    database_url: str = "sqlite:///./data/wheel_vocabulary.db"
    cors_origins: list[str] = []
    log_level: str = "INFO"

    # REQ-002-003: 4 MiB. Above War and Peace (~3.2 MB of public-domain plain
    # text) and below the synchronous-request timeout risk the design quantified
    # for 10 MiB. Overridable with MAX_IMPORT_SIZE_BYTES.
    max_import_size_bytes: int = 4_194_304

    # REQ-003-003, design §P4: the default annotation language is
    # configuration, never a hardcode inside the port, the domain value
    # object, or the persisted schema — this field is the ONE place a
    # default lives. `analyzer_models` maps a language code to the pipeline
    # package name `infrastructure/nlp/registry.py` loads; adding a second
    # language is a config + adapter change, no migration.
    annotation_language: str = "en"
    analyzer_models: dict[str, str] = {"en": "en_core_web_sm"}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (reads env once at first call)."""
    return Settings()
