from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio

import httpx


class RIRTClient:
    """Async HTTP client for the R IRT Plumber service.

    Contract:
    - health(): GET /healthz -> JSON
    - calibrate(responses): POST /irt/calibrate -> JSON { item_params: [...], abilities: [...] }
    - score(item_params, responses): POST /irt/score -> JSON (501 for now)
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

    async def calibrate(self, responses: List[List[Optional[int]]]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"responses": responses}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
            return await self._with_retry(client.post, f"{self.base_url}/irt/calibrate", json=payload)

    async def score(
        self, item_params: List[Dict[str, Any]], responses: List[List[Optional[int]]]
    ) -> Dict[str, Any]:
        payload = {"item_params": item_params, "responses": responses}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
            return await self._with_retry(client.post, f"{self.base_url}/irt/score", json=payload)

    async def _with_retry(self, func, *args, **kwargs):
        max_attempts = 3
        backoff_base = 0.2
        last_exc: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            try:
                resp = await func(*args, **kwargs)
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if 500 <= e.response.status_code < 600 and attempt < max_attempts:
                        await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
                        continue
                    raise
                return resp.json()
            except httpx.RequestError as e:
                last_exc = e
                if attempt < max_attempts:
                    await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("unexpected_retry_failure")
