#!/usr/bin/env bash
# Apply branch protection and required checks to multiple branch patterns.
# Usage: ./scripts/gh_branch_protection_apply_all.sh <owner> <repo> "check1,check2" [patterns...]
# Defaults to patterns: main release/* feature/*
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <owner> <repo> <required_checks_csv> [patterns...]" >&2
  exit 1
fi
OWNER="$1"; REPO="$2"; CHECKS="$3"; shift 3
PATTERNS=("${@:-}")
if [[ ${#PATTERNS[@]} -eq 0 ]]; then
  PATTERNS=("main" "release/*" "feature/*")
fi

# Fetch remote branches
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

git ls-remote --heads "https://github.com/$OWNER/$REPO.git" | awk '{print $2}' | sed 's#refs/heads/##' > "$TMP"

match() { local name="$1" pat="$2"; [[ "$name" == $pat ]]; }

while read -r BR; do
  for P in "${PATTERNS[@]}"; do
    if match "$BR" "$P"; then
      echo "Applying protection to $BR"
      bash "$(dirname "$0")/gh_branch_protection_update.sh" "$OWNER" "$REPO" "$BR" "$CHECKS" || echo "Failed for $BR" >&2
      break
    fi
  done
done < "$TMP"

echo "Done."
