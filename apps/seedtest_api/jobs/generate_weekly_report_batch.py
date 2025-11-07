"""
Generate weekly reports for multiple users (batch mode).
This is an enhanced version that supports:
- Cohort-based filtering
- Parallel processing (optional)
- Progress tracking
- Error handling per user

Environment:
  REPORT_WEEK_START (optional): Week start date (YYYY-MM-DD, defaults to last week)
  REPORT_FORMAT (optional): Output format (html, pdf, default: pdf)
  S3_BUCKET (required): S3 bucket name
  COHORT_FILTER (optional): SQL WHERE clause for user filtering (e.g., "org_id = 'org123'")
  MAX_USERS (optional): Maximum users to process (default: 1000)
  PARALLEL (optional): Number of parallel workers (default: 1, no parallelization)
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

# Ensure "apps.*" imports work
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
from apps.seedtest_api.jobs.generate_weekly_report import (
    generate_report_for_user,
    main as single_user_main,
)
from apps.seedtest_api.services.db import get_session
from apps.seedtest_api.services.metrics import week_start as iso_week_start


def load_active_users(
    session,
    week_start: date,
    cohort_filter: Optional[str] = None,
    max_users: int = 1000,
) -> List[str]:
    """Load active users for the given week.
    
    Args:
        session: Database session
        week_start: Week start date
        cohort_filter: Optional SQL WHERE clause (e.g., "org_id = 'org123'")
        max_users: Maximum number of users to return
    
    Returns:
        List of user IDs
    """
    base_query = """
        SELECT DISTINCT user_id
        FROM weekly_kpi
        WHERE week_start = :week_start
    """
    
    if cohort_filter:
        base_query += f" AND {cohort_filter}"
    
    base_query += " ORDER BY user_id LIMIT :max_users"
    
    result = session.execute(
        text(base_query),
        {"week_start": week_start, "max_users": max_users},
    )
    
    return [row[0] for row in result.fetchall()]


def generate_reports_batch(
    week_start: date,
    cohort_filter: Optional[str] = None,
    max_users: int = 1000,
    parallel: int = 1,
    dry_run: bool = False,
) -> dict:
    """Generate reports for multiple users in batch.
    
    Args:
        week_start: Week start date
        cohort_filter: Optional SQL WHERE clause for filtering
        max_users: Maximum users to process
        parallel: Number of parallel workers (currently not implemented, sequential only)
        dry_run: If True, skip S3 upload and DB save
    
    Returns:
        Dictionary with summary stats: {processed, failed, skipped, total}
    """
    template_dir = Path(__file__).parent.parent.parent / "reports" / "quarto"
    if not template_dir.exists():
        print(f"[ERROR] Template directory not found: {template_dir}")
        return {"processed": 0, "failed": 0, "skipped": 0, "total": 0}
    
    output_format = os.getenv("REPORT_FORMAT", "pdf")
    s3_bucket = os.getenv("S3_BUCKET") if not dry_run else None
    
    with get_session() as session:
        user_ids = load_active_users(session, week_start, cohort_filter, max_users)
    
    if not user_ids:
        print(f"[INFO] No users found for week={week_start} with filter={cohort_filter}")
        return {"processed": 0, "failed": 0, "skipped": 0, "total": 0}
    
    total = len(user_ids)
    processed = 0
    failed = 0
    skipped = 0
    
    print(
        f"[INFO] Generating reports for {total} users; "
        f"week={week_start}, format={output_format}, "
        f"cohort_filter={cohort_filter}, dry_run={dry_run}"
    )
    
    for idx, user_id in enumerate(user_ids, 1):
        try:
            result = generate_report_for_user(
                user_id,
                week_start,
                template_dir,
                output_format,
                s3_bucket,
            )
            
            if result:
                processed += 1
                if idx % 10 == 0:
                    print(f"[PROGRESS] {idx}/{total} processed; success={processed}, failed={failed}")
            else:
                skipped += 1
                print(f"[WARN] Skipped user={user_id} (no KPIs or render failed)")
        
        except Exception as e:
            failed += 1
            print(f"[ERROR] Failed for user={user_id}: {e}")
            # Continue processing other users
            continue
    
    summary = {
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
    }
    
    print(
        f"[INFO] Batch complete: processed={processed}, failed={failed}, "
        f"skipped={skipped}, total={total}"
    )
    
    return summary


def main() -> int:
    """CLI entry point for batch report generation."""
    parser = argparse.ArgumentParser(
        description="Generate weekly reports for multiple users (batch mode)"
    )
    parser.add_argument(
        "--week",
        type=str,
        help="Week start date (YYYY-MM-DD), defaults to last week",
    )
    parser.add_argument(
        "--cohort",
        type=str,
        help="SQL WHERE clause for user filtering (e.g., 'org_id = \\'org123\\'')",
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=1000,
        help="Maximum users to process (default: 1000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip S3 upload and DB save",
    )
    
    args = parser.parse_args()
    
    # Parse week start date
    if args.week:
        week_start = date.fromisoformat(args.week)
    else:
        week_start = iso_week_start(date.today() - timedelta(weeks=1))
    
    # Generate reports
    summary = generate_reports_batch(
        week_start=week_start,
        cohort_filter=args.cohort,
        max_users=args.max_users,
        parallel=1,  # Sequential for now; parallel processing can be added later
        dry_run=args.dry_run,
    )
    
    # Return exit code based on results
    if summary["failed"] > 0:
        return 1
    if summary["processed"] == 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

