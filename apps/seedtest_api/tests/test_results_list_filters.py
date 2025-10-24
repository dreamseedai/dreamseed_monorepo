import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Skip if no DB configured
if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL not set; skipping DB-backed listing filters tests", allow_module_level=True)

pytestmark = pytest.mark.db

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services.db import get_session  # noqa: E402
from seedtest_api.services.result_service import upsert_result  # noqa: E402

client = TestClient(app)


def test_results_list_filters_and_sort(monkeypatch):
    # Bypass auth
    monkeypatch.setenv("LOCAL_DEV", "true")

    # Seed three rows
    upsert_result("fsess1", {"score": {"raw": 1, "scaled": 10}}, 1, 10, user_id="user_X", exam_id=301)
    upsert_result("fsess2", {"score": {"raw": 2, "scaled": 20}}, 2, 20, user_id="user_X", exam_id=301)
    upsert_result("fsess3", {"score": {"raw": 3, "scaled": 30}}, 3, 30, user_id="user_Y", exam_id=302)

    # Mark one as failed to test status filter
    with get_session() as s:
        s.execute(text("UPDATE exam_results SET status='failed' WHERE session_id=:sid"), {"sid": "fsess2"})

    # Filter by status
    r = client.get("/api/seedtest/results", params={"status": ["failed"]})
    assert r.status_code == 200
    data = r.json()
    assert all(item["status"] == "failed" for item in data.get("items", []))

    # Sort by created_at ascending and ensure non-decreasing order
    r2 = client.get("/api/seedtest/results", params={"sort_by": "created_at", "order": "asc", "limit": 50})
    assert r2.status_code == 200
    d2 = r2.json()
    items = d2.get("items", [])
    for i in range(1, len(items)):
        assert items[i]["created_at"] >= items[i-1]["created_at"]

    # Date range (updated_at)
    # Use a very old from date to include all; just validates parsing/flow
    r3 = client.get("/api/seedtest/results", params={"date_from": "2000-01-01T00:00:00Z"})
    assert r3.status_code == 200
