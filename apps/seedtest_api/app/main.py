"""FastAPI application (proposed structure).

This file now hosts the actual FastAPI app. The legacy entrypoint at
`seedtest_api.main` re-exports this `app` for backward compatibility.
"""

import importlib
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import text

from ..core.config import config as app_config
from ..middleware.correlation import CorrelationIdMiddleware
from ..services import db as db_service
from .api.routers.analysis import router as analysis_router
from .api.routers.exams import router as exams_router
from .api.routers.results import router as results_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown logic."""
    # Startup
    app.state.config = app_config
    logging.getLogger(__name__).info(
        "Config loaded: APP_ENV=%s, DB=%s",
        app_config.APP_ENV,
        bool(app_config.DATABASE_URL),
    )

    # Optional DB connectivity check
    if app_config.DATABASE_URL:
        try:
            engine = db_service.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).warning("DB connectivity check failed: %s", e)

    yield

    # Shutdown (if needed, e.g., close connections)
    # db_service.close_engine() if you implement it


app = FastAPI(
    title="SeedTest API",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Initialize Sentry if configured
_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
if _sentry_dsn:
    try:  # pragma: no cover - optional dependency in dev
        sentry_sdk = importlib.import_module("sentry_sdk")
        fastapi_integration_mod = importlib.import_module(
            "sentry_sdk.integrations.fastapi"
        )
        FastApiIntegration = getattr(
            fastapi_integration_mod, "FastApiIntegration", None
        )
        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[FastApiIntegration()] if FastApiIntegration else None,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
            environment=os.getenv("SENTRY_ENV", os.getenv("ENV", "local")),
            release=os.getenv("SENTRY_RELEASE"),
        )
    except Exception:
        # If sentry-sdk is not available, skip initialization silently
        pass

# Middleware
app.add_middleware(CorrelationIdMiddleware)

# Routers
app.include_router(exams_router)
app.include_router(results_router)
app.include_router(analysis_router)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


# Global error handler (simple)
@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    return json_response(500, {"detail": "Internal Server Error"})


def json_response(status: int, body: dict):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status, content=body)


__all__ = ["app"]
