"""Redis configuration for token blacklist and session management."""
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.settings import settings


class RedisManager:
    """Manages Redis connections for the application."""

    _instance: Optional[Redis] = None

    @classmethod
    async def get_instance(cls) -> Redis:
        """Get or create Redis connection instance."""
        if cls._instance is None:
            cls._instance = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                db=settings.REDIS_TOKEN_BLACKLIST_DB,
            )
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """Close Redis connection."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


async def get_redis() -> Redis:
    """Dependency for FastAPI routes to get Redis connection."""
    return await RedisManager.get_instance()
