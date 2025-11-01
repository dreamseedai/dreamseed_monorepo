from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class RIrtClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        token: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("R_IRT_BASE_URL") or "").rstrip("/")
        self.timeout = float(timeout or os.getenv("R_IRT_TIMEOUT_SECS", "20"))
        self.token = token or os.getenv("R_IRT_INTERNAL_TOKEN") or None
        if not self.base_url:
            raise RuntimeError("R_IRT_BASE_URL is not configured")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def calibrate(
        self, observations: List[Dict[str, Any]], model: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/irt/calibrate"
        payload: Dict[str, Any] = {"observations": observations}
        if model:
            payload["model"] = model
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def score(
        self, item_params: Dict[str, Any], responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/irt/score"
        payload: Dict[str, Any] = {"item_params": item_params, "responses": responses}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()


__all__ = ["RIrtClient"]
