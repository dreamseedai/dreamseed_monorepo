"""
Detect inactive users and trigger immediate P/S recalculation.
- Finds users with no activity for N days (default 7)
- Triggers immediate recalculation of P(goal|state) and S(churn) for these users
- Updates weekly_kpi table with latest risk metrics
Environment:
  INACTIVITY_THRESHOLD_DAYS (optional, default 7): Number of days without activity
  KPI_LOOKBACK_DAYS (optional, default 30): Days to look back for user activity
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional


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
from apps.seedtest_api.services.metrics import (
    calculate_and_store_weekly_kpi,
    compute_churn_risk,
    compute_goal_attainment_probability,
    week_start as iso_week_start,
)

INACTIVITY_THRESHOLD_DAYS = int(os.getenv("INACTIVITY_THRESHOLD_DAYS", "7"))
KPI_LOOKBACK_DAYS = int(os.getenv("KPI_LOOKBACK_DAYS", "30"))


def find_inactive_users(session, threshold_days: int = 7) -> List[str]:
    """Find users who have been inactive for at least threshold_days.

    Checks multiple sources:
    1. exam_results.updated_at (or created_at) - most recent activity
    2. features_topic_daily.last_seen_at - last seen timestamp
    3. session.ended_at - last session end time

    Returns list of user_id strings.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)

    # Try multiple sources to find last activity
    inactive_users = set()

    # Source 1: exam_results
    result = session.execute(
        text(
            """
            SELECT DISTINCT user_id
            FROM exam_results
            WHERE user_id IS NOT NULL
              AND COALESCE(updated_at, created_at) < :cutoff
              AND user_id NOT IN (
                  SELECT DISTINCT user_id
                  FROM exam_results
                  WHERE user_id IS NOT NULL
                    AND COALESCE(updated_at, created_at) >= :cutoff
              )
        """
        ),
        {"cutoff": cutoff_date},
    )
    for row in result.fetchall():
        if row[0]:
            inactive_users.add(str(row[0]))

    # Source 2: features_topic_daily.last_seen_at
    result2 = session.execute(
        text(
            """
            SELECT DISTINCT user_id
            FROM features_topic_daily
            WHERE user_id IS NOT NULL
              AND (last_seen_at IS NULL OR last_seen_at < :cutoff)
              AND user_id NOT IN (
                  SELECT DISTINCT user_id
                  FROM features_topic_daily
                  WHERE user_id IS NOT NULL
                    AND (last_seen_at IS NOT NULL AND last_seen_at >= :cutoff)
              )
        """
        ),
        {"cutoff": cutoff_date},
    )
    for row in result2.fetchall():
        if row[0]:
            inactive_users.add(str(row[0]))

    # Source 3: session.ended_at
    result3 = session.execute(
        text(
            """
            SELECT DISTINCT student_id::text AS user_id
            FROM attempt
            WHERE student_id IS NOT NULL
              AND completed_at < :cutoff
              AND student_id::text NOT IN (
                  SELECT DISTINCT student_id::text
                  FROM attempt
                  WHERE student_id IS NOT NULL
                    AND completed_at >= :cutoff
              )
        """
        ),
        {"cutoff": cutoff_date},
    )
    for row in result3.fetchall():
        if row[0]:
            inactive_users.add(str(row[0]))

    # Also check session table if it exists
    try:
        result4 = session.execute(
            text(
                """
                SELECT DISTINCT user_id
                FROM session
                WHERE user_id IS NOT NULL
                  AND (ended_at IS NULL OR ended_at < :cutoff)
                  AND user_id NOT IN (
                      SELECT DISTINCT user_id
                      FROM session
                      WHERE user_id IS NOT NULL
                        AND (ended_at IS NOT NULL AND ended_at >= :cutoff)
                  )
            """
            ),
            {"cutoff": cutoff_date},
        )
        for row in result4.fetchall():
            if row[0]:
                inactive_users.add(str(row[0]))
    except Exception:
        # session table might not exist
        pass

    return sorted(list(inactive_users))


def recalculate_p_and_s(session, user_id: str, as_of_date: date) -> Optional[dict]:
    """Recalculate P(goal|state) and S(churn) for a user.

    Returns:
        Dict with 'P' and 'S' values, or None if calculation failed
    """
    try:
        # Calculate P (goal attainment probability)
        P = compute_goal_attainment_probability(session, user_id, target=None)

        # Calculate S (churn risk)
        S = compute_churn_risk(session, user_id, as_of_date)

        return {
            "P": P,
            "S": S,
        }
    except Exception as e:
        print(f"[ERROR] Failed to recalculate P/S for user={user_id}: {e}")
        return None


def update_weekly_kpi_with_p_s(
    session, user_id: str, week_start: date, P: Optional[float], S: Optional[float]
) -> None:
    """Update weekly_kpi with new P and S values.

    Preserves existing I_t, E_t, R_t, A_t values.
    """
    # Load existing KPIs
    result = session.execute(
        text(
            """
            SELECT kpis
            FROM weekly_kpi
            WHERE user_id = :user_id
              AND week_start = :week_start
            LIMIT 1
        """
        ),
        {"user_id": user_id, "week_start": week_start},
    )
    row = result.fetchone()

    if row and row[0]:
        import json

        kpis = row[0]
        if isinstance(kpis, str):
            kpis = json.loads(kpis)
        elif not isinstance(kpis, dict):
            kpis = {}
    else:
        kpis = {}

    # Update P and S
    if P is not None:
        kpis["P"] = P
    if S is not None:
        kpis["S"] = S

    # Upsert
    import json

    session.execute(
        text(
            """
            INSERT INTO weekly_kpi (user_id, week_start, kpis, updated_at)
            VALUES (:user_id, :week_start, :kpis::jsonb, NOW())
            ON CONFLICT (user_id, week_start)
            DO UPDATE SET
                kpis = jsonb_set(
                    COALESCE(weekly_kpi.kpis, '{}'::jsonb),
                    '{P}',
                    to_jsonb(:p_value)
                ),
                kpis = jsonb_set(
                    weekly_kpi.kpis,
                    '{S}',
                    to_jsonb(:s_value)
                ),
                updated_at = NOW()
        """
        ),
        {
            "user_id": user_id,
            "week_start": week_start,
            "kpis": json.dumps(kpis),
            "p_value": P if P is not None else kpis.get("P"),
            "s_value": S if S is not None else kpis.get("S"),
        },
    )
    session.commit()


def main(threshold_days: Optional[int] = None, dry_run: bool = False) -> int:
    """Detect inactive users and trigger P/S recalculation.

    Args:
        threshold_days: Inactivity threshold (defaults to INACTIVITY_THRESHOLD_DAYS)
        dry_run: If True, skip database commits

    Returns:
        Exit code: 0 on success, 1 on failure
    """
    import time

    start_time = time.time()

    threshold = (
        threshold_days if threshold_days is not None else INACTIVITY_THRESHOLD_DAYS
    )
    today = date.today()
    current_week_start = iso_week_start(today)

    processed = 0
    failed = 0

    try:
        with get_session() as session:
            inactive_users = find_inactive_users(session, threshold)

            if not inactive_users:
                print(f"[INFO] No inactive users found (threshold={threshold} days)")
                return 0

            print(
                f"[INFO] Found {len(inactive_users)} inactive users (threshold={threshold} days); dry_run={dry_run}"
            )

            for user_id in inactive_users:
                try:
                    # Recalculate P and S
                    ps_values = recalculate_p_and_s(session, user_id, today)

                    if ps_values:
                        if not dry_run:
                            # Update weekly_kpi with new P and S
                            update_weekly_kpi_with_p_s(
                                session,
                                user_id,
                                current_week_start,
                                ps_values.get("P"),
                                ps_values.get("S"),
                            )

                        processed += 1
                        if os.getenv("DEBUG", "").lower() == "true":
                            print(
                                f"[DEBUG] OK user={user_id} P={ps_values.get('P')} S={ps_values.get('S')}"
                            )
                    else:
                        failed += 1
                        print(f"[WARN] Could not calculate P/S for user={user_id}")

                except Exception as e:
                    failed += 1
                    print(f"[ERROR] user={user_id} error={e}")

            if dry_run:
                session.rollback()
                print("[INFO] Dry-run mode: rolled back all changes")

        duration_ms = int((time.time() - start_time) * 1000)
        print(
            f"[INFO] Summary: processed={processed}, failed={failed}, threshold={threshold} days, duration_ms={duration_ms}"
        )
        return 0 if failed == 0 else 1

    except Exception as e:
        print(f"[FATAL] Unhandled exception: {e}")
        import traceback

        traceback.print_exc()
        return 1


def cli() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect inactive users and trigger P/S recalculation"
    )
    parser.add_argument(
        "--threshold",
        help="Inactivity threshold in days (default: 7)",
        default=None,
        type=int,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not commit changes to database",
    )

    args = parser.parse_args()

    exit_code = main(threshold_days=args.threshold, dry_run=args.dry_run)
    exit(exit_code)


if __name__ == "__main__":
    cli()
