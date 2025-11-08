#!/usr/bin/env python3
# cSpell:ignore mirt lookback
from __future__ import annotations

"""
Recompute weekly KPIs for users as a one-shot.

Behavior:
- Discover users from mirt_ability (preferred) or exam_results as fallback.
- Determine the target week_start (ISO Monday) based on today unless overridden via env.
- Call calculate_and_store_weekly_kpi for each user.

Env flags:
- KPI_USERS_SINCE_DAYS: lookback in days when discovering users from exam_results (default 90)
- KPI_WEEK_START: explicit YYYY-MM-DD week start to recompute; if not set, use current week Monday
"""

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Set

import sqlalchemy as sa

from ..services.db import get_session
from ..services.metrics import calculate_and_store_weekly_kpi
from ..services.metrics import week_start as iso_week_start


def _distinct_users() -> Set[str]:
    users: Set[str] = set()
    with get_session() as s:
        # Preferred: users with ability
        try:
            rows = s.execute(sa.text("SELECT DISTINCT user_id FROM mirt_ability"))
            users.update(r[0] for r in rows.fetchall())
        except Exception:
            pass
    if users:
        return users
    # Fallback: users seen in exam_results within lookback
    lb_days = int(os.getenv("KPI_USERS_SINCE_DAYS", "90"))
    since_dt = datetime.now(tz=timezone.utc) - timedelta(days=lb_days)
    with get_session() as s:
        try:
            rows = s.execute(
                sa.text(
                    """
                    SELECT DISTINCT user_id
                    FROM exam_results
                    WHERE COALESCE(updated_at, created_at) >= :since
                    LIMIT 5000
                    """
                ),
                {"since": since_dt},
            ).fetchall()
            users.update(str(r[0]) for r in rows)
        except Exception:
            pass
    return users


def _resolve_week_start() -> date:
    v = os.getenv("KPI_WEEK_START")
    if v:
        try:
            return date.fromisoformat(v)
        except Exception:
            pass
    return iso_week_start(date.today())


def main() -> None:
    users = _distinct_users()
    if not users:
        print("No users found; skipping KPI recompute.")
        return
    ws = _resolve_week_start()
    n = 0
    with get_session() as s:
        for uid in users:
            try:
                calculate_and_store_weekly_kpi(s, uid, ws)
                n += 1
            except Exception as e:  # pragma: no cover
                print(f"WARN: KPI recompute failed for {uid}: {e}")
    print(f"Weekly KPI recompute finished. Users processed: {n} (week_start={ws}).")


if __name__ == "__main__":
    main()
