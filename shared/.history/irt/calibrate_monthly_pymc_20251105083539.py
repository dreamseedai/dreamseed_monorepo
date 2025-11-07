#!/usr/bin/env python3
"""
Bayesian IRT Calibration with PyMC
===================================
Monthly calibration using PyMC's 2PL hierarchical model

Features:
- Pure Python Bayesian IRT (PyMC + NumPy)
- NUTS sampler with automatic tuning
- Posterior diagnostics (ArviZ)
- Anchor item priors (optional)
- Drift detection
- PostgreSQL integration

Usage:
    python -m shared.irt.calibrate_monthly_pymc \
        --database-url postgresql://postgres:***@127.0.0.1/dreamseed \
        --min-responses 200 \
        --window-label "2025-10 monthly" \
        --samples 1000 \
        --tune 1000 \
        --chains 4

Dependencies:
    pip install pymc arviz sqlalchemy psycopg2-binary pandas numpy
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import arviz as az
import click
import numpy as np
import pandas as pd
import pymc as pm
import sqlalchemy as sa
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Database Operations
# ==============================================================================

class IRTDatabase:
    """Database interface for IRT calibration"""
    
    def __init__(self, database_url: str):
        self.engine = sa.create_engine(database_url)
    
    def create_window(self, label: Optional[str] = None) -> Dict:
        """Create or get calibration window"""
        with self.engine.begin() as conn:
            if label is None:
                # Auto-generate for previous month
                result = conn.execute(text("""
                    SELECT to_char(date_trunc('month', now() - interval '1 month'), 'YYYY-MM') || ' monthly' AS label
                """))
                label = result.scalar()
            
            # Check if exists
            result = conn.execute(
                text("SELECT id, start_at, end_at, label FROM shared_irt.windows WHERE label = :label"),
                {"label": label}
            )
            existing = result.mappings().first()
            
            if existing:
                logger.info(f"Using existing window: {existing['label']} (id={existing['id']})")
                return dict(existing)
            
            # Create new
            result = conn.execute(text("""
                INSERT INTO shared_irt.windows (label, start_at, end_at, population_tags)
                VALUES (
                    :label,
                    date_trunc('month', now() - interval '1 month'),
                    date_trunc('month', now()),
                    ARRAY['global']
                )
                RETURNING id, start_at, end_at, label
            """), {"label": label})
            
            win = dict(result.mappings().one())
            logger.info(f"Created window: {win['label']} (id={win['id']})")
            logger.info(f"Date range: {win['start_at']} to {win['end_at']}")
            return win
    
    def load_responses(self, window_id: int) -> pd.DataFrame:
        """Load response data for window"""
        with self.engine.connect() as conn:
            df = pd.read_sql(
                text("""
                    SELECT 
                        item_id, 
                        user_id_hash, 
                        CASE WHEN is_correct THEN 1 ELSE 0 END AS y
                    FROM shared_irt.item_responses
                    WHERE answered_at >= (SELECT start_at FROM shared_irt.windows WHERE id = :wid)
                      AND answered_at <  (SELECT end_at   FROM shared_irt.windows WHERE id = :wid)
                """),
                conn,
                params={"wid": window_id}
            )
        
        logger.info(f"Loaded {len(df)} total responses")
        return df
    
    def load_anchors(self, item_ids: List[int]) -> pd.DataFrame:
        """Load anchor item parameters"""
        with self.engine.connect() as conn:
            df = pd.read_sql(
                text("""
                    SELECT 
                        i.id as item_id,
                        c.a,
                        c.b,
                        c.c
                    FROM shared_irt.items i
                    JOIN shared_irt.item_parameters_current c ON c.item_id = i.id
                    WHERE i.is_anchor = TRUE
                      AND i.id = ANY(:ids)
                """),
                conn,
                params={"ids": item_ids}
            )
        
        if not df.empty:
            logger.info(f"Loaded {len(df)} anchor items")
        return df
    
    def load_baseline_params(self, item_ids: List[int]) -> pd.DataFrame:
        """Load baseline parameters for drift detection"""
        with self.engine.connect() as conn:
            df = pd.read_sql(
                text("""
                    SELECT item_id, a, b, c
                    FROM shared_irt.item_parameters_current
                    WHERE item_id = ANY(:ids)
                """),
                conn,
                params={"ids": item_ids}
            )
        
        return df
    
    def store_calibration(
        self,
        window_id: int,
        results: pd.DataFrame,
        loglik: float
    ):
        """Store calibration results"""
        with self.engine.begin() as conn:
            for _, row in results.iterrows():
                conn.execute(text("""
                    INSERT INTO shared_irt.item_calibration (
                        item_id, window_id, model, 
                        a_hat, b_hat, c_hat,
                        a_ci_low, a_ci_high, b_ci_low, b_ci_high,
                        n_responses, loglik
                    )
                    VALUES (
                        :item_id, :window_id, '2PL',
                        :a_hat, :b_hat, NULL,
                        :a_ci_low, :a_ci_high, :b_ci_low, :b_ci_high,
                        :n_responses, :loglik
                    )
                    ON CONFLICT (item_id, window_id) DO UPDATE SET
                        a_hat = EXCLUDED.a_hat,
                        b_hat = EXCLUDED.b_hat,
                        a_ci_low = EXCLUDED.a_ci_low,
                        a_ci_high = EXCLUDED.a_ci_high,
                        b_ci_low = EXCLUDED.b_ci_low,
                        b_ci_high = EXCLUDED.b_ci_high,
                        n_responses = EXCLUDED.n_responses,
                        loglik = EXCLUDED.loglik,
                        created_at = now()
                """), {
                    "item_id": int(row["item_id"]),
                    "window_id": window_id,
                    "a_hat": float(row["a_mean"]),
                    "b_hat": float(row["b_mean"]),
                    "a_ci_low": float(row["a_hdi_3%"]),
                    "a_ci_high": float(row["a_hdi_97%"]),
                    "b_ci_low": float(row["b_hdi_3%"]),
                    "b_ci_high": float(row["b_hdi_97%"]),
                    "n_responses": int(row["n_responses"]),
                    "loglik": loglik
                })
        
        logger.info(f"Stored {len(results)} calibration results")
    
    def store_drift_alerts(
        self,
        window_id: int,
        alerts: List[Dict]
    ):
        """Store drift alerts"""
        if not alerts:
            logger.info("No drift alerts to store")
            return
        
        with self.engine.begin() as conn:
            for alert in alerts:
                conn.execute(text("""
                    INSERT INTO shared_irt.drift_alerts (
                        item_id, window_id, metric, value, threshold, severity, message
                    )
                    VALUES (:item_id, :window_id, :metric, :value, :threshold, :severity, :message)
                """), alert)
        
        logger.info(f"Stored {len(alerts)} drift alerts")
    
    def update_current_params(
        self,
        window_id: int,
        stable_items: List[int]
    ):
        """Update current parameters for stable items"""
        with self.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO shared_irt.item_parameters_current (
                    item_id, model, a, b, c,
                    a_se, b_se,
                    version, effective_from
                )
                SELECT 
                    ic.item_id,
                    ic.model,
                    ic.a_hat,
                    ic.b_hat,
                    ic.c_hat,
                    (ic.a_ci_high - ic.a_ci_low) / 3.92,  -- Approximate SE
                    (ic.b_ci_high - ic.b_ci_low) / 3.92,
                    COALESCE((
                        SELECT version FROM shared_irt.item_parameters_current 
                        WHERE item_id = ic.item_id
                    ), 0) + 1,
                    now()
                FROM shared_irt.item_calibration ic
                WHERE ic.window_id = :window_id
                  AND ic.item_id = ANY(:stable_items)
                ON CONFLICT (item_id) DO UPDATE SET
                    a = EXCLUDED.a,
                    b = EXCLUDED.b,
                    a_se = EXCLUDED.a_se,
                    b_se = EXCLUDED.b_se,
                    version = EXCLUDED.version,
                    effective_from = EXCLUDED.effective_from,
                    updated_at = now()
            """), {"window_id": window_id, "stable_items": stable_items})
        
        logger.info(f"Updated parameters for {len(stable_items)} stable items")


# ==============================================================================
# PyMC 2PL Model
# ==============================================================================

def fit_pymc_2pl(
    df: pd.DataFrame,
    user_index: Dict,
    item_index: Dict,
    samples: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.9,
    anchor_priors: Optional[pd.DataFrame] = None
) -> Tuple[az.InferenceData, Dict]:
    """
    Fit 2PL IRT model using PyMC
    
    Model:
        theta_u ~ N(0, 1)              # User ability
        a_i ~ LogNormal(0, 0.2)         # Item discrimination (constrained > 0)
        b_i ~ N(0, 1)                   # Item difficulty
        
        P(y_ui = 1) = sigmoid(a_i * (theta_u - b_i))
    
    Args:
        df: Response data with columns [u, i, y]
        user_index: User ID to index mapping
        item_index: Item ID to index mapping
        samples: Number of MCMC samples
        tune: Number of tuning samples
        chains: Number of MCMC chains
        target_accept: Target acceptance rate
        anchor_priors: Optional anchor item priors (item_id, a, b)
    
    Returns:
        idata: ArviZ InferenceData object
        diagnostics: Model diagnostics dict
    """
    U = len(user_index)
    I = len(item_index)
    
    y = df["y"].values
    u = df["u"].values
    i = df["i"].values
    
    logger.info(f"Fitting PyMC 2PL model: {U} users, {I} items, {len(y)} responses")
    
    with pm.Model() as model:
        # User ability (standardized)
        theta = pm.Normal("theta", mu=0, sigma=1, shape=U)
        
        # Item parameters
        if anchor_priors is not None and not anchor_priors.empty:
            # Use informative priors for anchors
            logger.info(f"Using informative priors for {len(anchor_priors)} anchor items")
            
            # Default priors
            a_mu = np.zeros(I)
            a_sigma = 0.2 * np.ones(I)
            b_mu = np.zeros(I)
            b_sigma = np.ones(I)
            
            # Override with anchor priors
            for _, anchor in anchor_priors.iterrows():
                if anchor["item_id"] in item_index:
                    idx = item_index[anchor["item_id"]]
                    if not np.isnan(anchor["a"]):
                        a_mu[idx] = np.log(anchor["a"])  # LogNormal parameterization
                        a_sigma[idx] = 0.05  # Tight prior
                    if not np.isnan(anchor["b"]):
                        b_mu[idx] = anchor["b"]
                        b_sigma[idx] = 0.05  # Tight prior
            
            a = pm.LogNormal("a", mu=a_mu, sigma=a_sigma, shape=I)
            b = pm.Normal("b", mu=b_mu, sigma=b_sigma, shape=I)
        else:
            # Default priors
            a = pm.LogNormal("a", mu=0, sigma=0.2, shape=I)
            b = pm.Normal("b", mu=0, sigma=1, shape=I)
        
        # 2PL logistic model
        eta = a[i] * (theta[u] - b[i])
        p = pm.math.sigmoid(eta)
        
        # Likelihood
        y_obs = pm.Bernoulli("y_obs", p=p, observed=y)
        
        # Sample
        logger.info(f"Sampling: {samples} samples, {tune} tune, {chains} chains")
        idata = pm.sample(
            draws=samples,
            tune=tune,
            chains=chains,
            target_accept=target_accept,
            return_inferencedata=True,
            progressbar=True
        )
    
    # Diagnostics
    divergences = idata.sample_stats.diverging.sum().item()
    r_hat_max = az.rhat(idata).max().max().item()
    ess_bulk_min = az.ess(idata, method="bulk").min().min().item()
    
    diagnostics = {
        "divergences": divergences,
        "r_hat_max": r_hat_max,
        "ess_bulk_min": ess_bulk_min
    }
    
    logger.info(f"Sampling complete")
    logger.info(f"  Divergences: {divergences}")
    logger.info(f"  Max R-hat: {r_hat_max:.4f} (should be < 1.01)")
    logger.info(f"  Min ESS (bulk): {ess_bulk_min:.0f} (should be > 400)")
    
    if divergences > 0:
        logger.warning(f"Warning: {divergences} divergent transitions detected")
    if r_hat_max > 1.01:
        logger.warning(f"Warning: Max R-hat = {r_hat_max:.4f} > 1.01 (poor convergence)")
    if ess_bulk_min < 400:
        logger.warning(f"Warning: Min ESS = {ess_bulk_min:.0f} < 400 (low effective sample size)")
    
    return idata, diagnostics


# ==============================================================================
# Main Pipeline
# ==============================================================================

def run_calibration(
    database_url: str,
    window_label: Optional[str] = None,
    min_responses: int = 200,
    samples: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.9,
    drift_threshold_b: float = 0.25,
    drift_threshold_a: float = 0.2
):
    """Run full PyMC calibration pipeline"""
    
    db = IRTDatabase(database_url)
    
    # Step 1: Create window
    logger.info("Step 1: Creating calibration window...")
    win = db.create_window(window_label)
    win_id = win["id"]
    
    # Step 2: Load responses
    logger.info("Step 2: Loading response data...")
    resp = db.load_responses(win_id)
    
    if resp.empty:
        raise ValueError("No responses found for this window")
    
    # Step 3: Filter eligible items
    logger.info(f"Step 3: Filtering items (min_responses >= {min_responses})...")
    counts = resp.groupby("item_id").size()
    eligible = counts[counts >= min_responses].index.tolist()
    
    if not eligible:
        raise ValueError(f"No items with >= {min_responses} responses")
    
    logger.info(f"Eligible items: {len(eligible)}")
    
    df = resp[resp["item_id"].isin(eligible)].copy()
    
    # Create indexes
    user_index = {u: i for i, u in enumerate(df["user_id_hash"].unique())}
    item_index = {it: i for i, it in enumerate(df["item_id"].unique())}
    
    df["u"] = df["user_id_hash"].map(user_index)
    df["i"] = df["item_id"].map(item_index)
    
    logger.info(f"Final dataset: {len(df)} responses, {len(user_index)} users, {len(item_index)} items")
    
    # Step 4: Load anchor priors
    logger.info("Step 4: Loading anchor item priors...")
    anchors = db.load_anchors(eligible)
    
    # Step 5: Fit model
    logger.info("Step 5: Fitting PyMC 2PL model...")
    idata, diagnostics = fit_pymc_2pl(
        df, user_index, item_index,
        samples=samples, tune=tune, chains=chains,
        target_accept=target_accept,
        anchor_priors=anchors if not anchors.empty else None
    )
    
    # Step 6: Extract parameters
    logger.info("Step 6: Extracting item parameters...")
    summary = az.summary(idata, var_names=["a", "b"], hdi_prob=0.94)
    
    # Parse item parameters
    item_ids = np.array(list(item_index.keys()))
    
    results = pd.DataFrame({
        "item_id": item_ids,
        "a_mean": summary.filter(like="a[", axis=0)["mean"].values,
        "a_sd": summary.filter(like="a[", axis=0)["sd"].values,
        "a_hdi_3%": summary.filter(like="a[", axis=0)["hdi_3%"].values,
        "a_hdi_97%": summary.filter(like="a[", axis=0)["hdi_97%"].values,
        "b_mean": summary.filter(like="b[", axis=0)["mean"].values,
        "b_sd": summary.filter(like="b[", axis=0)["sd"].values,
        "b_hdi_3%": summary.filter(like="b[", axis=0)["hdi_3%"].values,
        "b_hdi_97%": summary.filter(like="b[", axis=0)["hdi_97%"].values,
    })
    
    results["n_responses"] = counts.reindex(item_ids).values
    
    # Log-likelihood
    loglik = idata.log_likelihood["y_obs"].sum().item()
    logger.info(f"Model log-likelihood: {loglik:.2f}")
    
    # Step 7: Store results
    logger.info("Step 7: Storing calibration results...")
    db.store_calibration(win_id, results, loglik)
    
    # Step 8: Drift detection
    logger.info("Step 8: Detecting parameter drift...")
    baseline = db.load_baseline_params(item_ids.tolist())
    
    if not baseline.empty:
        merged = results.merge(baseline, on="item_id", how="inner", suffixes=("", "_prev"))
        merged["delta_b"] = merged["b_mean"] - merged["b"]
        merged["delta_a"] = merged["a_mean"] - merged["a"]
        
        alerts = []
        for _, row in merged.iterrows():
            # Difficulty drift
            if abs(row["delta_b"]) > drift_threshold_b:
                severity = "high" if abs(row["delta_b"]) > 0.5 else "medium"
                alerts.append({
                    "item_id": int(row["item_id"]),
                    "window_id": win_id,
                    "metric": "Δb",
                    "value": float(row["delta_b"]),
                    "threshold": drift_threshold_b,
                    "severity": severity,
                    "message": f"Item {int(row['item_id'])}: Δb = {row['delta_b']:+.3f} (current: {row['b_mean']:.3f}, previous: {row['b']:.3f})"
                })
            
            # Discrimination drift
            if abs(row["delta_a"]) > drift_threshold_a:
                severity = "high" if abs(row["delta_a"]) > 0.4 else "medium"
                alerts.append({
                    "item_id": int(row["item_id"]),
                    "window_id": win_id,
                    "metric": "Δa",
                    "value": float(row["delta_a"]),
                    "threshold": drift_threshold_a,
                    "severity": severity,
                    "message": f"Item {int(row['item_id'])}: Δa = {row['delta_a']:+.3f} (current: {row['a_mean']:.3f}, previous: {row['a']:.3f})"
                })
        
        db.store_drift_alerts(win_id, alerts)
        
        if alerts:
            logger.warning(f"Detected {len(alerts)} drift alerts")
        else:
            logger.info("No significant drift detected ✓")
        
        # Step 9: Update stable items
        logger.info("Step 9: Updating current parameters for stable items...")
        stable_items = merged[
            (merged["delta_b"].abs() <= drift_threshold_b) &
            (merged["delta_a"].abs() <= drift_threshold_a)
        ]["item_id"].tolist()
        
        if stable_items:
            db.update_current_params(win_id, stable_items)
    else:
        logger.info("No baseline parameters - skipping drift detection")
        db.update_current_params(win_id, item_ids.tolist())
    
    logger.info("✓ Calibration complete")
    logger.info(f"  Window ID: {win_id}")
    logger.info(f"  Items calibrated: {len(results)}")
    logger.info(f"  Divergences: {diagnostics['divergences']}")
    logger.info(f"  Max R-hat: {diagnostics['r_hat_max']:.4f}")


# ==============================================================================
# CLI
# ==============================================================================

@click.command()
@click.option("--database-url", envvar="DATABASE_URL", required=True,
              help="PostgreSQL connection URL")
@click.option("--window-label", default=None,
              help="Window label (default: auto-generate for previous month)")
@click.option("--min-responses", default=200,
              help="Minimum responses per item")
@click.option("--samples", default=1000,
              help="MCMC samples (post-warmup)")
@click.option("--tune", default=1000,
              help="MCMC tuning/warmup samples")
@click.option("--chains", default=4,
              help="Number of MCMC chains")
@click.option("--target-accept", default=0.9,
              help="NUTS target acceptance rate")
@click.option("--drift-threshold-b", default=0.25,
              help="Difficulty drift threshold |Δb|")
@click.option("--drift-threshold-a", default=0.2,
              help="Discrimination drift threshold |Δa|")
def main(
    database_url: str,
    window_label: Optional[str],
    min_responses: int,
    samples: int,
    tune: int,
    chains: int,
    target_accept: float,
    drift_threshold_b: float,
    drift_threshold_a: float
):
    """Bayesian IRT calibration with PyMC"""
    run_calibration(
        database_url=database_url,
        window_label=window_label,
        min_responses=min_responses,
        samples=samples,
        tune=tune,
        chains=chains,
        target_accept=target_accept,
        drift_threshold_b=drift_threshold_b,
        drift_threshold_a=drift_threshold_a
    )


if __name__ == "__main__":
    main()
