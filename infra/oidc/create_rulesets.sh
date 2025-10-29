#!/usr/bin/env bash
# Create repository rulesets from JSON via GitHub API
# Usage: OWNER=dreamseedai REPO=dreamseed_monorepo ./infra/oidc/create_rulesets.sh [path/to/ruleset.json]
set -euo pipefail

OWNER=${OWNER:-dreamseedai}
REPO=${REPO:-dreamseed_monorepo}
RULESET_JSON=${1:-rulesets.json}

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI required" >&2; exit 1
fi

if [[ ! -f "$RULESET_JSON" ]]; then
  echo "Ruleset JSON not found: $RULESET_JSON" >&2; exit 1
fi

echo "Creating ruleset from $RULESET_JSON for $OWNER/$REPO"
# Requires repo admin permissions on the token
gh api -X POST \
  "/repos/$OWNER/$REPO/rulesets" \
  -H "Accept: application/vnd.github+json" \
  -F "ruleset=@$RULESET_JSON"

echo "Done. Review Repo → Settings → Rules."
