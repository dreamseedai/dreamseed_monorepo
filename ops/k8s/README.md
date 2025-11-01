# ops/k8s/ - Kustomize Wrapper Directory

## 📋 Overview

This directory contains **wrapper kustomizations** that reference the actual Kubernetes manifests located in `portal_front/ops/k8s/`. 

These wrappers exist to satisfy CI validation matrix requirements while maintaining the canonical manifests in their original location.

## 🗂️ Directory Structure

```
ops/k8s/
├── README.md                           # This file
├── r-plumber/                          # R Plumber API wrapper
│   ├── kustomization.yaml              → ../../portal_front/ops/k8s/r-plumber
│   └── overlays/
│       └── internal/
│           └── kustomization.yaml      → ../../../../portal_front/ops/k8s/r-plumber/overlays/internal
├── r-irt-plumber/                      # R IRT Plumber wrapper
│   ├── kustomization.yaml              → ../../portal_front/ops/k8s/r-irt-plumber
│   └── overlays/
│       └── internal/
│           └── kustomization.yaml      → ../../../../portal_front/ops/k8s/r-irt-plumber/overlays/internal
└── cron/                               # Cron placeholder (V1 scope excludes cron workloads)
    ├── kustomization.yaml
    └── configmap.yaml                  # Placeholder ConfigMap for CI validation
```

## 🎯 Purpose

### Why Wrappers?

1. **CI Validation Matrix**: `.github/workflows/k8s-validate.yml` expects paths like:
   - `ops/k8s/r-plumber`
   - `ops/k8s/r-irt-plumber`
   - `ops/k8s/cron`

2. **Canonical Source**: Actual manifests live in `portal_front/ops/k8s/` for historical reasons and monorepo layout

3. **Single Source of Truth**: Wrappers use `resources:` to reference the canonical location, avoiding duplication

### Cron Placeholder

The `ops/k8s/cron/` directory contains only a placeholder `ConfigMap` because:
- **V1 Scope Constraint**: V1 phase excludes background cron workloads
- **CI Requirement**: Kustomize build must succeed for all matrix targets
- **Future-Ready**: Real cron manifests can be added here or in `portal_front/ops/k8s/cron/` when V2+ scope expands

## ⚙️ CI Workflows

### K8s Kustomize & Kubeconform Validate

```yaml
strategy:
  matrix:
    target:
      - ops/k8s/r-plumber
      - ops/k8s/r-plumber/overlays/internal
      - ops/k8s/r-irt-plumber
      - ops/k8s/r-irt-plumber/overlays/internal
      - ops/k8s/cron
```

**Validation Steps**:
1. `kustomize build <target>` → Renders final YAML
2. `kubeconform validate` → Schema validation (K8s v1.28.0 + CRDs)
3. `conftest test` → Policy validation (OPA Rego rules)
4. `kyverno apply` → Dry-run policy enforcement

## 📝 Maintenance Guidelines

### Adding New Targets

If CI matrix adds new targets (e.g., `ops/k8s/r-stats-service`):

1. **Option A**: Create wrapper at root
   ```bash
   mkdir -p ops/k8s/r-stats-service
   cat > ops/k8s/r-stats-service/kustomization.yaml <<EOF
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   resources:
     - ../../portal_front/ops/k8s/r-stats-service
   EOF
   ```

2. **Option B**: Move canonical manifests to root (breaking change)
   - Requires updating ArgoCD Application sources
   - Requires updating deployment scripts/runbooks
   - **Not recommended** unless major refactor

### Updating Manifests

**✅ DO**: Edit canonical manifests in `portal_front/ops/k8s/`

**❌ DON'T**: Edit wrapper `kustomization.yaml` files (they only contain `resources:` references)

### Scope Guard Alignment

If adding paths to `ops/` that fail `Scope Guard (V1)`:

1. Check `.github/workflows/scope-guard.yml` patterns:
   ```bash
   DENY_RE='^(ops/|infra/|...)'
   EXEMPT_RE='^(infra/pdf_lambda/|infra/nginx/|infra/k8s/cronjobs/|...)'
   ```

2. Add exemption if V1-relevant:
   ```bash
   EXEMPT_RE='^(...|ops/k8s/)'
   ```

3. Document justification in PR description

## 🔍 Troubleshooting

### "Error: unable to find one of 'kustomization.yaml'"

**Cause**: Missing wrapper or incorrect path reference

**Fix**:
```bash
# Verify canonical path exists
ls -la portal_front/ops/k8s/<target>/kustomization.yaml

# Verify wrapper reference
grep -A1 "resources:" ops/k8s/<target>/kustomization.yaml
```

### "Error: no matches for kind X in version Y"

**Cause**: CRD not available in kubeconform schema registry

**Fix**: Update `.github/workflows/k8s-validate.yml`:
```yaml
env:
  CRD_SCHEMA_REGISTRY: 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/...'
```

### CI fails after adding new overlay

**Checklist**:
- [ ] Wrapper path matches CI matrix target exactly
- [ ] Relative path `../../portal_front/ops/k8s/...` resolves correctly
- [ ] Canonical kustomization.yaml exists and is valid
- [ ] No circular references in overlay chain

## 📚 Related Documentation

- **Canonical Manifests**: `portal_front/ops/k8s/*/README.md` (if exists)
- **CI Workflows**: `.github/workflows/k8s-validate.yml`, `.github/workflows/policy-validate.yml`
- **Scope Guard**: `.github/workflows/scope-guard.yml`
- **ArgoCD Apps**: `ops/argocd/apps/` (if using GitOps)

## 🤝 Contributing

When modifying K8s resources:

1. **Edit canonical manifests** in `portal_front/ops/k8s/`
2. **Test locally** (if kustomize installed):
   ```bash
   kustomize build ops/k8s/r-plumber | kubeconform -
   ```
3. **Let CI validate** all matrix targets automatically
4. **Keep wrappers minimal** (only `apiVersion`, `kind`, `resources`)

---

**Last Updated**: 2025-10-31  
**Maintained by**: Platform Engineering Team  
**Scope**: V1 Phase (Student/Retake/TTFP workflows only)
