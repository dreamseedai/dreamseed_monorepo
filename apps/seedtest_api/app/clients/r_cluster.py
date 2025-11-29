"""
R Cluster Plumber Client

Client for interacting with r-cluster-plumber service (or r-forecast-plumber with clustering).
Supports user segmentation using k-means or Gaussian mixture models (tidymodels).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class RClusterClient:
    """Client for R Cluster Plumber service (user segmentation)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        token: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("R_CLUSTER_BASE_URL") or "").rstrip("/")
        self.timeout = float(timeout or os.getenv("R_CLUSTER_TIMEOUT_SECS", "300"))
        self.token = token or os.getenv("R_CLUSTER_INTERNAL_TOKEN") or None
        if not self.base_url:
            raise RuntimeError("R_CLUSTER_BASE_URL is not configured")

    def _headers(self) -> Dict[str, str]:
        """Get HTTP headers including auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            # Also support X-Internal-Token for backward compatibility
            headers["X-Internal-Token"] = self.token
        return headers

    async def fit_clusters(
        self,
        data: List[Dict[str, Any]],
        *,
        method: str = "kmeans",
        n_clusters: Optional[int] = None,
        features: Optional[List[str]] = None,
        auto_select_k: bool = True,
    ) -> Dict[str, Any]:
        """
        Fit clustering model to user features.

        Args:
            data: List of dicts with user features:
                - user_id: str
                - engagement: float (A_t)
                - improvement: float (I_t)
                - efficiency: float (E_t)
                - recovery: float (R_t)
                - sessions: float (session count)
                - gap: float (mean gap between sessions)
                - avg_rt: float (average response time)
                - avg_hints: float (average hints per attempt)
                - total_attempts: float (total attempts)
            method: Clustering method ("kmeans" or "gaussian_mixture")
            n_clusters: Number of clusters (None for auto-select)
            features: List of feature names to use (default: all numeric features)
            auto_select_k: Whether to auto-select optimal k using silhouette/Gap statistic

        Returns:
            Dict with 'assignments' (user_id -> cluster_id), 'centers', 'metrics' (silhouette, etc.)
        """
        url = f"{self.base_url}/cluster/fit"
        payload: Dict[str, Any] = {
            "data": data,
            "method": method,
            "auto_select_k": auto_select_k,
        }
        if n_clusters is not None:
            payload["n_clusters"] = int(n_clusters)
        if features:
            payload["features"] = features

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def predict_segment(
        self,
        user_features: List[Dict[str, Any]],
        *,
        model_centers: Optional[List[List[float]]] = None,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Predict cluster assignment for new users.

        Args:
            user_features: List of dicts with user features (same format as fit_clusters)
            model_centers: Optional pre-fitted cluster centers (if None, uses last fitted model)
            features: List of feature names to use (must match fit_clusters features)

        Returns:
            Dict with 'assignments' (user_id -> cluster_id) and 'distances' (to nearest center)
        """
        url = f"{self.base_url}/cluster/predict"
        payload: Dict[str, Any] = {"user_features": user_features}
        if model_centers:
            payload["model_centers"] = model_centers
        if features:
            payload["features"] = features

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()


__all__ = ["RClusterClient"]
