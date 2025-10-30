import os
from fastapi.testclient import TestClient

# Ensure LOCAL_DEV to bypass auth for tests and teacher role for access
os.environ.setdefault("LOCAL_DEV", "true")
os.environ.setdefault("LOCAL_DEV_ROLES", "teacher")

from apps.seedtest_api.app.main import app


def test_questions_pagination_and_sorting():
    client = TestClient(app)

    # Seed a few items with different timestamps by updating
    # List first page with default sort (updated_at desc) & limit 3
    r = client.get("/api/seedtest/questions", params={"limit": 3, "page": 1})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "results" in data
    assert data["total"] >= 3
    page1 = data["results"]
    assert len(page1) <= 3

    # Page 2 should be different when total > 3
    if data["total"] > 3:
        r2 = client.get("/api/seedtest/questions", params={"limit": 3, "page": 2})
        assert r2.status_code == 200
        page2 = r2.json()["results"]
        # no overlap for simple offset pagination if enough items
        assert page1 != page2

    # Sorting by created_at asc should reverse the order versus default when total>1
    if data["total"] > 1:
        r3 = client.get("/api/seedtest/questions", params={"sort_by": "created_at", "order": "asc", "limit": 5, "page": 1})
        assert r3.status_code == 200
        asc_items = r3.json()["results"]
        r4 = client.get("/api/seedtest/questions", params={"sort_by": "created_at", "order": "desc", "limit": 5, "page": 1})
        desc_items = r4.json()["results"]
        if len(asc_items) > 1 and len(desc_items) > 1:
            assert asc_items[0]["id"] != desc_items[0]["id"]
