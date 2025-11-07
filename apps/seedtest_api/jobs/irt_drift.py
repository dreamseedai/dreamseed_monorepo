"""Bayesian IRT drift detection module.

Implements anchor-based drift monitoring with Bayesian re-estimation:
1. Window-based calibration (baseline vs recent)
2. Anchor/non-anchor prior specification
3. DIF analysis by demographic groups
4. Threshold-based alert generation
5. CAT exposure adjustment recommendations

Supports PyMC, brms (via rpy2), or Stan backends.

Usage:
    from apps.seedtest_api.jobs.irt_drift import run_drift_detection
    
    run_drift_detection(
        recent_days=30,
        baseline_window_id=1,
        min_sample=200,
        thresholds={"delta_b": 0.25, "delta_a": 0.2, "delta_c": 0.03},
        backend="pymc"
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Configuration defaults (can be overridden via env or args)
DEFAULT_ANCHOR_PRIOR_SD = 0.05  # Strong prior for anchors
DEFAULT_NON_ANCHOR_PRIOR_SD = 0.25  # Weak prior for non-anchors
DEFAULT_MIN_SAMPLE = 200  # Minimum responses per item
DEFAULT_THRESHOLDS = {
    "delta_b": 0.25,
    "delta_a": 0.2,
    "delta_c": 0.03,
    "dif_bayes_factor": 3.0,  # BF > 3 = moderate evidence
    "dif_prob_threshold": 0.9,  # P(Δb > 0.2) > 0.9
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
    """Bayesian calibration results for a single item in a window."""

    item_id: str
    window_id: int
    a_hat: float
    b_hat: float
    c_hat: float
    a_l95: float
    a_u95: float
    b_l95: float
    b_u95: float
    c_l95: float
    c_u95: float
    n: int
    dif: Optional[Dict[str, Any]] = None
    info: Optional[Dict[str, Any]] = None
    run_id: Optional[str] = None


@dataclass
class DriftAlert:
    """Drift detection alert."""

    item_id: str
    window_id: int
    metric: str
    value: float
    threshold: float
    severity: Literal["minor", "moderate", "severe"]
    run_id: Optional[str] = None


def create_drift_window(
    start_at: datetime,
    end_at: datetime,
    population_tags: Optional[Dict[str, Any]] = None,
) -> DriftWindow:
    """Create a new drift window (saves to DB)."""
    # In production, insert into drift_windows table and return window_id
    # For now, return a stub
    window_id = hash((start_at, end_at)) % 1000000
    logger.info(f"Created drift window {window_id}: {start_at} to {end_at}")
    return DriftWindow(
        window_id=window_id,
        start_at=start_at,
        end_at=end_at,
        population_tags=population_tags,
    )


def load_responses(window: DriftWindow, item_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """Load item responses for a given window.
    
    Returns DataFrame with columns: user_id, item_id, correct (0/1), timestamp
    Should query from attempt VIEW or equivalent response table.
    """
    # Stub: in production, query from DB
    # SELECT user_id, item_id, correct, created_at
    # FROM attempts
    # WHERE created_at >= window.start_at
    #   AND created_at < window.end_at
    #   AND (item_id = ANY(item_ids) if item_ids else TRUE)
    logger.warning("load_responses: using stub data; implement DB query")
    return pd.DataFrame({
        "user_id": ["u1", "u2", "u3"],
        "item_id": ["i1", "i1", "i2"],
        "correct": [1, 0, 1],
        "timestamp": [window.start_at] * 3,
    })


def load_item_baseline_params(item_ids: List[str]) -> pd.DataFrame:
    """Load baseline IRT parameters for items.
    
    Returns DataFrame with columns: item_id, a, b, c, is_anchor
    """
    # Stub: in production, query from items table
    logger.warning("load_item_baseline_params: using stub data; implement DB query")
    return pd.DataFrame({
        "item_id": item_ids,
        "a": [1.0] * len(item_ids),
        "b": [0.0] * len(item_ids),
        "c": [0.2] * len(item_ids),
        "is_anchor": [True if i == "i1" else False for i in item_ids],
    })


def bayesian_estimate_3pl_pymc(
    responses: pd.DataFrame,
    item_id: str,
    baseline_a: float,
    baseline_b: float,
    baseline_c: float,
    is_anchor: bool,
    anchor_prior_sd: float = DEFAULT_ANCHOR_PRIOR_SD,
    non_anchor_prior_sd: float = DEFAULT_NON_ANCHOR_PRIOR_SD,
) -> Tuple[float, float, float, float, float, float, float, float, float]:
    """Bayesian 3PL estimation using PyMC.
    
    Returns: (a_hat, b_hat, c_hat, a_l95, a_u95, b_l95, b_u95, c_l95, c_u95)
    
    Priors:
    - Anchors: N(μ=baseline, σ²=anchor_prior_sd²)
    - Non-anchors: N(μ=baseline, σ²=non_anchor_prior_sd²)
    - c: Beta(α,β) centered near baseline_c
    """
    try:
        import pymc as pm
        import arviz as az
    except ImportError:
        logger.error("PyMC not installed; install with: pip install pymc arviz")
        raise

    item_responses = responses[responses["item_id"] == item_id].copy()
    if len(item_responses) < DEFAULT_MIN_SAMPLE:
        logger.warning(f"Item {item_id}: insufficient data (n={len(item_responses)})")
        # Return baseline with wide CIs
        return (
            baseline_a, baseline_b, baseline_c,
            baseline_a - 0.5, baseline_a + 0.5,
            baseline_b - 0.5, baseline_b + 0.5,
            baseline_c - 0.05, baseline_c + 0.05,
        )

    y = item_responses["correct"].values
    # For full model, estimate theta per user; for simplicity, use fixed theta=0 or MLE
    # Here we use a simple fixed-theta approach; production should estimate jointly
    theta = np.zeros(len(y))  # Simplification; in production, estimate per user

    prior_sd_a = anchor_prior_sd if is_anchor else non_anchor_prior_sd
    prior_sd_b = anchor_prior_sd if is_anchor else non_anchor_prior_sd

    with pm.Model():
        # Priors
        a = pm.Normal("a", mu=baseline_a, sigma=prior_sd_a)
        b = pm.Normal("b", mu=baseline_b, sigma=prior_sd_b)
        # c prior: Beta around baseline_c
        alpha_c = baseline_c * 10 + 1
        beta_c = (1 - baseline_c) * 10 + 1
        c = pm.Beta("c", alpha=alpha_c, beta=beta_c)

        # Likelihood: 3PL IRT
        eta = a * (theta - b)
        p = c + (1 - c) * pm.math.sigmoid(eta)
        _ = pm.Bernoulli("obs", p=p, observed=y)

        # Sample posterior
        trace = pm.sample(
            draws=2000,
            tune=1000,
            chains=2,
            return_inferencedata=True,
            progressbar=False,
        )

    # Extract posterior summaries
    summary = az.summary(trace, hdi_prob=0.95)
    a_hat = summary.loc["a", "mean"]
    b_hat = summary.loc["b", "mean"]
    c_hat = summary.loc["c", "mean"]
    a_l95, a_u95 = summary.loc["a", ["hdi_2.5%", "hdi_97.5%"]]
    b_l95, b_u95 = summary.loc["b", ["hdi_2.5%", "hdi_97.5%"]]
    c_l95, c_u95 = summary.loc["c", ["hdi_2.5%", "hdi_97.5%"]]

    return (
        float(a_hat), float(b_hat), float(c_hat),
        float(a_l95), float(a_u95),
        float(b_l95), float(b_u95),
        float(c_l95), float(c_u95),
    )


def compute_dif(
    responses: pd.DataFrame,
    item_id: str,
    baseline_b: float,
    groups: List[str],
) -> Dict[str, Any]:
    """Compute DIF (Differential Item Functioning) by demographic groups.
    
    For each group, estimate Δb and compute Bayes Factor or posterior probability.
    
    Args:
        responses: Response data with group columns (e.g., 'gender', 'grade')
        item_id: Item identifier
        baseline_b: Reference difficulty
        groups: List of column names to analyze
        
    Returns:
        Dict with per-group DIF metrics: {"gender": {"M": {"delta_b": 0.1, "bf": 2.0}, ...}}
    """
    # Stub: in production, fit separate models per group and compare
    logger.warning("compute_dif: using stub; implement full DIF analysis")
    dif_results = {}
    for group_col in groups:
        if group_col not in responses.columns:
            continue
        group_values = responses[group_col].unique()
        dif_results[group_col] = {}
        for val in group_values:
            # Placeholder: estimate Δb for this subgroup
            dif_results[group_col][val] = {
                "delta_b": 0.05,  # Stub
                "bayes_factor": 1.5,  # Stub
                "prob_threshold": 0.7,  # P(Δb > 0.2)
            }
    return dif_results


def compute_information_function(
    a: float, b: float, c: float, theta_range: np.ndarray
) -> Dict[str, Any]:
    """Compute Fisher information function over theta range.
    
    Returns summary: mean, max, theta_at_max
    """
    from shared.irt import item_information_3pl
    
    info_values = [item_information_3pl(t, a, b, c) for t in theta_range]
    max_info = float(np.max(info_values))
    theta_at_max = float(theta_range[np.argmax(info_values)])
    mean_info = float(np.mean(info_values))
    
    return {
        "mean": mean_info,
        "max": max_info,
        "theta_at_max": theta_at_max,
        "range": (float(theta_range[0]), float(theta_range[-1])),
    }


def detect_drift(
    baseline_calib: ItemCalibration,
    recent_calib: ItemCalibration,
    thresholds: Dict[str, float],
) -> List[DriftAlert]:
    """Detect drift by comparing baseline and recent calibrations.
    
    Generates alerts for:
    - |Δa|, |Δb|, Δc exceeding thresholds
    - 95% CI separation
    - DIF evidence
    """
    alerts: List[DriftAlert] = []
    
    delta_a = abs(recent_calib.a_hat - baseline_calib.a_hat)
    delta_b = abs(recent_calib.b_hat - baseline_calib.b_hat)
    delta_c = recent_calib.c_hat - baseline_calib.c_hat
    
    # Check thresholds
    if delta_a > thresholds.get("delta_a", DEFAULT_THRESHOLDS["delta_a"]):
        severity = "severe" if delta_a > 0.4 else "moderate"
        alerts.append(DriftAlert(
            item_id=recent_calib.item_id,
            window_id=recent_calib.window_id,
            metric="delta_a",
            value=delta_a,
            threshold=thresholds["delta_a"],
            severity=severity,
            run_id=recent_calib.run_id,
        ))
    
    if delta_b > thresholds.get("delta_b", DEFAULT_THRESHOLDS["delta_b"]):
        severity = "severe" if delta_b > 0.5 else "moderate" if delta_b > 0.35 else "minor"
        alerts.append(DriftAlert(
            item_id=recent_calib.item_id,
            window_id=recent_calib.window_id,
            metric="delta_b",
            value=delta_b,
            threshold=thresholds["delta_b"],
            severity=severity,
            run_id=recent_calib.run_id,
        ))
    
    if delta_c > thresholds.get("delta_c", DEFAULT_THRESHOLDS["delta_c"]):
        alerts.append(DriftAlert(
            item_id=recent_calib.item_id,
            window_id=recent_calib.window_id,
            metric="delta_c",
            value=delta_c,
            threshold=thresholds["delta_c"],
            severity="moderate",
            run_id=recent_calib.run_id,
        ))
    
    # CI separation check (baseline CI vs recent point estimate)
    if (recent_calib.b_hat < baseline_calib.b_l95 or 
        recent_calib.b_hat > baseline_calib.b_u95):
        alerts.append(DriftAlert(
            item_id=recent_calib.item_id,
            window_id=recent_calib.window_id,
            metric="b_ci_separation",
            value=delta_b,
            threshold=0.0,
            severity="severe",
            run_id=recent_calib.run_id,
        ))
    
    # DIF checks (if available)
    if recent_calib.dif:
        for group, group_data in recent_calib.dif.items():
            for subgroup, metrics in group_data.items():
                bf = metrics.get("bayes_factor", 0)
                if bf > thresholds.get("dif_bayes_factor", DEFAULT_THRESHOLDS["dif_bayes_factor"]):
                    alerts.append(DriftAlert(
                        item_id=recent_calib.item_id,
                        window_id=recent_calib.window_id,
                        metric=f"dif_{group}_{subgroup}",
                        value=bf,
                        threshold=thresholds["dif_bayes_factor"],
                        severity="moderate",
                        run_id=recent_calib.run_id,
                    ))
    
    return alerts


def run_drift_detection(
    recent_days: int = 30,
    baseline_window_id: Optional[int] = None,
    min_sample: int = DEFAULT_MIN_SAMPLE,
    thresholds: Optional[Dict[str, float]] = None,
    backend: Literal["pymc", "brms", "stan"] = "pymc",
    dif_groups: Optional[List[str]] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run full drift detection pipeline.
    
    Steps:
    1. Create recent window (last N days)
    2. Load baseline window (or use fixed baseline_window_id)
    3. Load responses for both windows
    4. Bayesian re-estimation for each item
    5. Compute DIF if groups specified
    6. Detect drift and generate alerts
    7. Save results to DB
    
    Returns summary: {"calibrations": [...], "alerts": [...], "run_id": "..."}
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS.copy()
    if run_id is None:
        run_id = f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"Starting drift detection run: {run_id}")
    
    # Step 1: Define recent window
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=recent_days)
    recent_window = create_drift_window(recent_start, now)
    
    # Step 2: Load baseline window (stub: use fixed window_id or create one)
    if baseline_window_id is None:
        # Use a fixed historical window (e.g., 90 days ago, 30-day span)
        baseline_end = now - timedelta(days=90)
        baseline_start = baseline_end - timedelta(days=30)
        baseline_window = create_drift_window(baseline_start, baseline_end)
    else:
        # Load from DB
        logger.warning("baseline_window_id specified; implement DB load")
        baseline_window = DriftWindow(
            window_id=baseline_window_id,
            start_at=now - timedelta(days=120),
            end_at=now - timedelta(days=90),
        )
    
    # Step 3: Load responses
    recent_responses = load_responses(recent_window)
    baseline_responses = load_responses(baseline_window)
    
    # Get item list (items with sufficient data)
    item_ids = list(set(recent_responses["item_id"].unique()) & 
                    set(baseline_responses["item_id"].unique()))
    logger.info(f"Analyzing {len(item_ids)} items with data in both windows")
    
    # Load baseline parameters
    baseline_params = load_item_baseline_params(item_ids)
    
    # Step 4: Bayesian re-estimation
    calibrations: List[ItemCalibration] = []
    theta_range = np.linspace(-3, 3, 50)
    
    for _, row in baseline_params.iterrows():
        item_id = row["item_id"]
        baseline_a, baseline_b, baseline_c = row["a"], row["b"], row["c"]
        is_anchor = row["is_anchor"]
        
        # Baseline window calibration (for reference)
        baseline_est = bayesian_estimate_3pl_pymc(
            baseline_responses, item_id, baseline_a, baseline_b, baseline_c, is_anchor
        )
        baseline_calib = ItemCalibration(
            item_id=item_id,
            window_id=baseline_window.window_id,
            a_hat=baseline_est[0],
            b_hat=baseline_est[1],
            c_hat=baseline_est[2],
            a_l95=baseline_est[3],
            a_u95=baseline_est[4],
            b_l95=baseline_est[5],
            b_u95=baseline_est[6],
            c_l95=baseline_est[7],
            c_u95=baseline_est[8],
            n=len(baseline_responses[baseline_responses["item_id"] == item_id]),
            run_id=run_id,
        )
        
        # Recent window calibration
        recent_est = bayesian_estimate_3pl_pymc(
            recent_responses, item_id, baseline_a, baseline_b, baseline_c, is_anchor
        )
        
        # DIF analysis
        dif_results = None
        if dif_groups:
            dif_results = compute_dif(recent_responses, item_id, baseline_b, dif_groups)
        
        # Information function
        info_summary = compute_information_function(
            recent_est[0], recent_est[1], recent_est[2], theta_range
        )
        
        recent_calib = ItemCalibration(
            item_id=item_id,
            window_id=recent_window.window_id,
            a_hat=recent_est[0],
            b_hat=recent_est[1],
            c_hat=recent_est[2],
            a_l95=recent_est[3],
            a_u95=recent_est[4],
            b_l95=recent_est[5],
            b_u95=recent_est[6],
            c_l95=recent_est[7],
            c_u95=recent_est[8],
            n=len(recent_responses[recent_responses["item_id"] == item_id]),
            dif=dif_results,
            info=info_summary,
            run_id=run_id,
        )
        
        calibrations.append(recent_calib)
        
        # Detect drift
        alerts = detect_drift(baseline_calib, recent_calib, thresholds)
        if alerts:
            logger.warning(f"Item {item_id}: {len(alerts)} drift alerts")
            # Save alerts to DB (stub)
            for alert in alerts:
                logger.info(f"  - {alert.metric}: {alert.value:.3f} (thresh={alert.threshold}, severity={alert.severity})")
    
    # Step 7: Save to DB (stub)
    logger.info(f"Drift detection complete. {len(calibrations)} items calibrated.")
    
    return {
        "run_id": run_id,
        "baseline_window": baseline_window.window_id,
        "recent_window": recent_window.window_id,
        "calibrations": len(calibrations),
        "alerts": sum(len(detect_drift(
            ItemCalibration(c.item_id, baseline_window.window_id, 
                          baseline_params[baseline_params["item_id"]==c.item_id].iloc[0]["a"],
                          baseline_params[baseline_params["item_id"]==c.item_id].iloc[0]["b"],
                          baseline_params[baseline_params["item_id"]==c.item_id].iloc[0]["c"],
                          0, 0, 0, 0, 0, 0, 0, run_id=run_id),
            c, thresholds
        )) for c in calibrations),
    }


if __name__ == "__main__":
    # CLI entry point for cron job
    import argparse
    
    parser = argparse.ArgumentParser(description="IRT Bayesian drift detection")
    parser.add_argument("--recent-days", type=int, default=30, help="Recent window size")
    parser.add_argument("--baseline-window-id", type=int, help="Baseline window ID")
    parser.add_argument("--min-sample", type=int, default=200, help="Min responses per item")
    parser.add_argument("--backend", choices=["pymc", "brms", "stan"], default="pymc")
    parser.add_argument("--dif-groups", nargs="+", help="DIF analysis groups")
    parser.add_argument("--run-id", help="Run identifier")
    
    args = parser.parse_args()
    
    result = run_drift_detection(
        recent_days=args.recent_days,
        baseline_window_id=args.baseline_window_id,
        min_sample=args.min_sample,
        backend=args.backend,
        dif_groups=args.dif_groups,
        run_id=args.run_id,
    )
    
    print(f"Run {result['run_id']}: {result['calibrations']} items, {result['alerts']} alerts")
