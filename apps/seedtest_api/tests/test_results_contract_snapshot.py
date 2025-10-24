import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

# Ensure package path and LOCAL_DEV for bypass
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services import result_service  # noqa: E402

client = TestClient(app)

EXPECTED_KEYS = {
    "exam_session_id",
    "user_id",
    "exam_id",
    "score",
    "ability_estimate",
    "standard_error",
    "percentile",
    "topic_breakdown",
    "questions",
    "recommendations",
    "created_at",
    "status",
}


def test_result_contract_keyset_snapshot(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")

    def fake_state(_sid: str):
        return {
            "responses": [
                {"question_id": 1, "topic": "algebra", "correct": True},
                {"question_id": 2, "topic": "geometry", "correct": False},
            ],
            "theta": 0.0,
        }

    monkeypatch.setattr(result_service, "get_session_state", fake_state)

    sid = "SNAPSHOT_SESS_1"
    # Force deterministic created_at by updating after upsert
    from seedtest_api.services import result_service as rs  # type: ignore
    from seedtest_api.services.db import get_session  # type: ignore

    orig_upsert = rs.upsert_result

    def patched_upsert(session_id, result_json, score_raw, score_scaled, **kwargs):
        orig_upsert(session_id, result_json, score_raw, score_scaled, **kwargs)
        fixed = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        with get_session() as s:
            s.execute(text("UPDATE exam_results SET created_at=:t, updated_at=:t WHERE session_id=:sid"), {"t": fixed, "sid": session_id})

    monkeypatch.setattr(rs, "upsert_result", patched_upsert)

    r = client.post(f"/api/seedtest/exams/{sid}/result")
    assert r.status_code == 200, r.text
    data = r.json()

    # Snapshot-style: ensure the response keys match contract shape
    assert set(data.keys()) == EXPECTED_KEYS

    # A couple of type/shape sanity checks
    assert isinstance(data["topic_breakdown"], list)
    assert isinstance(data["questions"], list)

    # Fetch via GET (reads from DB) and assert deterministic timestamp
    r2 = client.get(f"/api/seedtest/exams/{sid}/result")
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert str(d2["created_at"]).startswith("2025-01-02T03:04:05")
