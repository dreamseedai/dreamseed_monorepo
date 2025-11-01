from __future__ import annotations

import os
from typing import Any, Dict

import pytest
from seedtest_api.app.clients.r_irt import RIrtClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _Resp:
    def __init__(self, body: Dict[str, Any]):
        self._body = body

    def raise_for_status(self):  # noqa: D401
        return None

    def json(self):
        return self._body


@pytest.mark.anyio
async def test_r_irt_client_calibrate(monkeypatch):
    monkeypatch.setenv("R_IRT_BASE_URL", "http://localhost:9000")
    captured: Dict[str, Any] = {}

    class _AC:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _Resp(
                {"ok": True, "item_params": [], "abilities": [], "fit_meta": {}}
            )

    monkeypatch.setattr("httpx.AsyncClient", _AC)

    client = RIrtClient()
    out = await client.calibrate(
        [{"user_id": "U1", "item_id": "Q1", "is_correct": True, "responded_at": "..."}],
        model="2PL",
    )
    assert out.get("ok") is True
    assert captured["url"].endswith("/irt/calibrate")
    assert captured["json"]["model"] == "2PL"
    assert isinstance(captured["headers"], dict)


@pytest.mark.anyio
async def test_r_irt_client_score(monkeypatch):
    monkeypatch.setenv("R_IRT_BASE_URL", "http://localhost:9001")
    captured: Dict[str, Any] = {}

    class _AC:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _Resp({"ok": True, "scores": []})

    monkeypatch.setattr("httpx.AsyncClient", _AC)

    client = RIrtClient()
    out = await client.score(
        {"items": []}, [{"user_id": "U1", "item_id": "Q1", "is_correct": True}]
    )
    assert out.get("ok") is True
    assert captured["url"].endswith("/irt/score")
    assert "item_params" in captured["json"] and "responses" in captured["json"]
