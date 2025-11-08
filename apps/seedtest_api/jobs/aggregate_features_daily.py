"""
Aggregate daily topic features from attempt VIEW and update features_topic_daily.
- Uses attempt VIEW to compute: attempts, correct, avg_time_ms, rt_median, hints
- Optionally includes IRT theta estimates from mirt_ability or student_topic_theta
- Upserts to features_topic_daily table (Dev Contract 2-6)
Environment:
  AGG_LOOKBACK_DAYS (optional, default 7): Number of days to aggregate back from today
  AGG_INCLUDE_THETA (optional, default false): Whether to include IRT theta estimates
"""
# cSpell:ignore LOOKBACK Upserted
from __future__ import annotations

from datetime import date, datetime, timedelta
import os
import sys
from pathlib import Path

# Ensure "apps.*" imports work when running this file directly
def _ensure_project_root_on_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "apps" / "seedtest_api").is_dir():
            path_str = str(parent)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
            break

_ensure_project_root_on_path()

from sqlalchemy import text
from apps.seedtest_api.services.db import get_session
from apps.seedtest_api.services.metrics import compute_improvement_index

LOOKBACK_DAYS = int(os.getenv("AGG_LOOKBACK_DAYS", "7"))
INCLUDE_THETA = os.getenv("AGG_INCLUDE_THETA", "false").lower() == "true"


def _distinct_user_topic_date_combos(session, since_date: date) -> list[tuple[str, str, date]]:
    """Find all (user_id, topic_id, date) combinations from attempt VIEW."""
    result = session.execute(
        text("""
            SELECT DISTINCT
                student_id::text AS user_id,
                topic_id,
                DATE(completed_at) AS date
            FROM attempt
            WHERE completed_at >= :since
              AND student_id IS NOT NULL
              AND topic_id IS NOT NULL
            ORDER BY user_id, topic_id, date
        """),
        {"since": datetime.combine(since_date, datetime.min.time())},
    )
    return [(row[0], row[1], row[2]) for row in result.fetchall()]


def _aggregate_one_day(session, user_id: str, topic_id: str, target_date: date) -> dict:
    """Aggregate stats for one user/topic/date combination."""
    date_start = datetime.combine(target_date, datetime.min.time())
    date_end = date_start + timedelta(days=1)
    
    result = session.execute(
        text("""
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
        """),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "date_start": date_start,
            "date_end": date_end,
        },
    )
    row = result.fetchone()
    
    if row is None or (row[0] or 0) == 0:
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


def _load_theta_if_needed(session, user_id: str, topic_id: str, target_date: date) -> tuple[float | None, float | None]:
    """Load IRT theta estimate if INCLUDE_THETA is enabled.
    Order: student_topic_theta (topic-level) -> mirt_ability (user-level fallback).
    """
    if not INCLUDE_THETA:
        return (None, None)
    
    # Try student_topic_theta first (topic-level theta)
    result = session.execute(
        text("""
            SELECT theta, se
            FROM student_topic_theta
            WHERE user_id = :user_id
              AND topic_id = :topic_id
              AND updated_at <= :target_date
            ORDER BY updated_at DESC
            LIMIT 1
        """),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "target_date": datetime.combine(target_date, datetime.max.time()),
        },
    )
    row = result.fetchone()
    if row and row[0] is not None:
        return (float(row[0]), float(row[1]) if row[1] is not None else None)
    
    # Fallback: use latest user-level theta from mirt_ability up to the date
    result2 = session.execute(
        text("""
            SELECT theta, se
            FROM mirt_ability
            WHERE user_id = :user_id
              AND fitted_at <= :target_date
            ORDER BY fitted_at DESC
            LIMIT 1
        """),
        {
            "user_id": user_id,
            "target_date": datetime.combine(target_date, datetime.max.time()),
        },
    )
    row2 = result2.fetchone()
    if row2 and row2[0] is not None:
        return (float(row2[0]), float(row2[1]) if row2[1] is not None else None)
    
    return (None, None)


def _upsert_features_daily(
    session,
    user_id: str,
    topic_id: str,
    target_date: date,
    stats: dict,
    theta_estimate: float | None = None,
    theta_sd: float | None = None,
    improvement: float | None = None,
) -> None:
    """Upsert one row to features_topic_daily."""
    session.execute(
        text("""
            INSERT INTO features_topic_daily
              (user_id, topic_id, date, attempts, correct, avg_time_ms, hints,
               theta_estimate, theta_sd, rt_median, improvement, last_seen_at, computed_at)
            VALUES
              (:user_id, :topic_id, :date, :attempts, :correct, :avg_time_ms, :hints,
               :theta_estimate, :theta_sd, :rt_median, :improvement, NOW(), NOW())
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
        """),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "date": target_date,
            "attempts": stats["attempts"],
            "correct": stats["correct"],
            "avg_time_ms": stats["avg_time_ms"],
            "hints": stats["hints"],
            "theta_estimate": theta_estimate,
            "theta_sd": theta_sd,
            "rt_median": stats["rt_median"],
            "improvement": improvement,
        },
    )
    session.commit()


def main(anchor_date: date | None = None, dry_run: bool = False) -> int:
    """Aggregate daily topic features for all active users/topics.
    
    Args:
        anchor_date: Date to aggregate for (defaults to yesterday, as today may be incomplete)
        dry_run: If True, skip database commits (for testing)
    
    Returns:
        Exit code: 0 on success, 1 on failure
    """
    import time
    start_time = time.time()
    
    # Default to yesterday (today's data may be incomplete)
    if anchor_date is None:
        anchor_date = date.today() - timedelta(days=1)
    
    since_date = anchor_date - timedelta(days=LOOKBACK_DAYS)
    
    processed = 0
    failed = 0
    
    try:
        with get_session() as session:
            combos = _distinct_user_topic_date_combos(session, since_date)
            
            if not combos:
                print(f"[INFO] No (user_id, topic_id, date) combinations found (lookback={LOOKBACK_DAYS} days); exiting.")
                return 0
            
            print(f"[INFO] Aggregating features for {len(combos)} (user, topic, date) combinations; since={since_date}, anchor={anchor_date}, dry_run={dry_run}")
            
            for user_id, topic_id, target_date in combos:
                # Skip future dates
                if target_date > anchor_date:
                    continue
                
                try:
                    stats = _aggregate_one_day(session, user_id, topic_id, target_date)
                    
                    # Load theta if needed
                    theta_estimate, theta_sd = _load_theta_if_needed(session, user_id, topic_id, target_date)
                    
                    # Calculate improvement index (accuracy or theta-based delta)
                    improvement = None
                    try:
                        improvement = compute_improvement_index(
                            session, user_id, target_date, window_days=14
                        )
                    except Exception as e:
                        if os.getenv("DEBUG", "").lower() == "true":
                            print(f"[DEBUG] Improvement calculation failed for user={user_id} topic={topic_id} date={target_date}: {e}")
                    
                    if not dry_run:
                        _upsert_features_daily(
                            session,
                            user_id,
                            topic_id,
                            target_date,
                            stats,
                            theta_estimate,
                            theta_sd,
                            improvement,
                        )
                    
                    processed += 1
                    
                    if os.getenv("DEBUG", "").lower() == "true":
                        print(f"[DEBUG] OK user={user_id} topic={topic_id} date={target_date} attempts={stats['attempts']}")
                
                except Exception as e:
                    failed += 1
                    print(f"[ERROR] user={user_id} topic={topic_id} date={target_date} error={e}")
            
            if dry_run:
                session.rollback()
                print("[INFO] Dry-run mode: rolled back all changes")
        
        duration_ms = int((time.time() - start_time) * 1000)
        print(f"[INFO] Summary: processed={processed}, failed={failed}, duration_ms={duration_ms}")
        return 0
        
    except Exception as e:
        print(f"[FATAL] Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cli() -> None:
    """CLI entry point with argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Aggregate daily topic features from attempt VIEW"
    )
    parser.add_argument(
        "--date",
        help="Anchor date (YYYY-MM-DD, defaults to yesterday)",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not commit changes to database",
    )
    
    args = parser.parse_args()
    
    anchor_date = None
    if args.date:
        try:
            anchor_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"[ERROR] Invalid date format: {args.date} (expected YYYY-MM-DD)")
            exit(1)
    
    exit_code = main(anchor_date=anchor_date, dry_run=args.dry_run)
    exit(exit_code)


if __name__ == "__main__":
    cli()

