"""
Redis caching utilities for API responses
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from fastapi import Request, Response


class RedisCache:
    """Redis cache manager for API responses"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis connection
        
        Args:
            redis_url: Redis connection URL
        """
        if not REDIS_AVAILABLE:
            print("WARNING: redis-py not installed. Caching disabled.")
            self.client = None
            return
        
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            print(f"✓ Redis connected: {redis_url}")
        except Exception as e:
            print(f"⚠ Redis connection failed: {e}. Caching disabled.")
            self.client = None
    
    def get(self, key: str) -> Optional[dict]:
        """
        Get cached value
        
        Args:
            key: Cache key
            
        Returns:
            Cached dict or None
        """
        if not self.client:
            return None
        
        try:
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Redis get error: {e}")
        
        return None
    
    def set(self, key: str, value: dict, ttl: int = 60) -> bool:
        """
        Set cached value with TTL
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (default 60)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value, default=str, ensure_ascii=False)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete cached value
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "student_detail:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis invalidate error: {e}")
            return 0


def compute_etag(data: Any) -> str:
    """
    Compute ETag hash from data
    
    Args:
        data: Data to hash (dict, list, etc.)
        
    Returns:
        MD5 hash as hex string
    """
    if isinstance(data, (dict, list)):
        body = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    else:
        body = str(data).encode("utf-8")
    
    return hashlib.md5(body).hexdigest()


def with_cache_and_etag(
    cache_key_fn: Callable,
    ttl: int = 60,
):
    """
    Decorator for caching API responses with ETag support
    
    Usage:
        @with_cache_and_etag(
            cache_key_fn=lambda teacher_id, student_id: f"student_detail:{teacher_id}:{student_id}",
            ttl=300,
        )
        async def get_student_detail(...):
            ...
    
    Args:
        cache_key_fn: Function to generate cache key from function args
        ttl: Cache TTL in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and response from FastAPI
            request: Optional[Request] = kwargs.get("request")
            response: Optional[Response] = kwargs.get("response")
            
            if not request or not response:
                # No request/response context, skip caching
                return await func(*args, **kwargs)
            
            # Get redis cache instance
            # TODO: Inject from dependency
            cache = RedisCache()
            
            # Generate cache key
            cache_key = cache_key_fn(*args, **kwargs)
            
            # Check cache
            cached_data = cache.get(cache_key)
            if cached_data:
                etag = compute_etag(cached_data)
                
                # Check If-None-Match header
                if_none_match = request.headers.get("if-none-match")
                if if_none_match == etag:
                    # 304 Not Modified
                    response.status_code = 304
                    return None
                
                # Return cached data with ETag
                response.headers["ETag"] = etag
                response.headers["X-Cache"] = "HIT"
                return cached_data
            
            # Cache miss - call original function
            result = await func(*args, **kwargs)
            
            if result:
                # Convert Pydantic model to dict if needed
                if hasattr(result, "model_dump"):
                    result_dict = result.model_dump()
                elif hasattr(result, "dict"):
                    result_dict = result.dict()
                else:
                    result_dict = result
                
                # Compute ETag and cache
                etag = compute_etag(result_dict)
                cache.set(cache_key, result_dict, ttl=ttl)
                
                response.headers["ETag"] = etag
                response.headers["X-Cache"] = "MISS"
            
            return result
        
        return wrapper
    return decorator


# Global cache instance (can be injected via dependency)
cache_client: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """
    FastAPI dependency to get Redis cache instance
    
    Returns:
        RedisCache instance
    """
    global cache_client
    if cache_client is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache_client = RedisCache(redis_url)
    return cache_client
