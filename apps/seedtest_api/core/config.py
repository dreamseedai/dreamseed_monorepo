"""Application configuration using Pydantic BaseSettings.

This module introduces a canonical Config class backed by environment variables
and .env files (via pydantic-settings). It coexists with the legacy
`seedtest_api.settings.Settings` for backward compatibility when present.
"""

from typing import List, Optional

from pydantic import AliasChoices, Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    # Core
    APP_ENV: str = "local"  # local | staging | production
    API_PREFIX: str = "/api/seedtest"
    LOCAL_DEV: bool = False

    # Feature flags / toggles
    ENABLE_ANALYSIS: bool = True
    RESULT_EXCLUDE_TIMESTAMPS: bool = False

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

    # Analysis / recommendation configuration
    ANALYSIS_ENGINE: str = "heuristic"  # heuristic | irt | mixed_effects
    RECOMMENDER_ENGINE: str = "rule"  # rule | content | hybrid
    CONTENT_CATALOG_PATH: Optional[str] = None
    ANALYSIS_GOAL_TARGETS: Optional[List[float]] = None
    ANALYSIS_GOAL_HORIZONS: Optional[List[int]] = None
    CAT_PRIOR_SD: float = 1.0

    # R Plumber microservice (internal service URL and auth)
    R_PLUMBER_BASE_URL: Optional[str] = Field(
        default=None, description="Base URL for R Plumber (ClusterIP or local dev)"
    )
    R_PLUMBER_INTERNAL_TOKEN: Optional[str] = Field(
        default=None, description="Shared secret for X-Internal-Token header"
    )
    R_PLUMBER_TIMEOUT_SECS: float = 15.0

    # R IRT Plumber microservice (internal service URL and auth)
    R_IRT_BASE_URL: Optional[str] = Field(
        default=None, description="Base URL for R IRT Plumber (ClusterIP or local dev)"
    )
    R_IRT_INTERNAL_TOKEN: Optional[str] = Field(
        default=None, description="Shared secret for X-Internal-Token header (IRT)"
    )
    R_IRT_TIMEOUT_SECS: float = 15.0

    model_config = SettingsConfigDict(
        env_file=("apps/seedtest_api/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Allow comma-separated values for list fields in env (e.g., "130,150")
    @field_validator("ANALYSIS_GOAL_TARGETS", mode="before")
    @classmethod
    def _parse_targets(cls, v):  # type: ignore[no-untyped-def]
        if v is None or isinstance(v, list):
            return v
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            out: List[float] = []
            for p in parts:
                try:
                    out.append(float(p))
                except Exception:
                    continue
            return out
        return v

    @field_validator("ANALYSIS_GOAL_HORIZONS", mode="before")
    @classmethod
    def _parse_horizons(cls, v):  # type: ignore[no-untyped-def]
        if v is None or isinstance(v, list):
            return v
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            out: List[int] = []
            for p in parts:
                try:
                    iv = int(p)
                    if iv > 0:
                        out.append(iv)
                except Exception:
                    continue
            return out
        return v


# Instance to be used by the app
config = Config()

# Back-compat export of legacy settings (optional)
try:  # pragma: no cover - optional back-compat
    from ..settings import settings as settings  # type: ignore  # noqa: E402,F401
except Exception:  # pragma: no cover - optional back-compat
    settings = None  # type: ignore

__all__ = ["Config", "config", "settings"]
