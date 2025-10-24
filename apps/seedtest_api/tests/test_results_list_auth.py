import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure app import path
import sys
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

pytestmark = pytest.mark.db

from seedtest_api.main import app
from seedtest_api.services.db import get_session
from sqlalchemy import text
from seedtest_api.deps import get_current_user, User


client = TestClient(app)


@pytest.fixture(autouse=True)
def _set_env_is_not_local_dev(monkeypatch):
    # Force strict auth behavior for listing
    monkeypatch.setenv("LOCAL_DEV", "false")


def _override_user(user: User):
    app.dependency_overrides[get_current_user] = lambda: user


def _clear_overrides():
    app.dependency_overrides.pop(get_current_user, None)


def _seed_rows():
    # Insert a few rows with explicit user_id/org_id
    with get_session() as s:
        s.execute(text("DELETE FROM exam_results"))
        s.execute(text(
            """
            INSERT INTO exam_results (session_id, status, result_json, score_raw, score_scaled, standard_error, percentile, org_id, user_id, exam_id, created_at, updated_at)
            VALUES
            ('sessA', 'ready', '{}'::jsonb, 5, 120, NULL, NULL, 10, 'stu1', 1, NOW(), NOW()),
            ('sessB', 'ready', '{}'::jsonb, 7, 130, NULL, NULL, 10, 'stu1', 2, NOW(), NOW()),
            ('sessC', 'ready', '{}'::jsonb, 9, 140, NULL, NULL, 20, 'stu2', 1, NOW(), NOW())
            """
        ))


def test_student_listing_is_auto_limited(monkeypatch):
    _seed_rows()
    try:
        _override_user(User(user_id="stu1", org_id=10, roles=["student"]))
        r = client.get("/api/seedtest/results")
        assert r.status_code == 200, r.text
        data = r.json()
        items = data.get("items") or []
        # Only stu1 sessions (2)
        assert len(items) == 2
        assert all(it.get("user_id") == "stu1" for it in items)
    finally:
        _clear_overrides()


def test_teacher_listing_defaults_to_org():
    _seed_rows()
    try:
        _override_user(User(user_id="t1", org_id=10, roles=["teacher"]))
        r = client.get("/api/seedtest/results")
        assert r.status_code == 200, r.text
        data = r.json()
        items = data.get("items") or []
        # Only org 10 sessions (2)
        assert len(items) == 2
        assert all(int(it.get("exam_id") or 0) in (1, 2) for it in items)
        # ensure no org 20 row
        assert all(it.get("user_id") != "stu2" for it in items)
    finally:
        _clear_overrides()


def test_student_cannot_use_org_override():
    _seed_rows()
    try:
        _override_user(User(user_id="stu1", org_id=10, roles=["student"]))
        r = client.get("/api/seedtest/results", params={"org_id": 10})
        assert r.status_code == 403
    finally:
        _clear_overrides()


def test_teacher_cannot_override_to_other_org():
    _seed_rows()
    try:
        _override_user(User(user_id="t1", org_id=10, roles=["teacher"]))
        r = client.get("/api/seedtest/results", params={"org_id": 20})
        assert r.status_code == 403
    finally:
        _clear_overrides()


def test_admin_can_scope_org_and_user():
    _seed_rows()
    try:
        _override_user(User(user_id="admin", org_id=None, roles=["admin"]))
        # Admin: org 20 only → 1 row (stu2)
        r1 = client.get("/api/seedtest/results", params={"org_id": 20})
        assert r1.status_code == 200, r1.text
        items1 = (r1.json().get("items") or [])
        assert len(items1) == 1 and items1[0].get("user_id") == "stu2"

        # Admin: org 10 + user stu1 → 2 rows
        r2 = client.get("/api/seedtest/results", params={"org_id": 10, "user_id": "stu1"})
        assert r2.status_code == 200, r2.text
        items2 = (r2.json().get("items") or [])
        assert len(items2) == 2 and all(it.get("user_id") == "stu1" for it in items2)
    finally:
        _clear_overrides()


def test_teacher_user_filter_respects_org_limit():
    _seed_rows()
    try:
        _override_user(User(user_id="t1", org_id=10, roles=["teacher"]))
        # Teacher tries to fetch user in other org; result should be empty but 200
        r = client.get("/api/seedtest/results", params={"user_id": "stu2"})
        assert r.status_code == 200, r.text
        items = r.json().get("items") or []
        assert len(items) == 0
    finally:
        _clear_overrides()
