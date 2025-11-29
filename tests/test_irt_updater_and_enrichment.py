from __future__ import annotations

from fastapi.testclient import TestClient

from adaptive_engine.main import app
from adaptive_engine import config as cfg


def test_irt_updater_settings_endpoints(monkeypatch):
    # Arrange: settings with admin token
    base = cfg.AppSettings(
        admin_token="secret",
        irt_update_enabled=False,
        irt_update_interval_sec=3600,
        irt_update_method="heuristic",
        irt_target_correct_rate=0.5,
        irt_learning_rate=0.1,
        irt_min_responses=None,
        irt_update_max_items_per_run=None,
        irt_stats_view="irt_item_stats",
        items_table="items",
        irt_change_log_table=None,
    )

    import adaptive_engine.routers.settings as settings_router
    monkeypatch.setattr(settings_router, "get_settings", lambda: base, raising=True)

    client = TestClient(app)

    # GET baseline
    r = client.get("/api/settings/irt-updater")
    assert r.status_code == 200
    data = r.json()
    assert data["method"] == "heuristic"
    assert data["target_correct_rate"] == 0.5

    # PATCH values
    r2 = client.patch(
        "/api/settings/irt-updater",
        headers={"X-Admin-Token": "secret"},
        json={
            "enabled": True,
            "interval_sec": 1800,
            "method": "mml",
            "target_correct_rate": 0.6,
            "learning_rate": 0.2,
            "min_responses": 30,
            "max_items_per_run": 100,
            "stats_view": "stats_vw",
            "items_table": "items_v2",
            "change_log_table": "item_param_changes",
        },
    )
    assert r2.status_code == 200
    after = r2.json()
    assert after["enabled"] is True
    assert after["interval_sec"] == 1800
    assert after["method"] == "mml"
    assert after["target_correct_rate"] == 0.6
    assert after["learning_rate"] == 0.2
    assert after["min_responses"] == 30
    assert after["max_items_per_run"] == 100
    assert after["stats_view"] == "stats_vw"
    assert after["items_table"] == "items_v2"
    assert after["change_log_table"] == "item_param_changes"


def test_finish_enrichment_hook(monkeypatch):
    client = TestClient(app)

    # Monkeypatch detailed feedback generator to predictable output
    import adaptive_engine.routers.exam_session as exam_router
    import adaptive_engine.services.feedback_generator as fb

    def fake_generate_detailed(responses, qmap, theta=None, se=None, scaled_score=None):
        return {
            "summary": {"percentile": 55.0},
            "items_review": [
                {"question_id": "q1", "topic": "Algebra"},
                {"question_id": "q2", "topic": "Geometry"},
            ],
            "topic_breakdown": {"Algebra": {"correct": 1, "total": 1}},
            "recommendations": ["Focus on Geometry"],
        }

    monkeypatch.setattr(exam_router, "generate_detailed_feedback", fake_generate_detailed, raising=True)

    # Monkeypatch enrichment to inject solution_html and topic benchmarks
    import adaptive_engine.services.db_enrichment as enr

    def fake_enrich(payload):
        items = payload.get("items_review", [])
        for it in items:
            it["solution_html"] = f"<p>Solution for {it['question_id']}</p>"
        payload["topic_breakdowns"] = {"Algebra": 0.7, "Geometry": 0.4}
        return payload

    monkeypatch.setattr(exam_router, "enrich_finish_payload", fake_enrich, raising=True)

    # Call finish
    finish_payload = {
        "responses": [
            {"question_id": "q1", "correct": True},
            {"question_id": "q2", "correct": False},
        ],
        "questions": {
            "q1": {"question_id": "q1", "a": 1.0, "b": 0.0, "c": 0.2},
            "q2": {"question_id": "q2", "a": 1.0, "b": 0.0, "c": 0.2},
        },
    }

    r = client.post("/api/exam/finish", json=finish_payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert isinstance(data.get("items_review"), list)
    assert all("solution_html" in it for it in data["items_review"])
