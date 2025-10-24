import time
from fastapi.testclient import TestClient

from apps.seedtest_api.app_adaptive_demo import app
from apps.seedtest_api.settings import settings


def test_max_items_stop(monkeypatch):
    client = TestClient(app)
    # Ensure fixed mode with low max_items for the test
    monkeypatch.setenv("CAT_MODE", "FIXED")
    monkeypatch.setenv("CAT_MAX_ITEMS", "1")
    # Recreate settings to pick up env
    from importlib import reload
    from apps.seedtest_api import settings as settings_mod
    reload(settings_mod)

    # Start and answer one item -> should terminate by max_items
    r = client.post("/demo/start", json={"theta0": 0.0})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    next_id = r.json()["next_item_id"]
    assert next_id is not None

    r2 = client.post(f"/demo/answer/{sid}", json={"item_id": next_id, "correct": True})
    assert r2.status_code == 200
    body = r2.json()
    assert body["terminated"] is True
    assert body["reason"] == "max_items"
    assert body["next_item_id"] is None


def test_sem_threshold_stop(monkeypatch):
    client = TestClient(app)
    # Variable mode with high threshold so it trips quickly
    monkeypatch.setenv("CAT_MODE", "VARIABLE")
    monkeypatch.setenv("CAT_SEM_THRESHOLD", "10.0")  # enormous to force stop after 1 item
    monkeypatch.setenv("CAT_MIN_ITEMS", "1")
    from importlib import reload
    from apps.seedtest_api import settings as settings_mod
    reload(settings_mod)

    r = client.post("/demo/start", json={"theta0": 0.0})
    sid = r.json()["session_id"]
    next_id = r.json()["next_item_id"]

    r2 = client.post(f"/demo/answer/{sid}", json={"item_id": next_id, "correct": True})
    assert r2.status_code == 200
    body = r2.json()
    assert body["terminated"] is True
    assert body["reason"] == "sem_threshold"


def test_item_cooldown_defers_next(monkeypatch):
    client = TestClient(app)
    # Set cooldown to 5 seconds
    monkeypatch.setenv("CAT_ITEM_COOLDOWN_SECONDS", "5")
    from importlib import reload
    from apps.seedtest_api import settings as settings_mod
    reload(settings_mod)

    r = client.post("/demo/start", json={"theta0": 0.0})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    nid = r.json()["next_item_id"]

    # First answer should return cooldown reason, not a next item
    r2 = client.post(f"/demo/answer/{sid}", json={"item_id": nid, "correct": True})
    assert r2.status_code == 200
    body = r2.json()
    assert body["terminated"] is False
    assert body["reason"] == "cooldown"
    assert body["next_item_id"] is None
    assert body.get("cooldown_remaining") is not None

    # Fast-forward cooldown by monkeypatching time
    # (Here we simply sleep slightly more than 5s to ensure environment compatibility)
    time.sleep(5.2)

    # Next answer should now provide a next item
    nxt = client.post(f"/demo/answer/{sid}", json={"item_id": nid, "correct": True})
    assert nxt.status_code == 200
    body2 = nxt.json()
    assert body2.get("reason") in (None, "pool_exhausted")


def test_min_test_time_gates_sem_stop(monkeypatch):
    client = TestClient(app)
    # Variable mode with very low SEM threshold to stop early, but require min time to gate
    monkeypatch.setenv("CAT_MODE", "VARIABLE")
    monkeypatch.setenv("CAT_SEM_THRESHOLD", "0.01")
    monkeypatch.setenv("CAT_MIN_ITEMS", "1")
    monkeypatch.setenv("CAT_MIN_TEST_TIME_SECONDS", "4")
    from importlib import reload
    from apps.seedtest_api import settings as settings_mod
    reload(settings_mod)

    r = client.post("/demo/start", json={"theta0": 0.0})
    sid = r.json()["session_id"]
    nid = r.json()["next_item_id"]
    # Answer immediately; should not terminate due to min test time
    r2 = client.post(f"/demo/answer/{sid}", json={"item_id": nid, "correct": True})
    assert r2.status_code == 200
    body = r2.json()
    assert body["terminated"] is False
    assert body.get("reason") in (None, "pool_exhausted", "cooldown")
    # Wait and try again to allow min time to pass
    time.sleep(4.2)
    # Use latest next step; if reason was cooldown, answer once more with same item id to clear
    # We don't track a new next id here; the demo will either terminate or move on.
    r3 = client.post(f"/demo/answer/{sid}", json={"item_id": nid, "correct": True})
    assert r3.status_code == 200
    body2 = r3.json()
    # Now it can terminate by SEM or proceed if pool ends; accept either but should not be gated anymore
    assert body2.get("reason") in ("sem_threshold", None, "pool_exhausted")


def test_manual_finish(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("CAT_MODE", "VARIABLE")
    from importlib import reload
    from apps.seedtest_api import settings as settings_mod
    reload(settings_mod)

    r = client.post("/demo/start", json={"theta0": 0.0})
    sid = r.json()["session_id"]
    nid = r.json()["next_item_id"]
    # Request manual finish
    r2 = client.post(f"/demo/answer/{sid}", json={"item_id": nid, "correct": True, "finish_now": True})
    assert r2.status_code == 200
    body = r2.json()
    assert body["terminated"] is True
    assert body["reason"] == "manual_finish"


def test_time_limit_stop(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("CAT_MAX_TIME_SECONDS", "2")
    # Ensure mode not blocking by max items immediately
    monkeypatch.setenv("CAT_MODE", "VARIABLE")
    from importlib import reload
    from apps.seedtest_api import settings as settings_mod
    reload(settings_mod)

    r = client.post("/demo/start", json={"theta0": 0.0})
    sid = r.json()["session_id"]
    nid = r.json()["next_item_id"]
    # Wait until time limit passes
    time.sleep(2.2)
    r2 = client.post(f"/demo/answer/{sid}", json={"item_id": nid, "correct": True})
    assert r2.status_code == 200
    body = r2.json()
    assert body["terminated"] is True
    assert body["reason"] == "time_limit"
