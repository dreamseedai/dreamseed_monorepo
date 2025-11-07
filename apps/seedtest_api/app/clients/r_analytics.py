"""
R Analytics Plumber Client

Client for interacting with r-analytics service (port 8010).
Supports topic theta scoring, improvement index, goal attainment, recommendations,
churn risk assessment, and report generation.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import httpx


class RAnalyticsClient:
    """Client for R Analytics Plumber service (port 8010)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        token: Optional[str] = None,
        auth_header: str = "X-Internal-Token",
    ) -> None:
        self.base_url = (base_url or os.getenv("R_ANALYTICS_BASE_URL", "")).rstrip("/")
        if not self.base_url:
            raise RuntimeError("R_ANALYTICS_BASE_URL not set")
        self.timeout = float(os.getenv("R_ANALYTICS_TIMEOUT_SECS", str(timeout or 20.0)))
        self.token = token or os.getenv("R_ANALYTICS_TOKEN")
        self.auth_header = auth_header  # "X-Internal-Token" or "Authorization"

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            if self.auth_header.lower().startswith("authorization"):
                h["Authorization"] = f"Bearer {self.token}"
            else:
                h[self.auth_header] = self.token
        return h

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(
                f"{self.base_url}{path}",
                headers=self._headers(),
                content=json.dumps(payload),
            )
            r.raise_for_status()
            return r.json()

    def health(self) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(f"{self.base_url}/health")
            r.raise_for_status()
            return r.json()

    # 7.1 endpoints (spec)

    def score_topic_theta(
        self, student_id: str, topic_ids: List[str]
    ) -> Dict[str, Any]:
        payload = {"student_id": student_id, "topic_ids": topic_ids}
        return self._post("/score/topic-theta", payload)

    def improvement_index(
        self, student_id: str, window_days: int = 14
    ) -> Dict[str, Any]:
        payload = {"student_id": student_id, "window_days": window_days}
        return self._post("/improvement/index", payload)

    def goal_attainment(
        self,
        student_id: str,
        subject_id: str,
        target_score: float,
        target_date: str,
    ) -> Dict[str, Any]:
        payload = {
            "student_id": student_id,
            "subject_id": subject_id,
            "target_score": target_score,
            "target_date": target_date,
        }
        return self._post("/goal/attainment", payload)

    def recommend_next_topics(
        self, student_id: str, k: int = 5
    ) -> Dict[str, Any]:
        payload = {"student_id": student_id, "k": k}
        return self._post("/recommend/next-topics", payload)

    def risk_churn(self, student_id: str) -> Dict[str, Any]:
        payload = {"student_id": student_id}
        return self._post("/risk/churn", payload)

    def report_generate(
        self, student_id: str, period: str = "weekly"
    ) -> Dict[str, Any]:
        payload = {"student_id": student_id, "period": period}
        return self._post("/report/generate", payload)


__all__ = ["RAnalyticsClient"]
