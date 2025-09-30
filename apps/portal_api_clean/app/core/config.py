from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = Field(default="DreamSeed Portal API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")

    database_url: str = Field(alias="DATABASE_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    access_token_expire_minutes: int = Field(default=120, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60*24*14, alias="REFRESH_TOKEN_EXPIRE_MINUTES")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    cookie_secure: bool = Field(default=True, alias="COOKIE_SECURE")
    cookie_samesite: Literal["lax","strict","none"] = Field(default="lax", alias="COOKIE_SAMESITE")
    refresh_cookie_name: str = Field(default="ds_refresh", alias="REFRESH_COOKIE_NAME")

    # Stripe
    stripe_secret_key: str | None = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_id: str | None = Field(default=None, alias="STRIPE_PRICE_ID")
    stripe_success_url: str | None = Field(default=None, alias="STRIPE_SUCCESS_URL")
    stripe_cancel_url: str | None = Field(default=None, alias="STRIPE_CANCEL_URL")
    stripe_portal_return_url: str | None = Field(default=None, alias="STRIPE_PORTAL_RETURN_URL")
    # Cache
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    cache_ttl_seconds: int = Field(default=15, alias="CACHE_TTL_SECONDS")
    # Observability
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    # Rate limit
    login_rate_limit_per_min: int = Field(default=5, alias="LOGIN_RATE_LIMIT_PER_MIN")
    login_rate_limit_burst: int = Field(default=5, alias="LOGIN_RATE_LIMIT_BURST")
    export_rate_limit_per_min: int = Field(default=10, alias="EXPORT_RATE_LIMIT_PER_MIN")
    # Admin
    admin_api_key: str | None = Field(default=None, alias="ADMIN_API_KEY")
    # CORS & Security Headers
    allowed_origins: str = Field(default="http://127.0.0.1:5172", alias="ALLOWED_ORIGINS")
    security_headers_enabled: bool = Field(default=True, alias="SECURITY_HEADERS_ENABLED")
    csp_enabled: bool = Field(default=False, alias="CSP_ENABLED")
    hsts_enabled: bool = Field(default=False, alias="HSTS_ENABLED")
    referrer_policy: str = Field(default="strict-origin", alias="REFERRER_POLICY")
    frame_ancestors: str = Field(default="none", alias="FRAME_ANCESTORS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
@lru_cache
def get_settings() -> "Settings":
    return Settings()  # type: ignore[call-arg]


def get_allowed_origins_list() -> list[str]:
    s = get_settings()
    return [o.strip() for o in s.allowed_origins.split(",") if o.strip()]
