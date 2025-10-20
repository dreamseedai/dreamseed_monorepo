#!/usr/bin/env bash
set -euo pipefail

# Usage: DS_PG_DSN='postgres://user:pass@host:5432/db' scripts/db/rollback_rls.sh

if [[ -z "${DS_PG_DSN:-}" ]]; then
  echo "Set DS_PG_DSN to a valid Postgres DSN" >&2
  exit 1
fi

read -r -d '' SQL <<'EOSQL'
-- Disable RLS quickly (emergency)
ALTER TABLE IF EXISTS attempts DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS responses DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS item_bank DISABLE ROW LEVEL SECURITY;

-- Optional: drop policies
DROP POLICY IF EXISTS attempts_policy_read ON attempts;
DROP POLICY IF EXISTS attempts_policy_insert ON attempts;
DROP POLICY IF EXISTS attempts_policy_update ON attempts;
DROP POLICY IF EXISTS responses_policy_read ON responses;
DROP POLICY IF EXISTS responses_policy_insert ON responses;
DROP POLICY IF EXISTS responses_policy_update ON responses;
DROP POLICY IF EXISTS item_bank_policy_read ON item_bank;
DROP POLICY IF EXISTS item_bank_policy_insert ON item_bank;
DROP POLICY IF EXISTS item_bank_policy_update ON item_bank;
EOSQL

echo "Rolling back RLS policies..."
psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -c "$SQL"
echo "Done."
#!/usr/bin/env bash
set -euo pipefail

# Usage: DS_PG_DSN='postgres://user:pass@host:5432/db' scripts/db/rollback_rls.sh

if [[ -z "${DS_PG_DSN:-}" ]]; then
  echo "Set DS_PG_DSN to a valid Postgres DSN" >&2
  exit 1
fi

read -r -d '' SQL <<'EOSQL'
-- Disable RLS quickly (emergency)
ALTER TABLE IF EXISTS attempts DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS responses DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS item_bank DISABLE ROW LEVEL SECURITY;

-- Optional: drop policies
DROP POLICY IF EXISTS attempts_policy_read ON attempts;
DROP POLICY IF EXISTS attempts_policy_write ON attempts;
DROP POLICY IF EXISTS responses_policy_read ON responses;
DROP POLICY IF EXISTS responses_policy_write ON responses;
DROP POLICY IF EXISTS item_bank_policy_read ON item_bank;
DROP POLICY IF EXISTS item_bank_policy_write ON item_bank;
EOSQL

echo "Rolling back RLS policies..."
psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -c "$SQL"
echo "Done."


