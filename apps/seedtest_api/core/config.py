"""Application configuration using Pydantic BaseSettings.

This module introduces a canonical Config class backed by environment variables
and .env files (via pydantic-settings). It coexists with the legacy
`seedtest_api.settings.Settings` for backward compatibility.
"""

from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    # Core
    APP_ENV: str = "local"  # local | staging | production
    API_PREFIX: str = "/api/seedtest"

    # Database
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="SQLAlchemy DSN, e.g., postgresql+psycopg2://user:pass@host:5432/db",
    )

    # JWT verification
    JWT_PUBLIC_KEY: Optional[str] = Field(
        default=None,
        description="PEM public key for JWT verification (multiline supported)",
    )
    # Accept either JWT_JWKS_URL or JWKS_URL from env
    JWKS_URL: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("JWT_JWKS_URL", "JWKS_URL"),
        description="JWKS endpoint for JWT verification (alternative to JWT_PUBLIC_KEY)",
    )
    JWT_ISS: Optional[str] = None
    JWT_AUD: Optional[str] = None

    # Local dev convenience
    LOCAL_DEV: bool = False

    # Result response configuration
    RESULT_EXCLUDE_TIMESTAMPS: bool = Field(
        default=False,
        description="When true, omit volatile fields (timestamps) from result responses",
    )

    # Analysis feature flag
    ENABLE_ANALYSIS: bool = Field(
        default=True,
        description="Enable or disable analysis endpoints",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "apps/seedtest_api/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# Instance to be used by the app
config = Config()

# Back-compat export of legacy settings
try:
    from ..settings import settings as settings  # noqa: E402
except ImportError:
    # If legacy settings module doesn't exist, use Config as a compatibility layer
    class SettingsCompat:
        def __getattr__(self, name: str):
            return getattr(config, name, None)

    settings = SettingsCompat()

__all__ = ["Config", "config", "settings"]
