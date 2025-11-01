"""Tests for metrics computation functions (Dev Contract 2)."""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

# Ensure package imports resolve
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.services import metrics as metrics_svc  # noqa: E402
from seedtest_api.services.metrics import (  # noqa: E402
    Attempt,
    calculate_and_store_weekly_kpi,
    compute_engagement,
    compute_improvement_index,
    compute_recovery_rate,
    compute_time_efficiency,
    load_attempts,
    upsert_weekly_kpi,
)

os.environ.setdefault("LOCAL_DEV", "true")


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session."""
    session = MagicMock(spec=Session)
    session.execute.return_value.mappings.return_value.all.return_value = []
    return session


def test_compute_improvement_index_no_data(mock_session):
    """Test compute_improvement_index returns None when no data."""
    result = compute_improvement_index(
        mock_session, "user1", date(2025, 1, 20), window_days=14
    )
    assert result is None


def test_compute_improvement_index_positive_delta(mock_session):
    """Test compute_improvement_index returns positive for improvement."""

    # Mock recent: 10 correct out of 20 (0.5)
    # Mock previous: 5 correct out of 20 (0.25)
    def mock_load_attempts(session, user_id, start, end):
        # Check if this is recent period (later dates) or previous period
        if end > datetime(2025, 1, 15, tzinfo=timezone.utc):
            # Recent period: higher accuracy (10/20 = 0.5)
            return [
                Attempt(
                    None, None, True if i < 10 else False, None, None, None, None, None
                )
                for i in range(20)
            ]
        else:
            # Previous period: lower accuracy (5/20 = 0.25)
            return [
                Attempt(
                    None, None, True if i < 5 else False, None, None, None, None, None
                )
                for i in range(20)
            ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_improvement_index(
        mock_session, "user1", date(2025, 1, 20), window_days=14
    )
    assert result is not None
    assert result > 0
    assert -1.0 <= result <= 1.0


def test_compute_improvement_index_negative_delta(mock_session):
    """Test compute_improvement_index returns negative for decline."""

    def mock_execute(stmt, params):
        result_mock = MagicMock()
        # Recent period: lower accuracy
        result_mock.mappings.return_value.all.return_value = ask_response_data(
            correct=5, total=20
        )
        return result_mock

    mock_session.execute = mock_execute

    # Mock load_attempts to return different data for recent vs prev
    def mock_load_attempts(session, user_id, start, end):
        if end > datetime(2025, 1, 10, tzinfo=timezone.utc):
            # Recent: lower
            return [
                Attempt(
                    None, None, True if i < 5 else False, None, None, None, None, None
                )
                for i in range(20)
            ]
        else:
            # Previous: higher
            return [
                Attempt(
                    None, None, True if i < 10 else False, None, None, None, None, None
                )
                for i in range(20)
            ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_improvement_index(
        mock_session, "user1", date(2025, 1, 20), window_days=14
    )
    # Should be negative or None
    if result is not None:
        assert result <= 0


def test_compute_time_efficiency_no_data(mock_session):
    """Test compute_time_efficiency returns None when no data."""
    result = compute_time_efficiency(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    assert result is None


def test_compute_time_efficiency_improvement(mock_session):
    """Test compute_time_efficiency returns positive for faster times."""

    def mock_load_attempts(session, user_id, start, end):
        if end > datetime(2025, 1, 1, tzinfo=timezone.utc):
            # Recent: faster (1000ms)
            return [
                Attempt(
                    None,
                    None,
                    True,
                    datetime.now(tz=timezone.utc),
                    1000,
                    None,
                    None,
                    None,
                )
                for _ in range(5)
            ]
        else:
            # Previous: slower (2000ms)
            return [
                Attempt(
                    None,
                    None,
                    True,
                    datetime.now(tz=timezone.utc),
                    2000,
                    None,
                    None,
                    None,
                )
                for _ in range(5)
            ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_time_efficiency(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    assert result is not None
    assert 0.0 < result <= 1.0  # Should be positive (faster = better)


def test_compute_time_efficiency_zero_median(mock_session):
    """Test compute_time_efficiency returns None when med_prev <= 0."""

    def mock_load_attempts(session, user_id, start, end):
        return [
            Attempt(
                None, None, True, datetime.now(tz=timezone.utc), 0, None, None, None
            )
            for _ in range(5)
        ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_time_efficiency(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    # Should return None when median is 0 or negative
    assert result is None


def test_compute_recovery_rate_no_prev_incorrect(mock_session):
    """Test compute_recovery_rate returns None when no previous incorrect."""

    def mock_load_attempts(session, user_id, start, end):
        # All correct in previous period
        return [
            Attempt(
                "q1",
                "topic1",
                True,
                datetime.now(tz=timezone.utc),
                None,
                None,
                None,
                None,
            )
            for _ in range(5)
        ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_recovery_rate(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    assert result is None


def test_compute_recovery_rate_successful_recovery(mock_session):
    """Test compute_recovery_rate returns positive for recovered items."""

    def mock_load_attempts(session, user_id, start, end):
        if end > datetime(2025, 1, 1, tzinfo=timezone.utc):
            # Recent: corrected (True)
            return [
                Attempt(
                    "q1",
                    "topic1",
                    True,
                    datetime.now(tz=timezone.utc),
                    None,
                    None,
                    None,
                    None,
                ),
                Attempt(
                    "q2",
                    "topic2",
                    True,
                    datetime.now(tz=timezone.utc),
                    None,
                    None,
                    None,
                    None,
                ),
            ]
        else:
            # Previous: incorrect
            return [
                Attempt(
                    "q1",
                    "topic1",
                    False,
                    datetime.now(tz=timezone.utc),
                    None,
                    None,
                    None,
                    None,
                ),
                Attempt(
                    "q2",
                    "topic2",
                    False,
                    datetime.now(tz=timezone.utc),
                    None,
                    None,
                    None,
                    None,
                ),
            ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_recovery_rate(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    assert result is not None
    assert 0.0 < result <= 1.0


def test_compute_engagement_no_data(mock_session):
    """Test compute_engagement returns None when no attempts."""

    def mock_load_attempts(session, user_id, start, end):
        return []  # Empty list should trigger None return

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_engagement(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    assert result is None


def test_compute_engagement_normalized_range(mock_session):
    """Test compute_engagement returns value in [0, 1] range."""

    def mock_load_attempts(session, user_id, start, end):
        # Create some attempts with various attributes
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        return [
            Attempt(
                f"q{i}",
                f"topic{i % 3}",
                i % 2 == 0,
                base_time + timedelta(days=i),
                1000,
                0,
                f"sess{i // 3}",
                600,
            )
            for i in range(10)
        ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_engagement(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    assert result is not None
    assert 0.0 <= result <= 1.0


def test_compute_engagement_with_missing_components(mock_session):
    """Test compute_engagement handles missing components gracefully."""

    def mock_load_attempts(session, user_id, start, end):
        # Minimal attempts without all fields
        return [
            Attempt(
                "q1",
                "topic1",
                True,
                datetime.now(tz=timezone.utc),
                None,
                None,
                "sess1",
                None,
            ),
            Attempt(
                "q2",
                "topic2",
                False,
                datetime.now(tz=timezone.utc),
                None,
                None,
                "sess1",
                None,
            ),
        ]

    metrics_svc.load_attempts = mock_load_attempts
    result = compute_engagement(
        mock_session, "user1", date(2025, 1, 20), window_days=28
    )
    # Should still return a value in [0, 1] using defaults/fallbacks
    assert result is not None
    assert 0.0 <= result <= 1.0


def test_upsert_weekly_kpi_insert(mock_session):
    """Test upsert_weekly_kpi performs INSERT on first run."""
    kpis = {"I_t": 0.1, "E_t": 0.2, "R_t": 0.3, "A_t": 0.4, "P": None, "S": None}

    # Mock execute to simulate no existing row
    mock_session.execute.return_value = None

    upsert_weekly_kpi(mock_session, "user1", date(2025, 1, 6), kpis)

    # Verify INSERT was called
    assert mock_session.execute.called
    call_args = str(mock_session.execute.call_args[0][0]).upper()
    assert "INSERT INTO WEEKLY_KPI" in call_args or "INSERT" in call_args
    mock_session.commit.assert_called_once()


def test_upsert_weekly_kpi_update(mock_session):
    """Test upsert_weekly_kpi performs UPDATE on conflict."""
    kpis = {"I_t": 0.15, "E_t": 0.25, "R_t": 0.35, "A_t": 0.45, "P": None, "S": None}

    # Mock execute to simulate ON CONFLICT
    mock_session.execute.return_value = None

    # First insert
    upsert_weekly_kpi(mock_session, "user1", date(2025, 1, 6), kpis)

    # Second call with different values should trigger UPDATE
    kpis2 = {"I_t": 0.2, "E_t": 0.3, "R_t": 0.4, "A_t": 0.5, "P": None, "S": None}
    upsert_weekly_kpi(mock_session, "user1", date(2025, 1, 6), kpis2)

    # Verify both INSERT and UPDATE via ON CONFLICT
    assert mock_session.execute.call_count >= 2
    mock_session.commit.assert_called()


def test_calculate_and_store_weekly_kpi_structure(mock_session):
    """Test calculate_and_store_weekly_kpi returns correct structure with P/S as None."""

    def mock_load_attempts(session, user_id, start, end):
        # Provide minimal data to allow computation
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        return [
            Attempt(
                f"q{i}",
                f"topic{i % 3}",
                i % 2 == 0,
                base_time + timedelta(days=i),
                1000 + i * 100,
                0,
                f"sess{i // 5}",
                600,
            )
            for i in range(20)
        ]

    metrics_svc.load_attempts = mock_load_attempts
    mock_session.execute.return_value = None

    result = calculate_and_store_weekly_kpi(mock_session, "user1", date(2025, 1, 6))

    assert "user_id" in result
    assert "week_start" in result
    assert "kpis" in result
    assert result["user_id"] == "user1"

    kpis = result["kpis"]
    # Verify all required keys are present
    assert "I_t" in kpis
    assert "E_t" in kpis
    assert "R_t" in kpis
    assert "A_t" in kpis
    assert "P" in kpis
    assert "S" in kpis
    # P and S should be None
    assert kpis["P"] is None
    assert kpis["S"] is None


# Helper function to create mock response data
def ask_response_data(correct: int, total: int):
    """Helper to create mock exam_results response data."""
    questions = []
    for i in range(total):
        questions.append(
            {
                "question_id": f"q{i}",
                "topic": f"topic{i % 3}",
                "is_correct": i < correct,
                "time_spent_sec": 2.0,
                "used_hints": 0,
            }
        )

    return [
        {
            "session_id": "sess1",
            "ts": datetime.now(tz=timezone.utc),
            "result_json": {"questions": questions},
        }
    ]


# --- Dev Contract 4: Goal attainment probability (P) tests ---


def test_compute_goal_attainment_probability_none_when_no_ability(
    mock_session, monkeypatch
):
    monkeypatch.setattr(
        metrics_svc, "load_user_ability_summary", lambda session, uid: None
    )
    p = metrics_svc.compute_goal_attainment_probability(
        mock_session, "user1", target=0.0
    )
    assert p is None


def test_compute_goal_attainment_probability_sd_le_zero(mock_session, monkeypatch):
    monkeypatch.setattr(
        metrics_svc, "load_user_ability_summary", lambda session, uid: (0.0, 0.0)
    )
    p = metrics_svc.compute_goal_attainment_probability(
        mock_session, "user1", target=0.0
    )
    assert p is None


def test_compute_goal_attainment_probability_normal_valid(mock_session, monkeypatch):
    monkeypatch.setattr(
        metrics_svc, "load_user_ability_summary", lambda session, uid: (0.0, 1.0)
    )
    p = metrics_svc.compute_goal_attainment_probability(
        mock_session, "user1", target=0.0
    )
    assert p is not None and 0.49 <= p <= 0.51


def test_compute_goal_attainment_probability_bayesian_flag_fallback(
    mock_session, monkeypatch
):
    monkeypatch.setenv("METRICS_USE_BAYESIAN", "true")
    monkeypatch.setattr(
        metrics_svc, "load_user_ability_summary", lambda session, uid: (0.0, 1.0)
    )
    p = metrics_svc.compute_goal_attainment_probability(
        mock_session, "user1", target=0.0
    )
    assert p is not None and 0.49 <= p <= 0.51


def test_calculate_and_store_weekly_kpi_sets_P_when_available(
    mock_session, monkeypatch
):
    # Focus on P: stub other KPIs and upsert
    monkeypatch.setattr(metrics_svc, "compute_improvement_index", lambda *a, **k: None)
    monkeypatch.setattr(metrics_svc, "compute_time_efficiency", lambda *a, **k: None)
    monkeypatch.setattr(metrics_svc, "compute_recovery_rate", lambda *a, **k: None)
    monkeypatch.setattr(metrics_svc, "compute_engagement", lambda *a, **k: None)
    monkeypatch.setattr(
        metrics_svc,
        "compute_goal_attainment_probability",
        lambda session, uid, target=None: 0.75,
    )

    captured: Dict[str, Any] = {}

    def fake_upsert(session, user_id, ws, kpis):
        captured["user_id"] = user_id
        captured["week_start"] = ws
        captured["kpis"] = kpis

    monkeypatch.setattr(metrics_svc, "upsert_weekly_kpi", fake_upsert)

    out = calculate_and_store_weekly_kpi(mock_session, "user1", date(2025, 1, 6))
    assert out["kpis"]["P"] == 0.75
    assert out["kpis"]["S"] is None
    assert captured["kpis"]["P"] == 0.75


# --- Dev Contract 5: Churn risk S(t) tests ---


def test_compute_churn_risk_near_zero_when_active(mock_session, monkeypatch):
    from seedtest_api.services import metrics as m

    # last_seen == as_of, many sessions, small gap -> ~0
    def fake_stats(session, user_id, lookback_days=56):
        return {
            "last_seen": date(2025, 1, 6),
            "sessions": 12,
            "mean_gap_days": 0.0,
            "first_seen": date(2024, 12, 1),
        }

    monkeypatch.setattr(m, "load_user_session_stats", fake_stats)
    r = m.compute_churn_risk(mock_session, "U1", as_of=date(2025, 1, 6))
    assert r is not None and r <= 0.05


def test_compute_churn_risk_near_one_when_stale(mock_session, monkeypatch):
    from seedtest_api.services import metrics as m

    # last_seen == as_of - horizon, no sessions, large gap -> ~1
    monkeypatch.setenv("METRICS_CHURN_HORIZON_DAYS", "14")

    def fake_stats(session, user_id, lookback_days=56):
        return {
            "last_seen": date(2025, 1, 6),
            "sessions": 0,
            "mean_gap_days": 7.0,
            "first_seen": date(2024, 10, 1),
        }

    monkeypatch.setattr(m, "load_user_session_stats", fake_stats)
    r = m.compute_churn_risk(
        mock_session, "U1", as_of=date(2025, 1, 20)
    )  # 14 days later
    assert r is not None and r >= 0.95


def test_compute_churn_risk_sessions_reduce_risk(mock_session, monkeypatch):
    from seedtest_api.services import metrics as m

    def stats_low(session, user_id, lookback_days=56):
        return {
            "last_seen": date(2025, 1, 6),
            "sessions": 1,
            "mean_gap_days": 3.0,
            "first_seen": date(2024, 12, 1),
        }

    def stats_high(session, user_id, lookback_days=56):
        return {
            "last_seen": date(2025, 1, 6),
            "sessions": 12,
            "mean_gap_days": 3.0,
            "first_seen": date(2024, 12, 1),
        }

    monkeypatch.setattr(m, "load_user_session_stats", stats_low)
    r_low = m.compute_churn_risk(mock_session, "U1", as_of=date(2025, 1, 10))
    monkeypatch.setattr(m, "load_user_session_stats", stats_high)
    r_high = m.compute_churn_risk(mock_session, "U1", as_of=date(2025, 1, 10))
    assert r_high is not None and r_low is not None and r_high < r_low


def test_compute_churn_risk_gap_increases_risk(mock_session, monkeypatch):
    from seedtest_api.services import metrics as m

    def stats_small(session, user_id, lookback_days=56):
        return {
            "last_seen": date(2025, 1, 6),
            "sessions": 5,
            "mean_gap_days": 1.0,
            "first_seen": date(2024, 12, 1),
        }

    def stats_large(session, user_id, lookback_days=56):
        return {
            "last_seen": date(2025, 1, 6),
            "sessions": 5,
            "mean_gap_days": 6.0,
            "first_seen": date(2024, 12, 1),
        }

    monkeypatch.setattr(m, "load_user_session_stats", stats_small)
    r_small = m.compute_churn_risk(mock_session, "U1", as_of=date(2025, 1, 10))
    monkeypatch.setattr(m, "load_user_session_stats", stats_large)
    r_large = m.compute_churn_risk(mock_session, "U1", as_of=date(2025, 1, 10))
    assert r_large is not None and r_small is not None and r_large > r_small


def test_compute_churn_risk_no_data(mock_session, monkeypatch):
    from seedtest_api.services import metrics as m

    monkeypatch.setattr(m, "load_user_session_stats", lambda *a, **k: None)
    r = m.compute_churn_risk(mock_session, "U1", as_of=date(2025, 1, 6))
    assert r is None


def test_compute_churn_risk_horizon_flag_effect(mock_session, monkeypatch):
    from seedtest_api.services import metrics as m

    # For same last_seen/as_of gap, smaller horizon should increase base and thus risk
    def fake_stats(session, user_id, lookback_days=56):
        return {
            "last_seen": date(2025, 1, 6),
            "sessions": 2,
            "mean_gap_days": 2.0,
            "first_seen": date(2024, 12, 1),
        }

    monkeypatch.setattr(m, "load_user_session_stats", fake_stats)
    as_of = date(2025, 1, 13)  # 7 days later
    monkeypatch.setenv("METRICS_CHURN_HORIZON_DAYS", "14")
    r14 = m.compute_churn_risk(mock_session, "U1", as_of=as_of)
    monkeypatch.setenv("METRICS_CHURN_HORIZON_DAYS", "7")
    r7 = m.compute_churn_risk(mock_session, "U1", as_of=as_of)
    assert r7 is not None and r14 is not None and r7 > r14


def test_calculate_and_store_weekly_kpi_sets_S_when_available(
    mock_session, monkeypatch
):
    from seedtest_api.services import metrics as m

    monkeypatch.setattr(m, "compute_improvement_index", lambda *a, **k: None)
    monkeypatch.setattr(m, "compute_time_efficiency", lambda *a, **k: None)
    monkeypatch.setattr(m, "compute_recovery_rate", lambda *a, **k: None)
    monkeypatch.setattr(m, "compute_engagement", lambda *a, **k: None)
    monkeypatch.setattr(m, "compute_goal_attainment_probability", lambda *a, **k: 0.5)
    monkeypatch.setattr(m, "compute_churn_risk", lambda *a, **k: 0.33)
    captured: Dict[str, Any] = {}

    def fake_upsert(session, user_id, ws, kpis):
        captured["kpis"] = kpis

    monkeypatch.setattr(m, "upsert_weekly_kpi", fake_upsert)
    out = m.calculate_and_store_weekly_kpi(mock_session, "U1", date(2025, 1, 6))
    assert out["kpis"]["S"] == 0.33
