import os

import pytest
from fastapi.testclient import TestClient

# Skip if no DB configured
if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL not set; skipping DB-backed listing API tests",
        allow_module_level=True,
    )

pytestmark = pytest.mark.db

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services.result_service import upsert_result  # noqa: E402

client = TestClient(app)


def test_results_list_endpoint(monkeypatch):
    # Make sure LOCAL_DEV bypass is on for auth
    monkeypatch.setenv("LOCAL_DEV", "true")

    uid1 = "user_A"
    uid2 = "user_B"

    upsert_result(
        "lsess1", {"score": {"raw": 1, "scaled": 11}}, 1, 11, user_id=uid1, exam_id=201
    )
    upsert_result(
        "lsess2", {"score": {"raw": 2, "scaled": 22}}, 2, 22, user_id=uid1, exam_id=202
    )
    upsert_result(
        "lsess3", {"score": {"raw": 3, "scaled": 33}}, 3, 33, user_id=uid2, exam_id=201
    )

    # List by user
    r = client.get(f"/api/seedtest/results?user_id={uid1}&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert len(data["items"]) <= 2
    assert all(item["user_id"] == uid1 for item in data["items"])

    # If next_cursor present, fetch next page
    cur = data.get("next_cursor")
    if cur:
        cu = cur.get("updated_at")
        cid = cur.get("id")
        r2 = client.get(
            f"/api/seedtest/results?user_id={uid1}&limit=2&cursor_updated_at={cu}&cursor_id={cid}"
        )
        assert r2.status_code == 200
        d2 = r2.json()
        assert "items" in d2

    # List by exam
    r3 = client.get("/api/seedtest/results?exam_id=201")
    assert r3.status_code == 200
    d3 = r3.json()
    assert all(it.get("exam_id") == 201 for it in d3.get("items", []))
