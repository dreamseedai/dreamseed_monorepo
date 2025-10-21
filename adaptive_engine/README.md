# Adaptive Testing Engine (FastAPI)

Minimal FastAPI app exposing adaptive test session endpoints: start, next, answer, finish.

## Quickstart

1. Create venv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install fastapi uvicorn numpy
# Optional (settings/env + Redis session backend)
pip install pydantic-settings redis
```

2. Run server

```bash
uvicorn adaptive_engine.main:app --reload --port 8008
```

3. Open docs

- http://localhost:8008/docs

## Endpoints

- POST /api/exam/start
- POST /api/exam/next
- POST /api/exam/answer
- POST /api/exam/finish
- GET /api/settings/selection
- PATCH /api/settings/selection
- DELETE /api/settings/selection  # reset to env defaults (also clears Redis cache)
- POST /api/settings/selection/reset-to-env  # alias to reset to env defaults
- GET /api/settings  # effective settings snapshot
- GET /api/health/redis

## Notes

- This is a lightweight scaffold intended for iteration inside the monorepo.
- Replace the heuristics with your production IRT and selection logic as needed.
- On startup, if ADAPTIVE_SESSION_BACKEND=redis but Redis isn't reachable, the app logs and falls back to memory.

## Settings (env)

Environment variables (prefix ADAPTIVE_):

- ADAPTIVE_SESSION_BACKEND: memory | redis (default: memory)
- ADAPTIVE_REDIS_URL: redis://localhost:6379/0
- ADAPTIVE_REDIS_KEY_PREFIX: "adaptive:" (prefix for keys, useful for multi-tenant isolation)
- ADAPTIVE_SESSION_TTL_SEC: 86400
- ADAPTIVE_SELECTION_PREFER_BALANCED: true/false
- ADAPTIVE_SELECTION_DETERMINISTIC: false/true
- ADAPTIVE_SELECTION_MAX_PER_TOPIC: integer
- ADAPTIVE_SELECTION_POLICY_TTL_SEC: TTL for persisted selection policy (seconds). If set, the policy auto-expires and falls back to env.

You can also GET/PATCH selection policy at runtime via /api/settings/selection. When Redis is configured, the policy is persisted (best-effort) so multiple instances share overrides.
