"""Application configuration.

All runtime configuration is loaded from environment variables (or a local
.env file). Nothing here should ever contain a hardcoded secret — secrets
live in .env, which is git-ignored.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SmartEval AI"
    environment: str = "development"
    debug: bool = True

    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "sqlite:///./smartevalai.db"

    gemini_api_key: str = ""

    max_upload_size_mb: int = 15
    allowed_upload_extensions: tuple[str, ...] = (".pdf", ".jpg", ".jpeg", ".png")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()