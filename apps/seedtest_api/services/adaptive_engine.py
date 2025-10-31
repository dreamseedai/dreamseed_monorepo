"""Adaptive engine session state management.

This module provides session state retrieval for adaptive testing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# In-memory session state storage (for active sessions)
_SESSION_STATES: Dict[str, Dict[str, Any]] = {}


def get_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session state for a given session_id.
    
    Returns None if session not found in memory.
    In production, this may also check DB or Redis.
    """
    return _SESSION_STATES.get(session_id)


def set_session_state(session_id: str, state: Dict[str, Any]) -> None:
    """Store session state in memory."""
    _SESSION_STATES[session_id] = state


def clear_session_state(session_id: str) -> None:
    """Remove session state from memory."""
    _SESSION_STATES.pop(session_id, None)


# Legacy compatibility functions for exams router

def next_difficulty(current_diff: int, correct: bool) -> int:
    """Calculate next difficulty based on correctness."""
    if correct:
        return min(current_diff + 1, 5)
    else:
        return max(current_diff - 1, 1)


def score_answer(answer_data: Dict[str, Any]) -> tuple[int, bool]:
    """Score an answer. Returns (score, is_correct)."""
    correct = bool(answer_data.get("correct", False))
    return 1 if correct else 0, correct


def next_question_stub(difficulty: int) -> Dict[str, Any]:
    """Stub function to return a question."""
    return {
        "question_id": f"q_stub_{difficulty}",
        "title": "Sample Question",
        "stem": "This is a placeholder question.",
        "options": ["A", "B", "C", "D"],
        "difficulty": difficulty,
    }


def select_next(session_id: str) -> Optional[Dict[str, Any]]:
    """Select next question for a session."""
    state = get_session_state(session_id)
    if not state:
        return None
    # Stub implementation
    return next_question_stub(3)


def start_session(exam_id: str, user_id: str, org_id: Optional[int] = None) -> Dict[str, Any]:
    """Start a new adaptive session."""
    import uuid
    from datetime import datetime, timezone
    
    session_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc).isoformat()
    
    state = {
        "session_id": session_id,
        "exam_id": exam_id,
        "user_id": user_id,
        "org_id": org_id,
        "theta": 0.0,
        "responses": [],
        "start_time": start_time,
    }
    set_session_state(session_id, state)
    return {
        "exam_session_id": session_id,
        "exam_id": exam_id,
        "start_time": start_time,
    }


def submit_answer(session_id: str, question_id: str, answer: str, elapsed_time: Optional[float] = None) -> Dict[str, Any]:
    """Submit an answer and update session state."""
    state = get_session_state(session_id)
    if not state:
        return {"error": "session_not_found"}
    
    # Stub: assume correct for now
    response = {
        "question_id": question_id,
        "answer": answer,
        "correct": True,  # Stub
        "elapsed_time": elapsed_time,
    }
    
    responses = state.get("responses", [])
    responses.append(response)
    state["responses"] = responses
    
    # Check if finished (stub: finish after 10 questions)
    finished = len(responses) >= 10
    if finished:
        state["completed"] = True
    
    set_session_state(session_id, state)
    
    return {
        "finished": finished,
        "result": {
            "score": len([r for r in responses if r.get("correct")]),
            "total": len(responses),
        } if finished else None,
    }


__all__ = [
    "get_session_state", 
    "set_session_state", 
    "clear_session_state",
    "next_difficulty",
    "score_answer",
    "next_question_stub",
    "select_next",
    "start_session",
    "submit_answer",
]

