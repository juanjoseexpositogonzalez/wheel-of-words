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

    All fields can be overridden by environment variables (case-insensitive).
    An optional .env file is loaded if present in the current working directory.
    """

    app_name: str = "wheel-vocabulary-api"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "sqlite:///./data/wheel_vocabulary.db"
    cors_origins: list[str] = []
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (reads env once at first call)."""
    return Settings()
