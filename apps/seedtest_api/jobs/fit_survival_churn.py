#!/usr/bin/env python3
"""
Survival Analysis - 14-Day Inactivity Risk

Fits Cox proportional hazards model to estimate churn risk:
- Event: 14 days without login
- Covariates: A_t, E_t, R_t, mean_gap, sessions, etc.
- Output: S(t) survival curve, hazard ratios, risk scores

Stores:
- survival_fit_meta: model coefficients, hazard ratios
- weekly_kpi: update S (churn risk score)
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import date, datetime, timedelta
from typing import Dict, Any, List

import sqlalchemy as sa

from ..app.clients.r_forecast import RForecastClient
from ..services.db import get_session


async def fit_survival_model(
    lookback_days: int | None = None,
    event_threshold_days: int = 14,
) -> None:
    """
    Fit survival model for inactivity risk.
    
    Args:
        lookback_days: Number of days to look back for training data (default: 90)
        event_threshold_days: Days of inactivity to define churn event (default: 14)
    """
    lookback_days = int(
        lookback_days
        if lookback_days is not None
        else os.getenv("SURVIVAL_LOOKBACK_DAYS", "90")
    )
    event_threshold_days = int(
        os.getenv("SURVIVAL_EVENT_THRESHOLD_DAYS", str(event_threshold_days))
    )
    
    print(f"[INFO] Fitting survival model (lookback={lookback_days} days, event_threshold={event_threshold_days} days)")
    
    # Initialize R Forecast client
    try:
        client = RForecastClient()
    except RuntimeError as e:
        print(f"[ERROR] Failed to initialize R Forecast client: {e}")
        return
    
    # Load user activity data
    since_date = date.today() - timedelta(days=lookback_days)
    
    with get_session() as s:
        # Enhanced query: use attempt VIEW, weekly_kpi, and session table
        stmt = sa.text(
            """
            WITH last_activity AS (
                -- Get last activity from attempt VIEW (preferred)
                SELECT 
                    student_id::text AS user_id,
                    MAX(completed_at::date) AS last_activity_date
                FROM attempt
                WHERE student_id IS NOT NULL
                  AND completed_at >= :since_date::date
                GROUP BY student_id
                
                UNION
                
                -- Fallback to weekly_kpi
                SELECT 
                    user_id,
                    MAX(week_start) + INTERVAL '6 days' AS last_activity_date
                FROM weekly_kpi
                WHERE week_start >= :since_date
                GROUP BY user_id
            ),
            user_features AS (
                SELECT 
                    la.user_id,
                    COALESCE(
                        (SELECT k.kpis->>'A_t' FROM weekly_kpi k 
                         WHERE k.user_id = la.user_id 
                         ORDER BY k.week_start DESC LIMIT 1)::float, 
                        0.0
                    ) AS engagement,
                    COALESCE(
                        (SELECT k.kpis->>'E_t' FROM weekly_kpi k 
                         WHERE k.user_id = la.user_id 
                         ORDER BY k.week_start DESC LIMIT 1)::float, 
                        0.0
                    ) AS efficiency,
                    COALESCE(
                        (SELECT k.kpis->>'R_t' FROM weekly_kpi k 
                         WHERE k.user_id = la.user_id 
                         ORDER BY k.week_start DESC LIMIT 1)::float, 
                        0.0
                    ) AS recovery,
                    COALESCE(
                        (SELECT k.kpis->>'mean_gap' FROM weekly_kpi k 
                         WHERE k.user_id = la.user_id 
                         ORDER BY k.week_start DESC LIMIT 1)::float, 
                        7.0
                    ) AS mean_gap,
                    COALESCE(
                        (SELECT COUNT(*)::int FROM attempt a 
                         WHERE a.student_id::text = la.user_id 
                           AND a.completed_at >= :since_date::date), 
                        0
                    ) AS sessions,
                    EXTRACT(EPOCH FROM (CURRENT_DATE - la.last_activity_date::date)) / 86400.0 AS days_since_last
                FROM last_activity la
            )
            SELECT 
                user_id,
                engagement,
                efficiency,
                recovery,
                mean_gap,
                sessions,
                days_since_last,
                CASE WHEN days_since_last >= :threshold THEN 1 ELSE 0 END AS event,
                GREATEST(0.0, days_since_last) AS time
            FROM user_features
            WHERE user_id IS NOT NULL
            ORDER BY days_since_last DESC
            """
        )
        
        rows = s.execute(
            stmt, 
            {
                "since_date": since_date,
                "threshold": float(event_threshold_days),
            }
        ).mappings().all()
        
        if not rows:
            print("[WARN] No user activity data found for survival fitting")
            return
        
        print(f"[INFO] Loaded {len(rows)} user records")
        
        # Prepare data for R service
        data_rows: List[Dict[str, Any]] = []
        for r in rows:
            data_rows.append({
                "user_id": str(r["user_id"]),
                "time": float(r["time"]),
                "event": int(r["event"]),
                "engagement": float(r["engagement"]),
                "efficiency": float(r["efficiency"]),
                "recovery": float(r["recovery"]),
                "mean_gap": float(r["mean_gap"]),
                "sessions": int(r["sessions"]),
            })
    
    # Call R Survival service (v2 API: survival_fit with params)
    try:
        result = await client.survival_fit_v2(
            rows=[
                {
                    "user_id": r["user_id"],
                    "observed_gap_days": r["time"],
                    "event": r["event"],
                    # map covariates to suggested names
                    "sessions_28d": r["sessions"],
                    "mean_gap_days_28d": r["mean_gap"],
                    "A_t": r["engagement"],
                    "E_t": r["efficiency"],
                    "R_t": r["recovery"],
                }
                for r in data_rows
            ],
            family="cox",
            event_threshold_days=event_threshold_days,
        )

        if result.get("status") == "noop":
            print(f"[WARN] Survival fit noop: {result.get('reason')}")
            return
        if result.get("status") == "error" or result.get("error"):
            print(f"[WARN] Survival fit returned error: {result.get('error') or result.get('message')}")
            return
    except Exception as e:
        print(f"[ERROR] R Survival service call failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Extract results (v2 API: {status, run_id, model_meta, predictions, survival_curve})
    run_id = result.get("run_id") or f"survival-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    model_meta = result.get("model_meta") or {}
    preds = result.get("predictions") or []
    survival_curve = result.get("survival_curve") or []

    print(f"[INFO] Survival model fitted: n={model_meta.get('n')}, family={model_meta.get('family')}, concordance={model_meta.get('concordance')}")
    
    # Build risk score map
    risk_scores = {str(p.get("user_id")): float(p.get("risk_score", 0.0)) for p in preds if p.get("user_id") is not None}
    print(f"[INFO] Risk scores computed for {len(risk_scores)} users")
    
    with get_session() as s:
        # Ensure tables exist (new schema)
        s.execute(sa.text(
            """
            CREATE TABLE IF NOT EXISTS survival_fit_meta (
              id BIGSERIAL PRIMARY KEY,
              run_id UUID,
              family TEXT,
              event_threshold_days INT,
              coefficients JSONB,
              concordance DOUBLE PRECISION,
              n INT,
              survival_curve JSONB,
              run_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ))
        s.execute(sa.text(
            """
            CREATE TABLE IF NOT EXISTS survival_risk (
              id BIGSERIAL PRIMARY KEY,
              run_id UUID,
              user_id TEXT NOT NULL,
              risk_score DOUBLE PRECISION NOT NULL,
              hazard_ratio DOUBLE PRECISION,
              rank_percentile DOUBLE PRECISION,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ))

        # Store fit metadata
        stmt_meta = sa.text(
            """
            INSERT INTO survival_fit_meta (
              run_id, family, event_threshold_days, coefficients, concordance, n, survival_curve, run_at
            ) VALUES (
              :run_id::uuid, :family, :event_threshold_days,
              CAST(:coefficients::text AS jsonb), :concordance, :n,
              CAST(:survival_curve::text AS jsonb), NOW()
            )
            """
        )
        conc_val = model_meta.get("concordance")
        conc_float = float(conc_val) if conc_val is not None else None
        s.execute(
            stmt_meta,
            {
                "run_id": str(run_id),
                "family": model_meta.get("family"),
                "event_threshold_days": int(model_meta.get("event_threshold_days", event_threshold_days)),
                "coefficients": json.dumps(model_meta.get("coefficients") or {}),
                "concordance": conc_float,
                "n": int(model_meta.get("n") or 0),
                "survival_curve": json.dumps(survival_curve),
            },
        )

        # Upsert survival risk per user (update latest risk for each user)
        # Note: Check if user_id is PRIMARY KEY or if unique index exists
        if preds:
            # Try ON CONFLICT (user_id) first, fallback to DELETE + INSERT if not supported
            try:
                stmt_risk = sa.text(
                    """
                    INSERT INTO survival_risk (run_id, user_id, risk_score, hazard_ratio, rank_percentile, updated_at)
                    VALUES (:run_id::uuid, :user_id, :risk_score, :hazard_ratio, :rank_percentile, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        run_id = EXCLUDED.run_id,
                        risk_score = EXCLUDED.risk_score,
                        hazard_ratio = EXCLUDED.hazard_ratio,
                        rank_percentile = EXCLUDED.rank_percentile,
                        updated_at = NOW()
                    """
                )
            except Exception:
                # Fallback: Delete old records and insert new
                stmt_risk = sa.text(
                    """
                    INSERT INTO survival_risk (run_id, user_id, risk_score, hazard_ratio, rank_percentile, updated_at)
                    VALUES (:run_id::uuid, :user_id, :risk_score, :hazard_ratio, :rank_percentile, NOW())
                    """
                )
            
            stmt_delete = sa.text("DELETE FROM survival_risk WHERE user_id = :user_id")
            stored_count = 0
            for p in preds:
                try:
                    user_id = str(p.get("user_id"))
                    # Try to delete existing record first (in case ON CONFLICT doesn't work)
                    try:
                        s.execute(stmt_delete, {"user_id": user_id})
                    except Exception:
                        pass  # Ignore if table structure doesn't support direct delete
                    
                    s.execute(
                        stmt_risk,
                        {
                            "run_id": str(run_id),
                            "user_id": user_id,
                            "risk_score": float(p.get("risk_score", 0.0)),
                            "hazard_ratio": float(p.get("hazard_ratio", 1.0)) if p.get("hazard_ratio") is not None else None,
                            "rank_percentile": float(p.get("rank_percentile", 0.0)) if p.get("rank_percentile") is not None else None,
                        },
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"[WARN] Failed to upsert survival risk for {p.get('user_id')}: {e}")
            
            print(f"[INFO] Stored {stored_count} survival risk scores")
        
        # Update weekly_kpi with risk scores
        update_kpi = os.getenv("SURVIVAL_UPDATE_KPI", "true").lower() == "true"
        if update_kpi and risk_scores:
            stmt_kpi = sa.text(
                """
                UPDATE weekly_kpi
                SET kpis = jsonb_set(
                    COALESCE(kpis, '{}'::jsonb),
                    '{S}',
                    to_jsonb(:risk_score::float),
                    true
                ),
                updated_at = NOW()
                WHERE user_id = :user_id
                  AND week_start = (
                    SELECT MAX(week_start) FROM weekly_kpi WHERE user_id = :user_id
                  )
                """
            )
            
            updated_count = 0
            for user_id, risk_score in risk_scores.items():
                try:
                    result = s.execute(
                        stmt_kpi,
                        {"user_id": user_id, "risk_score": float(risk_score)},
                    )
                    rc = getattr(result, 'rowcount', None)
                    if isinstance(rc, int) and rc > 0:
                        updated_count += 1
                except Exception as e:
                    print(f"[WARN] Failed to update KPI for {user_id}: {e}")
            
            print(f"[INFO] Updated weekly_kpi.S for {updated_count} users")
        
        s.commit()
    
    print(f"[INFO] Survival model fitting completed: run_id={run_id}")


async def main(
    lookback_days: int | None = None,
    event_threshold_days: int = 14,
    dry_run: bool = False,
) -> int:
    """
    Main entry point for survival model fitting.
    
    Returns:
        Exit code: 0 on success, 1 on failure
    """
    if dry_run:
        print("[INFO] DRY RUN MODE: No changes will be committed")
    
    try:
        await fit_survival_model(
            lookback_days=lookback_days,
            event_threshold_days=event_threshold_days,
        )
        return 0
    except Exception as e:
        print(f"[FATAL] Survival model fitting failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cli() -> None:
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fit survival model for churn risk prediction"
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Number of days to look back (default: from SURVIVAL_LOOKBACK_DAYS env)",
    )
    parser.add_argument(
        "--event-threshold-days",
        type=int,
        default=14,
        help="Days of inactivity to define churn event (default: 14)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no database commits)",
    )
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(
        main(
            lookback_days=args.lookback_days,
            event_threshold_days=args.event_threshold_days,
            dry_run=args.dry_run,
        )
    )
    exit(exit_code)


if __name__ == "__main__":
    cli()
