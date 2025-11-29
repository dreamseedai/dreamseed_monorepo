"""IRT Drift Monitor (V1 Frequentist).

Monitors IRT parameter drift using frequentist estimation (mirt/ltm).
Compares recent window vs baseline window, generates alerts on threshold violations.

Usage:
    python -m apps.seedtest_api.jobs.irt_drift_monitor --recent-days 30

Environment:
    DATABASE_URL: PostgreSQL connection string
    DRIFT_LOOKBACK_DAYS: Recent window size (default: 30)
    DRIFT_BASELINE_FROM: Baseline window start (optional, ISO format)
    DRIFT_BASELINE_TO: Baseline window end (optional, ISO format)
    DRIFT_MIN_SAMPLE: Minimum responses per item (default: 200)
    DRIFT_THRESHOLD_DELTA_B: Δb threshold (default: 0.25)
    DRIFT_THRESHOLD_DELTA_A: Δa threshold (default: 0.20)
    DRIFT_THRESHOLD_DELTA_C: Δc threshold (default: 0.03)
    R_IRT_PLUMBER_URL: R IRT service endpoint (default: http://r-irt-plumber:8000)
"""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

import httpx
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# Configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/seedtest")
R_IRT_PLUMBER_URL = os.getenv("R_IRT_PLUMBER_URL", "http://r-irt-plumber:8000")
DEFAULT_LOOKBACK_DAYS = int(os.getenv("DRIFT_LOOKBACK_DAYS", "30"))
DEFAULT_MIN_SAMPLE = int(os.getenv("DRIFT_MIN_SAMPLE", "200"))
DEFAULT_THRESHOLDS = {
    "delta_b": float(os.getenv("DRIFT_THRESHOLD_DELTA_B", "0.25")),
    "delta_a": float(os.getenv("DRIFT_THRESHOLD_DELTA_A", "0.20")),
    "delta_c": float(os.getenv("DRIFT_THRESHOLD_DELTA_C", "0.03")),
}


@dataclass
class DriftWindow:
    """Time window for drift analysis."""

    window_id: int
    start_at: datetime
    end_at: datetime
    population_tags: Optional[Dict[str, Any]] = None


@dataclass
class ItemCalibration:
    """Calibration results for a single item in a window."""

    item_id: int
    window_id: int
    a_hat: float
    b_hat: float
    c_hat: float
    a_l95: Optional[float]
    a_u95: Optional[float]
    b_l95: Optional[float]
    b_u95: Optional[float]
    c_l95: Optional[float]
    c_u95: Optional[float]
    n: int
    dif: Optional[Dict[str, Any]] = None
    info: Optional[Dict[str, Any]] = None
    run_id: Optional[str] = None


@dataclass
class DriftAlert:
    """Drift detection alert."""

    item_id: int
    window_id: int
    metric: str
    value: float
    threshold: float
    severity: Literal["minor", "moderate", "severe"]
    run_id: Optional[str] = None


def create_drift_window(
    engine,
    start_at: datetime,
    end_at: datetime,
    population_tags: Optional[Dict[str, Any]] = None,
) -> DriftWindow:
    """Create a new drift window in database."""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO drift_windows (start_at, end_at, population_tags)
                VALUES (:start_at, :end_at, :population_tags)
                RETURNING id
                """
            ),
            {
                "start_at": start_at,
                "end_at": end_at,
                "population_tags": population_tags,
            },
        )
        window_id = result.scalar_one()
        logger.info(f"Created drift window {window_id}: {start_at} to {end_at}")
        return DriftWindow(
            window_id=window_id,
            start_at=start_at,
            end_at=end_at,
            population_tags=population_tags,
        )


def load_responses(
    engine, window: DriftWindow, min_sample: int = DEFAULT_MIN_SAMPLE
) -> pd.DataFrame:
    """Load item responses for a given window.

    Returns DataFrame with columns: item_id, user_id, correct (0/1)
    Filters to items with >= min_sample responses.
    """
    query = text(
        """
        WITH window_responses AS (
            SELECT 
                question_id::bigint AS item_id,
                student_id AS user_id,
                CASE WHEN correct THEN 1 ELSE 0 END AS correct
            FROM attempts
            WHERE created_at >= :start_at
              AND created_at < :end_at
              AND question_id IS NOT NULL
              AND student_id IS NOT NULL
        ),
        item_counts AS (
            SELECT item_id, COUNT(*) AS n
            FROM window_responses
            GROUP BY item_id
            HAVING COUNT(*) >= :min_sample
        )
        SELECT wr.item_id, wr.user_id, wr.correct
        FROM window_responses wr
        INNER JOIN item_counts ic ON wr.item_id = ic.item_id
        ORDER BY wr.item_id, wr.user_id
        """
    )

    with engine.connect() as conn:
        df = pd.read_sql(
            query,
            conn,
            params={
                "start_at": window.start_at,
                "end_at": window.end_at,
                "min_sample": min_sample,
            },
        )

    logger.info(
        f"Loaded {len(df)} responses for {df['item_id'].nunique()} items from window {window.window_id}"
    )
    return df


def call_r_irt_calibrate(
    responses_df: pd.DataFrame,
    model: str = "3PL",
) -> Dict[int, Dict[str, float]]:
    """Call R IRT plumber service to calibrate items.

    Args:
        responses_df: DataFrame with columns [item_id, user_id, correct]
        model: "2PL" or "3PL"

    Returns:
        Dict mapping item_id to {a, b, c, a_se, b_se, c_se}
    """
    # Prepare payload: wide-format matrix (rows=users, cols=items)
    response_matrix = responses_df.pivot_table(
        index="user_id",
        columns="item_id",
        values="correct",
        aggfunc="first",  # Should be unique per user-item
    )

    # Convert to list of lists for JSON
    payload = {
        "responses": response_matrix.values.tolist(),
        "item_ids": response_matrix.columns.tolist(),
        "model": model,
    }

    try:
        logger.info(f"Calling R IRT service at {R_IRT_PLUMBER_URL}/irt/calibrate")
        resp = httpx.post(
            f"{R_IRT_PLUMBER_URL}/irt/calibrate",
            json=payload,
            timeout=300.0,  # 5 minutes
        )
        resp.raise_for_status()
        result = resp.json()

        # Parse result: expected format {"item_id": {"a": ..., "b": ..., "c": ..., "a_se": ..., ...}}
        item_params = {}
        for item_data in result.get("items", []):
            item_id = int(item_data["item_id"])
            item_params[item_id] = {
                "a": item_data["a"],
                "b": item_data["b"],
                "c": item_data.get("c", 0.0),
                "a_se": item_data.get("a_se", 0.0),
                "b_se": item_data.get("b_se", 0.0),
                "c_se": item_data.get("c_se", 0.0),
            }

        logger.info(f"Calibrated {len(item_params)} items via R IRT service")
        return item_params

    except Exception as e:
        logger.error(f"R IRT calibration failed: {e}")
        raise


def compute_information_summary(a: float, b: float, c: float) -> Dict[str, float]:
    """Compute simple information function summary.

    Returns max info and theta at max for 3PL item.
    """
    from shared.irt import item_information_3pl
    import numpy as np

    theta_range = np.linspace(-3, 3, 50)
    info_values = [item_information_3pl(t, a, b, c) for t in theta_range]
    max_info = float(np.max(info_values))
    theta_at_max = float(theta_range[np.argmax(info_values)])

    return {
        "max": max_info,
        "theta_at_max": theta_at_max,
    }


def detect_drift(
    baseline_calib: ItemCalibration,
    recent_calib: ItemCalibration,
    thresholds: Dict[str, float],
) -> List[DriftAlert]:
    """Detect drift by comparing baseline and recent calibrations."""
    alerts: List[DriftAlert] = []

    delta_a = abs(recent_calib.a_hat - baseline_calib.a_hat)
    delta_b = abs(recent_calib.b_hat - baseline_calib.b_hat)
    delta_c = recent_calib.c_hat - baseline_calib.c_hat

    # Check thresholds
    if delta_a > thresholds.get("delta_a", DEFAULT_THRESHOLDS["delta_a"]):
        severity = "severe" if delta_a > 0.4 else "moderate"
        alerts.append(
            DriftAlert(
                item_id=recent_calib.item_id,
                window_id=recent_calib.window_id,
                metric="delta_a",
                value=delta_a,
                threshold=thresholds["delta_a"],
                severity=severity,
                run_id=recent_calib.run_id,
            )
        )

    if delta_b > thresholds.get("delta_b", DEFAULT_THRESHOLDS["delta_b"]):
        severity = (
            "severe" if delta_b > 0.5 else "moderate" if delta_b > 0.35 else "minor"
        )
        alerts.append(
            DriftAlert(
                item_id=recent_calib.item_id,
                window_id=recent_calib.window_id,
                metric="delta_b",
                value=delta_b,
                threshold=thresholds["delta_b"],
                severity=severity,
                run_id=recent_calib.run_id,
            )
        )

    if delta_c > thresholds.get("delta_c", DEFAULT_THRESHOLDS["delta_c"]):
        alerts.append(
            DriftAlert(
                item_id=recent_calib.item_id,
                window_id=recent_calib.window_id,
                metric="delta_c",
                value=delta_c,
                threshold=thresholds["delta_c"],
                severity="moderate",
                run_id=recent_calib.run_id,
            )
        )

    # CI separation check (if CIs available)
    if (
        baseline_calib.b_l95 is not None
        and baseline_calib.b_u95 is not None
        and (
            recent_calib.b_hat < baseline_calib.b_l95
            or recent_calib.b_hat > baseline_calib.b_u95
        )
    ):
        alerts.append(
            DriftAlert(
                item_id=recent_calib.item_id,
                window_id=recent_calib.window_id,
                metric="b_ci_separation",
                value=delta_b,
                threshold=0.0,
                severity="severe",
                run_id=recent_calib.run_id,
            )
        )

    return alerts


def save_calibrations(engine, calibrations: List[ItemCalibration]) -> None:
    """Save calibration results to database."""
    if not calibrations:
        return

    records = [
        {
            "item_id": c.item_id,
            "window_id": c.window_id,
            "a_hat": c.a_hat,
            "b_hat": c.b_hat,
            "c_hat": c.c_hat,
            "a_l95": c.a_l95,
            "a_u95": c.a_u95,
            "b_l95": c.b_l95,
            "b_u95": c.b_u95,
            "c_l95": c.c_l95,
            "c_u95": c.c_u95,
            "n": c.n,
            "dif": c.dif,
            "info": c.info,
            "run_id": c.run_id,
        }
        for c in calibrations
    ]

    df = pd.DataFrame(records)
    with engine.begin() as conn:
        df.to_sql("item_calibration", conn, if_exists="append", index=False)

    logger.info(f"Saved {len(calibrations)} calibration records")


def save_alerts(engine, alerts: List[DriftAlert]) -> None:
    """Save drift alerts to database."""
    if not alerts:
        return

    records = [
        {
            "item_id": a.item_id,
            "window_id": a.window_id,
            "metric": a.metric,
            "value": a.value,
            "threshold": a.threshold,
            "severity": a.severity,
            "run_id": a.run_id,
        }
        for a in alerts
    ]

    df = pd.DataFrame(records)
    with engine.begin() as conn:
        df.to_sql("drift_alerts", conn, if_exists="append", index=False)

    logger.info(f"Saved {len(alerts)} drift alerts")


def run_drift_monitor(
    recent_days: int = DEFAULT_LOOKBACK_DAYS,
    baseline_from: Optional[datetime] = None,
    baseline_to: Optional[datetime] = None,
    min_sample: int = DEFAULT_MIN_SAMPLE,
    thresholds: Optional[Dict[str, float]] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run full drift monitoring pipeline."""
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS.copy()
    if run_id is None:
        run_id = f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    engine = create_engine(DATABASE_URL)
    logger.info(f"Starting drift monitor run: {run_id}")

    # Step 1: Define recent window
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=recent_days)
    recent_window = create_drift_window(engine, recent_start, now)

    # Step 2: Define baseline window
    if baseline_from and baseline_to:
        baseline_window = create_drift_window(engine, baseline_from, baseline_to)
    else:
        # Default: use quarterly baseline (90-120 days ago)
        baseline_end = now - timedelta(days=90)
        baseline_start = baseline_end - timedelta(days=30)
        baseline_window = create_drift_window(engine, baseline_start, baseline_end)

    # Step 3: Load responses
    recent_responses = load_responses(engine, recent_window, min_sample)
    baseline_responses = load_responses(engine, baseline_window, min_sample)

    # Get item list (items with data in both windows)
    recent_items = set(recent_responses["item_id"].unique())
    baseline_items = set(baseline_responses["item_id"].unique())
    common_items = recent_items & baseline_items
    logger.info(f"Analyzing {len(common_items)} items with data in both windows")

    if len(common_items) == 0:
        logger.warning("No common items between windows; exiting")
        return {"run_id": run_id, "calibrations": 0, "alerts": 0}

    # Step 4: Calibrate via R IRT service
    baseline_params = call_r_irt_calibrate(baseline_responses, model="3PL")
    recent_params = call_r_irt_calibrate(recent_responses, model="3PL")

    # Step 5: Build calibration objects and detect drift
    calibrations: List[ItemCalibration] = []
    all_alerts: List[DriftAlert] = []

    for item_id in common_items:
        if item_id not in baseline_params or item_id not in recent_params:
            continue

        bp = baseline_params[item_id]
        rp = recent_params[item_id]

        # Compute CIs (±1.96 * SE for 95% CI)
        baseline_calib = ItemCalibration(
            item_id=item_id,
            window_id=baseline_window.window_id,
            a_hat=bp["a"],
            b_hat=bp["b"],
            c_hat=bp["c"],
            a_l95=bp["a"] - 1.96 * bp["a_se"],
            a_u95=bp["a"] + 1.96 * bp["a_se"],
            b_l95=bp["b"] - 1.96 * bp["b_se"],
            b_u95=bp["b"] + 1.96 * bp["b_se"],
            c_l95=max(0, bp["c"] - 1.96 * bp["c_se"]),
            c_u95=min(1, bp["c"] + 1.96 * bp["c_se"]),
            n=len(baseline_responses[baseline_responses["item_id"] == item_id]),
            run_id=run_id,
        )

        # Information function summary
        info_summary = compute_information_summary(rp["a"], rp["b"], rp["c"])

        recent_calib = ItemCalibration(
            item_id=item_id,
            window_id=recent_window.window_id,
            a_hat=rp["a"],
            b_hat=rp["b"],
            c_hat=rp["c"],
            a_l95=rp["a"] - 1.96 * rp["a_se"],
            a_u95=rp["a"] + 1.96 * rp["a_se"],
            b_l95=rp["b"] - 1.96 * rp["b_se"],
            b_u95=rp["b"] + 1.96 * rp["b_se"],
            c_l95=max(0, rp["c"] - 1.96 * rp["c_se"]),
            c_u95=min(1, rp["c"] + 1.96 * rp["c_se"]),
            n=len(recent_responses[recent_responses["item_id"] == item_id]),
            info=info_summary,
            run_id=run_id,
        )

        calibrations.append(recent_calib)

        # Detect drift
        alerts = detect_drift(baseline_calib, recent_calib, thresholds)
        all_alerts.extend(alerts)

        if alerts:
            logger.warning(f"Item {item_id}: {len(alerts)} drift alerts")

    # Step 6: Save results
    save_calibrations(engine, calibrations)
    save_alerts(engine, all_alerts)

    logger.info(
        f"Drift monitor complete. {len(calibrations)} items calibrated, {len(all_alerts)} alerts"
    )

    return {
        "run_id": run_id,
        "baseline_window": baseline_window.window_id,
        "recent_window": recent_window.window_id,
        "calibrations": len(calibrations),
        "alerts": len(all_alerts),
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="IRT drift monitor (V1 frequentist)")
    parser.add_argument(
        "--recent-days",
        type=int,
        default=DEFAULT_LOOKBACK_DAYS,
        help="Recent window size in days",
    )
    parser.add_argument(
        "--baseline-from",
        type=str,
        help="Baseline window start (ISO format)",
    )
    parser.add_argument(
        "--baseline-to",
        type=str,
        help="Baseline window end (ISO format)",
    )
    parser.add_argument(
        "--min-sample",
        type=int,
        default=DEFAULT_MIN_SAMPLE,
        help="Minimum responses per item",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="Run identifier",
    )

    args = parser.parse_args()

    baseline_from = (
        datetime.fromisoformat(args.baseline_from) if args.baseline_from else None
    )
    baseline_to = datetime.fromisoformat(args.baseline_to) if args.baseline_to else None

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    result = run_drift_monitor(
        recent_days=args.recent_days,
        baseline_from=baseline_from,
        baseline_to=baseline_to,
        min_sample=args.min_sample,
        run_id=args.run_id,
    )

    print(
        f"Run {result['run_id']}: {result['calibrations']} calibrations, {result['alerts']} alerts"
    )


if __name__ == "__main__":
    main()
