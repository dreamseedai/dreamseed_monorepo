#!/usr/bin/env python3
from __future__ import annotations

"""Print row counts for key analytics tables.

Tables:
- mirt_item_params
- mirt_ability
- mirt_fit_meta
- student_topic_theta
- weekly_kpi

Uses the app's DB session helper so DATABASE_URL resolution stays consistent.
"""

import sqlalchemy as sa
from ..services.db import get_session


def _count(table: str) -> str:
    try:
        with get_session() as s:
            row = s.execute(sa.text(f"SELECT COUNT(*) FROM {table}"))
            n = row.scalar()  # type: ignore[assignment]
            return f"{table}: {int(n)}"
    except Exception as e:  # noqa: BLE001
        return f"{table}: ERROR ({e})"


def main() -> None:
    tables = [
        "mirt_item_params",
        "mirt_ability",
        "mirt_fit_meta",
        "student_topic_theta",
        "weekly_kpi",
    ]
    for t in tables:
        print(_count(t))


if __name__ == "__main__":
    main()
