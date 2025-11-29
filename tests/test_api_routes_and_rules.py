import random

import pytest
from fastapi.testclient import TestClient

from adaptive_engine.main import app
from adaptive_engine import config as cfg


@pytest.fixture(autouse=True)
def deterministic_random(monkeypatch):
    random.seed(42)
    yield


def test_exam_flow_start_next_answer_state(monkeypatch):
    client = TestClient(app)

    # Configure policy to be deterministic for predictability
    monkeypatch.setattr(
        cfg,
        "get_selection_policy",
        lambda: cfg.SelectionPolicy(prefer_balanced=False, deterministic=True, max_per_topic=None, top_k_random=None, info_band_fraction=0.05),
        raising=True,
    )

    # Start session
    r = client.post("/api/exam/start", json={"user_id": 1, "exam_id": 7})
    assert r.status_code == 200
    data = r.json()
    session_id = data["session_id"]
    assert data["status"] == "started"

    # Next question (first-item heuristic applies when seen_ids is empty)
    available = [
        {"question_id": "Q1", "a": 1.0, "b": -0.2, "c": 0.2, "topic": "T1"},
        {"question_id": "Q2", "a": 1.0, "b": 0.1, "c": 0.2, "topic": "T2"},
    ]
    r = client.post("/api/exam/next", params={"session_id": session_id}, json={"theta": 0.0, "available_questions": available, "seen_ids": []})
    assert r.status_code == 200
    q = r.json()["question"]
    assert q is not None

    # Submit answer, check histories update and no stop (with high threshold implied)
    r = client.post(
        "/api/exam/answer",
        params={"session_id": session_id},
        json={"theta": 0.0, "question": q, "correct": True, "answered_items": []},
    )
    assert r.status_code == 200
    ans = r.json()
    assert "theta_after" in ans
    assert "std_error" in ans

    # Check state endpoint contains histories
    r = client.get("/api/exam/state", params={"session_id": session_id})
    assert r.status_code == 200
    st = r.json()
    assert st["answered_count"] >= 1
    assert len(st["theta_history"]) >= 2  # initial + after answer
    assert len(st["se_history"]) >= 1


def test_stop_rules_edge_cases():
    from adaptive_engine.services.stop_rules import should_stop

    # Stop by max questions
    assert should_stop(num_answered=10, max_questions=10, elapsed_time_sec=0, time_limit_sec=None, std_error=1.0) is True
    # Stop by time limit
    assert should_stop(num_answered=1, max_questions=10, elapsed_time_sec=60, time_limit_sec=60, std_error=1.0) is True
    # Stop by SE threshold
    assert should_stop(num_answered=1, max_questions=10, elapsed_time_sec=0, time_limit_sec=60, std_error=0.2, threshold=0.3) is True
    # Continue when none reached
    assert should_stop(num_answered=1, max_questions=10, elapsed_time_sec=10, time_limit_sec=60, std_error=0.5, threshold=0.3) is False


def test_irt_math_edge_cases():
    from adaptive_engine.utils.irt_math import irt_probability, fisher_information

    # Extreme theta*a leading to overflow should clamp
    p_hi = irt_probability(theta=10.0, a=10.0, b=0.0, c=0.2)
    assert 0.99 <= p_hi <= 1.0
    p_lo = irt_probability(theta=-10.0, a=10.0, b=0.0, c=0.2)
    assert abs(p_lo - 0.2) < 1e-6

    # Fisher information stable when denom small
    info = fisher_information(theta=0.0, a=1.0, b=0.0, c=0.2)
    assert info >= 0.0
