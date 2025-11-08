from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class RGlmmClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        token: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("R_GLMM_BASE_URL") or "").rstrip("/")
        self.timeout = float(timeout or os.getenv("GLMM_TIMEOUT_SECS", "30"))
        self.token = token or os.getenv("R_GLMM_INTERNAL_TOKEN") or None
        if not self.base_url:
            raise RuntimeError("R_GLMM_BASE_URL is not configured")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def fit_progress(
        self,
        rows: List[Dict[str, Any]],
        *,
        formula: str = "score ~ week + (week|student) + (1|topic)",
        family: str = "gaussian",
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/glmm/fit_progress"
        payload: Dict[str, Any] = {"rows": rows, "formula": formula, "family": family}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()


__all__ = ["RGlmmClient"]
