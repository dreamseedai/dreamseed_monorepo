from __future__ import annotations

import threading
import uuid
from typing import Dict, Optional

from adaptive_engine.models.session import SessionState


_LOCK = threading.RLock()
_SESSIONS: Dict[str, SessionState] = {}


def create_session(user_id: int, exam_id: int, time_limit_sec: Optional[int] = None) -> SessionState:
    session_id = str(uuid.uuid4())
    state = SessionState(session_id=session_id, user_id=user_id, exam_id=exam_id, remaining_time_sec=time_limit_sec)
    with _LOCK:
        _SESSIONS[session_id] = state
    return state


def get_session(session_id: str) -> Optional[SessionState]:
    with _LOCK:
        return _SESSIONS.get(session_id)


def update_session(state: SessionState) -> None:
    with _LOCK:
        _SESSIONS[state.session_id] = state


def clear_sessions() -> None:
    with _LOCK:
        _SESSIONS.clear()
