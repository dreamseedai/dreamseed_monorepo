#!/usr/bin/env bash
# Create a finalized project_config.json tailored to a Projects V2 board.
# It inspects Status/Priority options and maps common labels to the closest option names.
# Requires: gh CLI, jq
# Usage:
#   ./scripts/gh_project_finalize_config.sh <org> <project_number> [--output path]
# Example:
#   ./scripts/gh_project_finalize_config.sh your-org 42 --output portal_front/project_management/project_config.json
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <project_org> <project_number> [--output path]" >&2
  exit 1
fi

ORG="$1"; shift
PROJECT_NUMBER="$1"; shift
OUTPUT_PATH="portal_front/project_management/project_config.json"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT_PATH="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then echo "gh is required" >&2; exit 1; fi
if ! command -v jq >/dev/null 2>&1; then echo "jq is required" >&2; exit 1; fi

projectId=$(gh api graphql -f query='query($org:String!,$number:Int!){organization(login:$org){projectV2(number:$number){id title}}}' -f org="$ORG" -F number=$PROJECT_NUMBER --jq '.data.organization.projectV2.id')
if [[ -z "$projectId" ]]; then
  echo "Error: unable to resolve project id" >&2
  exit 1
fi

FIELDS_JSON=$(gh api graphql -f query='query($project:ID!){node(id:$project){... on ProjectV2{fields(first:100){nodes{__typename ... on ProjectV2FieldCommon{id name} ... on ProjectV2SingleSelectField{id name options{id name}} ... on ProjectV2IterationField{id name configuration{iterations{title id}}}}}}}}' -f project=$projectId --jq '.data.node.fields.nodes')
STATUS_NAMES=$(echo "$FIELDS_JSON" | jq -r '[.[] | select(.name=="Status") | .options[]?.name // empty]')
PRIORITY_NAMES=$(echo "$FIELDS_JSON" | jq -r '[.[] | select(.name=="Priority") | .options[]?.name // empty]')

# jq helper to pick the first matching option from candidate list (case-insensitive contains)
read -r -d '' JQ_PICK <<'JQ'
  def pick($opts; $cands):
    ($cands[] | ascii_downcase) as $cand
    | ($opts[] | {name:., key:(ascii_downcase)})
    | select(.key==$cand or (.key|contains($cand)))
    | .name
    // empty;
JQ

# Build mapping using heuristic candidates
CONFIG=$(jq -n \
  --argjson status "$STATUS_NAMES" \
  --argjson prio "$PRIORITY_NAMES" \
  --arg storyPrefix "sp:" \
  --arg iterPrefix "iter:" \
  --rawfile pickfn <(echo "$JQ_PICK") \
  'include "pick" as $p? // empty | .'
  )
# The above include trick is not directly supported; instead embed function in the same program.
# Re-run with embedded function.
CONFIG=$(jq -n \
  --argjson status "$STATUS_NAMES" \
  --argjson prio "$PRIORITY_NAMES" \
  --arg storyPrefix "sp:" \
  --arg iterPrefix "iter:" \
  'def pick($opts; $cands):
     reduce $cands[] as $c (null;
       if . then .
       else ( $opts[] | {name:., key:(ascii_downcase)} )
         | select(.key==( $c|ascii_downcase ) or (.key|contains( $c|ascii_downcase )))
         | .name
       end);

   def coalesce($x; $fallback): if ($x|type) == "string" and ($x|length)>0 then $x else $fallback end;

   {
     statusLabelMap: {
       triage:    coalesce( pick($status; ["Inbox","Triage","Todo","Backlog"]) ; "Inbox" ),
       roadmap:   coalesce( pick($status; ["Backlog","Todo"]) ; "Backlog" ),
       implementation: coalesce( pick($status; ["In Progress","Doing","Progress","WIP"]) ; "In Progress" ),
       review:    coalesce( pick($status; ["In Review","Review","Code Review"]) ; "In Review" ),
       qa:        coalesce( pick($status; ["QA","Verification","Testing"]) ; "QA" ),
       blocked:   coalesce( pick($status; ["Blocked","On Hold"]) ; "Blocked" ),
       done:      coalesce( pick($status; ["Done","Closed","Complete"]) ; "Done" )
     },
     storyPointsLabelPrefix: $storyPrefix,
     priorityLabelMap: {
       p1: coalesce( pick($prio; ["P1","High","Urgent","Critical"]) ; ( $prio[0] // "P1" ) ),
       p2: coalesce( pick($prio; ["P2","Medium","Normal"]) ; ( $prio[1] // "P2" ) ),
       p3: coalesce( pick($prio; ["P3","Low"]) ; ( $prio[2] // "P3" ) )
     },
     iterationFromLabelPrefix: $iterPrefix
   }'
)

echo "$CONFIG" | jq '.' > "$OUTPUT_PATH"
echo "Wrote finalized config to $OUTPUT_PATH" >&2
