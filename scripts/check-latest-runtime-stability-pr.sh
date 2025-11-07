#!/usr/bin/env bash
set -euo pipefail

# Usage: OWNER=your-org REPO=your-repo scripts/check-latest-runtime-stability-pr.sh

if [[ -z "${OWNER:-}" || -z "${REPO:-}" ]]; then
  echo "Set OWNER and REPO env vars." >&2
  exit 1
fi

PR=$(gh pr list --repo "$OWNER/$REPO" --state merged --label runtime-stability --limit 1 --json number,mergedAt --jq '.[0].number')
if [[ -z "${PR:-}" || "$PR" == "null" ]]; then
  echo "No merged PR with label runtime-stability found" >&2
  exit 2
fi
echo "Merged PR #: $PR"

if gh api "repos/$OWNER/$REPO/issues/$PR/comments" --paginate | jq -r '.[].body' | grep -F "Post-merge E2E Checklist (Runtime Stability)" >/dev/null; then
  echo "Checklist comment found"
else
  echo "Checklist comment NOT found" >&2
  exit 3
fi

