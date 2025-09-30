#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

# Offline mode SQL preview (no execution)
alembic upgrade head --sql > /tmp/alembic_dryrun_head.sql
echo "[dryrun] SQL written to /tmp/alembic_dryrun_head.sql"


