#!/usr/bin/env bash
set -euo pipefail

# One-shot helper to spin up local Postgres via Docker Compose, run Alembic, then pytest.
# Usage:
#   apps/seedtest_api/scripts/dev_db_test.sh [pytest-args...]
#
# Defaults to running the listing auth smoke tests if no args are provided.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"            # apps/seedtest_api
REPO_ROOT="$(cd "${PKG_DIR}/../.." && pwd)"          # repo root
COMPOSE_FILE="${REPO_ROOT}/docker-compose.db.yml"

# Allow overriding the host port via DB_PORT (default 5432)
export DB_PORT="${DB_PORT:-5432}"

DB_DSN="postgresql+psycopg2://user:pass@127.0.0.1:${DB_PORT}/dreamseed_db"
export DATABASE_URL="${DATABASE_URL:-$DB_DSN}"

echo "[dev-db-test] Using DATABASE_URL=${DATABASE_URL}"

echo "[dev-db-test] Checking if database is already reachable..."
SHOULD_START_DB=1
if ${PY_BIN:-python3} - <<'PY'
import os, sys
import psycopg2
dsn = os.environ.get("DATABASE_URL")
if dsn and dsn.startswith("postgresql+psycopg2://"):
    dsn = "postgresql://" + dsn.split("postgresql+psycopg2://",1)[1]
try:
    psycopg2.connect(dsn).close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
then
  echo "[dev-db-test] DB reachable, will not start docker compose."
  SHOULD_START_DB=0
fi

if [[ ${SHOULD_START_DB} -eq 1 ]]; then
  echo "[dev-db-test] Bringing up Postgres via docker compose (DB_PORT=${DB_PORT})..."
  set +e
  docker compose -f "${COMPOSE_FILE}" up -d db
  DC_RC=$?
  set -e
  if [[ ${DC_RC} -ne 0 ]]; then
    echo "[dev-db-test] docker compose up failed (rc=${DC_RC}). Checking if a DB is already running on ${DATABASE_URL}..."
    if ${PY_BIN:-python3} - <<'PY'
import os, sys
import psycopg2
dsn = os.environ.get("DATABASE_URL")
if dsn and dsn.startswith("postgresql+psycopg2://"):
    dsn = "postgresql://" + dsn.split("postgresql+psycopg2://",1)[1]
try:
    psycopg2.connect(dsn).close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
    then
      echo "[dev-db-test] Existing DB detected; continuing without compose."
    else
      echo "[dev-db-test] No reachable DB and compose failed. Ensure port ${DB_PORT} is free, set DB_PORT to an open port, or override DATABASE_URL to your running DB." >&2
      exit 1
    fi
  fi
fi

# Pick a Python to use (prefer package venv)
PY_BIN="python3"
if [[ -x "${PKG_DIR}/.venv/bin/python" ]]; then
  PY_BIN="${PKG_DIR}/.venv/bin/python"
fi

echo "[dev-db-test] Waiting for database to accept connections..."
ATTEMPTS=0
until "${PY_BIN}" - <<'PY'
import os, sys, time
import psycopg2
from urllib.parse import urlparse

dsn = os.environ.get("DATABASE_URL")
if not dsn:
    sys.exit(1)
try:
    # psycopg2 doesn't understand +psycopg2 scheme; strip suffix
    if dsn.startswith("postgresql+psycopg2://"):
        dsn = "postgresql://" + dsn.split("postgresql+psycopg2://",1)[1]
    conn = psycopg2.connect(dsn)
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(2)
PY
do
  ATTEMPTS=$((ATTEMPTS+1))
  if [[ ${ATTEMPTS} -ge 60 ]]; then
    echo "[dev-db-test] Timed out waiting for DB after ${ATTEMPTS} attempts" >&2
    exit 1
  fi
  sleep 1
done

echo "[dev-db-test] Ensuring alembic_version.version_num can hold long revision ids..."
"${PY_BIN}" - <<'PY'
import os
import psycopg2

dsn = os.environ.get("DATABASE_URL")
if dsn and dsn.startswith("postgresql+psycopg2://"):
  dsn = "postgresql://" + dsn.split("postgresql+psycopg2://",1)[1]

try:
  with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
      # Attempt to widen regardless; ignore failures if table/column doesn't exist
      try:
        cur.execute("ALTER TABLE IF EXISTS alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
        conn.commit()
      except Exception:
        conn.rollback()
      # If table does not exist yet, create it with proper column type so Alembic uses it
      try:
        cur.execute("""
          CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(128) NOT NULL
          )
        """)
        conn.commit()
      except Exception:
        conn.rollback()
except Exception:
  # If connection fails here, the readiness loop above would have already errored
  pass
PY

echo "[dev-db-test] Applying Alembic migrations..."
pushd "${PKG_DIR}" >/dev/null
"${PY_BIN}" -m alembic upgrade head

echo "[dev-db-test] Running pytest..."
if [[ $# -eq 0 ]]; then
  # default to listing auth smoke tests
  TEST_PATHS=("apps/seedtest_api/tests/test_results_list_auth.py")
else
  TEST_PATHS=("$@")
fi

# Ensure import path resolves when run from repo root
export PYTHONPATH="${REPO_ROOT}/apps:${PYTHONPATH:-}"

popd >/dev/null

# Run from repo root to mirror CI layout
cd "${REPO_ROOT}"
"${PY_BIN}" -m pytest -q "${TEST_PATHS[@]}"
