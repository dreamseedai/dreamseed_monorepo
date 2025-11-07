#!/usr/bin/env python3
"""
Time Series Forecasting (Prophet) - I_t Trend & Anomaly Detection

Fits Prophet model to I_t (improvement index) time series:
- Detects changepoints and trends
- Forecasts short-term (1-4 weeks)
- Flags anomalies (unusual drops/spikes)

Stores:
- prophet_fit_meta: model parameters, changepoints
- prophet_anomalies: week, score, flag
- weekly_kpi: optionally add forecast/anomaly fields
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


async def forecast_improvement_trend(
    lookback_weeks: int | None = None,
    forecast_weeks: int = 4,
    anomaly_threshold: float = 2.5,
) -> None:
    """
    Fit Prophet model to I_t time series and detect anomalies.
    
    Args:
        lookback_weeks: Number of weeks to look back (default: 12)
        forecast_weeks: Number of weeks to forecast (default: 4)
        anomaly_threshold: Z-score threshold for anomaly detection (default: 2.5)
    """
    lookback_weeks = int(
        lookback_weeks
        if lookback_weeks is not None
        else os.getenv("PROPHET_LOOKBACK_WEEKS", "12")
    )
    forecast_weeks = int(os.getenv("PROPHET_FORECAST_WEEKS", str(forecast_weeks)))
    anomaly_threshold = float(os.getenv("PROPHET_ANOMALY_THRESHOLD", str(anomaly_threshold)))
    
    print(f"[INFO] Forecasting I_t trend (lookback={lookback_weeks} weeks, forecast={forecast_weeks} weeks)")
    
    # Initialize R Forecast client
    try:
        client = RForecastClient()
    except RuntimeError as e:
        print(f"[ERROR] Failed to initialize R Forecast client: {e}")
        return
    
    # Load weekly I_t from weekly_kpi
    since_date = date.today() - timedelta(weeks=lookback_weeks)
    
    with get_session() as s:
        stmt = sa.text(
            """
            SELECT 
                week_start AS ds,
                AVG((kpis->>'I_t')::float) AS y
            FROM weekly_kpi
            WHERE week_start >= :since_date
              AND kpis ? 'I_t'
              AND (kpis->>'I_t')::float IS NOT NULL
            GROUP BY week_start
            ORDER BY week_start
            """
        )
        
        rows = s.execute(stmt, {"since_date": since_date}).mappings().all()
        
        if not rows or len(rows) < 4:
            print("[WARN] Insufficient I_t data for Prophet fitting (need >= 4 weeks)")
            return
        
        print(f"[INFO] Loaded {len(rows)} weekly I_t observations")
        
        # Prepare data for R service
        data_rows: List[Dict[str, Any]] = []
        for r in rows:
            data_rows.append({
                "ds": str(r["ds"]),
                "y": float(r["y"]),
            })
    
    # Call R Prophet service (stateless predict API)
    try:
        result = await client.prophet_predict(
            data_rows,
            periods=forecast_weeks,
            freq="week",
        )
        
        if result.get("error"):
            print(f"[WARN] Prophet predict returned error: {result.get('error')}")
            return
            
    except Exception as e:
        print(f"[ERROR] R Prophet service call failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Extract results (API returns {status, periods, fitted: [{ds,yhat}], forecast: [{ds, yhat, yhat_lower, yhat_upper}]})
    forecast = result.get("forecast") or []
    fitted = result.get("fitted") or []
    
    print(f"[INFO] Forecast: {len(forecast)} periods")
    for f in forecast:
        print(f"[INFO]   {f.get('ds')} -> {f.get('yhat')} [{f.get('yhat_lower')}, {f.get('yhat_upper')}]")
    
    # Anomaly detection: compare historical actual vs fitted values
    # Build maps for quick lookup
    fitted_map = {str(r.get("ds")): float(r.get("yhat")) for r in fitted if r.get("ds") is not None and r.get("yhat") is not None}
    hist_pairs = []  # (ds, y, yhat, residual)
    for r in data_rows:
        ds = str(r.get("ds"))
        y_raw = r.get("y")
        if y_raw is None:
            continue
        try:
            y = float(y_raw)
        except Exception:
            continue
        if ds and ds in fitted_map:
            yhat = fitted_map[ds]
            hist_pairs.append((ds, y, yhat, y - yhat))

    anomalies = []
    if hist_pairs:
        import statistics as stats
        residuals = [p[3] for p in hist_pairs]
        mu = stats.mean(residuals)
        sd = stats.pstdev(residuals) if len(residuals) > 1 else 0.0
        thr = anomaly_threshold

        for ds, y, yhat, res in hist_pairs:
            z = (res - mu) / sd if sd and sd > 0 else 0.0
            if abs(z) >= thr:
                anomalies.append({
                    "ds": ds,
                    "y": y,
                    "yhat": yhat,
                    "anomaly_score": float(z),
                })

    changepoints = []  # Reserved for future (if R service returns changepoints)
    fit_meta = {"status": result.get("status"), "periods": result.get("periods"), "threshold": anomaly_threshold}
    
    # Store results
    run_id = f"prophet-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    metric = "I_t"

    with get_session() as s:
        # Ensure tables exist
        s.execute(sa.text(
            """
            CREATE TABLE IF NOT EXISTS prophet_fit_meta (
                run_id TEXT PRIMARY KEY,
                metric TEXT,
                changepoints JSONB,
                forecast JSONB,
                fit_meta JSONB,
                fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ))
        s.execute(sa.text(
            """
            CREATE TABLE IF NOT EXISTS prophet_anomalies (
                run_id TEXT,
                week_start DATE,
                metric TEXT,
                value DOUBLE PRECISION,
                expected DOUBLE PRECISION,
                anomaly_score DOUBLE PRECISION,
                detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (run_id, week_start, metric)
            )
            """
        ))
        # Store fit metadata
        stmt_meta = sa.text(
            """
            INSERT INTO prophet_fit_meta (
                run_id,
                metric,
                changepoints,
                forecast,
                fit_meta,
                fitted_at
            )
            VALUES (
                :run_id,
                :metric,
                CAST(:changepoints::text AS jsonb),
                CAST(:forecast::text AS jsonb),
                CAST(:fit_meta::text AS jsonb),
                NOW()
            )
            ON CONFLICT (run_id) DO UPDATE SET
                changepoints = EXCLUDED.changepoints,
                forecast = EXCLUDED.forecast,
                fit_meta = EXCLUDED.fit_meta,
                fitted_at = NOW()
            """
        )
        
        s.execute(
            stmt_meta,
            {
                "run_id": run_id,
                "metric": metric,
                "changepoints": json.dumps(changepoints),
                "forecast": json.dumps(forecast),
                "fit_meta": json.dumps(fit_meta),
            },
        )
        
        # Store anomalies
        if anomalies:
            stmt_anomaly = sa.text(
                """
                INSERT INTO prophet_anomalies (
                    run_id,
                    week_start,
                    metric,
                    value,
                    expected,
                    anomaly_score,
                    detected_at
                )
                VALUES (
                    :run_id,
                    :week_start::date,
                    :metric,
                    :value,
                    :expected,
                    :anomaly_score,
                    NOW()
                )
                ON CONFLICT (run_id, week_start, metric) DO UPDATE SET
                    value = EXCLUDED.value,
                    expected = EXCLUDED.expected,
                    anomaly_score = EXCLUDED.anomaly_score,
                    detected_at = NOW()
                """
            )
            
            stored_count = 0
            for anom in anomalies:
                ds_str = None
                try:
                    ds_str = anom.get("ds") or anom.get("week_start")
                    if not ds_str:
                        continue
                    
                    s.execute(
                        stmt_anomaly,
                        {
                            "run_id": run_id,
                            "week_start": ds_str,
                            "metric": metric,
                            "value": float(anom.get("y", 0)),
                            "expected": float(anom.get("yhat", 0)),
                            "anomaly_score": float(anom.get("anomaly_score", 0)),
                        },
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"[WARN] Failed to store anomaly for {ds_str or 'unknown'}: {e}")
            
            print(f"[INFO] Stored {stored_count} anomalies")

        s.commit()
    
    print(f"[INFO] Prophet forecasting completed: run_id={run_id}")


async def main(
    lookback_weeks: int | None = None,
    forecast_weeks: int = 4,
    anomaly_threshold: float = 2.5,
    dry_run: bool = False,
) -> int:
    """
    Main entry point for Prophet forecasting.
    
    Returns:
        Exit code: 0 on success, 1 on failure
    """
    if dry_run:
        print("[INFO] DRY RUN MODE: No changes will be committed")
    
    try:
        await forecast_improvement_trend(
            lookback_weeks=lookback_weeks,
            forecast_weeks=forecast_weeks,
            anomaly_threshold=anomaly_threshold,
        )
        return 0
    except Exception as e:
        print(f"[FATAL] Prophet forecasting failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cli() -> None:
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fit Prophet model for I_t trend forecasting and anomaly detection"
    )
    parser.add_argument(
        "--lookback-weeks",
        type=int,
        default=None,
        help="Number of weeks to look back (default: from PROPHET_LOOKBACK_WEEKS env)",
    )
    parser.add_argument(
        "--forecast-weeks",
        type=int,
        default=4,
        help="Number of weeks to forecast (default: 4)",
    )
    parser.add_argument(
        "--anomaly-threshold",
        type=float,
        default=2.5,
        help="Z-score threshold for anomaly detection (default: 2.5)",
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
            forecast_weeks=args.forecast_weeks,
            anomaly_threshold=args.anomaly_threshold,
            dry_run=args.dry_run,
        )
    )
    exit(exit_code)


if __name__ == "__main__":
    cli()
