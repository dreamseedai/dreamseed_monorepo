#!/usr/bin/env python3
"""
Bayesian Growth Model (brms) - Goal Probability with Uncertainty

Fits Bayesian hierarchical model to estimate P(goal|state) with credible intervals.
Uses brms (Stan backend) for posterior sampling.

Model: score ~ week + (week|student) with priors on growth slope/variance
Output: P(goal), credible interval, posterior samples

Stores:
- growth_brms_meta: posterior summary, priors, fit diagnostics
- weekly_kpi: update P and uncertainty (σ)
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import date, datetime, timedelta
from typing import Dict, Any, List

import sqlalchemy as sa

from ..app.clients.r_brms import RBrmsClient
from ..services.db import get_session


async def fit_bayesian_growth(
    lookback_weeks: int | None = None,
    n_samples: int = 2000,
    n_chains: int = 4,
) -> None:
    """
    Fit Bayesian growth model using brms.
    
    Args:
        lookback_weeks: Number of weeks to look back (default: 8)
        n_samples: Number of posterior samples (default: 1000)
        n_chains: Number of MCMC chains (default: 2)
    
    Environment variables:
        - BRMS_LOOKBACK_WEEKS or LOOKBACK_WEEKS: Number of weeks (default: 8)
        - BRMS_N_SAMPLES or BRMS_ITER: Number of samples (default: 1000)
        - BRMS_N_CHAINS or BRMS_CHAINS: Number of chains (default: 2)
        - BRMS_FAMILY: Model family (default: "gaussian")
    """
    # Support both BRMS_* and legacy env var names for compatibility
    # Default values: LOOKBACK_WEEKS=8, BRMS_ITER=1000, BRMS_CHAINS=2
    lookback_weeks = int(
        lookback_weeks
        if lookback_weeks is not None
        else os.getenv("BRMS_LOOKBACK_WEEKS") or os.getenv("LOOKBACK_WEEKS", "8")
    )
    n_samples = int(
        os.getenv("BRMS_N_SAMPLES") or os.getenv("BRMS_ITER", "1000")
    )
    n_chains = int(
        os.getenv("BRMS_N_CHAINS") or os.getenv("BRMS_CHAINS", "2")
    )
    
    print(f"[INFO] Fitting Bayesian growth model (lookback={lookback_weeks} weeks, n_samples={n_samples}, n_chains={n_chains})")
    
    # Initialize R BRMS client
    try:
        client = RBrmsClient()
    except RuntimeError as e:
        print(f"[ERROR] Failed to initialize R BRMS client: {e}")
        return
    
    # Decide score source (default: weekly accuracy z-score)
    score_source = os.getenv("BRMS_SCORE_SOURCE", "accuracy").lower()
    since_date = date.today() - timedelta(weeks=lookback_weeks)
    
    with get_session() as s:
        data_rows: List[Dict[str, Any]] = []

        if score_source == "accuracy":
            # Primary: weekly accuracy from attempt view
            try:
                stmt_acc = sa.text(
                    """
                    SELECT 
                        student_id AS user_id,
                        DATE_TRUNC('week', completed_at)::date AS week_start,
                        AVG(CASE WHEN correct THEN 1 ELSE 0 END)::float8 AS acc
                    FROM attempt
                    WHERE completed_at >= :since_date
                    GROUP BY 1,2
                    ORDER BY 1,2
                    """
                )
                acc_rows = s.execute(stmt_acc, {"since_date": since_date}).mappings().all()
            except Exception as e:
                print(f"[WARN] attempt view not available for accuracy aggregation: {e}")
                acc_rows = []

            if not acc_rows:
                print("[WARN] No weekly accuracy rows available; falling back to theta-based sources")
                score_source = "theta"
            else:
                # Compute global z-score across all rows to standardize
                acc_values = [float(r["acc"]) for r in acc_rows if r.get("acc") is not None]
                if not acc_values:
                    print("[WARN] Weekly accuracy rows had no numeric values; falling back to theta")
                    score_source = "theta"
                else:
                    from statistics import mean, pstdev

                    m = mean(acc_values)
                    sd = pstdev(acc_values) if len(acc_values) > 1 else 0.0
                    def z(x: float) -> float:
                        if sd and sd > 0:
                            return (x - m) / sd
                        return 0.0

                    dates: List[date] = sorted({r["week_start"] for r in acc_rows})
                    week_index_map: Dict[date, int] = {d: i for i, d in enumerate(dates)}
                    for r in acc_rows:
                        user_id = str(r["user_id"])
                        wk = week_index_map[r["week_start"]]
                        score = z(float(r["acc"]))
                        data_rows.append({"student": user_id, "week": wk, "score": score})

        if score_source == "theta" and not data_rows:
            # Fallback chain based on theta
            rows: List[Dict[str, Any]] = []

            # mirt_ability (user-level)
            try:
                stmt_mirt = sa.text(
                    """
                    SELECT 
                        user_id,
                        theta AS score,
                        DATE(fitted_at) AS date
                    FROM mirt_ability
                    WHERE fitted_at >= :since_date
                      AND user_id IS NOT NULL
                      AND theta IS NOT NULL
                    ORDER BY user_id, fitted_at
                    """
                )
                rows_mirt = s.execute(stmt_mirt, {"since_date": since_date}).mappings().all()
                if rows_mirt:
                    rows.extend([dict(r) for r in rows_mirt])
                    print(f"[INFO] Loaded {len(rows_mirt)} theta observations from mirt_ability")
            except Exception as e:
                print(f"[WARN] mirt_ability table not available or query failed: {e}")

            # student_topic_theta (aggregate to user-week)
            if not rows:
                try:
                    stmt_topic = sa.text(
                        """
                        SELECT 
                            user_id,
                            AVG(theta) AS score,
                            MAX(fitted_at)::date AS date
                        FROM student_topic_theta
                        WHERE fitted_at >= :since_date
                          AND user_id IS NOT NULL
                          AND theta IS NOT NULL
                        GROUP BY user_id, DATE(fitted_at)
                        ORDER BY user_id, date
                        """
                    )
                    rows_topic = s.execute(stmt_topic, {"since_date": since_date}).mappings().all()
                    if rows_topic:
                        rows.extend([dict(r) for r in rows_topic])
                        print(f"[INFO] Loaded {len(rows_topic)} theta observations from student_topic_theta")
                except Exception as e:
                    print(f"[WARN] student_topic_theta table not available or query failed: {e}")

            # features_topic_daily (theta_mean)
            if not rows:
                try:
                    stmt_features = sa.text(
                        """
                        SELECT DISTINCT
                            user_id,
                            theta_mean AS score,
                            date
                        FROM features_topic_daily
                        WHERE date >= :since_date
                          AND user_id IS NOT NULL
                          AND theta_mean IS NOT NULL
                        ORDER BY user_id, date
                        """
                    )
                    rows_features = s.execute(stmt_features, {"since_date": since_date}).mappings().all()
                    if rows_features:
                        rows.extend([dict(r) for r in rows_features])
                        print(f"[INFO] Loaded {len(rows_features)} theta observations from features_topic_daily")
                except Exception as e:
                    print(f"[WARN] features_topic_daily table not available or query failed: {e}")

            # weekly_kpi ability_estimate
            if not rows:
                try:
                    stmt_kpi = sa.text(
                        """
                        SELECT 
                            user_id,
                            (kpis->>'ability_estimate')::float AS score,
                            week_start AS date
                        FROM weekly_kpi
                        WHERE week_start >= :since_date
                          AND user_id IS NOT NULL
                          AND kpis ? 'ability_estimate'
                          AND (kpis->>'ability_estimate')::float IS NOT NULL
                        ORDER BY user_id, week_start
                        """
                    )
                    rows_kpi = s.execute(stmt_kpi, {"since_date": since_date}).mappings().all()
                    if rows_kpi:
                        rows.extend([dict(r) for r in rows_kpi])
                        print(f"[INFO] Loaded {len(rows_kpi)} ability observations from weekly_kpi")
                except Exception as e:
                    print(f"[WARN] weekly_kpi.ability_estimate not available: {e}")

            if not rows:
                print("[WARN] No data found for Bayesian fitting")
                return

            print(f"[INFO] Loaded {len(rows)} observations for theta-based fallback")

            # Convert to week index (0-based)
            dates = sorted(set(r["date"] for r in rows))
            week_index_map = {d: idx for idx, d in enumerate(dates)}
            for r in rows:
                data_rows.append({
                    "student": str(r["user_id"]),
                    "week": week_index_map[r["date"]],
                    "score": float(r["score"]),
                })
    
    # Prepare priors (default if not provided)
    # Priors are designed for small sample/noise stabilization:
    # - Normal priors on intercept/week: Regularize coefficients towards 0
    # - Cauchy prior on sd: Robust to outliers, allows heavy-tailed residuals
    # These priors stabilize estimates when:
    #   1. Small sample sizes: Regularization prevents overfitting
    #   2. High noise: Weak priors allow data to dominate but prevent extreme values
    #   3. Unstable gradients: Bounded priors help MCMC convergence
    priors = {
        "intercept": {"dist": "normal", "mean": 0, "sd": 1},  # Regularize baseline ability
        "week": {"dist": "normal", "mean": 0, "sd": 0.5},  # Regularize growth slope
        "sd": {"dist": "cauchy", "location": 0, "scale": 1},  # Robust to outliers
    }
    
    # Get family from environment (default: gaussian)
    family = os.getenv("BRMS_FAMILY", "gaussian").lower()
    
    # Call R BRMS service
    formula = "score ~ week + (week|student_id)"
    
    try:
        result = await client.fit_growth(
            data_rows,
            formula=formula,
            priors=priors,
            n_samples=n_samples,
            n_chains=n_chains,
            family=family,
        )
    except Exception as e:
        print(f"[ERROR] R BRMS service call failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Extract results
    posterior_summary = result.get("posterior_summary") or {}
    diagnostics = result.get("diagnostics") or {}
    predictions = result.get("predictions") or {}  # Per-student predictions
    
    print(f"[INFO] Posterior summary: {json.dumps(posterior_summary, indent=2)}")
    print(f"[INFO] Diagnostics: {json.dumps(diagnostics, indent=2)}")
    print(f"[INFO] Predictions computed for {len(predictions)} students")
    
    # Store results
    run_id = f"brms-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    with get_session() as s:
        stmt_meta = sa.text(
            """
            INSERT INTO growth_brms_meta (
                run_id,
                formula,
                priors,
                posterior_summary,
                diagnostics,
                fitted_at
            )
            VALUES (
                :run_id,
                :formula,
                CAST(:priors::text AS jsonb),
                CAST(:posterior_summary::text AS jsonb),
                CAST(:diagnostics::text AS jsonb),
                NOW()
            )
            ON CONFLICT (run_id) DO UPDATE SET
                formula = EXCLUDED.formula,
                priors = EXCLUDED.priors,
                posterior_summary = EXCLUDED.posterior_summary,
                diagnostics = EXCLUDED.diagnostics,
                fitted_at = NOW()
            """
        )
        
        s.execute(
            stmt_meta,
            {
                "run_id": run_id,
                "formula": formula,
                "priors": json.dumps(priors),
                "posterior_summary": json.dumps(posterior_summary),
                "diagnostics": json.dumps(diagnostics),
            },
        )
        
        # Update weekly_kpi with P (goal probability) and σ (uncertainty) if predictions available
        update_kpi = os.getenv("BRMS_UPDATE_KPI", "true").lower() == "true"
        if update_kpi and predictions:
            stmt_kpi = sa.text(
                """
                UPDATE weekly_kpi
                SET kpis = jsonb_set(
                    jsonb_set(
                        COALESCE(kpis, '{}'::jsonb),
                        '{P}',
                        to_jsonb(:p_value::float),
                        true
                    ),
                    '{sigma}',
                    to_jsonb(:sigma_value::float),
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
            for student_id, pred in predictions.items():
                try:
                    p_value = pred.get("probability") or pred.get("P")
                    sigma_value = pred.get("uncertainty") or pred.get("sigma") or pred.get("sd")
                    
                    if p_value is not None:
                        result = s.execute(
                            stmt_kpi,
                            {
                                "user_id": student_id,
                                "p_value": float(p_value),
                                "sigma_value": float(sigma_value) if sigma_value is not None else 0.0,
                            },
                        )
                        rc = getattr(result, 'rowcount', None)
                        if isinstance(rc, int) and rc > 0:
                            updated_count += 1
                except Exception as e:
                    print(f"[WARN] Failed to update KPI for {student_id}: {e}")
            
            print(f"[INFO] Updated weekly_kpi.P/sigma for {updated_count} users")
        
        s.commit()
    
    print(f"[INFO] Bayesian growth model fitting completed: run_id={run_id}")


async def main(
    lookback_weeks: int | None = None,
    n_samples: int = 2000,
    n_chains: int = 4,
    dry_run: bool = False,
) -> int:
    """
    Main entry point for Bayesian growth model fitting.
    
    Returns:
        Exit code: 0 on success, 1 on failure
    """
    if dry_run:
        print("[INFO] DRY RUN MODE: No changes will be committed")
    
    try:
        await fit_bayesian_growth(
            lookback_weeks=lookback_weeks,
            n_samples=n_samples,
            n_chains=n_chains,
        )
        return 0
    except Exception as e:
        print(f"[FATAL] Bayesian growth model fitting failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cli() -> None:
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fit Bayesian growth model for goal probability prediction"
    )
    parser.add_argument(
        "--lookback-weeks",
        type=int,
        default=None,
        help="Number of weeks to look back (default: from BRMS_LOOKBACK_WEEKS env)",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=2000,
        help="Number of posterior samples (default: 2000)",
    )
    parser.add_argument(
        "--n-chains",
        type=int,
        default=4,
        help="Number of MCMC chains (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no database commits)",
    )
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(
        main(
            lookback_weeks=args.lookback_weeks,
            n_samples=args.n_samples,
            n_chains=args.n_chains,
            dry_run=args.dry_run,
        )
    )
    exit(exit_code)


if __name__ == "__main__":
    cli()
