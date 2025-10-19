#!/usr/bin/env bash
set -euo pipefail

# Usage: DS_PG_DSN='postgres://user:pass@host:5432/db' scripts/db/apply_rls.sh

if [[ -z "${DS_PG_DSN:-}" ]]; then
  echo "Set DS_PG_DSN to a valid Postgres DSN" >&2
  exit 1
fi

echo "Applying RLS helpers and policies..."
psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -f db/rls/rls_policies.sql
echo "Done."


