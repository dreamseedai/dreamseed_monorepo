"""
Adaptive Engine State Store - Redis-based persistence

Provides Redis-based storage for AdaptiveEngine state.
"""
from __future__ import annotations
from typing import List
import json

import redis.asyncio as redis

from app.core.services.exam_engine import AdaptiveEngine


class AdaptiveEngineStateStore:
    """
    Redis-based AdaptiveEngine state store.
    
    Key format: adaptive_engine:{exam_session_id}
    Value format: JSON with theta, item_params_list, responses
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client

    def _key(self, exam_session_id: int) -> str:
        return f"adaptive_engine:{exam_session_id}"

    async def load_engine(
        self,
        exam_session_id: int,
        initial_theta: float = 0.0
    ) -> AdaptiveEngine:
        """Load engine state from Redis or create new engine."""
        key = self._key(exam_session_id)
        raw = await self.redis.get(key)
        
        if not raw:
            return AdaptiveEngine(initial_theta=initial_theta)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return AdaptiveEngine(initial_theta=initial_theta)

        engine = AdaptiveEngine(initial_theta=data.get("theta", initial_theta))
        engine.item_params_list = data.get("item_params_list", [])
        engine.responses = data.get("responses", [])
        
        return engine

    async def save_engine(
        self,
        exam_session_id: int,
        engine: AdaptiveEngine,
        ttl_sec: int = 3600
    ) -> None:
        """Save AdaptiveEngine state to Redis as JSON."""
        key = self._key(exam_session_id)
        
        payload = {
            "theta": engine.theta,
            "item_params_list": engine.item_params_list,
            "responses": engine.responses,
        }
        
        raw = json.dumps(payload)
        await self.redis.set(key, raw, ex=ttl_sec)

    async def delete_engine(self, exam_session_id: int) -> None:
        """Delete engine state from Redis."""
        key = self._key(exam_session_id)
        await self.redis.delete(key)

    async def exists(self, exam_session_id: int) -> bool:
        """Check if engine state exists in Redis."""
        key = self._key(exam_session_id)
        return await self.redis.exists(key) > 0

    async def get_all_sessions(self) -> List[int]:
        """Get all active exam session IDs with saved states."""
        pattern = "adaptive_engine:*"
        keys = await self.redis.keys(pattern)
        
        session_ids = []
        for key in keys:
            try:
                session_id = int(key.split(":")[-1])
                session_ids.append(session_id)
            except (ValueError, IndexError):
                continue
        
        return session_ids

    async def clear_all(self) -> int:
        """Clear all adaptive engine states from Redis."""
        pattern = "adaptive_engine:*"
        keys = await self.redis.keys(pattern)
        
        if keys:
            return await self.redis.delete(*keys)
        return 0
