from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from seedtest_api.main import app


class _ResultProxy:
    def __init__(self, rows: List[Dict[str, Any]]):
        self._rows = rows

    def mappings(self):
        class _M:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows
        return _M(self._rows)


class _DBTopic:
    def execute(self, stmt, params=None):  # noqa: D401
        # Recognize query by text content
        sql = str(stmt)
        if "FROM student_topic_theta" in sql:
            # return two topic rows
            return _ResultProxy([
                {
                    "topic_id": "algebra",
                    "theta": 0.3,
                    "se": 0.2,
                    "fitted_at": datetime(2025, 1, 15, tzinfo=timezone.utc),
                },
                {
                    "topic_id": "geometry",
                    "theta": -0.1,
                    "se": 0.4,
                    "fitted_at": datetime(2025, 1, 14, tzinfo=timezone.utc),
                },
            ])
        # Default empty
        return _ResultProxy([])


class _DBAbility:
    def execute(self, stmt, params=None):
        sql = str(stmt)
        if "FROM student_topic_theta" in sql:
            # Simulate no topic-level rows
            return _ResultProxy([])
        if "FROM mirt_ability" in sql:
            return _ResultProxy([
                {"theta": 0.5, "se": 0.1, "fitted_at": datetime(2025, 1, 10, tzinfo=timezone.utc)},
                {"theta": 0.4, "se": 0.2, "fitted_at": datetime(2025, 1, 5, tzinfo=timezone.utc)},
            ])
        return _ResultProxy([])


def test_get_irt_theta_topic_level(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    # Override DB dependency to our stub
    app.dependency_overrides.clear()
    from seedtest_api.db.session import get_db
    app.dependency_overrides[get_db] = lambda: _DBTopic()

    client = TestClient(app)
    resp = client.get(
        "/api/seedtest/analysis/irt/theta",
        params={"user_id": "U1", "since": "2025-01-01", "topics": "algebra,geometry"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list) and len(data) == 2
    assert set(k for k in data[0].keys()) == {"topic_id", "theta", "se", "model", "fitted_at"}
    assert data[0]["topic_id"] == "algebra"


def test_get_irt_theta_fallback_general_ability(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    app.dependency_overrides.clear()
    from seedtest_api.db.session import get_db
    app.dependency_overrides[get_db] = lambda: _DBAbility()

    client = TestClient(app)
    resp = client.get(
        "/api/seedtest/analysis/irt/theta",
        params={"user_id": "U1"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list) and len(data) >= 1
    assert data[0]["topic_id"] is None
    assert data[0]["theta"] == 0.5


def test_get_irt_theta_bad_since(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    client = TestClient(app)
    resp = client.get(
        "/api/seedtest/analysis/irt/theta",
        params={"user_id": "U1", "since": "bad-date"},
    )
    assert resp.status_code == 400
