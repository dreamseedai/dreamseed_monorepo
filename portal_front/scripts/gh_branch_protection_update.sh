#!/usr/bin/env bash
# Update branch protection and required status checks
# Requires: gh CLI admin access
# Usage: ./scripts/gh_branch_protection_update.sh <owner> <repo> <branch> "check1,check2,check3" [--reviews 1] [--enforce-admins true] [--strict true] [--dry-run]
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <owner> <repo> <branch> <required_checks_csv> [--reviews N] [--enforce-admins true|false] [--strict true|false] [--dry-run]"
  exit 1
fi

OWNER="$1"; shift
REPO="$1"; shift
BRANCH="$1"; shift
CHECKS_CSV="$1"; shift

REQUIRED_REVIEWS=1
ENFORCE_ADMINS=true
STRICT_CHECKS=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reviews)
      REQUIRED_REVIEWS="$2"; shift 2 ;;
    --enforce-admins)
      ENFORCE_ADMINS="$2"; shift 2 ;;
    --strict)
      STRICT_CHECKS="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    *)
      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2; exit 1
fi

IFS=',' read -r -a CHECKS <<< "$CHECKS_CSV"

echo "Applying protection on $OWNER/$REPO:$BRANCH"

# Build gh api flags for contexts array
CTX_FLAGS=()
for c in "${CHECKS[@]}"; do
  c_trimmed="${c## }"; c_trimmed="${c_trimmed%% }"
  [[ -z "$c_trimmed" ]] && continue
  CTX_FLAGS+=( -f "required_status_checks.contexts[]=$c_trimmed" )
done

# Compose command
CMD=( gh api -X PUT -H "Accept: application/vnd.github+json" \
  "/repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  -f "required_status_checks.strict=$STRICT_CHECKS" \
  -f "enforce_admins=$ENFORCE_ADMINS" \
  -f "required_pull_request_reviews.required_approving_review_count=$REQUIRED_REVIEWS" \
  -f restrictions= "${CTX_FLAGS[@]}" )

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY-RUN] Would run: ${CMD[*]}"
else
  "${CMD[@]}"
fi

echo "Done."