"""
R BRMS Plumber Client

Client for interacting with r-brms-plumber service.
Supports Bayesian growth modeling using brms (Stan backend).

Module-level helpers are provided for simple integrations (e.g., metrics.py):
- prob_goal(mu, sd, target) -> float uses /growth/predict when available,
  falls back to Normal approximation if the service is unreachable.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class RBrmsClient:
    """Client for R BRMS Plumber service (Bayesian growth modeling)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        token: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("R_BRMS_BASE_URL") or "").rstrip("/")
        self.timeout = float(timeout or os.getenv("R_BRMS_TIMEOUT_SECS", "600"))
        self.token = token or os.getenv("R_BRMS_INTERNAL_TOKEN") or None
        if not self.base_url:
            raise RuntimeError("R_BRMS_BASE_URL is not configured")

    def _headers(self) -> Dict[str, str]:
        """Get HTTP headers including auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            # Also support X-Internal-Token for backward compatibility
            headers["X-Internal-Token"] = self.token
        return headers

    def _base(self) -> str:
        return self.base_url.rstrip("/")

    async def fit_growth(
        self,
        data: List[Dict[str, Any]],
        *,
        formula: str = "score ~ week + (week|student_id)",
        priors: Optional[Dict[str, Any]] = None,
        n_samples: int = 2000,
        n_chains: int = 4,
        n_warmup: int = 1000,
        family: str = "gaussian",
    ) -> Dict[str, Any]:
        """
        Fit Bayesian growth model using brms.

        Args:
            data: List of dicts with 'student_id', 'week', 'score'
            formula: Model formula (default: hierarchical growth)
            priors: Prior distributions (optional, uses defaults if None)
            n_samples: Number of posterior samples (default: 2000)
            n_chains: Number of MCMC chains (default: 4)
            n_warmup: Number of warmup iterations (default: 1000)

        Returns:
            Dict with 'posterior_summary', 'diagnostics', 'predictions' (per student)
        """
        # Adapt to r-brms-plumber /growth/fit contract: expects { rows: [{student, week, score}], family, iter, chains }
        url = f"{self._base()}/growth/fit"
        rows: List[Dict[str, Any]] = []
        for d in data:
            if d is None:
                continue
            stu = d.get("student") or d.get("student_id")
            wk = d.get("week")
            sc = d.get("score")
            if stu is None or wk is None or sc is None:
                continue
            rows.append({"student": str(stu), "week": float(wk), "score": float(sc)})
        payload: Dict[str, Any] = {
            "rows": rows,
            "family": family,
            "iter": int(n_samples),
            "chains": int(n_chains),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def predict_goal_probability(
        self,
        user_features: Dict[str, Any],
        *,
        target_score: float,
        model_coefficients: Optional[Dict[str, float]] = None,
        credible_interval: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Predict goal attainment probability P(goal|state) with credible interval.

        Args:
            user_features: Dict with user features (e.g., current_score, trend)
            target_score: Target score to achieve
            model_coefficients: Optional pre-fitted coefficients
            credible_interval: Credible interval level (default: 0.95)

        Returns:
            Dict with 'probability' (P), 'lower' (lower bound), 'upper' (upper bound), 'uncertainty' (σ)
        """
        url = f"{self._base()}/growth/predict"
        payload: Dict[str, Any] = {
            "user_features": user_features,
            "target_score": target_score,
            "credible_interval": credible_interval,
        }
        if model_coefficients:
            payload["model_coefficients"] = model_coefficients

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    def prob_goal(self, mu: float, sd: float, target: float) -> float:
        """
        Compute goal probability P(score >= target | mu, sd).

        This is a convenience method for integration with metrics.py.
        Uses normal approximation (fallback when R service unavailable).

        Args:
            mu: Mean (expected score)
            sd: Standard deviation
            target: Target score

        Returns:
            Probability in [0, 1]
        """
        # Try service first; on failure, fallback to normal approximation
        try:
            import httpx

            url = f"{self._base()}/growth/predict"
            payload = {"mean": float(mu), "sd": float(sd), "target": float(target)}
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(url, json=payload, headers=self._headers())
                r.raise_for_status()
                data = r.json()
                return float(data.get("probability", 0.0))
        except Exception:
            # Fallback to Normal approximation without external deps
            import math

            z = (target - mu) / max(sd, 1e-6)  # Avoid division by zero
            prob = 0.5 * (1.0 + math.erf(-z / math.sqrt(2.0)))
            return max(0.0, min(1.0, float(prob)))


def _base_url() -> str:
    return (
        os.getenv("R_BRMS_BASE_URL")
        or "http://r-brms-plumber.seedtest.svc.cluster.local:80"
    ).rstrip("/")


def _timeout() -> float:
    try:
        return float(os.getenv("R_BRMS_TIMEOUT_SECS", "600"))
    except Exception:
        return 600.0


def _headers() -> Dict[str, str]:
    token = os.getenv("R_BRMS_INTERNAL_TOKEN")
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def prob_goal(mu: float, sd: float, target: float) -> float:
    """Module-level helper used by metrics.py.

    Attempts to call /growth/predict; on failure, uses Normal approximation.
    """
    # Try service first
    try:
        import httpx

        url = f"{_base_url()}/growth/predict"
        payload = {"mean": float(mu), "sd": float(sd), "target": float(target)}
        with httpx.Client(timeout=_timeout()) as client:
            r = client.post(url, headers=_headers(), json=payload)
            r.raise_for_status()
            data = r.json()
            return float(data.get("probability", 0.0))
    except Exception:
        # Fallback to Normal approximation
        import math

        z = (target - mu) / max(sd, 1e-6)
        prob = 0.5 * (1.0 + math.erf(-z / math.sqrt(2.0)))
        return max(0.0, min(1.0, float(prob)))


__all__ = ["RBrmsClient", "prob_goal"]
