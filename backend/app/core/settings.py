"""Application settings configuration."""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TOKEN_BLACKLIST_DB: int = 1  # Separate DB for token blacklist
    REDIS_MAX_CONNECTIONS: int = 10

    # JWT
    JWT_SECRET: str = "your-super-secret-key-here-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Security
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Application
    APP_NAME: str = "DreamSeed API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production


# Global settings instance
settings = Settings()
