from __future__ import annotations

import json
import uuid
from typing import Optional

import redis

from adaptive_engine.config import get_settings
from adaptive_engine.models.session import SessionState


class RedisSessionStore:
    def __init__(self) -> None:
        s = get_settings()
        self._r = redis.Redis.from_url(s.redis_url, decode_responses=True)
        self._ttl = int(s.session_ttl_sec)
        self._prefix = f"{s.redis_key_prefix}sess:"

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"

    def create_session(
        self, user_id: int, exam_id: int, time_limit_sec: Optional[int] = None
    ) -> SessionState:
        session_id = str(uuid.uuid4())
        state = SessionState(
            session_id=session_id,
            user_id=user_id,
            exam_id=exam_id,
            remaining_time_sec=time_limit_sec,
        )
        self.save(state)
        return state

    def get(self, session_id: str) -> Optional[SessionState]:
        data = self._r.get(self._key(session_id))
        if data is None:
            return None
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")
        data_str = str(data)
        obj = json.loads(data_str)
        return SessionState.model_validate(obj)

    def save(self, state: SessionState) -> None:
        key = self._key(state.session_id)
        self._r.setex(key, self._ttl, json.dumps(state.model_dump()))

    def clear_all(self) -> None:
        # Caution: in a shared Redis, consider scanning by prefix
        for key in self._r.scan_iter(match=f"{self._prefix}*"):
            self._r.delete(key)


_store_singleton: Optional[RedisSessionStore] = None


def get_redis_store() -> RedisSessionStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = RedisSessionStore()
    return _store_singleton
