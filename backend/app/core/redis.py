"""
redis.py

Redis client configuration and utilities for DreamSeedAI.

Provides:
 - Async Redis client singleton
 - Connection management
 - Configuration from environment variables

Usage:
    from app.core.redis import get_redis
    
    redis_client = get_redis()
    await redis_client.set("key", "value")
    value = await redis_client.get("key")
"""

from functools import lru_cache
import redis.asyncio as redis
import os
from typing import Optional


@lru_cache
def get_redis() -> redis.Redis:
    """
    Get global async Redis client (singleton).
    
    Configuration via environment variables:
    - REDIS_URL: Full Redis URL (default: redis://localhost:6379/0)
    - REDIS_HOST: Redis host (default: localhost)
    - REDIS_PORT: Redis port (default: 6379)
    - REDIS_DB: Redis database number (default: 0)
    - REDIS_PASSWORD: Redis password (optional)
    
    Returns:
        redis.Redis: Async Redis client with decode_responses=True
    
    Example:
        # Using REDIS_URL
        REDIS_URL=redis://localhost:6379/0
        
        # Or individual settings
        REDIS_HOST=localhost
        REDIS_PORT=6379
        REDIS_DB=0
        REDIS_PASSWORD=secret
    """
    # Priority 1: Use REDIS_URL if provided
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis.from_url(
            redis_url,
            decode_responses=True,
            encoding="utf-8"
        )
    
    # Priority 2: Build from individual settings
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    password = os.getenv("REDIS_PASSWORD")
    
    return redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True,
        encoding="utf-8"
    )


async def ping_redis() -> bool:
    """
    Test Redis connection.
    
    Returns:
        bool: True if Redis is reachable, False otherwise
    
    Example:
        if await ping_redis():
            print("✅ Redis is ready")
        else:
            print("❌ Redis connection failed")
    """
    try:
        client = get_redis()
        await client.ping()
        return True
    except Exception as e:
        print(f"Redis ping failed: {e}")
        return False


async def clear_redis_cache(pattern: str = "*") -> int:
    """
    Clear Redis keys matching pattern.
    
    Args:
        pattern: Redis key pattern (default: "*" = all keys)
    
    Returns:
        int: Number of keys deleted
    
    Example:
        # Clear all adaptive engine states
        await clear_redis_cache("adaptive_engine:*")
        
        # Clear everything
        await clear_redis_cache("*")
    """
    client = get_redis()
    keys = await client.keys(pattern)
    if keys:
        return await client.delete(*keys)
    return 0


# For testing/development
async def get_redis_info() -> dict:
    """
    Get Redis server information.
    
    Returns:
        dict: Redis INFO command output
    """
    client = get_redis()
    return await client.info()
