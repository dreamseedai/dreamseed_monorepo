"""
adaptive_state_store.py

Redis-based state storage for AdaptiveEngine.

This module provides persistent storage for adaptive exam engine state,
allowing engines to survive across API requests and server restarts.

Architecture:
 - Redis stores serialized engine state (theta, item history, responses)
 - TTL prevents memory leaks (default: 1 hour)
 - Fallback to DB reconstruction if Redis state is lost

Key Format:
    adaptive_engine:{exam_session_id}

Value Format (JSON):
    {
      "theta": float,
      "standard_error": float,
      "item_params_list": [{"a": 1.5, "b": 0.2, "c": 0.2}, ...],
      "responses": [true, false, true, ...],
      "max_items": int
    }

Usage:
    from app.core.redis import get_redis
    from app.services.adaptive_state_store import AdaptiveEngineStateStore
    
    redis_client = get_redis()
    store = AdaptiveEngineStateStore(redis_client)
    
    # Save engine state
    engine = AdaptiveEngine(initial_theta=0.5)
    await store.save_engine(exam_session_id=123, engine=engine)
    
    # Load engine state
    engine = await store.load_engine(exam_session_id=123)
    
    # Delete when exam completes
    await store.delete_engine(exam_session_id=123)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import logging

import redis.asyncio as redis

from app.services.exam_engine import AdaptiveEngine


logger = logging.getLogger(__name__)


class AdaptiveEngineStateStore:
    """
    Redis-based state storage for AdaptiveEngine instances.
    
    Manages serialization/deserialization of engine state to Redis,
    with automatic TTL and fallback handling.
    
    Attributes:
        redis: Async Redis client
        default_ttl: Default TTL for engine state (seconds)
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        default_ttl: int = 3600
    ):
        """
        Initialize state store.
        
        Args:
            redis_client: Async Redis client
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl

    def _key(self, exam_session_id: int) -> str:
        """
        Generate Redis key for exam session.
        
        Args:
            exam_session_id: ID of exam session
        
        Returns:
            Redis key string
        """
        return f"adaptive_engine:{exam_session_id}"

    async def load_engine(
        self,
        exam_session_id: int,
        initial_theta: float = 0.0,
        max_items: int = 20
    ) -> AdaptiveEngine:
        """
        Load AdaptiveEngine state from Redis.
        
        If state doesn't exist or is corrupted, creates new engine
        with provided initial values.
        
        Args:
            exam_session_id: ID of exam session
            initial_theta: Initial theta if creating new engine
            max_items: Max items if creating new engine
        
        Returns:
            AdaptiveEngine: Loaded or newly created engine
        
        Example:
            engine = await store.load_engine(
                exam_session_id=123,
                initial_theta=0.5
            )
        """
        key = self._key(exam_session_id)
        
        try:
            raw = await self.redis.get(key)
            if not raw:
                logger.info(
                    f"No engine state found for session {exam_session_id}, "
                    f"creating new engine with theta={initial_theta}"
                )
                return AdaptiveEngine(
                    initial_theta=initial_theta,
                    max_items=max_items
                )

            data = json.loads(raw)
            
            # Reconstruct engine from saved state
            engine = AdaptiveEngine(
                initial_theta=data.get("theta", initial_theta),
                max_items=data.get("max_items", max_items)
            )
            
            # Restore history
            engine.item_params_list = data.get("item_params_list", [])
            engine.responses = data.get("responses", [])
            
            logger.debug(
                f"Loaded engine for session {exam_session_id}: "
                f"theta={engine.theta:.3f}, items={len(engine.responses)}"
            )
            
            return engine

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode engine state for session {exam_session_id}: {e}"
            )
            # Return fresh engine on corruption
            return AdaptiveEngine(
                initial_theta=initial_theta,
                max_items=max_items
            )
        
        except Exception as e:
            logger.error(
                f"Error loading engine for session {exam_session_id}: {e}"
            )
            # Fallback to new engine
            return AdaptiveEngine(
                initial_theta=initial_theta,
                max_items=max_items
            )

    async def save_engine(
        self,
        exam_session_id: int,
        engine: AdaptiveEngine,
        ttl_sec: Optional[int] = None
    ) -> bool:
        """
        Save AdaptiveEngine state to Redis.
        
        Serializes engine to JSON and stores with TTL to prevent
        memory leaks from abandoned exams.
        
        Args:
            exam_session_id: ID of exam session
            engine: AdaptiveEngine instance to save
            ttl_sec: TTL in seconds (default: use default_ttl)
        
        Returns:
            bool: True if save succeeded, False otherwise
        
        Example:
            success = await store.save_engine(
                exam_session_id=123,
                engine=engine,
                ttl_sec=7200  # 2 hours
            )
        """
        key = self._key(exam_session_id)
        ttl = ttl_sec or self.default_ttl
        
        try:
            # Serialize engine state
            payload = {
                "theta": engine.theta,
                "standard_error": engine.get_session_summary()["standard_error"],
                "item_params_list": engine.item_params_list,
                "responses": engine.responses,
                "max_items": engine.max_items,
                "items_completed": len(engine.responses)
            }
            
            raw = json.dumps(payload)
            await self.redis.set(key, raw, ex=ttl)
            
            logger.debug(
                f"Saved engine for session {exam_session_id}: "
                f"theta={engine.theta:.3f}, items={len(engine.responses)}, ttl={ttl}s"
            )
            
            return True

        except Exception as e:
            logger.error(
                f"Failed to save engine for session {exam_session_id}: {e}"
            )
            return False

    async def delete_engine(self, exam_session_id: int) -> bool:
        """
        Delete engine state from Redis.
        
        Call this when exam is completed to free memory.
        
        Args:
            exam_session_id: ID of exam session
        
        Returns:
            bool: True if deleted, False if key didn't exist
        
        Example:
            await store.delete_engine(exam_session_id=123)
        """
        key = self._key(exam_session_id)
        
        try:
            result = await self.redis.delete(key)
            
            if result:
                logger.info(f"Deleted engine state for session {exam_session_id}")
            else:
                logger.debug(f"No engine state to delete for session {exam_session_id}")
            
            return bool(result)

        except Exception as e:
            logger.error(
                f"Failed to delete engine for session {exam_session_id}: {e}"
            )
            return False

    async def exists(self, exam_session_id: int) -> bool:
        """
        Check if engine state exists in Redis.
        
        Args:
            exam_session_id: ID of exam session
        
        Returns:
            bool: True if state exists, False otherwise
        """
        key = self._key(exam_session_id)
        return bool(await self.redis.exists(key))

    async def get_ttl(self, exam_session_id: int) -> int:
        """
        Get remaining TTL for engine state.
        
        Args:
            exam_session_id: ID of exam session
        
        Returns:
            int: Remaining TTL in seconds (-2 if key doesn't exist, -1 if no TTL)
        """
        key = self._key(exam_session_id)
        return await self.redis.ttl(key)

    async def extend_ttl(
        self,
        exam_session_id: int,
        additional_seconds: int
    ) -> bool:
        """
        Extend TTL for engine state.
        
        Useful for long exams to prevent expiration.
        
        Args:
            exam_session_id: ID of exam session
            additional_seconds: Seconds to add to current TTL
        
        Returns:
            bool: True if extended, False otherwise
        """
        key = self._key(exam_session_id)
        
        try:
            current_ttl = await self.redis.ttl(key)
            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                await self.redis.expire(key, new_ttl)
                logger.debug(
                    f"Extended TTL for session {exam_session_id} by {additional_seconds}s"
                )
                return True
            return False

        except Exception as e:
            logger.error(
                f"Failed to extend TTL for session {exam_session_id}: {e}"
            )
            return False

    async def get_all_active_sessions(self) -> List[int]:
        """
        Get all active exam session IDs from Redis.
        
        Returns:
            List[int]: List of exam session IDs with stored state
        
        Example:
            active_sessions = await store.get_all_active_sessions()
            print(f"Active exams: {len(active_sessions)}")
        """
        pattern = "adaptive_engine:*"
        keys = await self.redis.keys(pattern)
        
        session_ids = []
        for key in keys:
            try:
                # Extract session ID from key
                session_id = int(key.split(":")[-1])
                session_ids.append(session_id)
            except (ValueError, IndexError):
                logger.warning(f"Invalid engine key format: {key}")
        
        return session_ids

    async def get_engine_summary(self, exam_session_id: int) -> Optional[Dict[str, Any]]:
        """
        Get summary of engine state without loading full engine.
        
        Args:
            exam_session_id: ID of exam session
        
        Returns:
            Dict with summary info, or None if not found
        
        Example:
            summary = await store.get_engine_summary(123)
            print(f"Theta: {summary['theta']}, Items: {summary['items_completed']}")
        """
        key = self._key(exam_session_id)
        
        try:
            raw = await self.redis.get(key)
            if not raw:
                return None
            
            data = json.loads(raw)
            
            return {
                "theta": data.get("theta", 0.0),
                "standard_error": data.get("standard_error", 999.0),
                "items_completed": data.get("items_completed", 0),
                "max_items": data.get("max_items", 20),
                "ttl": await self.get_ttl(exam_session_id)
            }

        except Exception as e:
            logger.error(
                f"Failed to get engine summary for session {exam_session_id}: {e}"
            )
            return None
