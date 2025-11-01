from __future__ import annotations

from datetime import date
from typing import Any, Dict

from fastapi.testclient import TestClient

from seedtest_api.main import app


def test_get_weekly_metrics_empty_include_empty_true(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    import seedtest_api.routers.analysis as analysis_router

    def fake_list(db, user_id: str, weeks: int):
        return []

    # Mock at the router's import level
    monkeypatch.setattr(analysis_router, "list_weekly_kpi", fake_list)

    client = TestClient(app)
    resp = client.get(
        "/api/seedtest/analysis/metrics/weekly",
        params={"user_id": "U1", "weeks": 4, "include_empty": True},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_get_weekly_metrics_empty_404(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    import seedtest_api.routers.analysis as analysis_router

    monkeypatch.setattr(
        analysis_router, "list_weekly_kpi", lambda db, user_id, weeks: []
    )

    client = TestClient(app)
    resp = client.get(
        "/api/seedtest/analysis/metrics/weekly",
        params={"user_id": "U1", "weeks": 4, "include_empty": False},
    )
    assert resp.status_code == 404


def test_get_weekly_metrics_user_id_required(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    client = TestClient(app)
    resp = client.get(
        "/api/seedtest/analysis/metrics/weekly",
        params={"user_id": "", "weeks": 0},
    )
    assert resp.status_code == 400


def test_post_recompute_success_with_week_start(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    import seedtest_api.routers.analysis as analysis_router

    def fake_calc(db, user_id: str, ws: date) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "week_start": ws,
            "kpis": {
                "I_t": 0.1,
                "E_t": 0.2,
                "R_t": 0.3,
                "A_t": 0.4,
                "P": None,
                "S": None,
            },
        }

    monkeypatch.setattr(analysis_router, "calculate_and_store_weekly_kpi", fake_calc)

    client = TestClient(app)
    resp = client.post(
        "/api/seedtest/analysis/metrics/recompute",
        json={"user_id": "U1", "week_start": "2025-01-06"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_id"] == "U1"
    assert data["week_start"] == "2025-01-06"
    assert set(data["kpis"].keys()) == {"I_t", "E_t", "R_t", "A_t", "P", "S"}


def test_post_recompute_success_without_week_start(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    import seedtest_api.routers.analysis as analysis_router

    # Freeze iso_week_start to deterministic date
    monkeypatch.setattr(analysis_router, "iso_week_start", lambda d: date(2025, 1, 6))

    def fake_calc(db, user_id: str, ws: date) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "week_start": ws,
            "kpis": {
                "I_t": None,
                "E_t": None,
                "R_t": None,
                "A_t": None,
                "P": None,
                "S": None,
            },
        }

    monkeypatch.setattr(analysis_router, "calculate_and_store_weekly_kpi", fake_calc)

    client = TestClient(app)
    resp = client.post(
        "/api/seedtest/analysis/metrics/recompute",
        json={"user_id": "U1"},
    )
    # Even if KPIs are all None, endpoint returns 404 per spec's no-data condition
    assert resp.status_code == 404


def test_post_recompute_bad_date(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    import seedtest_api.routers.analysis as analysis_router

    # Ensure calculate is not called due to validation
    called = {"v": False}

    def fake_calc(db, user_id: str, ws: date) -> Dict[str, Any]:
        called["v"] = True
        return {"user_id": user_id, "week_start": ws, "kpis": {}}

    monkeypatch.setattr(analysis_router, "calculate_and_store_weekly_kpi", fake_calc)

    client = TestClient(app)
    resp = client.post(
        "/api/seedtest/analysis/metrics/recompute",
        json={"user_id": "U1", "week_start": "2025-13-99"},
    )
    assert resp.status_code == 400
    assert called["v"] is False
