"""Custom JWT strategy with JTI support for token blacklist."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Security
from fastapi.security import HTTPBearer
from fastapi_users.authentication.strategy import Strategy
from fastapi_users.jwt import decode_jwt, generate_jwt
from fastapi_users.manager import BaseUserManager

from app.core.redis_config import get_redis
from app.core.settings import settings
from app.models.user import User
from app.services.token_blacklist import TokenBlacklistService

bearer_transport = HTTPBearer()


class JWTStrategyWithBlacklist(Strategy[User, int]):
    """JWT Strategy with token blacklist support using JTI."""

    def __init__(
        self,
        secret: str,
        lifetime_seconds: int,
        token_audience: list[str] = ["fastapi-users:auth"],
        algorithm: str = "HS256",
    ):
        """Initialize JWT strategy with blacklist support.

        Args:
            secret: Secret key for JWT encoding
            lifetime_seconds: Token lifetime in seconds
            token_audience: JWT audience claim
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret = secret
        self.lifetime_seconds = lifetime_seconds
        self.token_audience = token_audience
        self.algorithm = algorithm

    async def read_token(
        self,
        token: Optional[str],
        user_manager: BaseUserManager[User, int],
    ) -> Optional[User]:
        """Verify JWT token and check blacklist.

        Args:
            token: JWT token string
            user_manager: User manager instance

        Returns:
            User object if valid, None otherwise
        """
        if token is None:
            return None

        try:
            # Decode and verify token
            data = decode_jwt(
                token,
                self.secret,
                self.token_audience,
                algorithms=[self.algorithm],
            )

            if not (user_id := data.get("user_id")) or not (jti := data.get("jti")):
                return None

            # Check if token is blacklisted
            redis_client = await get_redis()
            blacklist_service = TokenBlacklistService(redis_client)

            if await blacklist_service.is_blacklisted(jti):
                return None

            # Check if user's all tokens are blacklisted (e.g., after password change)
            if await blacklist_service.is_user_blacklisted(int(user_id)):
                return None

            # Get user from database
            user = await user_manager.get(int(user_id))
            return user

        except Exception:
            return None

    async def write_token(self, user: User) -> str:
        """Generate JWT token with JTI for blacklist support.

        Args:
            user: User object

        Returns:
            JWT token string with embedded JTI
        """
        # Generate unique JWT ID for blacklist tracking
        jti = str(uuid.uuid4())

        data = {
            "user_id": str(user.id),
            "aud": self.token_audience,
            "jti": jti,  # Add JTI for blacklist support
        }

        return generate_jwt(
            data,
            self.secret,
            self.lifetime_seconds,
            algorithm=self.algorithm,
        )

    async def destroy_token(self, token: str, user: User) -> None:
        """Blacklist the token on logout.

        Args:
            token: JWT token to blacklist
            user: User object (for additional validation)
        """
        try:
            # Decode token to get JTI and expiration
            data = decode_jwt(
                token,
                self.secret,
                self.token_audience,
                algorithms=[self.algorithm],
            )

            if not (jti := data.get("jti")) or not (exp := data.get("exp")):
                return

            # Blacklist the token
            redis_client = await get_redis()
            blacklist_service = TokenBlacklistService(redis_client)
            expires_at = datetime.utcfromtimestamp(exp)
            await blacklist_service.blacklist_token(jti, expires_at)

        except Exception:
            # If token decoding fails, nothing to blacklist
            pass


def get_jwt_strategy_with_blacklist() -> JWTStrategyWithBlacklist:
    """Get JWT strategy instance with blacklist support."""
    return JWTStrategyWithBlacklist(
        secret=settings.JWT_SECRET,
        lifetime_seconds=settings.JWT_EXPIRE_MINUTES * 60,
        algorithm=settings.JWT_ALGORITHM,
    )
