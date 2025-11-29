"""Integration tests for IRT drift monitor (V1 frequentist).

Tests:
    - Window creation and query
    - Response loading with sample size filter
    - Drift detection thresholds (Δa, Δb, Δc)
    - CI separation alerts
    - End-to-end pipeline with mock R IRT service
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text

from apps.seedtest_api.jobs.irt_drift_monitor import (
    DEFAULT_THRESHOLDS,
    DriftAlert,
    ItemCalibration,
    compute_information_summary,
    create_drift_window,
    detect_drift,
)

# Test database connection (override with env var)
TEST_DATABASE_URL = "postgresql://localhost/seedtest_test"


@pytest.fixture
def engine():
    """Test database engine."""
    eng = create_engine(TEST_DATABASE_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def clean_tables(engine):
    """Clean drift tables before each test."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM drift_alerts"))
        conn.execute(text("DELETE FROM item_calibration"))
        conn.execute(text("DELETE FROM drift_windows"))
    yield


def test_create_drift_window(engine, clean_tables):
    """Test drift window creation."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30)
    population_tags = {"program": "middle-school", "language": "ko"}

    window = create_drift_window(engine, start, now, population_tags)

    assert window.window_id > 0
    assert window.start_at == start
    assert window.end_at == now
    assert window.population_tags == population_tags

    # Verify in database
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM drift_windows WHERE id = :id"),
            {"id": window.window_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row.start_at == start
        assert row.end_at == now


def test_load_responses_sample_filter(engine, clean_tables):
    """Test response loading with minimum sample size filter."""
    # This test requires seeded test data in the attempts table
    # For now, we verify the query logic structure

    from apps.seedtest_api.jobs.irt_drift_monitor import load_responses

    now = datetime.now(timezone.utc)
    window = create_drift_window(engine, now - timedelta(days=7), now)

    # Load with high min_sample (should return empty if no test data)
    responses = load_responses(engine, window, min_sample=1000)

    # Verify structure (even if empty)
    assert "item_id" in responses.columns
    assert "user_id" in responses.columns
    assert "correct" in responses.columns


def test_detect_drift_thresholds():
    """Test drift detection threshold logic."""
    baseline = ItemCalibration(
        item_id=101,
        window_id=1,
        a_hat=1.2,
        b_hat=-0.5,
        c_hat=0.20,
        a_l95=1.0,
        a_u95=1.4,
        b_l95=-0.7,
        b_u95=-0.3,
        c_l95=0.15,
        c_u95=0.25,
        n=500,
    )

    # Test 1: delta_b violation (moderate)
    recent_moderate_b = ItemCalibration(
        item_id=101,
        window_id=2,
        a_hat=1.2,
        b_hat=-0.15,  # Δb = 0.35 > 0.25
        c_hat=0.20,
        a_l95=1.0,
        a_u95=1.4,
        b_l95=-0.3,
        b_u95=0.0,
        c_l95=0.15,
        c_u95=0.25,
        n=400,
        run_id="test_run_1",
    )

    alerts_moderate_b = detect_drift(baseline, recent_moderate_b, DEFAULT_THRESHOLDS)
    assert len(alerts_moderate_b) >= 1
    assert any(a.metric == "delta_b" for a in alerts_moderate_b)
    delta_b_alert = next(a for a in alerts_moderate_b if a.metric == "delta_b")
    assert delta_b_alert.severity in ["moderate", "minor"]
    assert delta_b_alert.value == pytest.approx(0.35, rel=0.01)

    # Test 2: delta_a violation (severe)
    recent_severe_a = ItemCalibration(
        item_id=101,
        window_id=2,
        a_hat=1.7,  # Δa = 0.5 > 0.4
        b_hat=-0.5,
        c_hat=0.20,
        a_l95=1.5,
        a_u95=1.9,
        b_l95=-0.7,
        b_u95=-0.3,
        c_l95=0.15,
        c_u95=0.25,
        n=400,
        run_id="test_run_2",
    )

    alerts_severe_a = detect_drift(baseline, recent_severe_a, DEFAULT_THRESHOLDS)
    assert len(alerts_severe_a) >= 1
    assert any(a.metric == "delta_a" for a in alerts_severe_a)
    delta_a_alert = next(a for a in alerts_severe_a if a.metric == "delta_a")
    assert delta_a_alert.severity == "severe"

    # Test 3: delta_c violation
    recent_delta_c = ItemCalibration(
        item_id=101,
        window_id=2,
        a_hat=1.2,
        b_hat=-0.5,
        c_hat=0.24,  # Δc = 0.04 > 0.03
        a_l95=1.0,
        a_u95=1.4,
        b_l95=-0.7,
        b_u95=-0.3,
        c_l95=0.19,
        c_u95=0.29,
        n=400,
        run_id="test_run_3",
    )

    alerts_delta_c = detect_drift(baseline, recent_delta_c, DEFAULT_THRESHOLDS)
    assert len(alerts_delta_c) >= 1
    assert any(a.metric == "delta_c" for a in alerts_delta_c)


def test_detect_drift_ci_separation():
    """Test CI separation alert."""
    baseline = ItemCalibration(
        item_id=102,
        window_id=1,
        a_hat=1.0,
        b_hat=-0.5,
        c_hat=0.20,
        a_l95=0.8,
        a_u95=1.2,
        b_l95=-0.7,
        b_u95=-0.3,
        c_l95=0.15,
        c_u95=0.25,
        n=500,
    )

    # Recent b_hat outside baseline CI
    recent_separated = ItemCalibration(
        item_id=102,
        window_id=2,
        a_hat=1.0,
        b_hat=0.2,  # Above baseline b_u95 = -0.3
        c_hat=0.20,
        a_l95=0.8,
        a_u95=1.2,
        b_l95=0.0,
        b_u95=0.4,
        c_l95=0.15,
        c_u95=0.25,
        n=400,
        run_id="test_run_ci",
    )

    alerts = detect_drift(baseline, recent_separated, DEFAULT_THRESHOLDS)

    # Should have both delta_b and CI separation alerts
    assert any(a.metric == "b_ci_separation" for a in alerts)
    ci_alert = next(a for a in alerts if a.metric == "b_ci_separation")
    assert ci_alert.severity == "severe"


def test_compute_information_summary():
    """Test information function summary calculation."""
    # High discrimination item
    info = compute_information_summary(a=1.5, b=-0.5, c=0.20)

    assert "max" in info
    assert "theta_at_max" in info
    assert info["max"] > 0.5  # Should have decent info
    assert -1.0 < info["theta_at_max"] < 0.0  # Should be near b


def test_save_and_load_calibrations(engine, clean_tables):
    """Test saving and loading calibration records."""
    from apps.seedtest_api.jobs.irt_drift_monitor import save_calibrations

    calibrations = [
        ItemCalibration(
            item_id=201,
            window_id=1,
            a_hat=1.3,
            b_hat=-0.4,
            c_hat=0.22,
            a_l95=1.1,
            a_u95=1.5,
            b_l95=-0.6,
            b_u95=-0.2,
            c_l95=0.17,
            c_u95=0.27,
            n=450,
            info={"max": 0.65, "theta_at_max": -0.35},
            run_id="test_save",
        ),
        ItemCalibration(
            item_id=202,
            window_id=1,
            a_hat=0.9,
            b_hat=0.3,
            c_hat=0.18,
            a_l95=0.7,
            a_u95=1.1,
            b_l95=0.1,
            b_u95=0.5,
            c_l95=0.13,
            c_u95=0.23,
            n=520,
            info={"max": 0.42, "theta_at_max": 0.35},
            run_id="test_save",
        ),
    ]

    save_calibrations(engine, calibrations)

    # Verify in database
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM item_calibration WHERE run_id = :run_id"),
            {"run_id": "test_save"},
        )
        rows = result.fetchall()
        assert len(rows) == 2

        # Check first record
        row1 = next(r for r in rows if r.item_id == 201)
        assert row1.a_hat == pytest.approx(1.3, rel=0.01)
        assert row1.b_hat == pytest.approx(-0.4, rel=0.01)
        assert row1.c_hat == pytest.approx(0.22, rel=0.01)
        assert row1.n == 450

        # Check info JSONB
        info_json = json.loads(row1.info) if isinstance(row1.info, str) else row1.info
        assert info_json["max"] == pytest.approx(0.65, rel=0.01)


def test_save_and_load_alerts(engine, clean_tables):
    """Test saving and loading drift alerts."""
    from apps.seedtest_api.jobs.irt_drift_monitor import save_alerts

    alerts = [
        DriftAlert(
            item_id=301,
            window_id=2,
            metric="delta_b",
            value=0.35,
            threshold=0.25,
            severity="moderate",
            run_id="test_alerts",
        ),
        DriftAlert(
            item_id=302,
            window_id=2,
            metric="delta_a",
            value=0.45,
            threshold=0.20,
            severity="severe",
            run_id="test_alerts",
        ),
    ]

    save_alerts(engine, alerts)

    # Verify in database
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM drift_alerts WHERE run_id = :run_id ORDER BY item_id"),
            {"run_id": "test_alerts"},
        )
        rows = result.fetchall()
        assert len(rows) == 2

        # Check first alert
        assert rows[0].item_id == 301
        assert rows[0].metric == "delta_b"
        assert rows[0].value == pytest.approx(0.35, rel=0.01)
        assert rows[0].severity == "moderate"

        # Check second alert
        assert rows[1].item_id == 302
        assert rows[1].severity == "severe"


@pytest.mark.integration
def test_end_to_end_pipeline_mock(engine, clean_tables, monkeypatch):
    """Test full pipeline with mocked R IRT service."""
    from apps.seedtest_api.jobs.irt_drift_monitor import run_drift_monitor

    # Mock R IRT calibrate function
    def mock_r_calibrate(responses_df, model="3PL"):
        # Return fixed parameters for known items
        items = responses_df["item_id"].unique()
        return {
            int(item_id): {
                "a": 1.2,
                "b": -0.3,
                "c": 0.20,
                "a_se": 0.1,
                "b_se": 0.15,
                "c_se": 0.05,
            }
            for item_id in items
        }

    # Monkeypatch the R IRT call
    import apps.seedtest_api.jobs.irt_drift_monitor as drift_module

    monkeypatch.setattr(drift_module, "call_r_irt_calibrate", mock_r_calibrate)

    # Mock load_responses to return synthetic data
    import pandas as pd

    def mock_load_responses(engine, window, min_sample=200):
        # Return synthetic data for 5 items
        data = []
        for item_id in [401, 402, 403, 404, 405]:
            for user_id in range(1, 251):  # 250 users
                data.append(
                    {
                        "item_id": item_id,
                        "user_id": user_id,
                        "correct": (item_id + user_id) % 2,  # Synthetic pattern
                    }
                )
        return pd.DataFrame(data)

    monkeypatch.setattr(drift_module, "load_responses", mock_load_responses)

    # Run pipeline
    result = run_drift_monitor(
        recent_days=30,
        min_sample=200,
        run_id="test_e2e",
    )

    # Verify results
    assert result["run_id"] == "test_e2e"
    assert result["calibrations"] == 5  # 5 common items
    assert result["alerts"] == 0  # No drift with identical params

    # Verify database state
    with engine.connect() as conn:
        # Check windows
        windows = conn.execute(
            text("SELECT id FROM drift_windows ORDER BY created_at DESC LIMIT 2")
        ).fetchall()
        assert len(windows) == 2

        # Check calibrations
        calibs = conn.execute(
            text("SELECT COUNT(*) FROM item_calibration WHERE run_id = :run_id"),
            {"run_id": "test_e2e"},
        ).scalar()
        assert calibs == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
