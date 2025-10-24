# Adaptive Demo Stop-Rule Tests

This folder includes integration tests for the FastAPI adaptive demo endpoints, focusing on termination criteria and timing controls.

## What’s covered
- Fixed-length termination by `CAT_MAX_ITEMS`
- Variable-length termination by SEM threshold `CAT_SEM_THRESHOLD`
- Server-enforced item cooldown `CAT_ITEM_COOLDOWN_SECONDS`
- Minimum test time gating for SEM-based stop `CAT_MIN_TEST_TIME_SECONDS`
- Manual finish (`finish_now`)
- Time limit stop `CAT_MAX_TIME_SECONDS`

## How it works
Tests use FastAPI’s `TestClient` and set environment variables via `monkeypatch.setenv(...)` per test, then `reload()` the settings module to apply them without impacting global runs.

## Key environment knobs
- `CAT_MODE`: `VARIABLE` or `FIXED`
- `CAT_SEM_THRESHOLD`: e.g., `0.30` to stop when SE ≤ threshold (VARIABLE mode)
- `CAT_MIN_ITEMS`: minimum items before SEM stop can apply
- `CAT_MAX_ITEMS`: hard cap for fixed or safety cap for variable
- `CAT_MAX_TIME_SECONDS`: end test when elapsed time ≥ limit
- `CAT_MIN_TEST_TIME_SECONDS`: gate SEM-based stop until at least this many seconds
- `CAT_ITEM_COOLDOWN_SECONDS`: defer next-item selection for this many seconds after an answer

## Running just these tests
```
pytest -q apps/seedtest_api/tests/test_adaptive_stop_rules.py
```

## Notes
- The adaptive demo is intentionally simple and uses an in-memory session store and a tiny item pool. In production, replace with durable storage and your full item bank.
- If timing-based tests are flaky in CI, modestly increase sleep amounts.
