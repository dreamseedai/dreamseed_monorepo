import os
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect


pytestmark = pytest.mark.db


def _has_table(engine, name: str) -> bool:
    try:
        insp = inspect(engine)
        return insp.has_table(name)
    except Exception:
        return False


def test_post_idempotency_replay(monkeypatch):
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping DB-dependent test")

    # Enable idempotency explicitly (default True)
    monkeypatch.setenv("ENABLE_IDEMPOTENCY", "true")
    monkeypatch.setenv("LOCAL_DEV", "true")

    from apps.seedtest_api.services import db as db_service
    engine = db_service.get_engine()
    if not _has_table(engine, "idempotency_records"):
        pytest.skip("idempotency_records table not present; ensure Alembic migrations applied")

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    payload = {
        "stem": "Idempotency test",
        "options": ["A", "B"],
        "answer": 0,
        "difficulty": "easy",
        "status": "draft",
    }
    key = f"k-{int(time.time()*1000)}"

    r1 = client.post("/api/seedtest/questions", json=payload, headers={"Idempotency-Key": key})
    assert r1.status_code in (200, 201), r1.text
    q1 = r1.json()

    r2 = client.post("/api/seedtest/questions", json=payload, headers={"Idempotency-Key": key})
    assert r2.status_code == r1.status_code
    q2 = r2.json()
    assert q1["id"] == q2["id"]


def test_post_idempotency_conflict(monkeypatch):
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping DB-dependent test")

    monkeypatch.setenv("ENABLE_IDEMPOTENCY", "true")
    monkeypatch.setenv("LOCAL_DEV", "true")

    from apps.seedtest_api.services import db as db_service
    engine = db_service.get_engine()
    if not _has_table(engine, "idempotency_records"):
        pytest.skip("idempotency_records table not present; ensure Alembic migrations applied")

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    key = f"k-{int(time.time()*1000)}-conflict"
    p1 = {"stem": "A", "options": ["A","B"], "answer": 0, "difficulty": "easy"}
    p2 = {"stem": "B", "options": ["A","B"], "answer": 1, "difficulty": "easy"}

    r1 = client.post("/api/seedtest/questions", json=p1, headers={"Idempotency-Key": key})
    assert r1.status_code in (200, 201), r1.text
    r2 = client.post("/api/seedtest/questions", json=p2, headers={"Idempotency-Key": key})
    assert r2.status_code == 409


def test_etag_put_precondition(monkeypatch):
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping DB-dependent test")

    # Require If-Match precondition
    monkeypatch.setenv("REQUIRE_IF_MATCH_PRECONDITION", "true")
    monkeypatch.setenv("LOCAL_DEV", "true")

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    # Create
    payload = {
        "stem": "ETag test",
        "options": ["A", "B"],
        "answer": 1,
        "difficulty": "medium",
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload)
    assert r.status_code in (200, 201)
    q = r.json()
    qid = q["id"]

    # Get to read ETag
    r = client.get(f"/api/seedtest/questions/{qid}")
    assert r.status_code == 200
    etag = r.headers.get("ETag")
    # ETag may be absent on some backends; skip if not provided
    if not etag:
        pytest.skip("ETag header not present (likely non-DB backend); skipping")

    # Update without If-Match should fail when required
    payload["stem"] = "ETag test updated"
    r2 = client.put(f"/api/seedtest/questions/{qid}", json=payload)
    assert r2.status_code == 428

    # Update with wrong If-Match should fail
    r3 = client.put(f"/api/seedtest/questions/{qid}", json=payload, headers={"If-Match": "\"wrong\""})
    assert r3.status_code == 412

    # Update with correct If-Match should succeed and return new ETag
    r4 = client.put(f"/api/seedtest/questions/{qid}", json=payload, headers={"If-Match": etag})
    assert r4.status_code == 200
    etag2 = r4.headers.get("ETag")
    assert etag2 and etag2 != etag
