from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from seedtest_api.jobs.mirt_calibrate import run_calibration


class _ResultProxy:
    def __init__(self, rows: List[Dict[str, Any]]):
        self._rows = rows

    def mappings(self):
        class _M:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        return _M(self._rows)


class _DummySession:
    def __init__(self):
        self.executed: List[Dict[str, Any]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, stmt, params=None):
        sql = str(stmt)
        # Record write statements
        if sql.strip().upper().startswith("INSERT INTO MIRT_ITEM_PARAMS"):
            self.executed.append({"type": "item", "params": params})
            return _ResultProxy([])
        if sql.strip().upper().startswith("INSERT INTO MIRT_ABILITY"):
            self.executed.append({"type": "ability", "params": params})
            return _ResultProxy([])
        if sql.strip().upper().startswith("INSERT INTO MIRT_FIT_META"):
            self.executed.append({"type": "meta", "params": params})
            return _ResultProxy([])
        # Read paths
        if "FROM responses" in sql:
            # Simulate missing table by raising
            raise Exception("no responses table")
        if "FROM exam_results" in sql:
            questions = [
                {"question_id": "Q1", "is_correct": True, "time_spent_sec": 2.0},
                {"question_id": "Q2", "correct": False, "time_spent_sec": 3.0},
            ]
            row = {
                "user_id": "U1",
                "session_id": "S1",
                "ts": datetime(2025, 1, 10, tzinfo=timezone.utc),
                "result_json": {"questions": questions},
            }
            return _ResultProxy([row])
        return _ResultProxy([])


class _DummySessionFactory:
    def __call__(self):
        return _DummySession()

    def __enter__(self):
        return _DummySession()

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeRIrt:
    async def calibrate(self, observations, model=None):
        return {
            "item_params": [
                {
                    "item_id": "Q1",
                    "model": model or "2PL",
                    "params": {"a": 1.0, "b": 0.0},
                    "version": "v1",
                }
            ],
            "abilities": [
                {
                    "user_id": "U1",
                    "theta": 0.3,
                    "se": 0.2,
                    "model": model or "2PL",
                    "version": "v1",
                }
            ],
            "fit_meta": {
                "run_id": "test-run",
                "model_spec": {"model": model or "2PL"},
                "metrics": {"n": len(observations)},
            },
        }


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_run_calibration_upserts(monkeypatch):
    dummy = _DummySession()

    class _GetSession:
        def __call__(self):
            return dummy

        def __enter__(self):
            return dummy

        def __exit__(self, exc_type, exc, tb):
            return False

    # Monkeypatch RIrtClient and get_session used in the job module
    from seedtest_api.jobs import mirt_calibrate as job_mod

    monkeypatch.setattr(job_mod, "get_session", _GetSession())
    monkeypatch.setattr(job_mod, "RIrtClient", lambda: _FakeRIrt())

    await run_calibration(lookback_days=7, model="2PL")

    # Validate that inserts were recorded
    types = [e["type"] for e in dummy.executed]
    assert "item" in types and "ability" in types and "meta" in types
    # Validate one of the payloads
    item_payloads = [e for e in dummy.executed if e["type"] == "item"]
    assert item_payloads[0]["params"]["item_id"] == "Q1"
