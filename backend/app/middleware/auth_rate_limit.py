"""
Rate Limiting Middleware for Auth Endpoints

Applies strict rate limits to sensitive authentication endpoints
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from app.core.rate_limiter import limiter, get_user_id_or_ip
from app.core.settings import settings


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply strict rate limits to auth endpoints.

    Endpoints:
    - POST /api/auth/login: 5 requests/minute/IP
    - POST /api/auth/register: 3 requests/hour/IP
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Apply rate limits to specific auth endpoints
        try:
            if method == "POST" and path == "/api/auth/login":
                # Login: 5/minute per IP
                key = get_user_id_or_ip(request)
                limiter.check_rate_limit(
                    f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute",
                    key_func=lambda: key,
                )
            elif method == "POST" and path == "/api/auth/register":
                # Register: 3/hour per IP
                key = get_user_id_or_ip(request)
                limiter.check_rate_limit(
                    f"{settings.RATE_LIMIT_REGISTER_PER_HOUR}/hour",
                    key_func=lambda: key,
                )
        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": str(e),
                    "retry_after": getattr(e, "retry_after", 60),
                },
                headers={
                    "Retry-After": str(getattr(e, "retry_after", 60)),
                },
            )

        response = await call_next(request)
        return response
