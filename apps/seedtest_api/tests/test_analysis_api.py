import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure LOCAL_DEV and import path
os.environ.setdefault("LOCAL_DEV", "true")
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services import result_service  # noqa: E402

client = TestClient(app)


def test_analysis_disabled_returns_501(monkeypatch):
    monkeypatch.setenv("ENABLE_ANALYSIS", "false")
    r = client.get("/api/seedtest/exams/S1/analysis")
    assert r.status_code == 501


def test_analysis_enabled_with_stubbed_result(monkeypatch):
    monkeypatch.setenv("ENABLE_ANALYSIS", "true")

    def fake_compute_result(session_id: str, force: bool = False, **kwargs):
        return {
            "session_id": session_id,
            "status": "ready",
            "score": {"raw": 3, "scaled": 65},
            "topics": [
                {"topic": "algebra", "correct": 2, "total": 3, "accuracy": 0.667},
                {"topic": "geometry", "correct": 1, "total": 2, "accuracy": 0.5},
            ],
            "ability_estimate": 0.1,
            "standard_error": 0.3,
            "percentile": 60,
        }

    monkeypatch.setattr(result_service, "get_result_from_db", lambda *a, **k: None)
    monkeypatch.setattr(result_service, "compute_result", fake_compute_result)

    r = client.get("/api/seedtest/exams/S1/analysis")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["exam_session_id"] == "S1"
    assert "ability" in body and "recommendations" in body
    assert isinstance(body["topic_insights"], list)
