import json
import time
import types

import pytest
from fastapi.testclient import TestClient

from adaptive_engine.main import app
from adaptive_engine import config as cfg


@pytest.fixture
def client():
    return TestClient(app)


def test_settings_root_hierarchy_across_namespaces(client, monkeypatch):
    # Prepare a fake Redis with two levels (math and math:algebra)
    class FakeRedis:
        def __init__(self):
            self.store: dict[str, str] = {}

        def get(self, key: str):
            return self.store.get(key)

        def scan_iter(self, match: str):
            pre, suf = match.split("*")
            for k in self.store:
                if k.startswith(pre) and k.endswith(suf):
                    yield k

    fake = FakeRedis()
    prefix = cfg.get_settings().redis_key_prefix
    payload_root = json.dumps(
        {
            "policy": {
                "prefer_balanced": True,
                "deterministic": False,
                "max_per_topic": None,
                "top_k_random": None,
                "info_band_fraction": 0.05,
            },
            "last_updated": "2025-01-01T00:00:00Z",
        }
    )
    payload_child = json.dumps(
        {
            "policy": {
                "prefer_balanced": False,
                "deterministic": True,
                "max_per_topic": 2,
                "top_k_random": 1,
                "info_band_fraction": 0.10,
            },
            "last_updated": "2025-02-02T00:00:00Z",
        }
    )
    fake.store[f"{prefix}math:selection_policy"] = payload_root
    fake.store[f"{prefix}math:algebra:selection_policy"] = payload_child

    # Patch redis client to fake
    monkeypatch.setattr(
        cfg,
        "redis",
        types.SimpleNamespace(
            Redis=types.SimpleNamespace(from_url=lambda *a, **k: fake)
        ),
    )

    client = TestClient(app)
    # GET global (should resolve to env if no redis global policy)
    r0 = client.get("/api/settings")
    assert r0.status_code == 200
    d0 = r0.json()
    assert d0["selection_policy_source"] in {"env", "redis"}

    # GET child namespace (should resolve to math:algebra specific policy)
    rc = client.get("/api/settings", params={"namespace": "math:algebra"})
    assert rc.status_code == 200
    dc = rc.json()
    assert dc["selection_policy_resolved_namespace"] == "math:algebra"
    assert dc["selection_policy"]["deterministic"] is True

    # GET parent namespace (math)
    rp = client.get("/api/settings", params={"namespace": "math"})
    assert rp.status_code == 200
    dp = rp.json()
    assert dp["selection_policy_resolved_namespace"] == "math"
    assert dp["selection_policy"]["deterministic"] is False


def test_reports_errors_no_session_and_empty_answered(client):
    # No session provided should be 400
    r = client.get("/api/reports/theta-se.png")
    assert r.status_code == 400

    # Start session but do not answer anything; request by session_id should be 400
    s = client.post("/api/exam/start", json={"user_id": 11, "exam_id": 1})
    sid = s.json()["session_id"]
    r2 = client.get("/api/reports/theta-se.png", params={"session_id": sid})
    assert r2.status_code == 400


def test_db_hooks_telemetry_and_irt_updater(monkeypatch):
    # Mock psycopg2 to exercise DB codepaths for telemetry and updater
    import adaptive_engine.services.telemetry as tel
    import adaptive_engine.services.irt_updater as upd

    class FakeCursor:
        def __init__(self):
            self._rows = [("Q1",), ("Q2",)]
            self.executed = []

        def execute(self, q, params=None):
            self.executed.append((q, params))

        def fetchall(self):
            # For exposure select, return rows; for stats view, return mocked stats
            return [("Q1",), ("Q2",)]

        def close(self):
            pass

    class FakeConn:
        def __init__(self):
            self.cur = FakeCursor()
            self.commits = 0
            self.rollbacks = 0

        def cursor(self):
            return self.cur

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

        def close(self):
            pass

    class FakePsy:
        def __init__(self, mode="tel"):
            self.mode = mode
            self.conns = []
            self.last_conn = None

        def connect(self, dsn):
            conn = FakeConn()
            self.conns.append(conn)
            self.last_conn = conn
            return conn

    # Configure settings with a dummy database_url
    base = cfg.AppSettings(
        database_url="postgres://u:p@h/db", irt_stats_view="stats", items_table="items"
    )
    monkeypatch.setattr(cfg, "get_settings", lambda: base, raising=True)
    # Patch module-local get_settings where imported at definition time
    monkeypatch.setattr(tel, "get_settings", lambda: base, raising=True)

    # Patch psycopg2 getter to return our fake for telemetry
    fake_psy = FakePsy("tel")
    monkeypatch.setattr(tel, "_get_psycopg2", lambda: fake_psy, raising=True)

    # Exercise telemetry DB functions (should not raise)
    tel.log_exposure("sid", 1, 1, "Q1")
    tel.log_response("sid", 1, 1, "Q1", True)

    # Validate SQL executed for telemetry: two INSERTs with expected parameters
    executed_all = []
    for c in fake_psy.conns:
        executed_all.extend(c.cur.executed)
    # Expect two statements
    assert any(
        "INSERT INTO item_exposure" in (q if isinstance(q, str) else "")
        and params == ("sid", 1, 1, "Q1")
        for q, params in executed_all
    )
    assert any(
        "INSERT INTO item_response" in (q if isinstance(q, str) else "")
        and params == ("sid", 1, 1, "Q1", True)
        for q, params in executed_all
    )

    # Validate updater fetch_stats_from_db executes SELECT against configured view
    fake_psy_fetch = FakePsy("fetch")
    monkeypatch.setattr(upd, "_get_psycopg2", lambda: fake_psy_fetch, raising=True)
    base_fetch = cfg.AppSettings(
        database_url="postgres://u:p@h/db", irt_stats_view="stats"
    )
    monkeypatch.setattr(cfg, "get_settings", lambda: base_fetch, raising=True)
    monkeypatch.setattr(upd, "get_settings", lambda: base_fetch, raising=True)
    list(upd.fetch_stats_from_db())  # force iteration
    executed_fetch = []
    for c in fake_psy_fetch.conns:
        executed_fetch.extend(c.cur.executed)
    assert any(
        "SELECT question_id, a, b, c, correct_rate FROM stats"
        in (q if isinstance(q, str) else "")
        for q, _ in executed_fetch
    )

    # Now patch updater DB functions: fetch_stats returns two rows
    def fake_iter():
        yield {"question_id": "Q1", "a": 1.0, "b": 0.0, "c": 0.2, "correct_rate": 0.6}
        yield {"question_id": "Q2", "a": 0.8, "b": 0.2, "c": 0.2, "correct_rate": 0.4}

    monkeypatch.setattr(upd, "fetch_stats_from_db", lambda: fake_iter(), raising=True)
    # Patch persist to a no-op that records calls
    calls = []
    monkeypatch.setattr(
        upd,
        "persist_update_to_db",
        lambda q, a, b, c: calls.append((q, a, b, c)),
        raising=True,
    )
    n = upd.run_irt_update_once(
        fetch_stats=upd.fetch_stats_from_db, persist_update=upd.persist_update_to_db
    )
    assert n == 2
    assert len(calls) == 2

    # (Optional) we already validated fetch SQL and run_irt_update_once logic; skip direct persist SQL assertion to avoid brittleness
