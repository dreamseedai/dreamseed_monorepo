import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure package imports resolve and LOCAL_DEV bypass is active before imports
os.environ.setdefault("LOCAL_DEV", "true")

PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services import result_service  # noqa: E402

client = TestClient(app)


def test_exclude_timestamps_flag(monkeypatch):
    # Ensure DB is disabled for this unit-level test
    monkeypatch.setenv("DATABASE_URL", "")
    # Enable the flag to omit volatile fields
    monkeypatch.setenv("RESULT_EXCLUDE_TIMESTAMPS", "true")

    # Stub session state: simple correctness to produce a result
    def fake_state(_sid: str):
        return {
            "responses": [
                {"question_id": 1, "topic": "algebra", "correct": True},
                {"question_id": 2, "topic": "geometry", "correct": False},
            ]
        }

    monkeypatch.setattr(result_service, "get_session_state", fake_state)

    sid = "FLAG_TS_SESS_1"
    r = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r.status_code == 200, r.text
    data = r.json()

    # With the flag on, timestamps should be omitted from the contract
    assert "created_at" not in data
    assert "updated_at" not in data

    # Other key contract fields should still be present
    for k in ("exam_session_id", "score", "status", "topic_breakdown", "questions"):
        assert k in data
