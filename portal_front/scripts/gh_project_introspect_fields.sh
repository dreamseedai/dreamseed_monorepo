#!/usr/bin/env bash
# Inspect GitHub Projects (Projects V2) fields/options and emit a config skeleton
# Requires: gh CLI authenticated with access, jq
# Usage:
#   ./scripts/gh_project_introspect_fields.sh <project_org> <project_number> [--output-config path]
# Example:
#   ./scripts/gh_project_introspect_fields.sh your-org 42 --output-config portal_front/project_management/project_config.generated.json
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <project_org> <project_number> [--output-config path]" >&2
  exit 1
fi

ORG="$1"; shift
PROJECT_NUMBER="$1"; shift
OUTPUT_CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-config) OUTPUT_CONFIG="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then echo "gh is required" >&2; exit 1; fi
if ! command -v jq >/dev/null 2>&1; then echo "jq is required" >&2; exit 1; fi

projectId=$(gh api graphql -f query='query($org:String!,$number:Int!){organization(login:$org){projectV2(number:$number){id title}}}' -f org="$ORG" -F number=$PROJECT_NUMBER --jq '.data.organization.projectV2.id')
if [[ -z "$projectId" ]]; then
  echo "Error: could not resolve project id for $ORG #$PROJECT_NUMBER" >&2
  exit 1
fi

echo "Inspecting fields for $ORG project #$PROJECT_NUMBER ..." >&2
FIELDS_JSON=$(gh api graphql -f query='query($project:ID!){node(id:$project){... on ProjectV2{fields(first:100){nodes{__typename ... on ProjectV2FieldCommon{id name} ... on ProjectV2SingleSelectField{id name options{id name}} ... on ProjectV2IterationField{id name configuration{iterations{title id}}}}}}}}' -f project=$projectId --jq '.data.node.fields.nodes')

STATUS_OPTIONS=$(echo "$FIELDS_JSON" | jq -r '[.[] | select(.name=="Status") | .options[]?.name]')
PRIORITY_OPTIONS=$(echo "$FIELDS_JSON" | jq -r '[.[] | select(.name=="Priority") | .options[]?.name]')
ITERATIONS=$(echo "$FIELDS_JSON" | jq -r '[.[] | select(.name=="Iteration") | .configuration.iterations[]?.title]')

# Emit human-readable summary
{
  echo "Status options:" >&2
  echo "$STATUS_OPTIONS" | jq -r '.[]?' | sed 's/^/  - /' >&2 || true
  echo "Priority options:" >&2
  echo "$PRIORITY_OPTIONS" | jq -r '.[]?' | sed 's/^/  - /' >&2 || true
  echo "Iteration titles (current config):" >&2
  echo "$ITERATIONS" | jq -r '.[]?' | sed 's/^/  - /' >&2 || true
} >/dev/stderr

# Build a config skeleton
CONFIG=$(jq -n --argjson statusOpt "$STATUS_OPTIONS" --argjson prioOpt "$PRIORITY_OPTIONS" '{
  statusLabelMap: {
    triage: "Inbox",
    roadmap: "Backlog",
    implementation: "In Progress",
    review: "In Review",
    qa: "QA",
    blocked: "Blocked",
    done: "Done"
  },
  storyPointsLabelPrefix: "sp:",
  priorityLabelMap: ( $prioOpt | map({key: (.[0:2]|ascii_downcase) // . , val: .}) | from_entries ),
  iterationFromLabelPrefix: "iter:"
}')

# Note: priorityLabelMap auto-skeleton uses first two chars lowercased as keys (e.g., "Hi"->"hi"). Adjust as needed.

echo "$CONFIG" | jq '.'

if [[ -n "$OUTPUT_CONFIG" ]]; then
  echo "$CONFIG" > "$OUTPUT_CONFIG"
  echo "Wrote config skeleton to $OUTPUT_CONFIG" >&2
fi
