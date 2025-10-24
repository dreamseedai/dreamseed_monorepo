import os
import json
from fastapi.testclient import TestClient
from ..main import app


def test_healthz():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True


def test_env_snippet_minimum_example(monkeypatch):
    # Minimum: org + tags, TTL=0 (re-detect every query scenario)
    monkeypatch.setenv("BANK_ORG_ID", "2002")
    monkeypatch.setenv("BANK_TAGS", "itembank,new-schema")
    monkeypatch.setenv("TAGS_KIND_TTL_SEC", "0")

    from ..settings import Settings
    s = Settings()
    assert s.BANK_ORG_ID == 2002
    assert s.bank_tags == ["itembank", "new-schema"]
    assert s.TAGS_KIND_TTL_SEC == 0
