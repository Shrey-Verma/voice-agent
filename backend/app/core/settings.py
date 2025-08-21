"""Application settings and configuration."""

from enum import Enum
from functools import lru_cache
from typing import Self

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    app_env: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"

    # Supabase
    supabase_url: str | None = None
    supabase_key: str | None = None

    # OpenAI
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @classmethod
    def parse_env(cls) -> Self:
        return cls.model_validate({})


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings.parse_env()


settings = get_settings()