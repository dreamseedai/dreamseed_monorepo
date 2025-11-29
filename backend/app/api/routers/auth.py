"""
Authentication router
Provides register, login, logout, and user info endpoints
"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.users import auth_backend, fastapi_users
from app.core.database import get_async_db
from app.schemas.user_schemas import UserCreate, UserRead, UserUpdate
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# FastAPI-Users provides these routers automatically:
# - POST /register
# - POST /login
# - POST /logout
# - GET /me (current user info)

# Register router
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)

# Auth router (login/logout)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
)

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
