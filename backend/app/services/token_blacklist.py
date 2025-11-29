"""Token blacklist service for managing invalidated JWT tokens."""
from datetime import datetime, timedelta
from typing import Optional

from redis.asyncio import Redis

from app.core.settings import settings


class TokenBlacklistService:
    """Service for managing blacklisted JWT tokens."""

    def __init__(self, redis_client: Redis):
        """Initialize blacklist service with Redis client.

        Args:
            redis_client: Redis connection instance
        """
        self.redis = redis_client
        self.prefix = "blacklist:token:"

    async def blacklist_token(
        self,
        jti: str,
        expires_at: datetime,
    ) -> bool:
        """Add a token to the blacklist.

        Args:
            jti: JWT ID (unique identifier from token)
            expires_at: Token expiration datetime

        Returns:
            True if successfully blacklisted, False otherwise
        """
        key = f"{self.prefix}{jti}"

        # Calculate TTL: token should remain in blacklist until it expires naturally
        ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())

        if ttl_seconds <= 0:
            # Token already expired, no need to blacklist
            return True

        # Store in Redis with TTL matching token expiration
        await self.redis.setex(
            key,
            ttl_seconds,
            value="blacklisted",
        )

        return True

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted.

        Args:
            jti: JWT ID to check

        Returns:
            True if token is blacklisted, False otherwise
        """
        key = f"{self.prefix}{jti}"
        result = await self.redis.exists(key)
        return result > 0

    async def blacklist_user_tokens(
        self,
        user_id: int,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Blacklist all tokens for a specific user.

        This is useful for scenarios like:
        - User password change
        - User account suspension
        - Force logout from all devices

        Args:
            user_id: User ID whose tokens should be blacklisted
            expires_at: Optional expiration datetime. If not provided,
                       uses default JWT expiration

        Returns:
            True if successfully blacklisted
        """
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(
                minutes=settings.JWT_EXPIRE_MINUTES
            )

        key = f"blacklist:user:{user_id}"
        ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())

        if ttl_seconds <= 0:
            return True

        await self.redis.setex(
            key,
            ttl_seconds,
            value="blacklisted",
        )

        return True

    async def is_user_blacklisted(self, user_id: int) -> bool:
        """Check if all tokens for a user are blacklisted.

        Args:
            user_id: User ID to check

        Returns:
            True if user's tokens are blacklisted, False otherwise
        """
        key = f"blacklist:user:{user_id}"
        result = await self.redis.exists(key)
        return result > 0

    async def remove_from_blacklist(self, jti: str) -> bool:
        """Remove a token from blacklist (rarely needed).

        Args:
            jti: JWT ID to remove from blacklist

        Returns:
            True if successfully removed or didn't exist
        """
        key = f"{self.prefix}{jti}"
        await self.redis.delete(key)
        return True

    async def get_blacklist_count(self) -> int:
        """Get total number of blacklisted tokens.

        Returns:
            Number of blacklisted tokens
        """
        cursor = 0
        count = 0

        # Scan through all blacklisted tokens
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match=f"{self.prefix}*",
                count=100,
            )
            count += len(keys)

            if cursor == 0:
                break

        return count
