"""
Aggregate daily topic features into features_topic_daily for active user/topic pairs.

- Uses services.features_backfill.backfill_features_topic_daily
- Enumerates (user_id, topic_id) pairs from attempt VIEW for a target date
- Idempotent upsert into features_topic_daily

Environment:
  None required (uses DATABASE_URL via settings)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import sys
from pathlib import Path

def _ensure_project_root_on_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "apps" / "seedtest_api").is_dir():
            path_str = str(parent)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
            break

def _import_services():
    try:
        from apps.seedtest_api.services.db import get_session  # type: ignore
        from apps.seedtest_api.services.features_backfill import (  # type: ignore
            backfill_features_topic_daily,
        )
        return get_session, backfill_features_topic_daily
    except Exception:
        _ensure_project_root_on_path()
        from apps.seedtest_api.services.db import get_session  # type: ignore
        from apps.seedtest_api.services.features_backfill import (  # type: ignore
            backfill_features_topic_daily,
        )
        return get_session, backfill_features_topic_daily

try:
    from sqlalchemy import text  # type: ignore
except Exception:
    def text(sql: str) -> str:  # type: ignore
        return sql


def _pairs_for_date(session, target_date: date) -> list[tuple[str, str]]:
    d0 = datetime.combine(target_date, datetime.min.time())
    d1 = d0 + timedelta(days=1)
    rows = session.execute(
        text(
            """
            SELECT student_id::text AS user_id, topic_id
            FROM attempt
            WHERE completed_at >= :d0 AND completed_at < :d1
              AND student_id IS NOT NULL AND topic_id IS NOT NULL
            GROUP BY 1,2
            LIMIT 200000
            """
        ),
        {"d0": d0, "d1": d1},
    ).fetchall()
    return [(r[0], r[1]) for r in rows if r[0] and r[1]]


def main(anchor_date: date | None = None, dry_run: bool = False) -> int:
    """Aggregate features for the given date (default: yesterday).

    Returns 0 on success.
    """
    import time

    start = time.time()
    target = anchor_date or (date.today() - timedelta(days=1))

    processed = 0
    failed = 0

    try:
        get_session, backfill_features_topic_daily = _import_services()
        with get_session() as session:
            pairs = _pairs_for_date(session, target)
            if not pairs:
                print(f"[INFO] No attempt pairs for date={target}; exiting")
                return 0

            print(f"[INFO] Aggregating features_topic_daily for {len(pairs)} pairs; date={target} dry_run={dry_run}")
            for user_id, topic_id in pairs:
                try:
                    backfill_features_topic_daily(session, user_id, topic_id, target)
                    processed += 1
                except Exception as e:
                    failed += 1
                    print(f"[ERROR] user={user_id} topic={topic_id} err={e}")

            if dry_run:
                session.rollback()
                print("[INFO] Dry-run mode: rolled back all changes")

        dur_ms = int((time.time() - start) * 1000)
        print(f"[INFO] Summary: processed={processed} failed={failed} date={target} duration_ms={dur_ms}")
        return 0
    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback

        traceback.print_exc()
        return 1


def cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate features_topic_daily for a date (default: yesterday)")
    parser.add_argument("--date", help="YYYY-MM-DD", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    anchor = None
    if args.date:
        try:
            anchor = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"[ERROR] invalid --date: {args.date}")
            sys.exit(1)

    sys.exit(main(anchor_date=anchor, dry_run=args.dry_run))


if __name__ == "__main__":
    cli()
