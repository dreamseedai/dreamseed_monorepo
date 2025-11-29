"""
FastAPI-Users integration for authentication
Using async SQLAlchemy
"""

import logging
import os
import time
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.jwt_strategy import get_jwt_strategy_with_blacklist
from app.models.user import User
from app.services.email_service import (
    send_verification_email,
    send_password_reset_email,
)


# JWT Secret - in production, use environment variable
SECRET = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION")
RESET_PASSWORD_TOKEN_SECRET = os.getenv("AUTH_RESET_TOKEN_SECRET", SECRET)
VERIFICATION_TOKEN_SECRET = os.getenv("AUTH_VERIFICATION_TOKEN_SECRET", SECRET)

# Email mode: "console" for dev (no real email), "smtp" for production
EMAIL_MODE = os.getenv("EMAIL_MODE", "console")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Setup logger for timing diagnostics
logger = logging.getLogger(__name__)


# ---- User Database (async version) ----
async def get_user_db(session: AsyncSession = Depends(get_async_db)):
    yield SQLAlchemyUserDatabase(session, User)


# ---- User Manager ----
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = VERIFICATION_TOKEN_SECRET

    async def create(
        self,
        user_create,
        safe: bool = False,
        request: Optional[Request] = None,
    ):
        """Override create to add timing diagnostics"""
        t0 = time.perf_counter()
        logger.info("[UserManager.create] start for email: %s", user_create.email)

        # Call parent create method
        t1 = time.perf_counter()
        user = await super().create(user_create, safe=safe, request=request)
        t2 = time.perf_counter()

        logger.info(
            "[UserManager.create] super().create (validation+hash+db): %.3fs", t2 - t1
        )
        logger.info("[UserManager.create] total: %.3fs", t2 - t0)

        return user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """
        Called after successful user registration.

        NOTE: This hook executes BEFORE the HTTP response is sent to the client.
        Any slow operations here (SMTP, external APIs) will block the response.

        For production, use BackgroundTasks or a message queue (Celery/RQ).
        """
        t0 = time.perf_counter()
        logger.info("[on_after_register] start for user %s (%s)", user.id, user.email)

        print(f"✅ User {user.id} ({user.email}) registered with role: {user.role}")

        # Send verification email (console mode = instant, smtp mode = blocks)
        t1 = time.perf_counter()
        send_verification_email(user.email)
        t2 = time.perf_counter()

        logger.info("[on_after_register] email send: %.3fs", t2 - t1)
        logger.info("[on_after_register] total: %.3fs", t2 - t0)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after password reset request. Sends reset email."""
        send_password_reset_email(user.email, token)

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after verification request. Sends verification email."""
        send_verification_email(user.email, token)


# ---- User Manager Dependency ----
async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# ---- Auth Backend ----
bearer_transport = BearerTransport(tokenUrl="/api/auth/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy_with_blacklist,
)

# ---- FastAPI Users Instance ----
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Export commonly used dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
