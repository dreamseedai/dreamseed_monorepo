import os
import sys
from pathlib import Path

import pytest

# Ensure package import path and local dev defaults where needed
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.services import result_service  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402


def test_compute_result_basic_success(monkeypatch):
    # No DB path
    monkeypatch.setattr(result_service, "_has_db", lambda: False)

    # Provide a simple session state: 2 correct of 3, topics algebra(2), geometry(1)
    def fake_state(_sid: str):
        return {
            "responses": [
                {"question_id": 1, "topic": "algebra", "correct": True},
                {"question_id": 2, "topic": "algebra", "correct": False},
                {"question_id": 3, "topic": "geometry", "correct": True},
            ],
            "theta": 0.12,
        }

    monkeypatch.setattr(result_service, "get_session_state", fake_state)

    out = result_service.compute_result("sess-1", force=False)
    assert out["status"] == "ready"
    assert out["score"]["raw"] == 2
    # scaled is int around 106 (0.12*50 + 100)
    assert int(out["score"]["scaled"]) in (106,)

    # topic breakdown
    topics = {t["topic"]: t for t in out["topics"]}
    assert topics["algebra"]["total"] == 2
    assert topics["algebra"]["correct"] == 1
    assert topics["geometry"]["total"] == 1
    assert topics["geometry"]["correct"] == 1


def test_compute_result_cache_hit_returns_existing(monkeypatch):
    # Simulate DB present and pre-existing row
    monkeypatch.setattr(result_service, "_has_db", lambda: True)

    existing = {
        "session_id": "sess-cache",
        "status": "ready",
        "score_raw": 3,
        "score_scaled": 120,
        "topics": [{"topic": "algebra", "correct": 3, "total": 5, "accuracy": 0.6}],
    }
    monkeypatch.setattr(
        result_service,
        "get_result_from_db",
        lambda sid, expected_user_id=None: existing,
    )

    # Guard: ensure compute path isn't called
    def boom(_sid: str):
        raise AssertionError("get_session_state should not be called on cache hit")

    monkeypatch.setattr(result_service, "get_session_state", boom)

    out = result_service.compute_result("sess-cache", force=False)
    # Should be exactly the DB path remapped by compute_result caller (here: passthrough)
    assert out["status"] == "ready"
    assert out.get("score_raw") == 3 or (
        out.get("score") and out["score"].get("raw") == 3
    )


def test_compute_result_force_recompute_overrides_cache(monkeypatch):
    monkeypatch.setattr(result_service, "_has_db", lambda: True)
    # Pretend there is an old cached record
    monkeypatch.setattr(
        result_service,
        "get_result_from_db",
        lambda sid, expected_user_id=None: {
            "session_id": sid,
            "status": "ready",
            "score_raw": 1,
            "score_scaled": 50,
        },
    )

    # Provide a new state to force recompute
    def fake_state(_sid: str):
        return {
            "responses": [
                {"question_id": 1, "topic": "algebra", "correct": True},
                {"question_id": 2, "topic": "algebra", "correct": True},
            ]
        }

    monkeypatch.setattr(result_service, "get_session_state", fake_state)

    called = {"upsert": False}

    def fake_upsert(session_id, result_json, score_raw, score_scaled, **kwargs):
        called["upsert"] = True
        assert session_id == "sess-recompute"
        assert isinstance(result_json, dict)

    monkeypatch.setattr(result_service, "upsert_result", fake_upsert)

    out = result_service.compute_result("sess-recompute", force=True)
    assert out["status"] == "ready"
    # New raw score 2
    assert out["score"]["raw"] == 2
    assert called["upsert"] is True


def test_compute_result_error_marks_failed(monkeypatch):
    monkeypatch.setattr(result_service, "_has_db", lambda: True)

    # State exists but aggregate throws
    monkeypatch.setattr(
        result_service,
        "get_session_state",
        lambda _sid: {"responses": [{"correct": True}]},
    )

    def boom_aggregate(_state):
        raise RuntimeError("aggregate failed")

    monkeypatch.setattr(
        result_service, "aggregate_from_session_state", lambda _s: boom_aggregate(_s)
    )

    failed_flag = {"called": False}

    def fake_fail(session_id, **kwargs):
        failed_flag["called"] = True
        assert session_id == "sess-fail"

    monkeypatch.setattr(result_service, "_upsert_failed", fake_fail)

    with pytest.raises(Exception):
        result_service.compute_result("sess-fail", force=True)
    assert failed_flag["called"] is True


def test_upsert_integrity_error_fetches_existing(monkeypatch):
    # Enable DB presence for this unit path, but keep actual DB out by stubbing calls
    monkeypatch.setattr(result_service, "_has_db", lambda: True)

    # Return a minimal state so compute path executes
    monkeypatch.setattr(
        result_service,
        "get_session_state",
        lambda _sid: {"responses": [{"correct": True}]},
    )

    # Simulate integrity error on upsert (race) and existing row is retrievable
    def boom_upsert(*args, **kwargs):
        raise IntegrityError("", {}, Exception("dup"))

    monkeypatch.setattr(result_service, "upsert_result", boom_upsert)
    monkeypatch.setattr(
        result_service,
        "get_result_from_db",
        lambda session_id, expected_user_id=None: {
            "session_id": session_id,
            "status": "ready",
            "score_raw": 1,
            "score_scaled": 100,
        },
    )

    out = result_service.compute_result("sess-race", force=True)
    assert out["status"] == "ready"
    # Ensure winner's values surfaced
    assert out.get("score_raw") == 1 or (
        out.get("score") and out["score"].get("raw") == 1
    )


def test_db_not_completed_short_circuit(monkeypatch):
    # Simulate DB present and an exam_sessions row with completed = false
    monkeypatch.setattr(result_service, "_has_db", lambda: True)

    class _FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, stmt, params):
            class _Res:
                def mappings(self):
                    class _M:
                        def first(self):
                            return {"completed": False}

                    return _M()

            return _Res()

    class _FakeEngine:
        def connect(self):
            return _FakeConn()

    monkeypatch.setattr(result_service, "get_engine", lambda: _FakeEngine())
    monkeypatch.setattr(result_service, "get_session_state", lambda _sid: None)

    out = result_service.compute_result("sess-incomplete", force=False)
    assert out.get("status") == "not_completed"
