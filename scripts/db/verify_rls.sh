#!/usr/bin/env bash
set -euo pipefail
: "${DS_PG_DSN:?DS_PG_DSN not set}"

SQL=$(cat <<'SQL'
BEGIN;
SELECT current_setting('seedtest.org_id', true) AS before;
SET LOCAL seedtest.org_id = '123';
SELECT current_setting('seedtest.org_id', true) AS within_tx;
ROLLBACK;
SQL
)

echo "[INFO] Verifying SET LOCAL seedtest.org_id"
psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -c "$SQL"
