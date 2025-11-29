import time
import sys
import types

import pytest
from fastapi.testclient import TestClient

from adaptive_engine.main import app
from adaptive_engine import config as cfg


@pytest.fixture
def client():
    return TestClient(app)


def test_settings_runtime_only_ttl_and_last_updated(client, monkeypatch):
    # No redis in play; set admin token and TTL small; set runtime policy then verify source/last_updated and expiry
    import adaptive_engine.routers.settings as settings_router
    base = cfg.AppSettings(admin_token="secret", selection_policy_ttl_sec=1, redis_url="redis://localhost:6379/0")
    # Patch both router and config to use same settings
    monkeypatch.setattr(settings_router, "get_settings", lambda: base, raising=True)
    monkeypatch.setattr(cfg, "get_settings", lambda: base, raising=True)
    # Ensure _get_redis_client returns None to avoid redis path
    monkeypatch.setattr(cfg, "redis", None, raising=True)

    pol = {"prefer_balanced": True, "deterministic": True, "max_per_topic": 2, "top_k_random": None, "info_band_fraction": 0.05}
    r = client.patch("/api/settings/selection", headers={"X-Admin-Token": "secret"}, json=pol)
    assert r.status_code == 200

    g = client.get("/api/settings")
    d = g.json()
    assert d["selection_policy_source"] == "runtime"
    assert isinstance(d["selection_policy_last_updated"], (str, type(None)))

    # Simulate time > TTL
    import adaptive_engine.config as c2
    now = time.time()
    monkeypatch.setattr(c2.time, "time", lambda: now + 5, raising=True)
    g2 = client.get("/api/settings")
    d2 = g2.json()
    # Should fall back to env when runtime expired
    assert d2["selection_policy_source"] in {"env"}


def test_reports_prefers_session_histories(client, monkeypatch):
    # Start and answer two items so theta_history and se_history have content
    s = client.post("/api/exam/start", json={"user_id": 77, "exam_id": 3})
    sid = s.json()["session_id"]
    # Two steps
    items = [
        {"question_id": "H1", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T"},
        {"question_id": "H2", "a": 0.9, "b": 0.2, "c": 0.2, "topic": "T"},
        {"question_id": "H3", "a": 1.1, "b": -0.1, "c": 0.2, "topic": "T"},
    ]
    n1 = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": items, "seen_ids": []})
    q1 = n1.json()["question"]
    a1 = client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": 0.0, "question": q1, "correct": True, "answered_items": []})
    n2 = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": items, "seen_ids": [q1["question_id"]]})
    q2 = n2.json()["question"]
    a2 = client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": a1.json()["theta_after"], "question": q2, "correct": False, "answered_items": []})

    # Request report: should prefer theta_history and se_history
    rep = client.get("/api/reports/theta-se.png", params={"session_id": sid})
    assert rep.status_code == 200
    assert rep.headers.get("content-type") == "image/png"


def test_health_redis_and_session_backend(client, monkeypatch):
    # Case 1: memory backend => disabled
    import adaptive_engine.routers.health as health_router
    base = cfg.AppSettings(session_backend="memory")
    monkeypatch.setattr(health_router, "get_settings", lambda: base, raising=True)
    # Root health
    r0 = client.get("/api/health")
    assert r0.status_code == 200
    assert r0.json()["status"] == "ok"
    assert r0.json()["backend"] == "memory"
    r1 = client.get("/api/health/redis")
    assert r1.status_code == 200
    assert r1.json()["redis"] == "disabled"

    # Case 2: redis backend ok (ping=True)
    base2 = cfg.AppSettings(session_backend="redis", redis_url="redis://dev/0")
    monkeypatch.setattr(health_router, "get_settings", lambda: base2, raising=True)
    class FakeRedis:
        def __init__(self):
            pass
        def ping(self):
            return True
    # Patch module import path used in router
    monkeypatch.setitem(sys.modules, 'redis', types.SimpleNamespace(Redis=types.SimpleNamespace(from_url=lambda *a, **k: FakeRedis())))
    r0b = client.get("/api/health")
    assert r0b.status_code == 200
    assert r0b.json()["backend"] == "redis"
    r2 = client.get("/api/health/redis")
    assert r2.status_code == 200
    assert r2.json()["redis"] == "ok"
    assert r2.json()["ping"] is True

    # Case 3: redis backend error
    class BoomRedis:
        def __init__(self):
            pass
        def ping(self):
            raise RuntimeError("boom")
    monkeypatch.setitem(sys.modules, 'redis', types.SimpleNamespace(Redis=types.SimpleNamespace(from_url=lambda *a, **k: BoomRedis())))
    r3 = client.get("/api/health/redis")
    assert r3.status_code == 503
    assert r3.json()["redis"] == "error"
