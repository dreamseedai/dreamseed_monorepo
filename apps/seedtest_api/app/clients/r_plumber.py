from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio
import time

import httpx


class RPlumberClient:
    """Async HTTP client for the R Plumber service.

    Contract:
    - health(): GET /healthz -> JSON
    - glmm_fit(observations, formula?): POST /glmm/fit -> JSON { model: {...}, warnings?: [...]} 
    - glmm_predict(model, newdata): POST /glmm/predict -> JSON { predictions: [...] }
    - forecast_summary(mean, sd, target): POST /forecast/summary -> JSON { prob: float }
    """

    def __init__(
        self, base_url: str, timeout: float = 15.0, internal_token: Optional[str] = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.internal_token = internal_token

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.internal_token:
            h["X-Internal-Token"] = self.internal_token
        return h

    async def health(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._with_retry(client.get, f"{self.base_url}/healthz")

    async def glmm_fit(
        self, observations: List[Dict[str, Any]], formula: Optional[str] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"observations": observations}
        if formula:
            payload["formula"] = formula
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
            return await self._with_retry(client.post, f"{self.base_url}/glmm/fit", json=payload)

    async def glmm_predict(
        self, model: Dict[str, Any], newdata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        payload = {"model": model, "newdata": newdata}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
            return await self._with_retry(client.post, f"{self.base_url}/glmm/predict", json=payload)

    async def forecast_summary(self, mean: float, sd: float, target: float) -> Dict[str, Any]:
        payload = {"mean": mean, "sd": sd, "target": target}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
            return await self._with_retry(client.post, f"{self.base_url}/forecast/summary", json=payload)

    async def _with_retry(self, func, *args, **kwargs):
        """Execute an HTTP call with simple exponential backoff.

        Retries on httpx.RequestError or 5xx responses.
        """
        max_attempts = 3
        backoff_base = 0.2  # seconds
        last_exc: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            try:
                resp = await func(*args, **kwargs)
                # Raise for 4xx/5xx; we will retry only 5xx
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if 500 <= e.response.status_code < 600 and attempt < max_attempts:
                        delay = backoff_base * (2 ** (attempt - 1))
                        await asyncio.sleep(delay)
                        continue
                    raise
                return resp.json()
            except (httpx.RequestError) as e:
                last_exc = e
                if attempt < max_attempts:
                    delay = backoff_base * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                    continue
                raise
        # Should not reach here; re-raise last exception if any
        if last_exc:
            raise last_exc
        raise RuntimeError("unexpected_retry_failure")
