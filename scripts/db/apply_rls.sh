#!/usr/bin/env bash
set -euo pipefail

: "${DS_PG_DSN:?DS_PG_DSN not set}"  # e.g. DS_PG_DSN="postgresql://user:pass@host:5432/db?sslmode=require"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SQL_FILE="$ROOT_DIR/db/rls/rls_policies.sql"

echo "[INFO] Applying RLS policies from $SQL_FILE"
psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -f "$SQL_FILE"

echo "[OK] RLS policies applied successfully"
#!/usr/bin/env bash
set -euo pipefail

: "${DS_PG_DSN:?DS_PG_DSN not set}"  # e.g. DS_PG_DSN="postgresql://user:pass@host:5432/db?sslmode=require"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SQL_FILE="$ROOT_DIR/db/rls/rls_policies.sql"

echo "[INFO] Applying RLS policies from $SQL_FILE"
psql "$DS_PG_DSN" -v ON_ERROR_STOP=1 -P pager=off -f "$SQL_FILE"

echo "[OK] RLS policies applied successfully"


