#!/usr/bin/env bash
# Close duplicate issues that share the same [ID] title prefix, keeping the newest issue open.
# Usage: ./scripts/gh_issues_cleanup_duplicates.sh <owner> <repo> [--search "query"] [--label label] [--dry-run]
# Examples:
#   ./scripts/gh_issues_cleanup_duplicates.sh dreamseedai dreamseed_monorepo --search "in:title [PR-]"
#   ./scripts/gh_issues_cleanup_duplicates.sh dreamseedai dreamseed_monorepo --label roadmap
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <owner> <repo> [--search query] [--label label] [--reason reason] [--dry-run]" >&2
  exit 1
fi
OWNER="$1"; REPO="$2"; shift 2
SEARCH_Q=""; LABEL=""; REASON=""; DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --search) SEARCH_Q="$2"; shift 2 ;;
    --label) LABEL="$2"; shift 2 ;;
    --reason) REASON="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown flag: $1" >&2; shift ;;
  esac
done

# Build gh issue list arguments
ARGS=(--repo "$OWNER/$REPO" --state open --json number,title,createdAt --limit 1000)
[[ -n "$SEARCH_Q" ]] && ARGS+=(--search "$SEARCH_Q")
[[ -n "$LABEL" ]] && ARGS+=(--label "$LABEL")

ISSUES_JSON=$(gh issue list "${ARGS[@]}" 2>/dev/null || true)
if [[ -z "$ISSUES_JSON" || "$ISSUES_JSON" == "null" ]]; then
  echo "No issues found with given filters."; exit 0
fi

# Group by leading [ID] prefix robustly (tolerate missing/irregular titles)
DUP_GROUPS=$(echo "$ISSUES_JSON" | jq -c '
  map(select(.title != null))
  | map({num: .number, title: .title, id: (.title | (try capture("^\\[(?<id>[^\\]]+)\\]\\s").id catch ""))})
  | map(select(.id != ""))
  | group_by(.id)
  | map(select(length>1))
')

if [[ $(echo "$DUP_GROUPS" | jq -r 'length') -eq 0 ]]; then
  echo "No duplicate groups (by [ID] prefix) found."; exit 0
fi

echo "Duplicate groups detected: $(echo "$DUP_GROUPS" | jq -r 'length')"

CLOSED_ANY=false

# Iterate groups; keep highest issue number, close others
for row in $(echo "$DUP_GROUPS" | jq -c '.[]'); do
  ID=$(echo "$row" | jq -r '.[0].id')
  # sort by number descending; keep first
  SORTED=$(echo "$row" | jq -c 'sort_by(.num) | reverse')
  KEEP_NUM=$(echo "$SORTED" | jq -r '.[0].num')
  TO_CLOSE=$(echo "$SORTED" | jq -r '.[1:] | .[].num')
  echo "Group [$ID]: keeping #$KEEP_NUM, closing: $(echo "$TO_CLOSE" | tr '\n' ' ')"
  for n in $TO_CLOSE; do
    if $DRY_RUN; then
      echo "DRY-RUN: gh issue close #$n --comment 'Closed as duplicate of #$KEEP_NUM'"
    else
      # Optional close reason
      if [[ -n "${REASON:-}" ]]; then
        # Try to pass reason; if unsupported by gh version, fall back without reason
        if gh issue close --repo "$OWNER/$REPO" "$n" --comment "Closed as duplicate of #$KEEP_NUM" --reason "$REASON" 2>/dev/null; then
          :
        else
          gh issue close --repo "$OWNER/$REPO" "$n" --comment "Closed as duplicate of #$KEEP_NUM" || true
        fi
      else
        gh issue close --repo "$OWNER/$REPO" "$n" --comment "Closed as duplicate of #$KEEP_NUM" || true
      fi
      CLOSED_ANY=true
    fi
  done
done

if $DRY_RUN; then
  echo "Dry-run complete: no issues were closed."
else
  if $CLOSED_ANY; then
    echo "Duplicate cleanup complete."
  else
    echo "No duplicates closed."
  fi
fi
