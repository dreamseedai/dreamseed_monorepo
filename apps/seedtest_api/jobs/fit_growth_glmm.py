#!/usr/bin/env python3
"""
GLMM Growth Model Fitting Job

Fits mixed-effects model to separate average trend from individual/topic effects:
  score ~ week + (week|student) + (1|topic)

Where:
- score: normalized achievement (e.g., z-scored weekly accuracy)
- week: week index (0, 1, 2, ...)
- student: random intercept + slope per student
- topic: random intercept per topic

Stores:
- growth_glmm_meta: fixed effects, random effects, fit metrics
- weekly_kpi: optionally update with individual slopes
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import date, datetime, timedelta

import httpx
import sqlalchemy as sa

from ..services.db import get_session


def week_start(d: date) -> date:
    """Return Monday of the ISO week containing date d."""
    return d - timedelta(days=d.weekday())


async def fit_growth_model(
    lookback_weeks: int | None = None,
    min_observations: int = 10,
) -> None:
    """
    Fit GLMM growth model to weekly scores.

    Args:
        lookback_weeks: Number of weeks to look back (default: 12)
        min_observations: Minimum observations per student (default: 10)
    """
    lookback_weeks = int(
        lookback_weeks
        if lookback_weeks is not None
        else os.getenv("GLMM_LOOKBACK_WEEKS", "12")
    )
    min_observations = int(
        min_observations
        if min_observations is not None
        else os.getenv("GLMM_MIN_OBSERVATIONS", "10")
    )

    # R GLMM service URL
    r_glmm_url = os.getenv(
        "R_GLMM_BASE_URL", "http://r-glmm-plumber.seedtest.svc.cluster.local:80"
    )
    r_glmm_token = os.getenv("R_GLMM_INTERNAL_TOKEN")
    timeout_secs = int(os.getenv("R_GLMM_TIMEOUT_SECS", "300"))

    print(f"[INFO] Fitting GLMM growth model (lookback={lookback_weeks} weeks)")

    # Load weekly scores from features_topic_daily
    # score = z-scored accuracy per week
    since_date = date.today() - timedelta(weeks=lookback_weeks)

    with get_session() as s:
        stmt = sa.text(
            """
            WITH weekly_agg AS (
                SELECT 
                    user_id,
                    topic_id,
                    DATE_TRUNC('week', date)::date AS week_start,
                    SUM(correct) AS correct,
                    SUM(attempts) AS attempts,
                    CASE 
                        WHEN SUM(attempts) > 0 
                        THEN SUM(correct)::float / SUM(attempts)
                        ELSE NULL
                    END AS accuracy
                FROM features_topic_daily
                WHERE date >= :since_date
                  AND attempts > 0
                GROUP BY user_id, topic_id, DATE_TRUNC('week', date)::date
            ),
            user_stats AS (
                SELECT 
                    user_id,
                    AVG(accuracy) AS mean_acc,
                    STDDEV(accuracy) AS sd_acc
                FROM weekly_agg
                WHERE accuracy IS NOT NULL
                GROUP BY user_id
                HAVING COUNT(*) >= :min_obs
            )
            SELECT 
                w.user_id,
                w.topic_id,
                w.week_start,
                w.accuracy,
                u.mean_acc,
                u.sd_acc,
                CASE 
                    WHEN u.sd_acc > 0 
                    THEN (w.accuracy - u.mean_acc) / u.sd_acc
                    ELSE 0
                END AS score_z
            FROM weekly_agg w
            INNER JOIN user_stats u ON w.user_id = u.user_id
            WHERE w.accuracy IS NOT NULL
            ORDER BY w.user_id, w.week_start
            """
        )

        rows = (
            s.execute(stmt, {"since_date": since_date, "min_obs": min_observations})
            .mappings()
            .all()
        )

        if not rows:
            print("[WARN] No data found for GLMM fitting")
            return

        print(f"[INFO] Loaded {len(rows)} weekly observations")

        # Convert to week index (0, 1, 2, ...)
        week_starts = sorted(set(r["week_start"] for r in rows))
        week_index_map = {ws: idx for idx, ws in enumerate(week_starts)}

        # Prepare data for R GLMM service
        data_rows = []
        for r in rows:
            data_rows.append(
                {
                    "student_id": str(r["user_id"]),
                    "topic_id": str(r["topic_id"]),
                    "week": week_index_map[r["week_start"]],
                    "score": float(r["score_z"]),
                }
            )

        print(f"[INFO] Prepared {len(data_rows)} rows for GLMM fitting")

    # Call R GLMM service
    headers = {"Content-Type": "application/json"}
    if r_glmm_token:
        headers["X-Internal-Token"] = r_glmm_token

    payload = {
        "data": data_rows,
        "formula": "score ~ week + (week|student_id) + (1|topic_id)",
        "family": "gaussian",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_secs) as client:
            response = await client.post(
                f"{r_glmm_url}/glmm/fit_progress",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as e:
        print(f"[ERROR] R GLMM service call failed: {e}")
        return
    except Exception as e:
        print(f"[ERROR] Unexpected error calling R GLMM service: {e}")
        return

    # Extract results
    fixed_effects = result.get("fixed_effects") or {}
    random_effects = result.get("random_effects") or {}
    fit_metrics = result.get("fit_metrics") or {}

    print(f"[INFO] Fixed effects: {fixed_effects}")
    print(f"[INFO] Random effects summary: {list(random_effects.keys())}")
    print(f"[INFO] Fit metrics: {fit_metrics}")

    # Store results in growth_glmm_meta
    with get_session() as s:
        stmt_meta = sa.text(
            """
            INSERT INTO growth_glmm_meta (
                run_id, 
                formula, 
                fixed_effects, 
                random_effects_summary,
                fit_metrics, 
                fitted_at
            )
            VALUES (
                :run_id,
                :formula,
                CAST(:fixed_effects::text AS jsonb),
                CAST(:random_effects_summary::text AS jsonb),
                CAST(:fit_metrics::text AS jsonb),
                NOW()
            )
            ON CONFLICT (run_id) DO UPDATE SET
                fixed_effects = EXCLUDED.fixed_effects,
                random_effects_summary = EXCLUDED.random_effects_summary,
                fit_metrics = EXCLUDED.fit_metrics,
                fitted_at = NOW()
            """
        )

        run_id = f"glmm-{datetime.utcnow().isoformat()}"

        s.execute(
            stmt_meta,
            {
                "run_id": run_id,
                "formula": payload["formula"],
                "fixed_effects": json.dumps(fixed_effects),
                "random_effects_summary": json.dumps(
                    {
                        "student_slopes": len(
                            random_effects.get("student_id", {}).get("week", [])
                        ),
                        "topic_intercepts": len(
                            random_effects.get("topic_id", {}).get("(Intercept)", [])
                        ),
                    }
                ),
                "fit_metrics": json.dumps(fit_metrics),
            },
        )

        # Optionally update weekly_kpi with individual slopes
        update_kpi = os.getenv("GLMM_UPDATE_KPI", "false").lower() == "true"
        if update_kpi and random_effects.get("student_id"):
            student_slopes = random_effects["student_id"].get("week", {})
            print(
                f"[INFO] Updating weekly_kpi with {len(student_slopes)} student slopes"
            )

            stmt_kpi = sa.text(
                """
                UPDATE weekly_kpi
                SET kpis = jsonb_set(
                    COALESCE(kpis, '{}'::jsonb),
                    '{growth_slope}',
                    to_jsonb(:slope::float),
                    true
                )
                WHERE user_id = :user_id
                  AND week_start = (
                    SELECT MAX(week_start) FROM weekly_kpi WHERE user_id = :user_id
                  )
                """
            )

            for student_id, slope in student_slopes.items():
                try:
                    s.execute(
                        stmt_kpi,
                        {"user_id": student_id, "slope": float(slope)},
                    )
                except Exception as e:
                    print(f"[WARN] Failed to update KPI for {student_id}: {e}")

        s.commit()

    print(f"[INFO] GLMM growth model fitting completed: run_id={run_id}")


async def main() -> None:
    await fit_growth_model()


if __name__ == "__main__":
    asyncio.run(main())
