from __future__ import annotations

"""
SeedTest API — End-to-End Smoke Test (in-process)

This script runs a tiny end-to-end flow using FastAPI's TestClient:
  1) Create a new exam session
  2) Iterate: fetch next question → submit an answer (dummy)
  3) Fetch the result (refresh=true)
  4) Optionally fetch the analysis payload

It requires no external server and runs in-process against the FastAPI app.
If a DATABASE_URL is provided and tables are present, the result is also
persisted; otherwise it operates in compute-only mode.

Exit code 0 on success; non-zero on failure.
"""

import json
import os
import sys
from typing import Any, Dict

from fastapi.testclient import TestClient


def _assert_keys(data: Dict[str, Any], keys: list[str]) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise AssertionError(f"Missing keys in response: {missing}")


def run_smoke(max_steps: int = 5, do_analysis: bool = True) -> None:
    # Local dev bypass for auth and stable contract for diff-friendly JSON
    os.environ.setdefault("LOCAL_DEV", "true")
    os.environ.setdefault("RESULT_EXCLUDE_TIMESTAMPS", "true")

    # Import app lazily to honor env
    from apps.seedtest_api.app.main import app

    client = TestClient(app)

    # 1) Create a session
    r = client.post("/api/seedtest/exams", json={"exam_id": "math_adaptive"})
    r.raise_for_status()
    sess = r.json()
    session_id = sess["exam_session_id"]

    # 2) Loop: get next and submit answers
    steps = 0
    while steps < max_steps:
        rr = client.get(f"/api/seedtest/exams/{session_id}/next")
        rr.raise_for_status()
        nx = rr.json()
        if bool(nx.get("done")):
            break
        q = (nx.get("question") or {})
        qid = q.get("id") or "1"
        payload = {"question_id": str(qid), "answer": "A", "elapsed_time": 1}
        sr = client.post(
            f"/api/seedtest/exams/{session_id}/response", json=payload
        )
        sr.raise_for_status()
        steps += 1

    # 3) Fetch result with refresh=true to ensure a response body
    res = client.get(f"/api/seedtest/exams/{session_id}/result", params={"refresh": True})
    res.raise_for_status()
    body = res.json()
    # Basic contract checks
    _assert_keys(
        body,
        [
            "exam_session_id",
            "user_id",
            "score",
            "score_detail",
            "ability_estimate",
            "standard_error",
            "percentile",
            "topic_breakdown",
            "recommendations",
            "status",
        ],
    )
    if str(body.get("status")).lower() != "ready":
        raise AssertionError(f"Unexpected status: {body.get('status')}")

    # 4) Optional analysis
    if do_analysis and os.getenv("ENABLE_ANALYSIS", "true").lower() == "true":
        ar = client.get(f"/api/seedtest/exams/{session_id}/analysis")
        if ar.status_code == 501:
            # Analysis disabled — acceptable
            pass
        else:
            ar.raise_for_status()
            a = ar.json()
            _assert_keys(a, ["exam_session_id", "ability", "topic_insights", "recommendations"])

    # Print compact JSON for CI logs
    print("RESULT:", json.dumps(body, ensure_ascii=False))


if __name__ == "__main__":
    try:
        run_smoke(max_steps=int(os.getenv("E2E_STEPS", "5")))
    except Exception as e:  # noqa: BLE001
        print(f"E2E_SMOKE_FAILED: {e}")
        sys.exit(1)
    sys.exit(0)
