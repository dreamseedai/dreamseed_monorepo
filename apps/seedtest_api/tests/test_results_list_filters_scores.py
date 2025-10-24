import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Skip if no DB configured
if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL not set; skipping score/last_n_days filters tests", allow_module_level=True)

pytestmark = pytest.mark.db

from seedtest_api.main import app  # noqa: E402
from seedtest_api.services.db import get_session  # noqa: E402
from seedtest_api.services.result_service import upsert_result  # noqa: E402

client = TestClient(app)


def test_min_max_scaled_filters(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")

    # Seed rows with different scaled scores
    upsert_result("msess1", {"score": {"raw": 1, "scaled": 12}}, 1, 12, user_id="user_S", exam_id=501)
    upsert_result("msess2", {"score": {"raw": 2, "scaled": 25}}, 2, 25, user_id="user_S", exam_id=501)
    upsert_result("msess3", {"score": {"raw": 3, "scaled": 37}}, 3, 37, user_id="user_S", exam_id=501)

    # min only
    r1 = client.get("/api/seedtest/results", params={"min_score_scaled": 20})
    assert r1.status_code == 200
    scores1 = [it["score_scaled"] for it in r1.json().get("items", [])]
    assert all(s is None or s >= 20 for s in scores1)  # None-safe

    # max only
    r2 = client.get("/api/seedtest/results", params={"max_score_scaled": 20})
    assert r2.status_code == 200
    scores2 = [it["score_scaled"] for it in r2.json().get("items", [])]
    assert all(s is None or s <= 20 for s in scores2)

    # both min and max
    r3 = client.get("/api/seedtest/results", params={"min_score_scaled": 15, "max_score_scaled": 30})
    assert r3.status_code == 200
    scores3 = [it["score_scaled"] for it in r3.json().get("items", [])]
    assert all(s is None or (15 <= s <= 30) for s in scores3)


def test_last_n_days_convenience(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")

    # Seed rows and control updated_at timestamps
    upsert_result("dsess1", {"score": {"raw": 1, "scaled": 10}}, 1, 10, user_id="user_T", exam_id=601)
    upsert_result("dsess2", {"score": {"raw": 2, "scaled": 20}}, 2, 20, user_id="user_T", exam_id=601)
    upsert_result("dsess3", {"score": {"raw": 3, "scaled": 30}}, 3, 30, user_id="user_T", exam_id=601)

    t_old = datetime.now(timezone.utc) - timedelta(days=7)
    t_mid = datetime.now(timezone.utc) - timedelta(days=2)
    t_new = datetime.now(timezone.utc) - timedelta(hours=1)
    with get_session() as s:
        s.execute(text("UPDATE exam_results SET updated_at=:t WHERE session_id='dsess1'"), {"t": t_old})
        s.execute(text("UPDATE exam_results SET updated_at=:t WHERE session_id='dsess2'"), {"t": t_mid})
        s.execute(text("UPDATE exam_results SET updated_at=:t WHERE session_id='dsess3'"), {"t": t_new})

    # last_n_days=3 should include dsess2 and dsess3
    r = client.get("/api/seedtest/results", params={"last_n_days": 3, "sort_by": "updated_at", "order": "asc", "limit": 100})
    assert r.status_code == 200
    ids = [it["session_id"] for it in r.json().get("items", [])]
    assert "dsess1" not in ids

    # Explicit updated_from should override last_n_days
    explicit_from = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    r2 = client.get(
        "/api/seedtest/results",
        params={"last_n_days": 30, "updated_from": explicit_from, "sort_by": "updated_at", "order": "asc", "limit": 100},
    )
    assert r2.status_code == 200
    ids2 = [it["session_id"] for it in r2.json().get("items", [])]
    # Only dsess3 is within the last 1 day
    assert "dsess3" in ids2
    assert "dsess2" not in ids2
    assert "dsess1" not in ids2


def test_min_max_raw_filters(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")

    # Seed rows with different raw scores
    upsert_result("rsess1", {"score": {"raw": 5, "scaled": 50}}, 5, 50, user_id="user_R", exam_id=701)
    upsert_result("rsess2", {"score": {"raw": 15, "scaled": 60}}, 15, 60, user_id="user_R", exam_id=701)
    upsert_result("rsess3", {"score": {"raw": 25, "scaled": 70}}, 25, 70, user_id="user_R", exam_id=701)

    # min only
    r1 = client.get("/api/seedtest/results", params={"min_score_raw": 10})
    assert r1.status_code == 200
    raws1 = [it["score_raw"] for it in r1.json().get("items", [])]
    assert all(r is None or r >= 10 for r in raws1)

    # max only
    r2 = client.get("/api/seedtest/results", params={"max_score_raw": 20})
    assert r2.status_code == 200
    raws2 = [it["score_raw"] for it in r2.json().get("items", [])]
    assert all(r is None or r <= 20 for r in raws2)

    # both min and max
    r3 = client.get("/api/seedtest/results", params={"min_score_raw": 10, "max_score_raw": 20})
    assert r3.status_code == 200
    raws3 = [it["score_raw"] for it in r3.json().get("items", [])]
    assert all(r is None or (10 <= r <= 20) for r in raws3)


def test_last_n_hours_and_weeks(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")

    upsert_result("hsess1", {"score": {"raw": 1, "scaled": 10}}, 1, 10, user_id="user_H", exam_id=801)
    upsert_result("hsess2", {"score": {"raw": 2, "scaled": 20}}, 2, 20, user_id="user_H", exam_id=801)
    upsert_result("hsess3", {"score": {"raw": 3, "scaled": 30}}, 3, 30, user_id="user_H", exam_id=801)

    now = datetime.now(timezone.utc)
    h_old = now - timedelta(weeks=3)   # very old
    h_mid = now - timedelta(hours=6)
    h_new = now - timedelta(hours=1)
    with get_session() as s:
        s.execute(text("UPDATE exam_results SET updated_at=:t WHERE session_id='hsess1'"), {"t": h_old})
        s.execute(text("UPDATE exam_results SET updated_at=:t WHERE session_id='hsess2'"), {"t": h_mid})
        s.execute(text("UPDATE exam_results SET updated_at=:t WHERE session_id='hsess3'"), {"t": h_new})

    # last_n_hours=2 -> only hsess3
    r1 = client.get("/api/seedtest/results", params={"last_n_hours": 2, "sort_by": "updated_at", "order": "asc"})
    assert r1.status_code == 200
    ids1 = [it["session_id"] for it in r1.json().get("items", [])]
    assert "hsess3" in ids1 and "hsess2" not in ids1 and "hsess1" not in ids1

    # last_n_weeks=2 (no explicit updated_from and no last_n_hours) -> hsess2, hsess3 included
    r2 = client.get("/api/seedtest/results", params={"last_n_weeks": 2, "sort_by": "updated_at", "order": "asc"})
    assert r2.status_code == 200
    ids2 = [it["session_id"] for it in r2.json().get("items", [])]
    assert "hsess2" in ids2 and "hsess3" in ids2 and "hsess1" not in ids2


def test_score_equality_and_created_last_n(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")

    upsert_result("esess1", {"score": {"raw": 8, "scaled": 48}}, 8, 48, user_id="user_E", exam_id=901)
    upsert_result("esess2", {"score": {"raw": 18, "scaled": 58}}, 18, 58, user_id="user_E", exam_id=901)
    upsert_result("esess3", {"score": {"raw": 28, "scaled": 68}}, 28, 68, user_id="user_E", exam_id=901)

    # Equality filters should return exact matches
    r1 = client.get("/api/seedtest/results", params={"score_raw_eq": 18})
    assert r1.status_code == 200
    ids1 = [it["session_id"] for it in r1.json().get("items", [])]
    assert "esess2" in ids1 and "esess1" not in ids1 and "esess3" not in ids1

    r2 = client.get("/api/seedtest/results", params={"score_scaled_eq": 68})
    assert r2.status_code == 200
    ids2 = [it["session_id"] for it in r2.json().get("items", [])]
    assert "esess3" in ids2 and "esess1" not in ids2 and "esess2" not in ids2

    # created_last_n_* convenience should apply when created_from is not explicit
    now = datetime.now(timezone.utc)
    c_old = now - timedelta(weeks=5)
    c_mid = now - timedelta(days=3)
    c_new = now - timedelta(hours=3)
    with get_session() as s:
        s.execute(text("UPDATE exam_results SET created_at=:t WHERE session_id='esess1'"), {"t": c_old})
        s.execute(text("UPDATE exam_results SET created_at=:t WHERE session_id='esess2'"), {"t": c_mid})
        s.execute(text("UPDATE exam_results SET created_at=:t WHERE session_id='esess3'"), {"t": c_new})

    r3 = client.get("/api/seedtest/results", params={"created_last_n_days": 2, "sort_by": "created_at", "order": "asc"})
    assert r3.status_code == 200
    ids3 = [it["session_id"] for it in r3.json().get("items", [])]
    # Only esess3 created within last 2 days
    assert "esess3" in ids3 and "esess2" not in ids3 and "esess1" not in ids3
