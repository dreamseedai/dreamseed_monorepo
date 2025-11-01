#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import sqlalchemy as sa

# Reuse app DB utilities
from ..services.db import get_session
from ..app.clients.r_irt import RIrtClient


async def run_calibration(
    lookback_days: int | None = None, model: str | None = None
) -> None:
    lookback_days = int(
        lookback_days
        if lookback_days is not None
        else os.getenv("IRT_CALIB_LOOKBACK_DAYS", "30")
    )
    model = (model or os.getenv("IRT_MODEL") or "2PL").strip()

    observations: List[Dict[str, Any]] = []

    # Extract observations (user_id, item_id, is_correct, responded_at)
    since_dt = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
    stmt = sa.text(
        """
        SELECT user_id, item_id, is_correct, responded_at
        FROM responses
        WHERE responded_at >= :since
        ORDER BY responded_at
        LIMIT 10000
        """
    )
    # If `responses` table is not present, try to derive from exam_results JSON
    with get_session() as s:
        try:
            rows = s.execute(stmt, {"since": since_dt}).mappings().all()
            for r in rows:
                observations.append(
                    {
                        "user_id": r["user_id"],
                        "item_id": r["item_id"],
                        "is_correct": bool(r["is_correct"]),
                        "responded_at": str(r["responded_at"]),
                    }
                )
        except Exception:
            # Ensure the session is usable after a failed statement (e.g., missing table)
            try:
                s.rollback()
            except Exception:
                pass
            stmt2 = sa.text(
                """
                SELECT user_id, session_id, COALESCE(updated_at, created_at) AS ts, result_json
                FROM exam_results
                WHERE COALESCE(updated_at, created_at) >= :since
                ORDER BY COALESCE(updated_at, created_at)
                LIMIT 10000
                """
            )
            try:
                rows = s.execute(stmt2, {"since": since_dt}).mappings().all()
            except Exception:
                rows = []
            for r in rows:
                doc = r.get("result_json") or {}
                for q in doc.get("questions") or []:
                    iid = q.get("question_id")
                    if iid is None:
                        continue
                    is_corr = q.get("is_correct")
                    if is_corr is None:
                        is_corr = q.get("correct")
                    observations.append(
                        {
                            "user_id": r.get("user_id"),
                            "item_id": str(iid),
                            "is_correct": (
                                bool(is_corr) if is_corr is not None else None
                            ),
                            "responded_at": str(r.get("ts")),
                        }
                    )

    if not observations:
        print("No observations found; exiting.")
        return

    client = RIrtClient()
    result = await client.calibrate(observations, model=model)

    # Expected result contains item_params, abilities, and fit metadata
    items = result.get("item_params") or []
    abilities = result.get("abilities") or []
    meta = result.get("fit_meta") or {}

    up_item = sa.text(
        """
        INSERT INTO mirt_item_params (item_id, model, params, version, fitted_at)
        VALUES (:item_id, :model, CAST(:params::text AS jsonb), COALESCE(:version,'v1'), NOW())
        ON CONFLICT (item_id) DO UPDATE SET params=EXCLUDED.params, model=EXCLUDED.model, version=EXCLUDED.version, fitted_at=NOW()
        """
    )
    up_ability = sa.text(
        """
        INSERT INTO mirt_ability (user_id, theta, se, model, version, fitted_at)
        VALUES (:user_id, :theta, :se, :model, COALESCE(:version,'v1'), NOW())
        ON CONFLICT (user_id, version) DO UPDATE SET theta=EXCLUDED.theta, se=EXCLUDED.se, model=EXCLUDED.model, fitted_at=NOW()
        """
    )
    up_meta = sa.text(
        """
        INSERT INTO mirt_fit_meta (run_id, model_spec, metrics, fitted_at)
        VALUES (:run_id, CAST(:model_spec::text AS jsonb), CAST(:metrics::text AS jsonb), NOW())
        ON CONFLICT (run_id) DO UPDATE SET model_spec=EXCLUDED.model_spec, metrics=EXCLUDED.metrics, fitted_at=NOW()
        """
    )

    with get_session() as s:
        for it in items:
            s.execute(
                up_item,
                {
                    "item_id": str(it.get("item_id")),
                    "model": str(it.get("model") or model),
                    "params": json.dumps(it.get("params") or {}),
                    "version": str(it.get("version") or "v1"),
                },
            )
        for ab in abilities:
            s.execute(
                up_ability,
                {
                    "user_id": str(ab.get("user_id")),
                    "theta": float(ab.get("theta") or 0.0),
                    "se": float(ab.get("se") or 0.0),
                    "model": str(ab.get("model") or model),
                    "version": str(ab.get("version") or "v1"),
                },
            )
        run_id = (
            meta.get("run_id") or f"fit-{datetime.now(tz=timezone.utc).isoformat()}"
        )
        s.execute(
            up_meta,
            {
                "run_id": str(run_id),
                "model_spec": json.dumps(meta.get("model_spec") or {}),
                "metrics": json.dumps(meta.get("metrics") or {}),
            },
        )

    print("Calibration upsert completed.")


async def main() -> None:
    await run_calibration()


if __name__ == "__main__":
    asyncio.run(main())
