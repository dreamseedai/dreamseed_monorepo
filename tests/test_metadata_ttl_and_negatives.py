import time
import types
import json

import pytest
from fastapi.testclient import TestClient

from adaptive_engine.main import app
from adaptive_engine import config as cfg


@pytest.fixture
def client():
    return TestClient(app)


def test_settings_root_metadata_fields(client, monkeypatch):
    # Patch get_settings for admin token and policy TTL
    import adaptive_engine.routers.settings as settings_router

    monkeypatch.setattr(
        settings_router,
        "get_settings",
        lambda: cfg.AppSettings(admin_token="secret", selection_policy_ttl_sec=60),
        raising=True,
    )

    # Write a runtime policy in a specific namespace
    policy = {
        "prefer_balanced": False,
        "deterministic": True,
        "max_per_topic": 1,
        "top_k_random": None,
        "info_band_fraction": 0.05,
    }
    r = client.patch(
        "/api/settings/selection",
        params={"namespace": "math:algebra"},
        headers={"X-Admin-Token": "secret"},
        json=policy,
    )
    assert r.status_code == 200

    # Query effective settings with resolve_hierarchy
    r = client.get("/api/settings", params={"namespace": "math:algebra"})
    assert r.status_code == 200
    data = r.json()
    assert data["selection_policy_source"] in {"runtime", "redis"}  # runtime expected
    assert data["selection_policy_resolved_namespace"] == "math:algebra"
    assert isinstance(data["selection_policy_last_updated"], (str, type(None)))


def test_reports_with_session_id(client, monkeypatch):
    # Start a session and answer one item to populate answered info
    r = client.post("/api/exam/start", json={"user_id": 9, "exam_id": 42})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    # Request next to get a question
    available = [
        {"question_id": "X1", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T"},
        {"question_id": "X2", "a": 0.8, "b": 0.1, "c": 0.2, "topic": "T"},
    ]
    n = client.post(
        "/api/exam/next",
        params={"session_id": sid},
        json={"theta": 0.0, "available_questions": available, "seen_ids": []},
    )
    assert n.status_code == 200
    q = n.json()["question"]
    assert q is not None
    # Answer
    a = client.post(
        "/api/exam/answer",
        params={"session_id": sid},
        json={"theta": 0.0, "question": q, "correct": True, "answered_items": []},
    )
    assert a.status_code == 200

    # Now request report by session_id
    rep = client.get("/api/reports/theta-se.png", params={"session_id": sid})
    assert rep.status_code == 200
    assert rep.headers.get("content-type") == "image/png"


def test_selection_policy_ttl_and_last_updated(client, monkeypatch):
    # Configure TTL to short value and patch time to simulate expiry
    import adaptive_engine.routers.settings as settings_router

    base = cfg.AppSettings(admin_token="secret", selection_policy_ttl_sec=1)
    # Patch both router and config to ensure set_selection_policy uses TTL
    monkeypatch.setattr(settings_router, "get_settings", lambda: base, raising=True)
    monkeypatch.setattr(cfg, "get_settings", lambda: base, raising=True)

    # Set runtime policy
    policy = {
        "prefer_balanced": True,
        "deterministic": True,
        "max_per_topic": None,
        "top_k_random": None,
        "info_band_fraction": 0.05,
    }
    r = client.patch(
        "/api/settings/selection", headers={"X-Admin-Token": "secret"}, json=policy
    )
    assert r.status_code == 200

    # Immediately should report runtime source and a last_updated string
    r = client.get("/api/settings")
    data = r.json()
    assert data["selection_policy_source"] in {"runtime", "redis"}
    assert isinstance(data["selection_policy_last_updated"], (str, type(None)))

    # Simulate time passing beyond TTL by patching time.time used in config
    import adaptive_engine.config as c2

    start = time.time()
    monkeypatch.setattr(c2.time, "time", lambda: start + 5, raising=True)

    # After TTL, policy should expire back to env defaults (source likely 'env')
    r2 = client.get("/api/settings")
    data2 = r2.json()
    assert data2["selection_policy_source"] in {"env", "redis"}


def test_reports_bad_input_and_settings_bad_token(client, monkeypatch):
    # Reports: mismatched arrays should yield 400
    r = client.get(
        "/api/reports/theta-se.png", params=[("theta", 0.0), ("se", 0.5), ("se", 0.4)]
    )
    assert r.status_code == 400

    # Settings reset-to-env: bad token should 401 when admin token is set
    import adaptive_engine.routers.settings as settings_router

    monkeypatch.setattr(
        settings_router,
        "get_settings",
        lambda: cfg.AppSettings(admin_token="secret"),
        raising=True,
    )
    r2 = client.post("/api/settings/selection/reset-to-env")
    assert r2.status_code == 401
