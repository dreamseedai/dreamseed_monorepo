"""Backfill features_topic_daily from attempt VIEW and metrics calculations."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_session


def backfill_features_topic_daily(
    session: Session,
    user_id: str,
    topic_id: str,
    target_date: date,
    *,
    attempts: int | None = None,
    correct: int | None = None,
    avg_time_ms: int | None = None,
    hints: int | None = None,
    theta_estimate: float | None = None,
    theta_sd: float | None = None,
    rt_median: int | None = None,
    improvement: float | None = None,
) -> None:
    """Upsert daily topic features for a user.

    Args:
        session: Database session
        user_id: User identifier (TEXT)
        topic_id: Topic identifier (TEXT)
        target_date: Target date for aggregation
        attempts: Number of attempts (auto-calculated if None)
        correct: Number of correct attempts (auto-calculated if None)
        avg_time_ms: Average response time in milliseconds (auto-calculated if None)
        hints: Number of hints used (auto-calculated if None)
        theta_estimate: IRT theta estimate (optional)
        theta_sd: IRT theta standard deviation (optional)
        rt_median: Median response time in milliseconds (optional)
        improvement: Improvement score (optional)
    """
    # Auto-calculate from attempt VIEW if not provided
    if attempts is None or correct is None or avg_time_ms is None or hints is None:
        stats = _calculate_stats_from_attempt(session, user_id, topic_id, target_date)
        if attempts is None:
            attempts = stats.get("attempts", 0)
        if correct is None:
            correct = stats.get("correct", 0)
        if avg_time_ms is None:
            avg_time_ms = stats.get("avg_time_ms")
        if hints is None:
            hints = stats.get("hints", 0)
        if rt_median is None:
            rt_median = stats.get("rt_median")

    session.execute(
        text(
            """
            INSERT INTO features_topic_daily
              (user_id, topic_id, date, attempts, correct, avg_time_ms, hints,
               theta_estimate, theta_sd, rt_median, improvement)
            VALUES
              (:user_id, :topic_id, :date, :attempts, :correct, :avg_time_ms, :hints,
               :theta_estimate, :theta_sd, :rt_median, :improvement)
            ON CONFLICT (user_id, topic_id, date)
            DO UPDATE SET
              attempts = EXCLUDED.attempts,
              correct = EXCLUDED.correct,
              avg_time_ms = EXCLUDED.avg_time_ms,
              hints = EXCLUDED.hints,
              theta_estimate = EXCLUDED.theta_estimate,
              theta_sd = EXCLUDED.theta_sd,
              rt_median = EXCLUDED.rt_median,
              improvement = EXCLUDED.improvement,
              last_seen_at = NOW(),
              computed_at = NOW()
        """
        ),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "date": target_date,
            "attempts": attempts,
            "correct": correct,
            "avg_time_ms": avg_time_ms,
            "hints": hints,
            "theta_estimate": theta_estimate,
            "theta_sd": theta_sd,
            "rt_median": rt_median,
            "improvement": improvement,
        },
    )
    session.commit()


def _calculate_stats_from_attempt(
    session: Session,
    user_id: str,
    topic_id: str,
    target_date: date,
) -> dict[str, Any]:
    """Calculate statistics from attempt VIEW for a given user/topic/date."""
    date_start = datetime.combine(target_date, datetime.min.time())
    date_end = date_start + timedelta(days=1)

    result = session.execute(
        text(
            """
            SELECT
              COUNT(*) AS attempts,
              SUM(CASE WHEN correct THEN 1 ELSE 0 END)::int AS correct,
              AVG(response_time_ms)::int AS avg_time_ms,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms)::int AS rt_median,
              SUM(CASE WHEN hint_used THEN 1 ELSE 0 END)::int AS hints
            FROM attempt
            WHERE student_id::text = :user_id
              AND topic_id = :topic_id
              AND completed_at >= :date_start
              AND completed_at < :date_end
        """
        ),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "date_start": date_start,
            "date_end": date_end,
        },
    )
    row = result.fetchone()

    if row is None:
        return {
            "attempts": 0,
            "correct": 0,
            "avg_time_ms": None,
            "rt_median": None,
            "hints": 0,
        }

    return {
        "attempts": row[0] or 0,
        "correct": row[1] or 0,
        "avg_time_ms": int(row[2]) if row[2] is not None else None,
        "rt_median": int(row[3]) if row[3] is not None else None,
        "hints": row[4] or 0,
    }


def backfill_user_topic_range(
    session: Session,
    user_id: str,
    topic_id: str,
    start_date: date,
    end_date: date,
    *,
    include_theta: bool = False,
) -> int:
    """Backfill features_topic_daily for a date range.

    Args:
        session: Database session
        user_id: User identifier
        topic_id: Topic identifier
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        include_theta: Whether to include IRT theta estimates (requires mirt_ability lookup)

    Returns:
        Number of days backfilled
    """
    current_date = start_date
    count = 0

    while current_date <= end_date:
        # Load theta if requested
        theta_estimate = None
        theta_sd = None
        if include_theta:
            theta_data = _load_user_topic_theta(
                session, user_id, topic_id, current_date
            )
            if theta_data:
                theta_estimate = theta_data.get("theta")
                theta_sd = theta_data.get("se")

        backfill_features_topic_daily(
            session,
            user_id,
            topic_id,
            current_date,
            theta_estimate=theta_estimate,
            theta_sd=theta_sd,
        )
        count += 1
        current_date += timedelta(days=1)

    return count


def _load_user_topic_theta(
    session: Session,
    user_id: str,
    topic_id: str,
    target_date: date,
) -> dict[str, float] | None:
    """Load IRT theta estimate for a user/topic as of a given date.

    This looks up from student_topic_theta or mirt_ability tables.
    """
    # Try student_topic_theta first
    result = session.execute(
        text(
            """
            SELECT theta, se
            FROM student_topic_theta
            WHERE user_id = :user_id
              AND topic_id = :topic_id
              AND fitted_at <= :target_date
            ORDER BY fitted_at DESC
            LIMIT 1
        """
        ),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "target_date": datetime.combine(target_date, datetime.max.time()),
        },
    )
    row = result.fetchone()

    if row and row[0] is not None:
        return {
            "theta": float(row[0]),
            "se": float(row[1]) if row[1] is not None and row[1] != "None" else None,
        }

    return None
