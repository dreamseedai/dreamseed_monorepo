# Database RLS Scripts

This folder contains helper scripts to apply, verify, and rollback Row-Level Security (RLS) for the seedtest schema/tables.

Requirements:
- Environment variable DS_PG_DSN set to a valid Postgres DSN. Example: postgres://user:pass@host:5432/db
- psql available in PATH

Scripts:
- apply_rls.sh: Applies helpers and policies from db/rls/rls_policies.sql
- verify_rls.sh: Sanity-checks seedtest.current_org_id and SET LOCAL behavior
- rollback_rls.sh: Disables RLS and drops policies (optional)

Typical flow:
1) export DS_PG_DSN=postgres://user:pass@host:5432/db
2) scripts/db/apply_rls.sh
3) scripts/db/verify_rls.sh
4) If needed, scripts/db/rollback_rls.sh

Notes:
- The application should set SET LOCAL seedtest.org_id per request/transaction; see apps/seedtest_api/rls_context.py
- If using PgBouncer in transaction pooling mode, ensure SET LOCAL occurs within the same transaction as the query workload.