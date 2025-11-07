#!/usr/bin/env python3
# cSpell:ignore mirt
from __future__ import annotations

"""Ops verification: print table counts and hit key APIs for a sample user.

Steps:
- Print row counts for IRT/metrics tables (reuses verify_counts).
- Pick a sample user_id from mirt_ability (preferred), or weekly_kpi, or exam_results.
- Call theta API and weekly KPIs API with LOCAL_DEV=true.

Exits 0 even if sample user is not found; prints a helpful note instead of failing.
"""

import os
from typing import Optional

import sqlalchemy as sa
from fastapi.testclient import TestClient

from ..jobs.verify_counts import main as counts_main
from ..main import app
from ..services.db import get_session
from ..settings import settings as app_settings


def _find_sample_user() -> Optional[str]:
    # 1) From mirt_ability (latest first)
    with get_session() as s:
        try:
            row = s.execute(
                sa.text(
                    """
                    SELECT user_id
                    FROM mirt_ability
                    ORDER BY fitted_at DESC
                    LIMIT 1
                    """
                )
            ).first()
            if row and row[0]:
                return str(row[0])
        except Exception:
            pass
    # 2) From weekly_kpi (latest first)
    with get_session() as s:
        try:
            row = s.execute(
                sa.text(
                    """
                    SELECT user_id
                    FROM weekly_kpi
                    ORDER BY week_start DESC
                    LIMIT 1
                    """
                )
            ).first()
            if row and row[0]:
                return str(row[0])
        except Exception:
            pass
    # 3) From exam_results (latest first)
    with get_session() as s:
        try:
            row = s.execute(
                sa.text(
                    """
                    SELECT user_id
                    FROM exam_results
                    ORDER BY COALESCE(updated_at, created_at) DESC
                    LIMIT 1
                    """
                )
            ).first()
            if row and row[0]:
                return str(row[0])
        except Exception:
            pass
    return None


def main() -> None:
    # Ensure LOCAL_DEV for auth bypass
    os.environ.setdefault("LOCAL_DEV", "true")

    print("== Table counts ==")
    counts_main()

    uid = _find_sample_user()
    if not uid:
        print(
            "No sample user found (mirt_ability/weekly_kpi/exam_results empty). Skipping API calls."
        )
        return

    api_prefix = app_settings.API_PREFIX.rstrip("/")
    client = TestClient(app)

    print(f"\n== API checks for user_id={uid} ==")
    # Theta API
    r1 = client.get(f"{api_prefix}/analysis/irt/theta", params={"user_id": uid})
    print(f"GET {api_prefix}/analysis/irt/theta -> {r1.status_code}")
    # Limit output noise
    try:
        body = r1.json()
        print(f"  items: {len(body) if isinstance(body, list) else 'n/a'}")
    except Exception:
        pass

    # Weekly KPIs API
    r2 = client.get(
        f"{api_prefix}/analysis/metrics/weekly",
        params={"user_id": uid, "weeks": 4, "include_empty": True},
    )
    print(f"GET {api_prefix}/analysis/metrics/weekly -> {r2.status_code}")
    try:
        body2 = r2.json()
        print(f"  rows: {len(body2) if isinstance(body2, list) else 'n/a'}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
