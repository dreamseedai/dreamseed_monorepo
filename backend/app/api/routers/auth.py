"""
Authentication router
Provides register, login, logout, and user info endpoints
"""

import time
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.users import auth_backend, fastapi_users
from app.core.database import get_async_db
from app.core.rate_limiter import limiter
from app.core.settings import settings
from app.schemas.user_schemas import UserCreate, UserRead, UserUpdate
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# FastAPI-Users provides these routers automatically:
# - POST /register
# - POST /login
# - POST /logout
# - GET /me (current user info)

# Note: Rate limiting headers are automatically added by slowapi
# Specific endpoints have stricter limits than the global default

# Register router
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
# Apply rate limit to register endpoint
for route in register_router.routes:
    if route.path == "/" and "POST" in route.methods:
        route.endpoint = limiter.limit(f"{settings.RATE_LIMIT_REGISTER_PER_HOUR}/hour")(
            route.endpoint
        )
router.include_router(register_router)

# Auth router (login/logout)
auth_router = fastapi_users.get_auth_router(auth_backend)
# Apply rate limit to login endpoint
for route in auth_router.routes:
    if route.path == "/login" and "POST" in route.methods:
        route.endpoint = limiter.limit(f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute")(
            route.endpoint
        )
router.include_router(auth_router)

# Users router (me endpoint)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
)


@router.get("/me", response_model=UserRead, tags=["auth"])
async def get_current_user_info(
    user: User = Depends(fastapi_users.current_user(active=True)),
):
    """
    Get current authenticated user information

    Returns:
        Current user data (id, email, role, etc.)
    """
    return user


@router.post("/register_dev", tags=["auth", "diagnostics"])
async def register_dev(db: AsyncSession = Depends(get_async_db)):
    """
    Diagnostic endpoint to test DB connection speed without full registration logic

    This helps isolate whether slowness is from DB/infrastructure or business logic.
    """
    start = time.perf_counter()

    # Simple DB ping
    result = await db.execute("SELECT 1")

    end = time.perf_counter()
    elapsed = end - start

    print(f"[register_dev] DB ping: {elapsed:.4f}s")

    return {
        "ok": True,
        "db_ping_seconds": round(elapsed, 4),
        "message": "If this is fast (<0.1s), DB is fine. Slowness is in register business logic.",
    }
