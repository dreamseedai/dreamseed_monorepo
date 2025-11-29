from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from adaptive_engine.config import get_settings


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def root_health():
    s = get_settings()
    return JSONResponse({"status": "ok", "backend": s.session_backend}, status_code=status.HTTP_200_OK)


@router.get("/redis")
def redis_health():
    s = get_settings()
    if s.session_backend != "redis":
        return JSONResponse({"backend": s.session_backend, "redis": "disabled"}, status_code=status.HTTP_200_OK)
    try:
        import redis  # type: ignore

        r = redis.Redis.from_url(s.redis_url, decode_responses=True)  # type: ignore[attr-defined]
        pong = r.ping()
        return JSONResponse({"backend": s.session_backend, "redis": "ok", "ping": pong}, status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse({"backend": s.session_backend, "redis": "error", "detail": str(e)}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
