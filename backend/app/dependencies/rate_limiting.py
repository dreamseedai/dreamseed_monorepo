"""
Rate Limiting Dependencies

FastAPI dependencies for rate limiting specific endpoints
"""

from fastapi import Request, HTTPException
from app.core.rate_limiter import limiter
from app.core.settings import settings


async def rate_limit_login(request: Request):
    """
    Rate limit for login endpoint: 5 requests per minute per IP

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    try:
        await limiter.check_rate_limit(
            f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute",
            request,
        )
    except Exception as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.RATE_LIMIT_LOGIN_PER_MINUTE} requests per minute",
            headers={"Retry-After": "60"},
        )


async def rate_limit_register(request: Request):
    """
    Rate limit for register endpoint: 3 requests per hour per IP

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    try:
        await limiter.check_rate_limit(
            f"{settings.RATE_LIMIT_REGISTER_PER_HOUR}/hour",
            request,
        )
    except Exception as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.RATE_LIMIT_REGISTER_PER_HOUR} requests per hour",
            headers={"Retry-After": "3600"},
        )


async def rate_limit_refresh(request: Request):
    """
    Rate limit for token refresh: 10 requests per hour per user

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    try:
        await limiter.check_rate_limit(
            f"{settings.RATE_LIMIT_REFRESH_PER_HOUR}/hour",
            request,
        )
    except Exception as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.RATE_LIMIT_REFRESH_PER_HOUR} requests per hour",
            headers={"Retry-After": "3600"},
        )
