import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from seedtest_api.services import result_service  # type: ignore

# Ensure package imports resolve and LOCAL_DEV bypass is active before imports
os.environ.setdefault("LOCAL_DEV", "true")

PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.main import app  # noqa: E402

client = TestClient(app)


def _stub_state(monkeypatch):
    def fake_state(_sid: str):
        return {
            "responses": [
                {"question_id": 1, "topic": "algebra", "correct": True},
                {"question_id": 2, "topic": "geometry", "correct": False},
            ]
        }

    monkeypatch.setattr(result_service, "get_session_state", fake_state)


def test_stable_true_omits_timestamps(monkeypatch):
    # Ensure global flag is off to verify per-request override
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("RESULT_EXCLUDE_TIMESTAMPS", "false")
    _stub_state(monkeypatch)
    sid = "STABLE_SESS_1"

    r = client.post(f"/api/seedtest/exams/{sid}/result", params={"stable": True})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "created_at" not in data
    assert "updated_at" not in data  # model already excludes updated_at


def test_stable_false_includes_created_at_even_when_env_true(monkeypatch):
    # Turn on global exclusion but override per-request to include
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("RESULT_EXCLUDE_TIMESTAMPS", "true")
    _stub_state(monkeypatch)
    sid = "STABLE_SESS_2"

    r = client.post(f"/api/seedtest/exams/{sid}/result", params={"stable": False})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "created_at" in data  # per-request false forces include
    # updated_at remains excluded by response_model_exclude
