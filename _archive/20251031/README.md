# Archive 2025-10-31

This folder contains code paths archived under the V1 Guardrails cleanup.

Moved items:
- ops/k8s/ -> _archive/20251031/ops_k8s/

Reason:
- Out-of-scope for Tutor V1 (operational automation and cluster configs)
- Scope Guard enforces this path to be non-modifiable during V1

Rollback:
- `git mv _archive/20251031/ops_k8s ops/k8s`

Notes:
- See .github/PULL_REQUEST_TEMPLATE_DELETE.md for standard checklist when creating the archive PR.
