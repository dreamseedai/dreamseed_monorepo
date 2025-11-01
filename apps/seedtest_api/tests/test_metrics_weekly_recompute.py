from __future__ import annotations

from fastapi.testclient import TestClient

from seedtest_api.main import app


def test_weekly_recompute_endpoint_happy_path(monkeypatch):
    monkeypatch.setenv("LOCAL_DEV", "true")
    # Monkeypatch the metrics recompute function to avoid DB usage
    import seedtest_api.routers.metrics as metrics_router

    def fake_recompute(db, weeks_window: int = 1, limit_users: int | None = None):
        return {
            "week_start": "2025-10-27",
            "users_considered": 3,
            "users_processed": 3,
        }

    # Some environments may enforce auth; stub get_current_user to a dummy
    def fake_get_current_user():
        return {"sub": "test-user"}

    monkeypatch.setattr(
        metrics_router, "recompute_weekly_kpi_for_recent_users", fake_recompute
    )
    # If the router imports shared.auth, this override is safe; if LOCAL_DEV=true it's unused
    if hasattr(metrics_router, "get_current_user"):
        monkeypatch.setattr(
            metrics_router, "get_current_user", lambda: fake_get_current_user()
        )

    client = TestClient(app)

    resp = client.post(
        "/api/seedtest/metrics/weekly/recompute",
        json={"weeks_window": 1, "limit_users": 10},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["week_start"] == "2025-10-27"
    assert data["users_considered"] == 3
    assert data["users_processed"] == 3
