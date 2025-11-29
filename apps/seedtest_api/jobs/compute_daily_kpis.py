"""
Compute daily KPIs (P/S and weekly aggregates) for all active users.
- Uses services.metrics.calculate_and_store_weekly_kpi
- Iterates distinct user_ids from exam_results in the last N days (default 30)
- Writes to weekly_kpi (Dev Contracts 1-5)
Environment:
  METRICS_DEFAULT_TARGET (optional)
  METRICS_USE_BAYESIAN (optional)
"""

# cSpell:ignore LOOKBACK kpis
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

# Fallback for sqlalchemy.text if SQLAlchemy is unavailable
try:
    from sqlalchemy import text  # type: ignore
except Exception:

    def text(sql: str) -> str:
        return sql


# Project imports (adjust if your project structure differs)
from apps.seedtest_api.services.db import get_session
from apps.seedtest_api.services.metrics import (
    calculate_and_store_weekly_kpi,
    week_start as iso_week_start,
)

LOOKBACK_DAYS = int(os.getenv("KPI_LOOKBACK_DAYS", "30"))


def _table_exists(session, name: str) -> bool:
    try:
        q = text(
            """
            SELECT EXISTS (
              SELECT 1 FROM information_schema.tables
              WHERE table_schema='public' AND table_name=:name
            )
            """
        )
        return bool(session.execute(q, {"name": name}).scalar())
    except Exception:
        return False


def _view_exists(session, name: str) -> bool:
    try:
        q = text(
            """
            SELECT EXISTS (
              SELECT 1 FROM information_schema.views
              WHERE table_schema='public' AND table_name=:name
            )
            """
        )
        return bool(session.execute(q, {"name": name}).scalar())
    except Exception:
        return False


def _distinct_recent_users(session) -> list[str]:
    """Find recent active users with robust fallbacks.

    Priority:
    1) mirt_ability by fitted_at (preferred if IRT is running)
    2) weekly_kpi by week_start (already computed users)
    3) exam_results by updated_at/created_at (raw source)
    Note: We intentionally avoid attempt VIEW here to keep user_id in original format.
    """
    since_dt = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)

    # 1) mirt_ability
    if _table_exists(session, "mirt_ability"):
        try:
            rows = session.execute(
                text(
                    """
                    SELECT DISTINCT user_id FROM mirt_ability
                    WHERE fitted_at >= :since
                    ORDER BY fitted_at DESC
                    LIMIT 100000
                    """
                ),
                {"since": since_dt},
            ).fetchall()
            users = [str(r[0]) for r in rows if r and r[0]]
            if users:
                return users
        except Exception:
            pass

    # 2) weekly_kpi (users that already have KPIs)
    if _table_exists(session, "weekly_kpi"):
        try:
            rows = session.execute(
                text(
                    """
                    SELECT DISTINCT user_id FROM weekly_kpi
                    WHERE week_start >= :since_week
                    ORDER BY week_start DESC
                    LIMIT 100000
                    """
                ),
                {"since_week": iso_week_start(since_dt.date())},
            ).fetchall()
            users = [str(r[0]) for r in rows if r and r[0]]
            if users:
                return users
        except Exception:
            pass

    # 3) exam_results (raw source)
    if _table_exists(session, "exam_results"):
        try:
            rows = session.execute(
                text(
                    """
                    SELECT DISTINCT user_id
                    FROM exam_results
                    WHERE (COALESCE(updated_at, created_at)) >= :since
                      AND user_id IS NOT NULL AND user_id <> ''
                    LIMIT 100000
                    """
                ),
                {"since": since_dt},
            ).fetchall()
            users = [str(r[0]) for r in rows if r and r[0]]
            if users:
                return users
        except Exception:
            pass

    return []


def main(anchor_date: date | None = None, dry_run: bool = False) -> int:
    """Compute daily KPIs for all active users.

    Args:
        anchor_date: Date to compute KPIs for (defaults to today)
        dry_run: If True, skip database commits (for testing)

    Returns:
        Exit code: 0 on success, 1 on failure
    """
    import time

    start_time = time.time()

    today = anchor_date or date.today()
    wk = iso_week_start(today)

    processed = 0
    failed = 0

    try:
        with get_session() as session:
            users = _distinct_recent_users(session)
            if not users:
                print(
                    f"[INFO] No recent users found (lookback={LOOKBACK_DAYS} days); exiting."
                )
                return 0

            print(
                f"[INFO] Computing KPIs for {len(users)} users; week_start={wk}, dry_run={dry_run}"
            )

            for uid in users:
                try:
                    payload = calculate_and_store_weekly_kpi(session, uid, wk)
                    processed += 1
                    # optional log
                    if os.getenv("DEBUG", "").lower() == "true":
                        print(f"[DEBUG] OK user={uid} kpis={payload.get('kpis',{})}")
                except Exception as e:
                    failed += 1
                    # best-effort; continue others
                    print(f"[ERROR] user={uid} error={e}")

            # Rollback if dry-run
            if dry_run:
                session.rollback()
                print("[INFO] Dry-run mode: rolled back all changes")

        duration_ms = int((time.time() - start_time) * 1000)
        print(
            f"[INFO] Summary: processed_users={processed}, failed_users={failed}, week={wk}, duration_ms={duration_ms}"
        )
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
        description="Compute daily KPIs for all active users"
    )
    parser.add_argument(
        "--date",
        help="Anchor date (YYYY-MM-DD, defaults to today)",
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
