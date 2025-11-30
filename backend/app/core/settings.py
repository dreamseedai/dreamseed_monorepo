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
    REDIS_RATE_LIMIT_DB: int = 2  # Separate DB for rate limiting
    REDIS_MAX_CONNECTIONS: int = 10

    # JWT
    JWT_SECRET: str = "your-super-secret-key-here-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5  # Brute force protection
    RATE_LIMIT_REGISTER_PER_HOUR: int = 3  # Spam account prevention
    RATE_LIMIT_REFRESH_PER_HOUR: int = 10  # Token abuse prevention
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 100  # General API protection

    # Security
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Application
    APP_NAME: str = "DreamSeed API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production


# Global settings instance
settings = Settings()
