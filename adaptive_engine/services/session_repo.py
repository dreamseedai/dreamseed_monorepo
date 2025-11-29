from __future__ import annotations

from typing import Optional

from adaptive_engine.config import get_settings
from adaptive_engine.models.session import SessionState
from adaptive_engine.services import session_store
from adaptive_engine.services.session_store_redis import get_redis_store


_backend_override: Optional[str] = None


def set_backend_override(backend: Optional[str]) -> None:
    global _backend_override
    _backend_override = backend


def _redis_available(redis_store) -> bool:
    try:
        r = redis_store._r  # type: ignore[attr-defined]
        return bool(r.ping())
    except Exception:
        return False


class SessionRepo:
    def __init__(self) -> None:
        s = get_settings()
        self.backend = _backend_override or s.session_backend
        if self.backend == "redis":
            self._redis = get_redis_store()
            if not _redis_available(self._redis):
                # Fallback to memory if ping fails
                self.backend = "memory"
                self._redis = None
        else:
            self._redis = None

    def create(self, user_id: int, exam_id: int, time_limit_sec: Optional[int] = None) -> SessionState:
        if self.backend == "redis" and self._redis is not None:
            return self._redis.create_session(user_id, exam_id, time_limit_sec)
        return session_store.create_session(user_id, exam_id, time_limit_sec)

    def get(self, session_id: str) -> Optional[SessionState]:
        if self.backend == "redis" and self._redis is not None:
            return self._redis.get(session_id)
        return session_store.get_session(session_id)

    def save(self, state: SessionState) -> None:
        if self.backend == "redis" and self._redis is not None:
            self._redis.save(state)
        else:
            session_store.update_session(state)

    def clear(self) -> None:
        if self.backend == "redis" and self._redis is not None:
            self._redis.clear_all()
        else:
            session_store.clear_sessions()


_repo_singleton: Optional[SessionRepo] = None


def get_session_repo() -> SessionRepo:
    global _repo_singleton
    if _repo_singleton is None:
        _repo_singleton = SessionRepo()
    return _repo_singleton
