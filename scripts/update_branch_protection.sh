#!/usr/bin/env bash
# Update branch protection using GitHub CLI
# Usage: GITHUB_TOKEN=<admin_repo_token> ./scripts/update_branch_protection.sh <owner/repo> <branch> "check1,check2,check3" [enforce_admins]
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install from https://cli.github.com/" >&2
  exit 1
fi

REPO=${1:-}
BRANCH=${2:-}
CHECKS=${3:-}
ENFORCE_ADMINS=${4:-true}

if [ -z "$REPO" ] || [ -z "$BRANCH" ] || [ -z "$CHECKS" ]; then
  echo "Usage: GITHUB_TOKEN=<admin_repo_token> $0 <owner/repo> <branch> \"check1,check2\" [enforce_admins]" >&2
  exit 1
fi

contexts=$(jq -R -s 'split(",") | map(. | gsub("^\\s+|\\s+$";""))' <<< "$CHECKS")
enforce=$(jq -n --arg s "$ENFORCE_ADMINS" '$s == "true"')

body=$(jq -n --argjson contexts "$contexts" --argjson enforce "$enforce" '{
  required_status_checks: { strict: true, contexts: $contexts },
  enforce_admins: $enforce,
  required_pull_request_reviews: null,
  restrictions: null
}')

echo "Applying protection to $REPO@$BRANCH with checks: $CHECKS (enforce_admins=$ENFORCE_ADMINS)"
echo "$body" | jq .

gh api -X PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/$REPO/branches/$BRANCH/protection" \
  --input - <<< "$body"

echo "Current protection:" && gh api -H "Accept: application/vnd.github+json" "repos/$REPO/branches/$BRANCH/protection" | jq .
