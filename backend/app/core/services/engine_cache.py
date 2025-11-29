"""
Adaptive Engine Cache Service

Manages caching of AdaptiveEngine instances using Redis.
Improves performance by persisting engine state between requests.
"""
import json
import pickle
from typing import Optional
from app.core.redis import get_redis
from app.core.services.exam_engine import AdaptiveEngine


class AdaptiveEngineCache:
    """
    Redis-based cache for AdaptiveEngine instances.
    
    Stores engine state to avoid recalculating from database on each request.
    """
    
    def __init__(self):
        self.redis = get_redis()
        self.key_prefix = "adaptive_engine"
        self.ttl = 3600  # 1 hour default TTL
    
    def _make_key(self, exam_session_id: int) -> str:
        """Generate Redis key for exam session"""
        return f"{self.key_prefix}:{exam_session_id}"
    
    async def get(self, exam_session_id: int) -> Optional[AdaptiveEngine]:
        """
        Retrieve cached engine from Redis.
        
        Args:
            exam_session_id: Exam session ID
            
        Returns:
            AdaptiveEngine if cached, None otherwise
        """
        key = self._make_key(exam_session_id)
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        try:
            # Deserialize engine state
            state = json.loads(data)
            
            # Reconstruct engine from state
            engine = AdaptiveEngine(initial_theta=state["theta"])
            
            # Restore responses and item params
            engine.responses = state.get("responses", [])
            engine.item_params_list = state.get("item_params_list", [])
            engine.theta = state["theta"]
            
            return engine
            
        except Exception as e:
            print(f"Error deserializing engine for session {exam_session_id}: {e}")
            return None
    
    async def set(
        self,
        exam_session_id: int,
        engine: AdaptiveEngine,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache engine in Redis.
        
        Args:
            exam_session_id: Exam session ID
            engine: AdaptiveEngine instance to cache
            ttl: Time-to-live in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful
        """
        key = self._make_key(exam_session_id)
        ttl = ttl or self.ttl
        
        try:
            # Get current engine state
            state = engine.get_state()
            
            # Serialize to JSON
            data = json.dumps({
                "theta": state["theta"],
                "se": state["standard_error"],
                "responses": engine.responses,
                "item_params_list": engine.item_params_list
            })
            
            # Store in Redis with TTL
            await self.redis.setex(key, ttl, data)
            return True
            
        except Exception as e:
            print(f"Error caching engine for session {exam_session_id}: {e}")
            return False
    
    async def delete(self, exam_session_id: int) -> bool:
        """
        Remove cached engine from Redis.
        
        Args:
            exam_session_id: Exam session ID
            
        Returns:
            bool: True if key was deleted
        """
        key = self._make_key(exam_session_id)
        result = await self.redis.delete(key)
        return result > 0
    
    async def exists(self, exam_session_id: int) -> bool:
        """
        Check if engine is cached.
        
        Args:
            exam_session_id: Exam session ID
            
        Returns:
            bool: True if cached
        """
        key = self._make_key(exam_session_id)
        return await self.redis.exists(key) > 0
    
    async def clear_all(self) -> int:
        """
        Clear all cached engines.
        
        Returns:
            int: Number of keys deleted
        """
        pattern = f"{self.key_prefix}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            dict: Cache stats (count, memory usage)
        """
        pattern = f"{self.key_prefix}:*"
        keys = await self.redis.keys(pattern)
        
        total_memory = 0
        for key in keys:
            memory = await self.redis.memory_usage(key)
            if memory:
                total_memory += memory
        
        return {
            "cached_engines": len(keys),
            "memory_bytes": total_memory,
            "memory_mb": round(total_memory / (1024 * 1024), 2)
        }


# Global cache instance
_cache_instance: Optional[AdaptiveEngineCache] = None


def get_engine_cache() -> AdaptiveEngineCache:
    """
    Get global AdaptiveEngineCache instance (singleton).
    
    Returns:
        AdaptiveEngineCache: Global cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AdaptiveEngineCache()
    return _cache_instance
