from __future__ import annotations

from datetime import datetime, timedelta, timezone, date
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from .metrics_calculator import MetricsCalculator


def _week_bounds(now: Optional[datetime] = None) -> tuple[date, datetime, datetime]:
    """Return (week_start_date, start_dt, end_dt) for the ISO week of `now`.

    We define week as starting Monday 00:00:00 UTC.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    # Normalize to UTC and get Monday of current week
    # Python: Monday = 0 ... Sunday = 6
    dow = now.weekday()
    monday = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(days=dow)
    week_start = datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc)
    start_dt = week_start
    end_dt = start_dt + timedelta(days=7)
    return week_start.date(), start_dt, end_dt


def recompute_weekly_kpi_for_recent_users(
    db: Session,
    weeks_window: int = 1,
    limit_users: Optional[int] = None,
) -> dict:
    """Recompute weekly KPI for users active in the recent window.

    - Finds distinct user_ids with exam_results in the last `weeks_window` weeks.
    - Computes KPIs using MetricsCalculator over that same window (best-effort approximation).
    - Upserts into weekly_kpi for the current ISO week_start.

    Returns a small summary dict with counts.
    """
    calc = MetricsCalculator(db)

    # Determine selection window: last `weeks_window` weeks from now
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(weeks=max(1, weeks_window))

    # Pick the target week bucket to store KPIs (the current week)
    week_start_date, _, _ = _week_bounds(now)

    # Select distinct users active in this window
    sql = text(
        """
        SELECT DISTINCT user_id
        FROM exam_results
        WHERE COALESCE(updated_at, created_at) >= :start
        ORDER BY user_id
        LIMIT :lim
        """
    )
    lim = limit_users if isinstance(limit_users, int) and limit_users > 0 else 10000
    rows = db.execute(sql, {"start": start_dt, "lim": lim}).mappings().all()
    user_ids = [str(r["user_id"]) for r in rows]

    processed = 0
    for uid in user_ids:
        try:
            kpis: Dict[str, Any] = {
                "improvement_index": calc.calculate_improvement_index(uid, weeks=weeks_window),
                "efficiency_index": calc.calculate_efficiency_index(uid, weeks=weeks_window),
                "recovery_index": calc.calculate_recovery_index(uid, weeks=weeks_window),
                "engagement_index": calc.calculate_engagement_index(uid, weeks=weeks_window),
                "dropout_risk": calc.calculate_dropout_risk(uid),
            }
            calc.upsert_weekly_kpi(uid, week_start_date, kpis)
            processed += 1
        except Exception:
            # Swallow per-user errors to keep the job resilient
            db.rollback()
            continue

    return {"week_start": str(week_start_date), "users_considered": len(user_ids), "users_processed": processed}
