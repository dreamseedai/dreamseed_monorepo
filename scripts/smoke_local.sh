#!/usr/bin/env bash
set -euo pipefail

echo "[Portal Front] http://localhost:5172"
curl -sI http://localhost:5172 | head -n1 || true

echo "[Portal API] http://127.0.0.1:8000/__ok (fallback :8010)"
curl -fsS http://127.0.0.1:8000/__ok || curl -fsS http://127.0.0.1:8010/__ok || echo "(not running)"


