import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure LOCAL_DEV and import path
os.environ.setdefault("LOCAL_DEV", "true")
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.main import app  # noqa: E402
from seedtest_api.routers import results as results_router  # noqa: E402

client = TestClient(app)


def test_list_opaque_cursor_roundtrip(monkeypatch):
    # Monkeypatch the DB-powered function to avoid DB
    # Prepare a fake page with a legacy next_cursor
    fake_items = [
        {
            "id": 123,
            "session_id": "sessX",
            "user_id": "u1",
            "exam_id": 5,
            "status": "ready",
            "score_raw": 2,
            "score_scaled": 20,
            "created_at": "2025-01-02T03:04:05Z",
            "updated_at": "2025-01-02T03:04:06Z",
        }
    ]
    fake_next = {"updated_at": "2025-01-02T03:04:06Z", "id": "123"}

    def fake_list_results_keyset(**kwargs):
        return {"items": fake_items, "next_cursor": fake_next}
    # Patch directly on the router module, which holds the imported symbol used by the endpoint
    monkeypatch.setattr(results_router, "list_results_keyset", fake_list_results_keyset)

    # First call: should return next_cursor_opaque token
    r1 = client.get("/api/seedtest/results", params={"limit": 1, "order": "asc"})
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    token = body1.get("next_cursor_opaque")
    assert isinstance(token, str) and token.startswith("v1:")

    # Decode token with router helper and feed as cursor param
    dec = results_router._decode_cursor(token)
    assert dec is not None
    ts_iso, _cid = dec
    assert ts_iso.startswith("2025-01-02T03:04:06")

    # Second call: server should accept the opaque cursor
    # We patch the list function to assert the cursor parsing path can run without error.
    def fake_list_results_keyset_page2(**kwargs):
        # Simulate empty next page
        return {"items": [], "next_cursor": None}

    monkeypatch.setattr(results_router, "list_results_keyset", fake_list_results_keyset_page2)
    r2 = client.get("/api/seedtest/results", params={"limit": 1, "cursor": token, "order": "asc"})
    assert r2.status_code == 200, r2.text
    assert r2.json().get("items") == []
