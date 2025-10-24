#!/usr/bin/env bash
set -euo pipefail

# Env Audit Script: verifies GCP ↔ Repo Vars ↔ GKE/WIF alignment
# Requirements: gcloud, kubectl (optional for deeper checks)

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; NC='\033[0m'
warn() { echo -e "${YEL}[WARN]${NC} $*" >&2; }
info() { echo -e "${GRN}[INFO]${NC} $*"; }
err()  { echo -e "${RED}[ERR ]${NC} $*" >&2; }

# Collect inputs (fallbacks for local runs)
: "${GCP_PROJECT_ID:=$(gcloud config get-value project 2>/dev/null || echo '')}"
: "${GKE_CLUSTER:=${GKE_CLUSTER:-}}"
: "${GKE_LOCATION:=${GKE_LOCATION:-}}"
: "${GCP_WIF_SERVICE_ACCOUNT:=${GCP_WIF_SERVICE_ACCOUNT:-}}"
: "${GCP_WORKLOAD_IDENTITY_PROVIDER:=${GCP_WORKLOAD_IDENTITY_PROVIDER:-}}"
: "${GCP_WIF_PROVIDER:=${GCP_WIF_PROVIDER:-}}"

# Normalize provider alias for local runs
if [[ -z "${GCP_WORKLOAD_IDENTITY_PROVIDER}" && -n "${GCP_WIF_PROVIDER}" ]]; then
  GCP_WORKLOAD_IDENTITY_PROVIDER="$GCP_WIF_PROVIDER"
fi

# Try to auto-detect cluster/location if missing (best-effort)
if [[ -z "${GKE_CLUSTER}" ]]; then
  GKE_CLUSTER=$(gcloud container clusters list --format='value(name)' | head -n1 || true)
fi
if [[ -z "${GKE_LOCATION}" && -n "${GKE_CLUSTER}" ]]; then
  GKE_LOCATION=$(gcloud container clusters list --filter="name=${GKE_CLUSTER}" --format='value(location)' || true)
fi

# Begin summary file
SUMMARY=audit-summary.md
: > "$SUMMARY"

fail_count=0

section() {
  echo "" | tee -a "$SUMMARY"
  echo "### $1" | tee -a "$SUMMARY"
}

check_var() {
  local name="$1" val="${!1:-}"
  if [[ -z "$val" ]]; then
    warn "$name is not set"
    echo "- $name: MISSING" >> "$SUMMARY"
    ((fail_count++))
  else
    info "$name=$val"
    echo "- $name: $val" >> "$SUMMARY"
  fi
}

section "Repo Variables (and autodetected)"
check_var GCP_PROJECT_ID
check_var GKE_CLUSTER
check_var GKE_LOCATION
check_var GCP_WIF_SERVICE_ACCOUNT
check_var GCP_WORKLOAD_IDENTITY_PROVIDER

# If project is missing, cloud checks will fail; continue gracefully
if [[ -z "$GCP_PROJECT_ID" ]]; then
  warn "GCP_PROJECT_ID missing; skipping cloud checks."
  echo "\nAudit finished with missing variables. See above." | tee -a "$SUMMARY"
  exit 1
fi

section "Enabled APIs"
required=(
  container.googleapis.com
  iamcredentials.googleapis.com
  sts.googleapis.com
  artifactregistry.googleapis.com
  secretmanager.googleapis.com
)

enabled=$(gcloud services list --enabled --project "$GCP_PROJECT_ID" --format='value(config.name)' || true)
for svc in "${required[@]}"; do
  if ! grep -qx "$svc" <<<"$enabled"; then
    err "API not enabled: $svc"
    echo "- $svc: NOT ENABLED" >> "$SUMMARY"
    ((fail_count++))
  else
    info "API enabled: $svc"
    echo "- $svc: enabled" >> "$SUMMARY"
  fi
done

section "GKE Cluster"
if [[ -z "$GKE_CLUSTER" || -z "$GKE_LOCATION" ]]; then
  warn "Cluster name/location missing; skipping cluster checks."
  echo "- cluster or location missing" >> "$SUMMARY"
  ((fail_count++))
else
  # Try region first, then zone
  if ! gcloud container clusters describe "$GKE_CLUSTER" --region="$GKE_LOCATION" --project="$GCP_PROJECT_ID" >/dev/null 2>&1; then
    if ! gcloud container clusters describe "$GKE_CLUSTER" --zone="$GKE_LOCATION" --project="$GCP_PROJECT_ID" >/dev/null 2>&1; then
      err "Cluster not found or inaccessible: $GKE_CLUSTER ($GKE_LOCATION)"
      echo "- cluster describe: FAILED" >> "$SUMMARY"
      ((fail_count++))
    else
      info "Cluster accessible via zone: $GKE_CLUSTER ($GKE_LOCATION)"
      echo "- cluster describe (zone): ok" >> "$SUMMARY"
    fi
  else
    info "Cluster accessible via region: $GKE_CLUSTER ($GKE_LOCATION)"
    echo "- cluster describe (region): ok" >> "$SUMMARY"
  fi

  # Try kube auth (best-effort)
  set +e
  gcloud container clusters get-credentials "$GKE_CLUSTER" --region="$GKE_LOCATION" --project="$GCP_PROJECT_ID" 2>/dev/null || \
  gcloud container clusters get-credentials "$GKE_CLUSTER" --zone="$GKE_LOCATION" --project="$GCP_PROJECT_ID" 2>/dev/null
  kubectl get ns seedtest >/dev/null 2>&1
  if [[ $? -eq 0 ]]; then
    info "kubectl access OK"
    echo "- kubectl access: ok" >> "$SUMMARY"
  else
    warn "kubectl access failed (may be expected if RBAC restricted)"
    echo "- kubectl access: failed" >> "$SUMMARY"
  fi
  set -e
fi

section "WIF bindings"
if [[ -z "$GCP_WIF_SERVICE_ACCOUNT" || -z "$GCP_WORKLOAD_IDENTITY_PROVIDER" ]]; then
  warn "WIF variables missing; skipping WIF checks."
  echo "- WIF check: skipped (vars missing)" >> "$SUMMARY"
  ((fail_count++))
else
  if gcloud iam service-accounts describe "$GCP_WIF_SERVICE_ACCOUNT" --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
    info "Service Account exists: $GCP_WIF_SERVICE_ACCOUNT"
    echo "- SA exists: yes" >> "$SUMMARY"
  else
    err "Service Account missing: $GCP_WIF_SERVICE_ACCOUNT"
    echo "- SA exists: NO" >> "$SUMMARY"
    ((fail_count++))
  fi

  # Smarter WIF binding detection
  # Normalize provider to pool path (strip trailing /providers/<provider>)
  POOL_PATH="$GCP_WORKLOAD_IDENTITY_PROVIDER"
  if [[ "$POOL_PATH" == *"/providers/"* ]]; then
    POOL_PATH="${POOL_PATH%%/providers/*}"
  fi

  OWNER_REPO_VAL="${OWNER_REPO:-${GITHUB_REPOSITORY:-}}"

  POL_JSON=$(gcloud iam service-accounts get-iam-policy "$GCP_WIF_SERVICE_ACCOUNT" --project "$GCP_PROJECT_ID" --format=json || echo '{}')
  # Attempt jq parsing; if jq missing, fallback to simple grep logic
  if command -v jq >/dev/null 2>&1; then
    MEMBERS=$(echo "$POL_JSON" | jq -r '.bindings[]? | select(.role=="roles/iam.workloadIdentityUser") | .members[]?')
  else
    MEMBERS=$(echo "$POL_JSON" | sed -n 's/.*"members":\s*\[\(.*\)\].*/\1/p' | tr -d '[]" ' | tr ',' '\n')
  fi

  if [[ -z "$MEMBERS" ]]; then
    err "WIF binding missing: roles/iam.workloadIdentityUser not found"
    echo "- WIF binding: MISSING" >> "$SUMMARY"
    ((fail_count++))
  else
    pass=""
    # Escape slashes for regex
    POOL_ESC=$(echo "$POOL_PATH" | sed 's/[\/\.^$*[]/\\&/g')
    if echo "$MEMBERS" | grep -Eq "^principal://iam.googleapis.com/.*/workloadIdentityPools/${POOL_ESC}/subject/"; then
      pass="yes"
    fi
    if [[ -z "$pass" && -n "$OWNER_REPO_VAL" ]]; then
      OR_ESC=$(echo "$OWNER_REPO_VAL" | sed 's/[\/\.^$*[]/\\&/g')
      if echo "$MEMBERS" | grep -Eq "^principalSet://iam.googleapis.com/.*/workloadIdentityPools/${POOL_ESC}/attribute\.repository/${OR_ESC}$"; then
        pass="yes"
      fi
    fi
    # Lenient fallback: attribute.repository match anywhere
    if [[ -z "$pass" && -n "$OWNER_REPO_VAL" ]]; then
      OR_ESC2=$(echo "$OWNER_REPO_VAL" | sed 's/[\/\.^$*[]/\\&/g')
      if echo "$MEMBERS" | grep -Eq "attribute\.repository/${OR_ESC2}$"; then
        warn "WIF binding matches attribute.repository but pool path not strictly matched; treating as PASS"
        pass="yes"
      fi
    fi

    if [[ -n "$pass" ]]; then
      info "WIF binding present (iam.workloadIdentityUser with pool/subject or attribute.repository)"
      echo "- WIF binding: present" >> "$SUMMARY"
    else
      err "WIF binding present but provider/pool did not match expected patterns"
      echo "- WIF binding: MISMATCH" >> "$SUMMARY"
      # For debugging, print members
      echo "$MEMBERS" | sed 's/^/  member: /'
      ((fail_count++))
    fi
  fi
fi

section "Result"
if [[ $fail_count -eq 0 ]]; then
  info "Audit PASSED"
  echo "All checks passed." >> "$SUMMARY"
  exit 0
else
  err "Audit FAILED with $fail_count issue(s)"
  echo "$fail_count issue(s) found. See details above." >> "$SUMMARY"
  exit 1
fi
