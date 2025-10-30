"""Minimal in-memory adaptive engine for SeedTest API.

Provides the functions imported by routers/services:
 - start_session, select_next, submit_answer, score_answer, next_difficulty, next_question_stub
 - get_session_state
 - fisher_information_3pl (for standard error calculations)

This implementation is intentionally simple and self-contained so local runs,
tests, and CI E2E smoke can execute without a DB.
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Dict, Optional


# In-memory session store (short-lived, dev/test only)
_SESSIONS: Dict[str, Dict[str, Any]] = {}
_TOPICS = ["대수", "기하", "확률"]


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def start_session(exam_id: str, user_id: str, org_id: int) -> Dict[str, Any]:
    sid = str(uuid.uuid4())
    _SESSIONS[sid] = {
        "session_id": sid,
        "exam_id": exam_id,
        "user_id": user_id,
        "org_id": org_id,
        "created_at": _now_iso(),
        "theta": 0.0,
        "step": 0,
        "responses": [],
        "finished": False,
        "max_steps": 5,
    }
    return {"exam_session_id": sid, "start_time": _now_iso(), "exam_id": exam_id}


def _gen_question(step: int) -> Dict[str, Any]:
    qid = str(step)
    topic = _TOPICS[step % len(_TOPICS)]
    return {
        "id": qid,
        "text": f"Q{qid}: {topic} 기본 개념 문제",
        "type": "mcq",
        "options": ["A", "B", "C", "D"],
        "_topic": topic,
    }


def next_question_stub(difficulty: Optional[int] = None) -> Dict[str, Any]:
    return _gen_question(1)


def select_next(session_id: str) -> Optional[Dict[str, Any]]:
    s = _SESSIONS.get(session_id)
    if not s or s.get("finished"):
        return None
    step = int(s.get("step", 0)) + 1
    s["step"] = step
    if step > int(s.get("max_steps", 5)):
        s["finished"] = True
        return None
    q = _gen_question(step)
    s["_last_q"] = q
    return q


def next_difficulty(prev: Optional[int], correct: bool) -> int:
    base = int(prev or 3)
    base += 1 if correct else -1
    return max(1, min(5, base))


def score_answer(data: Dict[str, Any]) -> tuple[int, bool]:
    try:
        qid = int(str(data.get("question_id")))
    except Exception:
        qid = 1
    correct_ans = "A" if (qid % 2 == 0) else "B"
    given = str(data.get("answer") or "").strip().upper()
    is_correct = given == correct_ans
    nd = next_difficulty(data.get("difficulty"), is_correct)
    return nd, is_correct


def submit_answer(
    session_id: str, question_id: str, answer: str, elapsed_time: Optional[float]
) -> Dict[str, Any]:
    s = _SESSIONS.get(session_id)
    if not s:
        return {"error": "session_not_found"}
    q = s.get("_last_q") or _gen_question(int(s.get("step", 1)))
    try:
        qid = int(str(question_id))
    except Exception:
        qid = int(s.get("step", 1))
    correct_ans = "A" if (qid % 2 == 0) else "B"
    is_correct = (answer or "").strip().upper() == correct_ans
    theta = float(s.get("theta", 0.0)) + (0.2 if is_correct else -0.2)
    s["theta"] = theta
    s.setdefault("responses", []).append(
        {
            "question_id": qid,
            "topic": q.get("_topic", "general"),
            "correct": bool(is_correct),
            "a": 1.0,
            "b": 0.0,
            "c": 0.2,
            "answer": answer,
            "correct_answer": correct_ans,
            "explanation": f"정답은 {correct_ans} 입니다.",
            "elapsed_time": float(elapsed_time or 0.0),
        }
    )
    finished = bool(s.get("finished")) or (
        int(s.get("step", 1)) >= int(s.get("max_steps", 5))
    )
    s["finished"] = finished
    if finished:
        return {"finished": True, "result": {"items": len(s.get("responses", []))}}
    return {"finished": False}


def get_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    s = _SESSIONS.get(session_id)
    if not s:
        return None
    return {
        "session_id": s.get("session_id"),
        "user_id": s.get("user_id"),
        "org_id": s.get("org_id"),
        "theta": s.get("theta"),
        "responses": list(s.get("responses", [])),
        "completed": bool(s.get("finished")),
        "started_at": s.get("created_at"),
        "updated_at": _now_iso(),
    }


def fisher_information_3pl(a: float, b: float, c: float, theta: float) -> float:
    try:
        a = float(a)
        b = float(b)
        c = float(c)
        theta = float(theta)
        c = max(0.0, min(0.35, c))
        L = 1.0 / (1.0 + math.exp(-a * (theta - b)))
        P = c + (1.0 - c) * L
        P = min(max(P, 1e-6), 1.0 - 1e-6)
        num = (a * (P - c) / (1.0 - c)) ** 2
        denom = P * (1.0 - P)
        return float(num / denom)
    except Exception:
        return 0.0


__all__ = [
    "start_session",
    "select_next",
    "submit_answer",
    "score_answer",
    "next_difficulty",
    "next_question_stub",
    "get_session_state",
    "fisher_information_3pl",
]
