#!/usr/bin/env bash
# Apply branch protection based on environment and tag rules
# - default branch (e.g., main): production checks
# - release/*: staging checks
# - feature/*: base checks
# Supports dry-run, parallel execution, and updater options (reviews/enforce/strict)
# Requires: gh CLI admin access; jq
# Usage: ./scripts/gh_apply_branch_protection_env.sh <owner> <repo> \
#   --prod-checks "check1,check2" --staging-checks "check3,check4" --base-checks "check5,check6" \
#   [--reviews N] [--enforce-admins true|false] [--strict true|false] [--parallel N] [--dry-run]
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <owner> <repo> --prod-checks <csv> --staging-checks <csv> --base-checks <csv>"
  exit 1
fi

OWNER="$1"; shift
REPO="$1"; shift

PROD_CHECKS=""; STAGING_CHECKS=""; BASE_CHECKS=""
REQUIRED_REVIEWS=1
ENFORCE_ADMINS=true
STRICT_CHECKS=true
PARALLEL=2
DRY_RUN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod-checks) PROD_CHECKS="$2"; shift 2 ;;
    --staging-checks) STAGING_CHECKS="$2"; shift 2 ;;
    --base-checks) BASE_CHECKS="$2"; shift 2 ;;
    --reviews) REQUIRED_REVIEWS="$2"; shift 2 ;;
    --enforce-admins) ENFORCE_ADMINS="$2"; shift 2 ;;
    --strict) STRICT_CHECKS="$2"; shift 2 ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then echo "gh is required" >&2; exit 1; fi
if ! command -v jq >/dev/null 2>&1; then echo "jq is required" >&2; exit 1; fi

UPDATER="$(dirname "$0")/gh_branch_protection_update.sh"
apply() {
  local branch="$1" checks="$2"
  echo "Applying checks [$checks] to $branch"
  local common=("$UPDATER" "$OWNER" "$REPO" "$branch" "$checks" --reviews "$REQUIRED_REVIEWS" --enforce-admins "$ENFORCE_ADMINS" --strict "$STRICT_CHECKS")
  if [[ "$DRY_RUN" == "true" ]]; then
    bash "${common[@]}" --dry-run || echo "[DRY-RUN] Failed (simulated) to apply to $branch" >&2
  else
    bash "${common[@]}" || echo "Failed to apply to $branch" >&2
  fi
}

# Determine default branch (fallback to main)
DEFAULT_BRANCH=$(gh repo view "$OWNER/$REPO" --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main)

# Fetch all branches with pagination
BRANCH_JSON=$(gh api --paginate -H "Accept: application/vnd.github+json" "/repos/$OWNER/$REPO/branches?per_page=100" 2>/dev/null || true)
mapfile -t ALL_BRANCHES < <(echo "$BRANCH_JSON" | jq -r -s 'map(.[]?.name)[]' 2>/dev/null || true)

# Build targets as branch|checks pairs
declare -a TARGETS=()
if [[ -n "$PROD_CHECKS" ]]; then TARGETS+=("$DEFAULT_BRANCH|$PROD_CHECKS"); fi
if [[ -n "$STAGING_CHECKS" && ${#ALL_BRANCHES[@]} -gt 0 ]]; then
  for b in "${ALL_BRANCHES[@]}"; do [[ "$b" == release/* ]] && TARGETS+=("$b|$STAGING_CHECKS"); done
fi
if [[ -n "$BASE_CHECKS" && ${#ALL_BRANCHES[@]} -gt 0 ]]; then
  for b in "${ALL_BRANCHES[@]}"; do [[ "$b" == feature/* ]] && TARGETS+=("$b|$BASE_CHECKS"); done
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "No target branches matched or no checks provided." >&2
  exit 0
fi

export -f apply
export UPDATER OWNER REPO REQUIRED_REVIEWS ENFORCE_ADMINS STRICT_CHECKS DRY_RUN
printf '%s\n' "${TARGETS[@]}" | xargs -r -P "$PARALLEL" -I {} bash -c '
  set -euo pipefail
  IFS="|" read -r BR CHK <<< "$1"
  apply "$BR" "$CHK"
' _ {}

echo "Done."