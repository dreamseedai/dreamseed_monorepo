import os
import sys
from pathlib import Path

# Ensure LOCAL_DEV bypass and import path
os.environ.setdefault("LOCAL_DEV", "true")

PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from fastapi.testclient import TestClient  # type: ignore
from seedtest_api.main import app

client = TestClient(app)


def test_finish_triggers_compute(monkeypatch):
    # Spy on compute_result used inside exams router
    calls = []

    # Import the router module where compute_result is referenced
    import seedtest_api.routers.exams as exams_mod

    def fake_compute_result(
        session_id: str, force: bool = False, *, user_id=None, exam_id=None
    ):
        calls.append(
            {
                "session_id": session_id,
                "force": force,
                "user_id": user_id,
                "exam_id": exam_id,
            }
        )
        # Return a minimal ready payload
        return {
            "session_id": session_id,
            "status": "ready",
            "score": {"raw": 0, "scaled": 0},
        }

    monkeypatch.setattr(exams_mod, "compute_result", fake_compute_result)

    # Create session (LOCAL_DEV stubbed auth grants exam:write)
    r = client.post("/api/seedtest/exams", json={"exam_id": "math_adaptive"})
    assert r.status_code == 200, r.text
    session_id = r.json()["exam_session_id"]

    # Submit answers until finished; bank IDs fallback to strings like "1","2",...
    # We can reuse the same id for simplicity since submit path doesn't enforce administered set.
    for i in range(10):
        rr = client.post(
            f"/api/seedtest/exams/{session_id}/response",
            json={"question_id": "1", "answer": "3"},
        )
        assert rr.status_code == 200, rr.text
        body = rr.json()
        if body.get("done"):
            break

    # At finish, router should have invoked compute_result once (idempotent semantics acceptable)
    assert len(calls) >= 1
    last = calls[-1]
    assert last["session_id"] == session_id
    # Should force recompute at finish
    assert last["force"] is True
    # LOCAL_DEV auth stub provides a dev user id by default
    assert last["user_id"] in ("dev-user", "", None)
