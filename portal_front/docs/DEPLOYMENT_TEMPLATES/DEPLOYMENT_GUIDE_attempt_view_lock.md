# Deployment Guide — attempt VIEW V1 Lock

Environments: Staging → Production
Owners: Backend, DevOps

## Prereqs
- CI green (Kustomize/Kubeconform, Kyverno/Conftest, tests)
- PR approved (#73)

## Staging (6 steps)
1. DB backup (optional)
2. Alembic upgrade
   - `alembic upgrade head`
3. Smoke tests
   - `pytest -k attempt_view_smoke -q`
   - `SELECT count(*) FROM attempt;`
   - `SELECT * FROM attempt ORDER BY completed_at DESC LIMIT 5;`
4. Downstream checks
   - ETL / Reports / Dashboards sample queries
5. Evidence
   - Attach outputs/screenshots/logs to PR #73
6. Approve for Prod (create Change Request)

## Production
- Maintenance window and CR approval
- Repeat steps (upgrade → smoke → downstream)
- 24h monitoring (API/ETL errors, query latency)

## Rollback
- `alembic downgrade <down_revision_of_view>`
- Re-validate downstream
