import json
import types
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adaptive_engine.main import app
from adaptive_engine import config as cfg


@pytest.fixture
def client():
    return TestClient(app)


def test_settings_read_and_write_with_admin_token(client, monkeypatch):
    # Set an admin token in settings
    import adaptive_engine.routers.settings as settings_router

    monkeypatch.setattr(
        settings_router,
        "get_settings",
        lambda: cfg.AppSettings(admin_token="secret"),
        raising=True,
    )

    # Reads should be allowed without token
    r = client.get("/api/settings/selection")
    assert r.status_code == 200

    # Writes should require token
    new_policy = {
        "prefer_balanced": False,
        "deterministic": True,
        "max_per_topic": 2,
        "top_k_random": 3,
        "info_band_fraction": 0.07,
    }
    r = client.patch("/api/settings/selection", json=new_policy)
    assert r.status_code == 401

    # With token, write succeeds
    r = client.patch(
        "/api/settings/selection", headers={"X-Admin-Token": "secret"}, json=new_policy
    )
    assert r.status_code == 200
    got = r.json()
    assert got["deterministic"] is True
    assert got["max_per_topic"] == 2

    # Delete (reset) requires token and returns env default (not None fields but deterministic may flip back)
    r = client.delete("/api/settings/selection", headers={"X-Admin-Token": "secret"})
    assert r.status_code == 200


def test_settings_namespaces_with_stubbed_redis(client, monkeypatch):
    # Stub Redis client in config to emulate two namespaces
    class FakeRedis:
        def __init__(self):
            self.store: dict[str, str] = {}

        def get(self, key: str) -> Any:
            return self.store.get(key)

        def set(self, key: str, value: str):
            self.store[key] = value

        def scan_iter(self, match: str):
            # Basic pattern support for "<prefix>*selection_policy"
            # We yield keys that start with prefix and end with selection_policy
            needle_prefix = match.split("*")[0]
            needle_suffix = match.split("*")[-1]
            for k in list(self.store.keys()):
                if k.startswith(needle_prefix) and k.endswith(needle_suffix):
                    yield k

    fake = FakeRedis()
    prefix = cfg.get_settings().redis_key_prefix
    # Store two namespace policies in Redis
    payload = json.dumps(
        {
            "policy": {
                "prefer_balanced": True,
                "deterministic": False,
                "max_per_topic": None,
                "top_k_random": None,
                "info_band_fraction": 0.05,
            },
            "last_updated": "2025-01-01T00:00:00Z",
        }
    )
    fake.set(f"{prefix}math:algebra:selection_policy", payload)
    fake.set(f"{prefix}math:selection_policy", payload)

    # Patch redis client factory to return our fake
    monkeypatch.setattr(
        cfg,
        "redis",
        types.SimpleNamespace(
            Redis=types.SimpleNamespace(from_url=lambda *a, **k: fake)
        ),
        raising=False,
    )

    # Query namespaces
    r = client.get("/api/settings/namespaces")
    assert r.status_code == 200
    data = r.json()
    names = data["namespaces"]
    assert "" in names  # global always included
    assert "math" in names
    assert "math:algebra" in names


def test_reports_theta_se_png(client):
    r = client.get(
        "/api/reports/theta-se.png",
        params=[
            ("theta", 0.0),
            ("theta", 0.5),
            ("se", 0.6),
            ("se", 0.5),
            ("title", "t"),
        ],
    )
    assert r.status_code == 200
    assert r.headers.get("content-type") == "image/png"


def test_ability_estimator_se_accumulation():
    from adaptive_engine.services.ability_estimator import estimate_standard_error

    # Higher info should reduce SE; simulate two steps with increasing info
    se1 = estimate_standard_error(theta=0.0, answered_items=[{"info": 0.5}])
    se2 = estimate_standard_error(
        theta=0.0, answered_items=[{"info": 0.5}, {"info": 2.0}]
    )
    assert se2 <= se1
