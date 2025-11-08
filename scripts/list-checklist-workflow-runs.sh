#!/usr/bin/env bash
set -euo pipefail

# Usage: OWNER=your-org REPO=your-repo scripts/list-checklist-workflow-runs.sh

if [[ -z "${OWNER:-}" || -z "${REPO:-}" ]]; then
  echo "Set OWNER and REPO env vars." >&2
  exit 1
fi

gh run list --repo "$OWNER/$REPO" --workflow "Post-merge E2E Checklist Comment" --limit 5
echo "---"
echo "To view a specific run: gh run view <RUN_ID> --repo $OWNER/$REPO"

