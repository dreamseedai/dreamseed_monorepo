from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from app.core.config import get_settings
from app.routers import auth, content, recommend
from app.routers import billing_stripe, export
import logging
import time
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        enable_tracing=True,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        environment=settings.app_env,
    )

# Inner API app mounted under /api so local dev at :8000 works with /api prefix
api = FastAPI(title=settings.app_name, redirect_slashes=False)

# CORS (production-driven origins)
def _origins():
    return [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

api.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@api.get("/__ok")
def api_ok():
    return {"ok": True, "env": settings.app_env}

api.include_router(auth.router)
api.include_router(content.router)
api.include_router(recommend.router)
api.include_router(billing_stripe.router)
api.include_router(export.router)

# Root app (mounts /api)
app = FastAPI(title=settings.app_name, redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/__ok")
def ok():
    return {"ok": True}


# Simple request logging middleware
logger = logging.getLogger("uvicorn.access")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    logger.info("%s %s %s %dms", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp: Response = await call_next(request)
    if settings.security_headers_enabled:
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY" if settings.frame_ancestors == "none" else "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", settings.referrer_policy)
        if settings.csp_enabled:
            path = request.url.path
            if path.startswith("/docs") or path.startswith("/redoc"):
                csp = [
                    "default-src 'self'",
                    "img-src 'self' data: https:",
                    "style-src 'self' 'unsafe-inline' https:",
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:",
                    "frame-ancestors " + (settings.frame_ancestors if settings.frame_ancestors != "none" else "'none'"),
                ]
            else:
                csp = [
                    "default-src 'none'",
                    "base-uri 'none'",
                    "frame-ancestors " + (settings.frame_ancestors if settings.frame_ancestors != "none" else "'none'"),
                ]
            resp.headers.setdefault("Content-Security-Policy", "; ".join(csp))
        if settings.hsts_enabled and request.url.scheme == "https":
            resp.headers.setdefault("Strict-Transport-Security", "max-age=15552000; includeSubDomains")
    return resp



@app.middleware("http")
async def add_vary_origin(request: Request, call_next):
    resp: Response = await call_next(request)
    resp.headers.setdefault("Vary", "Origin")
    return resp

# Mount the API under /api so that frontend requests to /api/... work in local dev
app.mount("/api", api)


