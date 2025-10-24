import os
from ..services.loader import build_loader_filters


def test_build_loader_filters_respects_env_changes(monkeypatch):
    # First value
    monkeypatch.setenv("BANK_ORG_ID", "111")
    f1 = build_loader_filters()
    assert f1["org_id"] == 111

    # Change env and call again without reloading modules; should pick up new value
    monkeypatch.setenv("BANK_ORG_ID", "222")
    f2 = build_loader_filters()
    assert f2["org_id"] == 222
