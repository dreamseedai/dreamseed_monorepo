import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

# Skip if no DB configured
if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL not set; skipping advanced filters tests", allow_module_level=True)

pytestmark = pytest.mark.db

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services.result_service import upsert_result  # noqa: E402
from seedtest_api.services.db import get_session  # noqa: E402

client = TestClient(app)


def test_status_csv_and_created_updated_ranges(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")

    # Seed rows
    upsert_result("asess1", {"score": {"raw": 1, "scaled": 11}}, 1, 11, user_id="user_Z", exam_id=401)
    upsert_result("asess2", {"score": {"raw": 2, "scaled": 22}}, 2, 22, user_id="user_Z", exam_id=402)
    upsert_result("asess3", {"score": {"raw": 3, "scaled": 33}}, 3, 33, user_id="user_Z", exam_id=403)

    # Manually set created_at and updated_at to specific times
    t0 = datetime.now(timezone.utc) - timedelta(days=2)
    t1 = datetime.now(timezone.utc) - timedelta(days=1)
    t2 = datetime.now(timezone.utc)
    with get_session() as s:
        s.execute(text("UPDATE exam_results SET created_at=:t, updated_at=:t, status='pending' WHERE session_id='asess1'"), {"t": t0})
        s.execute(text("UPDATE exam_results SET created_at=:t, updated_at=:t, status='failed'  WHERE session_id='asess2'"), {"t": t1})
        s.execute(text("UPDATE exam_results SET created_at=:t, updated_at=:t, status='ready'   WHERE session_id='asess3'"), {"t": t2})

    # Filter by status via CSV (failed,ready)
    r = client.get("/api/seedtest/results", params={"status_csv": "failed, ready"})
    assert r.status_code == 200
    statuses = {it["status"] for it in r.json().get("items", [])}
    assert statuses.issubset({"failed", "ready"})

    # created_from to include only newer items
    r2 = client.get("/api/seedtest/results", params={"created_from": (t1 - timedelta(hours=1)).isoformat()})
    assert r2.status_code == 200
    items2 = r2.json().get("items", [])
    assert all(datetime.fromisoformat(i["created_at"].replace("Z", "+00:00")) >= (t1 - timedelta(hours=1)) for i in items2)

    # updated_to to include only older items
    r3 = client.get("/api/seedtest/results", params={"updated_to": (t1 + timedelta(hours=1)).isoformat()})
    assert r3.status_code == 200
    items3 = r3.json().get("items", [])
    assert all(datetime.fromisoformat(i["updated_at"].replace("Z", "+00:00")) <= (t1 + timedelta(hours=1)) for i in items3)
