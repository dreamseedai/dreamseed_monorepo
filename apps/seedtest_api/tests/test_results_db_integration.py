import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Ensure import path to load seedtest_api
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services.db import get_session  # noqa: E402
from seedtest_api.services import result_service  # noqa: E402


pytestmark = pytest.mark.db

client = TestClient(app)


@pytest.fixture(autouse=True)
def _local_dev_true_env(monkeypatch):
    # Use LOCAL_DEV to keep auth permissive for these DB integration tests
    monkeypatch.setenv("LOCAL_DEV", "true")


def _clear_results(session_id: str):
    with get_session() as s:
        s.execute(text("DELETE FROM exam_results WHERE session_id = :sid"), {"sid": session_id})
        s.execute(text("DELETE FROM exam_sessions WHERE session_id = :sid"), {"sid": session_id})


def test_post_creates_db_and_get_returns_same(monkeypatch):
    sid = "11111111-1111-1111-1111-111111111111"
    _clear_results(sid)

    # Provide deterministic session state
    def fake_state(_sid: str):
        return {
            "responses": [
                {"question_id": 1, "topic": "alg", "correct": True},
                {"question_id": 2, "topic": "alg", "correct": False},
                {"question_id": 3, "topic": "geo", "correct": True},
            ]
        }

    monkeypatch.setattr(result_service, "get_session_state", fake_state)

    # POST should compute and upsert
    r = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["exam_session_id"] == sid
    assert body["status"] == "ready"

    # Row exists in DB
    with get_session() as s:
        cnt = s.execute(text("SELECT COUNT(*) FROM exam_results WHERE session_id = :sid"), {"sid": sid}).scalar()
        assert cnt == 1

    # GET without refresh should fetch cached
    r2 = client.get(f"/api/seedtest/exams/{sid}/result")
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2["exam_session_id"] == sid
    assert body2["status"] == "ready"


def test_post_twice_without_force_is_idempotent(monkeypatch):
    sid = "22222222-2222-2222-2222-222222222222"
    _clear_results(sid)

    # Simple state: 1/1 correct
    monkeypatch.setattr(
        result_service,
        "get_session_state",
        lambda _sid: {"responses": [{"question_id": 1, "topic": "alg", "correct": True}]},
    )

    r1 = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r1.status_code == 200
    d1 = r1.json()

    # Second POST without force should be a cache hit (no second upsert)
    r2 = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d1["score"] == d2["score"]

    with get_session() as s:
        cnt = s.execute(text("SELECT COUNT(*) FROM exam_results WHERE session_id = :sid"), {"sid": sid}).scalar()
        assert cnt == 1


def test_post_nonexistent_session_returns_404(monkeypatch):
    sid = "77777777-7777-7777-7777-777777777777"
    _clear_results(sid)
    # No state and no DB row
    monkeypatch.setattr(result_service, "get_session_state", lambda _sid: None)
    r = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r.status_code == 404


def test_unauthorized_calls_return_401(monkeypatch):
    # Strict mode and no Authorization header should 401
    monkeypatch.setenv("LOCAL_DEV", "false")
    sid = "55555555-5555-5555-5555-555555555555"
    _clear_results(sid)
    # GET
    r1 = client.get(f"/api/seedtest/exams/{sid}/result")
    assert r1.status_code == 401
    # POST
    r2 = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r2.status_code == 401


def test_post_force_recompute_updates_score(monkeypatch):
    sid = "66666666-6666-6666-6666-666666666666"
    _clear_results(sid)

    # Initial state: 1/2 correct
    monkeypatch.setattr(
        result_service,
        "get_session_state",
        lambda _sid: {
            "responses": [
                {"question_id": 1, "topic": "alg", "correct": True},
                {"question_id": 2, "topic": "alg", "correct": False},
            ]
        },
    )
    r1 = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r1.status_code == 200
    score1 = r1.json()["score"]

    # Change to 2/2 correct and force recompute
    monkeypatch.setattr(
        result_service,
        "get_session_state",
        lambda _sid: {
            "responses": [
                {"question_id": 1, "topic": "alg", "correct": True},
                {"question_id": 2, "topic": "alg", "correct": True},
            ]
        },
    )
    r2 = client.post(f"/api/seedtest/exams/{sid}/result", json={"force": True})
    assert r2.status_code == 200
    score2 = r2.json()["score"]
    assert score2 >= score1


    
