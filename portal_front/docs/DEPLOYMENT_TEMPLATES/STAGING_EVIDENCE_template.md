# Staging Evidence — attempt VIEW V1 Lock

- PR: #73
- Env: Staging
- Executor: <name>
- Date: <YYYY-MM-DD>

## Commands / Outputs
- `alembic upgrade head`: OK / logs attached
- `pytest -k attempt_view_smoke -q`: <output>
- `SELECT count(*) FROM attempt;`: <value>
- Recent rows (5):
```
<copy rows>
```

## Downstream Sample
- Report query 1: OK / output attached
- Dashboard panel X: OK / screenshot attached

## Decision
- [ ] Approve for Prod
- Notes:
