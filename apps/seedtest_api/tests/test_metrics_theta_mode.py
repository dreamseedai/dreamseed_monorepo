from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List

import pytest
from seedtest_api.services import metrics as metrics_svc
from seedtest_api.services.metrics import Attempt, compute_improvement_index


def _attempts(n: int) -> List[Attempt]:
    now = datetime(2025, 1, 20, tzinfo=timezone.utc)
    return [Attempt(None, None, True, now, None, None, None, None) for _ in range(n)]


def test_theta_mode_improvement_with_flag(monkeypatch):
    monkeypatch.setenv("METRICS_USE_IRT_THETA", "true")

    # Ensure enough exposure
    monkeypatch.setattr(metrics_svc, "load_attempts", lambda *a, **k: _attempts(10))

    seq = [(-0.1, 0.1), (0.2, 0.1)]

    def fake_latest(session, user_id, start_d, end_d):
        return seq.pop(0) if seq else (0.0, 0.1)

    monkeypatch.setattr(metrics_svc, "_latest_theta_in_window", fake_latest)

    r = compute_improvement_index(None, "U1", date(2025, 1, 20), window_days=14)  # type: ignore[arg-type]
    assert r is not None and r > 0


def test_theta_mode_gated_by_exposure(monkeypatch):
    monkeypatch.setenv("METRICS_USE_IRT_THETA", "true")
    # No exposure -> skip theta, fallback yields None
    monkeypatch.setattr(metrics_svc, "load_attempts", lambda *a, **k: [])
    r = compute_improvement_index(None, "U1", date(2025, 1, 20), window_days=14)  # type: ignore[arg-type]
    assert r is None
