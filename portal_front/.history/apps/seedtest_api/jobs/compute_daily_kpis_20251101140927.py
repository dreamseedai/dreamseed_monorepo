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
from apps.seedtest_api.services.metrics import calculate_and_store_weekly_kpi, week_start as iso_week_start
import sys
from pathlib import Path

LOOKBACK_DAYS = int(os.getenv("KPI_LOOKBACK_DAYS", "30"))


def _distinct_recent_users(session) -> list[str]:
    since = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    q = text(
        """
        SELECT DISTINCT user_id
        FROM exam_results
        WHERE updated_at >= :since OR created_at >= :since
          AND user_id IS NOT NULL AND user_id <> ''
        LIMIT 100000
        """
    )
    rows = session.execute(q, {"since": since}).fetchall()
    return [r[0] for r in rows if r[0]]


def main() -> None:
    today = date.today()
    wk = iso_week_start(today)
    with get_session() as session:
        users = _distinct_recent_users(session)
        if not users:
            print("No recent users found; exiting.")
            return

        print(f"Computing KPIs for {len(users)} users; week_start={wk}")
        for uid in users:
            try:
                payload = calculate_and_store_weekly_kpi(session, uid, wk)
                # optional log
                print(f"OK user={uid} kpis={payload.get('kpis',{})}")
            except Exception as e:
                # best-effort; continue others
                print(f"ERR user={uid} {e}")


if __name__ == "__main__":
    main()
