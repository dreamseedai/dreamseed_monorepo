#!/usr/bin/env python3
from __future__ import annotations

"""
Backfill topic-level theta (student_topic_theta) from general abilities (mirt_ability).

Strategy:
- For each user with a recent mirt_ability (or latest regardless), find topics they've engaged with
  using exam_results JSON (result_json.questions[].topic). If responses table exists, it can
  also be used to determine items -> topics once mapping is available; for now we rely on
  exam_results which already stores topic per question.
- Upsert one row per (user_id, topic_id) with theta/se/model/version/fitted_at from mirt_ability.

Env flags:
- BF_LOOKBACK_DAYS: lookback window to scan exam_results for topics (default 180)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Set

import sqlalchemy as sa

from ..services.db import get_session


def _distinct_users_with_ability() -> List[str]:
    with get_session() as s:
        try:
            rows = (
                s.execute(
                    sa.text(
                        """
                SELECT DISTINCT user_id FROM mirt_ability
            """
                    )
                )
                .mappings()
                .all()
            )
            return [r["user_id"] for r in rows]
        except Exception:
            return []


def _topics_for_user(user_id: str, since_dt: datetime) -> Set[str]:
    topics: Set[str] = set()
    with get_session() as s:
        try:
            rows = (
                s.execute(
                    sa.text(
                        """
                SELECT result_json
                FROM exam_results
                WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :since
                ORDER BY COALESCE(updated_at, created_at)
                LIMIT 2000
            """
                    ),
                    {"uid": user_id, "since": since_dt},
                )
                .mappings()
                .all()
            )
            for r in rows:
                doc = r.get("result_json") or {}
                for q in doc.get("questions") or []:
                    t = q.get("topic")
                    if t is not None and str(t).strip():
                        topics.add(str(t))
        except Exception:
            pass
    return topics


def _latest_ability(user_id: str) -> Dict[str, Any] | None:
    with get_session() as s:
        try:
            row = (
                s.execute(
                    sa.text(
                        """
                SELECT theta, se, model, version, fitted_at
                FROM mirt_ability
                WHERE user_id = :uid
                ORDER BY fitted_at DESC
                LIMIT 1
            """
                    ),
                    {"uid": user_id},
                )
                .mappings()
                .first()
            )
            return dict(row) if row else None
        except Exception:
            return None


def _upsert_topic_theta(user_id: str, topic_id: str, ability: Dict[str, Any]) -> None:
    with get_session() as s:
        s.execute(
            sa.text(
                """
                INSERT INTO student_topic_theta (user_id, topic_id, theta, se, model, version, fitted_at)
                VALUES (:uid, :tid, :theta, :se, :model, :version, :fitted_at)
                ON CONFLICT (user_id, topic_id)
                DO UPDATE SET theta=EXCLUDED.theta, se=EXCLUDED.se, model=EXCLUDED.model,
                              version=EXCLUDED.version, fitted_at=EXCLUDED.fitted_at
                """
            ),
            {
                "uid": user_id,
                "tid": topic_id,
                "theta": float(ability.get("theta") or 0.0),
                "se": (
                    float(ability.get("se") or 0.0)
                    if ability.get("se") is not None
                    else None
                ),
                "model": str(ability.get("model") or "mirt"),
                "version": str(ability.get("version") or "v1"),
                "fitted_at": ability.get("fitted_at") or datetime.now(tz=timezone.utc),
            },
        )


def main() -> None:
    lookback_days = int(os.getenv("BF_LOOKBACK_DAYS", "180"))
    since_dt = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
    users = _distinct_users_with_ability()
    if not users:
        print("No users found in mirt_ability; nothing to backfill.")
        return
    total_rows = 0
    for uid in users:
        ability = _latest_ability(uid)
        if not ability:
            continue
        tset = _topics_for_user(uid, since_dt)
        for tid in tset:
            _upsert_topic_theta(uid, tid, ability)
            total_rows += 1
    print(f"Backfill complete. Upserted {total_rows} topic thetas.")


if __name__ == "__main__":
    main()
