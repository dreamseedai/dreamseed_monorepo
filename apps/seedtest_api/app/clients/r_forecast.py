"""
R Forecast Plumber Client

Client for interacting with r-forecast-plumber service.
Supports Prophet time series forecasting and Survival analysis.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class RForecastClient:
    """Client for R Forecast Plumber service (Prophet and Survival)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        token: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("R_FORECAST_BASE_URL") or "").rstrip("/")
        self.timeout = float(timeout or os.getenv("R_FORECAST_TIMEOUT_SECS", "300"))
        self.token = token or os.getenv("R_FORECAST_INTERNAL_TOKEN") or None
        if not self.base_url:
            raise RuntimeError("R_FORECAST_BASE_URL is not configured")

    def _headers(self) -> Dict[str, str]:
        """Get HTTP headers including auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            # Also support X-Internal-Token for backward compatibility
            headers["X-Internal-Token"] = self.token
        return headers

    async def health(self) -> Dict[str, Any]:
        """Check service health and available engines."""
        url = f"{self.base_url}/healthz"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            return r.json()

    # ==================== Prophet (Time Series Forecasting) ====================

    async def prophet_fit(
        self,
        data: List[Dict[str, Any]],
        *,
        seasonality_mode: str = "additive",
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
    ) -> Dict[str, Any]:
        """
        Fit Prophet time series model.

        Args:
            data: List of dicts with 'ds' (date string) and 'y' (value)
            seasonality_mode: "additive" or "multiplicative"
            yearly_seasonality: Include yearly seasonality
            weekly_seasonality: Include weekly seasonality
            daily_seasonality: Include daily seasonality

        Returns:
            Dict with 'status', 'n_obs', 'date_range', 'params', 'model_id'
        """
        url = f"{self.base_url}/prophet/fit"
        payload: Dict[str, Any] = {
            "rows": data,
            "seasonality_mode": seasonality_mode,
            "yearly_seasonality": yearly_seasonality,
            "weekly_seasonality": weekly_seasonality,
            "daily_seasonality": daily_seasonality,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def prophet_predict(
        self,
        data: List[Dict[str, Any]],
        *,
        periods: int = 30,
        freq: str = "day",
    ) -> Dict[str, Any]:
        """
        Generate Prophet forecast.

        Args:
            data: Historical data (list of dicts with 'ds', 'y')
            periods: Number of periods to forecast
            freq: Frequency ("day", "week", "month")

        Returns:
            Dict with 'status', 'periods', 'forecast' (list of {ds, yhat, yhat_lower, yhat_upper})
        """
        url = f"{self.base_url}/prophet/predict"
        payload: Dict[str, Any] = {
            "rows": data,
            "periods": periods,
            "freq": freq,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def prophet_fit_series(
        self,
        series: List[Dict[str, Any]],
        *,
        horizon_weeks: int = 4,
        anomaly_threshold: float = 2.5,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Fit Prophet with weekly series and detect anomalies (new contract).

        Args:
            series: List of dicts with 'week_start' (YYYY-MM-DD) and 'I_t' (float)
            horizon_weeks: Forecast horizon in weeks
            anomaly_threshold: Absolute z-score threshold for anomalies
            options: Prophet options (seasonality_mode, yearly_seasonality, weekly_seasonality,
                     changepoint_prior_scale, n_changepoints, interval_width, seed)

        Returns:
            Dict with status, run_id, model_meta, last_observed_week, forecast, anomalies
        """
        url = f"{self.base_url}/prophet/fit"
        payload: Dict[str, Any] = {
            "series": series,
            "horizon_weeks": int(horizon_weeks),
            "anomaly_threshold": float(anomaly_threshold),
            "options": options or {},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    # ==================== Survival Analysis (Churn Prediction) ====================

    async def survival_fit(
        self,
        data: List[Dict[str, Any]],
        *,
        model: str = "cox",
    ) -> Dict[str, Any]:
        """
        Fit survival model (Cox PH or parametric).

        Args:
            data: List of dicts with 'time' (numeric), 'event' (0/1), and optional covariates
            model: "cox" (Cox proportional hazards), "exponential", "weibull", etc.

        Returns:
            Dict with 'status', 'model', 'n_obs', 'n_events', 'coefficients', 'summary'
        """
        url = f"{self.base_url}/survival/fit"
        payload: Dict[str, Any] = {
            "rows": data,
            "model": model,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def survival_fit_v2(
        self,
        rows: List[Dict[str, Any]],
        *,
        family: str = "cox",
        event_threshold_days: int = 14,
        regularization: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fit survival model (new contract) and score cohort risk.

        Args:
            rows: List of dicts with 'user_id', 'observed_gap_days', 'event', and covariates
            family: 'cox' or parametric ('weibull', etc.)
            event_threshold_days: Threshold defining churn event
            regularization: Optional dict for future use
            seed: Optional random seed

        Returns:
            Dict with status, run_id, model_meta, predictions, survival_curve
        """
        url = f"{self.base_url}/survival/fit"
        params: Dict[str, Any] = {
            "family": family,
            "event_threshold_days": int(event_threshold_days),
        }
        if seed is not None:
            params["seed"] = int(seed)
        if regularization:
            params["regularization"] = regularization
        payload: Dict[str, Any] = {"rows": rows, "params": params}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def survival_predict(
        self,
        data: List[Dict[str, Any]],
        *,
        time: float = 365,
        model: str = "cox",
        newdata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Predict survival probability at time t.

        Args:
            data: Training data (list of dicts with 'time', 'event', covariates)
            time: Time point for prediction (e.g., 365 days)
            model: "cox", "exponential", "weibull", etc.
            newdata: Optional new covariate data for prediction

        Returns:
            Dict with 'status', 'model', 'time', 'survival_prob'
        """
        url = f"{self.base_url}/survival/predict"
        payload: Dict[str, Any] = {
            "rows": data,
            "time": time,
            "model": model,
        }
        if newdata:
            payload["newdata"] = newdata
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    # ==================== Clustering (Tidymodels / Base R) ====================

    async def cluster_fit(
        self,
        data: List[Dict[str, Any]],
        *,
        method: str = "kmeans",
        k: int = 3,
        eps: float = 0.5,
        minPts: int = 5,
    ) -> Dict[str, Any]:
        """
        Fit clustering model.

        Args:
            data: List of dicts with 'user_id' and numeric features
            method: "kmeans", "hierarchical", or "dbscan"
            k: Number of clusters (for kmeans/hierarchical)
            eps: DBSCAN epsilon parameter
            minPts: DBSCAN minimum points parameter

        Returns:
            Dict with 'status', 'method', 'k'/'eps', 'clusters' (user_id -> cluster_id), 'centers' (for kmeans)
        """
        url = f"{self.base_url}/cluster/fit"
        payload: Dict[str, Any] = {
            "rows": data,
            "method": method,
        }
        if method in ("kmeans", "hierarchical"):
            payload["k"] = k
        if method == "dbscan":
            payload["eps"] = eps
            payload["minPts"] = minPts

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def cluster_predict(
        self,
        newdata: List[Dict[str, Any]],
        *,
        centers: List[List[float]],
    ) -> Dict[str, Any]:
        """
        Predict cluster assignment for new data.

        Args:
            newdata: List of dicts with 'user_id' and numeric features
            centers: Cluster centroids from fit (list of lists)

        Returns:
            Dict with 'status', 'clusters' (user_id -> cluster_id)
        """
        url = f"{self.base_url}/cluster/predict"
        payload: Dict[str, Any] = {
            "newdata": newdata,
            "centers": centers,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()


__all__ = ["RForecastClient"]
