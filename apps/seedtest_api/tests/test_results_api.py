import os
import sys
from pathlib import Path

# Ensure package imports resolve and LOCAL_DEV bypass is active before imports
os.environ.setdefault("LOCAL_DEV", "true")

# Add parent directory of this package (apps/) to sys.path so `seedtest_api` is importable
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from fastapi.testclient import TestClient  # type: ignore
from seedtest_api.main import app
from seedtest_api.services import result_service

client = TestClient(app)


def test_create_and_get_result(monkeypatch):
    # Stub session state with 2 correct out of 3
    def fake_get_session_state(session_id: str):
        return {
            "responses": [
                {"question_id": "q1", "topic": "algebra", "correct": True},
                {"question_id": "q2", "topic": "algebra", "correct": False},
                {"question_id": "q3", "topic": "geometry", "correct": True},
            ]
        }

    monkeypatch.setattr(result_service, "get_session_state", fake_get_session_state)

    sid = "SESSION_TEST_1"
    # Compute via POST (idempotent creator)
    r = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["exam_session_id"] == sid
    assert data["status"] == "ready"
    # score is the scaled score in contract
    assert isinstance(data["score"], (int, float))
    assert int(data["score"]) in (66, 67)

    # Fetch via GET with refresh=true (strict GET returns 404 if not cached)
    r2 = client.get(f"/api/seedtest/exams/{sid}/result", params={"refresh": True})
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2["exam_session_id"] == sid
    assert "topic_breakdown" in d2 and isinstance(d2["topic_breakdown"], list)
    assert "questions" in d2 and isinstance(d2["questions"], list)


def test_result_not_found(monkeypatch):
    def fake_none(_sid: str):
        return None

    monkeypatch.setattr(result_service, "get_session_state", fake_none)
    r = client.get("/api/seedtest/exams/NOPE/result")
    assert r.status_code == 404


def test_result_pdf_stub():
    r = client.get("/api/seedtest/exams/ANY/result/pdf")
    assert r.status_code == 501


def test_post_result_returns_400_when_not_completed(monkeypatch):
    # Simulate compute_result detecting an incomplete session (DB short-circuit)
    import seedtest_api.routers.results as results_mod
    monkeypatch.setattr(
        results_mod,
        "compute_result",
        lambda session_id, force=False, user_id=None, exam_id=None: {
            "session_id": session_id,
            "status": "not_completed",
        },
    )
    r = client.post("/api/seedtest/exams/00000000-0000-0000-0000-000000000000/result")
    assert r.status_code == 400
