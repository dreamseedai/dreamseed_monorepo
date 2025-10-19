#!/usr/bin/env bash
set -euo pipefail

# Usage: DS_PG_DSN='postgres://user:pass@host:5432/db' scripts/db/verify_rls.sh

if [[ -z "${DS_PG_DSN:-}" ]]; then
  echo "Set DS_PG_DSN to a valid Postgres DSN" >&2
  exit 1
fi

echo "Verifying RLS helpers (seedtest.current_org_id) and SET LOCAL behavior..."

# 1) Check current_setting before any SET LOCAL
psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -c "SELECT current_setting('seedtest.org_id', true) AS org_setting_before, seedtest.current_org_id() AS current_org_id_before;"

# 2) In a transaction, SET LOCAL and verify visibility, then rollback to ensure no leakage
read -r -d '' SQL <<'EOSQL'
BEGIN;
  SET LOCAL seedtest.org_id = '123';
  SELECT current_setting('seedtest.org_id', true) AS org_setting_after_set,
         seedtest.current_org_id() AS current_org_id_after_set;
ROLLBACK; -- discard local setting
-- After rollback, the setting should be NULL/empty again
SELECT current_setting('seedtest.org_id', true) AS org_setting_after_tx,
       seedtest.current_org_id() AS current_org_id_after_tx;
EOSQL

psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -c "$SQL"

echo "RLS helper verification complete."
