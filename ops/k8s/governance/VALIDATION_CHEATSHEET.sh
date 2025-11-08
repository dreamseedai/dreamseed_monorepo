#!/usr/bin/env bash
# Governance Deployment Validation Cheat Sheet
# Usage: bash ops/k8s/governance/VALIDATION_CHEATSHEET.sh [staging|prod]

set -euo pipefail

OVERLAY="${1:-staging}"
NAMESPACE="seedtest"
APP_NAME="seedtest-api-governance"
DEPLOY_NAME="seedtest-api"

if [[ "$OVERLAY" == "prod" ]]; then
  NAMESPACE="seedtest-prod"
fi

echo "🚀 Governance Deployment Validation - ${OVERLAY} environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. ArgoCD Sync
echo ""
echo "1️⃣  ArgoCD Sync"
echo "   argocd app sync ${APP_NAME}"
echo "   argocd app wait ${APP_NAME} --timeout 180"

# 2. ConfigMap Check
echo ""
echo "2️⃣  ConfigMap Verification"
echo "   kubectl -n ${NAMESPACE} get cm | grep governance-bundles"
echo ""
kubectl -n ${NAMESPACE} get cm 2>/dev/null | grep governance-bundles || echo "   ⚠️  ConfigMap not found (run sync first)"

# 3. Rollout Status
echo ""
echo "3️⃣  Deployment Rollout"
echo "   kubectl -n ${NAMESPACE} rollout status deploy/${DEPLOY_NAME}"
echo ""
kubectl -n ${NAMESPACE} get deploy ${DEPLOY_NAME} -o wide 2>/dev/null || echo "   ⚠️  Deployment not found"

# 4. ReplicaSet
echo ""
echo "4️⃣  ReplicaSet (check for new revision)"
echo "   kubectl -n ${NAMESPACE} get rs -l app=${DEPLOY_NAME}"
echo ""
kubectl -n ${NAMESPACE} get rs -l app=${DEPLOY_NAME} 2>/dev/null || echo "   ⚠️  ReplicaSet not found"

# 5. Pod Validation
echo ""
echo "5️⃣  Pod-Level Validation"
POD=$(kubectl -n ${NAMESPACE} get pod -l app=${DEPLOY_NAME} -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [[ -z "$POD" ]]; then
  echo "   ⚠️  No pods found for app=${DEPLOY_NAME}"
else
  echo "   Pod: ${POD}"
  echo ""
  
  echo "   📁 Mounted Files:"
  echo "      kubectl -n ${NAMESPACE} exec ${POD} -- ls -1 /app/governance/compiled"
  kubectl -n ${NAMESPACE} exec ${POD} -- ls -1 /app/governance/compiled 2>/dev/null || echo "      ⚠️  Mount path not accessible"
  
  echo ""
  echo "   🔧 Environment Variables:"
  echo "      kubectl -n ${NAMESPACE} exec ${POD} -- printenv | egrep 'POLICY_|GOVERNANCE_'"
  kubectl -n ${NAMESPACE} exec ${POD} -- printenv 2>/dev/null | egrep 'POLICY_|GOVERNANCE_' || echo "      ⚠️  Env vars not found"
  
  echo ""
  echo "   🩺 Policy Status Endpoint:"
  echo "      kubectl -n ${NAMESPACE} exec ${POD} -- curl -s http://localhost:8000/internal/policy/status"
  kubectl -n ${NAMESPACE} exec ${POD} -- curl -s http://localhost:8000/internal/policy/status 2>/dev/null | head -5 || echo "      ⚠️  Endpoint not reachable"
fi

# 6. Declarative Verification (local)
echo ""
echo "6️⃣  Declarative Config Verification (local)"
echo "   yq '.spec.template.spec.containers[0].env[] | select(.name==\"POLICY_BUNDLE_PATH\").value' \\"
echo "     ops/k8s/governance/overlays/${OVERLAY}/kustomization.yaml"

# 7. Quick Rollback Commands
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔙 Quick Rollback Commands:"
echo ""
echo "   # Rollback to previous version"
echo "   kubectl -n ${NAMESPACE} rollout undo deploy/${DEPLOY_NAME}"
echo ""
echo "   # Set strict mode to soft (emergency)"
echo "   kubectl -n ${NAMESPACE} set env deploy/${DEPLOY_NAME} POLICY_STRICT_MODE=soft"
echo ""
echo "   # Restart deployment (force reload)"
echo "   kubectl -n ${NAMESPACE} rollout restart deploy/${DEPLOY_NAME}"

# 8. Production Promotion
if [[ "$OVERLAY" == "staging" ]]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🚀 Production Promotion:"
  echo ""
  echo "   # Edit ArgoCD app to point to prod overlay"
  echo "   vi infra/argocd/apps/internal/seedtest-api-governance.yaml"
  echo "   # Change: path: ops/k8s/governance/overlays/prod"
  echo ""
  echo "   git commit -am 'feat(governance): promote to production'"
  echo "   git push origin feat/governance-production-ready"
  echo ""
  echo "   argocd app sync ${APP_NAME}"
fi

echo ""
echo "✅ Validation complete!"
