# Governance Deployment Runbook

## 📋 Current Configuration

**Deployment**: `seedtest-api`  
**Namespace**: `seedtest` (staging), `seedtest-prod` (production)  
**Container**: `seedtest-api`  
**Port**: 8000  
**GitOps**: ArgoCD (app-of-apps pattern)

---

## 🚀 Deployment & Validation

### 1. ArgoCD Auto-Sync Status

```bash
# Check ArgoCD app status
argocd app get seedtest-api-governance

# View resource tree (ConfigMap hash, ReplicaSet)
argocd app resources seedtest-api-governance

# Manual sync (if needed)
argocd app sync seedtest-api-governance
argocd app wait seedtest-api-governance --timeout 180
```

### 2. Cluster Verification

```bash
# ConfigMap created with hash
kubectl -n seedtest get cm | grep governance-bundles

# Deployment status
kubectl -n seedtest get deploy seedtest-api -o wide
kubectl -n seedtest describe deploy seedtest-api | sed -n '1,120p'

# ReplicaSet rollout
kubectl -n seedtest get rs -l app=seedtest-api
kubectl -n seedtest rollout status deploy/seedtest-api
```

### 3. Pod-Level Validation

```bash
# Get pod name
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')

# Check mounted files
kubectl -n seedtest exec $POD -- ls -1 /app/governance/compiled
# Expected: policy_bundle_phase0.json, policy_bundle_phase1.json, policy_bundle_prod.json

# Verify environment variables
kubectl -n seedtest exec $POD -- printenv | egrep 'POLICY_|GOVERNANCE_'
# Expected:
# POLICY_BUNDLE_ID=phase1
# GOVERNANCE_PHASE=1
# POLICY_STRICT_MODE=soft
# POLICY_BUNDLE_PATH=/app/governance/compiled/policy_bundle_phase1.json
# POLICY_HOT_RELOAD_ENABLED=true
```

### 4. Policy Endpoint Test

```bash
# Policy status
kubectl -n seedtest exec $POD -- curl -s http://localhost:8000/internal/policy/status

# Expected response:
# {
#   "bundle_id": "phase1",
#   "phase": 1,
#   "strict_mode": "soft",
#   "path": "/app/governance/compiled/policy_bundle_phase1.json",
#   "loaded": true
# }

# Hot reload test (after bundle update)
kubectl -n seedtest exec $POD -- curl -X POST http://localhost:8000/internal/policy/reload
```

---

## 🔄 Environment Promotion

### Staging → Production

**Option 1: Update ArgoCD Application Path**

Edit `infra/argocd/apps/internal/seedtest-api-governance.yaml`:

```yaml
spec:
  source:
    repoURL: https://github.com/dreamseedai/dreamseed_monorepo.git
    targetRevision: HEAD
    path: ops/k8s/governance/overlays/prod  # Changed from staging
  destination:
    namespace: seedtest-prod  # Production namespace
```

**Option 2: Create Separate Prod Application**

```bash
# Copy staging app
cp infra/argocd/apps/internal/seedtest-api-governance.yaml \
   infra/argocd/apps/internal/seedtest-api-governance-prod.yaml

# Edit:
# - metadata.name: seedtest-api-governance-prod
# - spec.source.path: ops/k8s/governance/overlays/prod
# - spec.destination.namespace: seedtest-prod
```

**Deploy Production**:

```bash
git add infra/argocd/apps/internal/seedtest-api-governance-prod.yaml
git commit -m "feat(governance): add production ArgoCD app"
git push origin feat/governance-production-ready

# Sync
argocd app sync seedtest-api-governance-prod
kubectl -n seedtest-prod rollout status deploy/seedtest-api
```

**Production Overlay Config** (`ops/k8s/governance/overlays/prod/kustomization.yaml`):
- Bundle: `prod`
- Phase: `2`
- Strict Mode: `enforce`
- Replicas: `5`
- Image Tag: `stable`
- Namespace: `seedtest-prod`

---

## 🛠️ Troubleshooting

### ArgoCD OutOfSync

```bash
argocd app sync seedtest-api-governance
argocd app wait seedtest-api-governance --timeout 180
```

### ConfigMap Created but No Pod Rollout

**Check hash suffix**:
```bash
kubectl -n seedtest get cm | grep governance-bundles
# Should show: governance-bundles-<hash>
```

**Verify `disableNameSuffixHash: false`** in `ops/k8s/governance/base/kustomization.yaml`.

**Manual rollout**:
```bash
kubectl -n seedtest rollout restart deploy/seedtest-api
```

### File Path Errors

**Verify mount path matches env**:
```bash
kubectl -n seedtest get deploy seedtest-api -o yaml | grep -A 5 "volumeMounts:"
kubectl -n seedtest get deploy seedtest-api -o yaml | grep "POLICY_BUNDLE_PATH"
```

### 403 Errors (Strict Mode)

**Temporarily lower enforcement**:

Edit overlay kustomization.yaml:
```yaml
- op: replace
  path: /spec/template/spec/containers/0/env/2/value
  value: "soft"  # Changed from "enforce"
```

**Check audit logs**:
```bash
kubectl -n seedtest logs -f deployment/seedtest-api | grep -i "policy.*deny"
```

---

## 🔙 Rollback Procedures

### 1. Rollback via Git Revert

```bash
# Find previous commit
git log --oneline ops/k8s/governance/base/compiled/

# Revert bundle change
git revert <commit-hash>
git push origin feat/governance-production-ready

# ArgoCD auto-syncs new ConfigMap hash → triggers rollout
```

### 2. Quick Bundle Switch

Edit overlay to point to previous bundle:

```yaml
# ops/k8s/governance/overlays/staging/kustomization.yaml
- op: replace
  path: /spec/template/spec/containers/0/env/0/value
  value: "phase0"  # Rollback to phase0
- op: replace
  path: /spec/template/spec/containers/0/env/3/value
  value: "/app/governance/compiled/policy_bundle_phase0.json"
```

```bash
git commit -am "rollback(governance): revert to phase0 bundle"
git push
argocd app sync seedtest-api-governance
```

### 3. ArgoCD History Rollback

```bash
# View history
argocd app history seedtest-api-governance

# Rollback to specific revision
argocd app rollback seedtest-api-governance <revision-number>
```

---

## 📊 Route → Action Mapping

### Standard Actions (from `policy_routes.py`)

| Route Pattern | HTTP Method | Action | Required Roles (phase1+) |
|---|---|---|---|
| `/api/v1/classes/*` | GET | `class:read` | all roles |
| `/api/v1/classes` | POST | `class:create` | admin, teacher |
| `/api/v1/students/*` | GET | `student:read` | all roles |
| `/api/v1/students` | POST | `student:create` | admin |
| `/api/v1/assignments/*` | GET | `assignment:read` | all roles |
| `/api/v1/assignments` | POST | `assignment:create` | admin, teacher (+ approval) |
| `/api/v1/assignment-templates/*` | GET | `assignment:template:read` | admin, teacher |
| `/api/v1/tutor/ask` | POST | `tutor:ask` | all roles (exam check) |
| `/api/v1/tutor/history` | GET | `tutor:read` | all roles |
| `/api/v1/risk/*` | GET | `risk:read` | admin (if risk_engine enabled) |
| `/internal/policy/*` | POST | `policy:write` | admin only |
| `/internal/audit/*` | GET | `audit:read` | admin only |
| `/api/seedtest/meta` | GET | `meta:read` | all roles |

### Phase Behavior

**Phase 0** (Observation):
- All roles: `*` (allow all)
- Audit logging enabled
- No blocking

**Phase 1** (RBAC Enforcement):
- Viewer: `class:read`, `student:read` only
- Teacher: + `assignment:create`, `assignment:template:read`, `tutor:read`
- Admin: all actions
- Strict mode: `soft` (log) or `enforce` (403)

**Phase 2** (Full Governance):
- + Content safety filtering
- + Teacher approval workflow for new content
- + Risk engine
- + Exam pipeline (tutor blocking)
- Strict mode: `enforce` (production)

---

## 🔍 One-Liner Validation

```bash
# Complete validation chain
argocd app sync seedtest-api-governance && \
kubectl -n seedtest rollout status deploy/seedtest-api && \
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}') && \
kubectl -n seedtest exec $POD -- ls -1 /app/governance/compiled && \
kubectl -n seedtest exec $POD -- printenv | egrep 'POLICY_|GOVERNANCE_' && \
kubectl -n seedtest exec $POD -- curl -s http://localhost:8000/internal/policy/status | jq
```

---

## 📝 Monitoring & Alerts

### Key Metrics

```bash
# ConfigMap change frequency
kubectl -n seedtest get events --field-selector involvedObject.kind=ConfigMap,involvedObject.name~=governance-bundles

# Deployment rollout history
kubectl -n seedtest rollout history deploy/seedtest-api

# Policy denial rate (if metrics exposed)
curl -s http://seedtest-api.seedtest.svc:9090/metrics | grep policy_deny_total
```

### Prometheus Queries

```promql
# Policy denials (if instrumented)
rate(policy_deny_total{namespace="seedtest"}[5m])

# ConfigMap reloads
kube_configmap_info{namespace="seedtest",configmap=~"governance-bundles-.*"}
```

---

## 🎯 Next Steps

1. **Initial Deployment**: ArgoCD auto-sync (2-5 min after push)
2. **Staging Validation**: 24-48h observation, review audit logs
3. **Production Promotion**: Switch to `prod` overlay with `enforce` mode
4. **Continuous Improvement**: Iterate on bundles based on audit patterns
5. **Hot Reload**: Update bundles → git push → auto-rollout via ConfigMap hash

**Contact**: Platform Team / #governance-alerts Slack channel
