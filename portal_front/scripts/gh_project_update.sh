#!/usr/bin/env bash
# Update GitHub Projects (Projects V2) item fields via GraphQL
# Requires: gh CLI with GH_TOKEN having project write access
# Usage: ./scripts/gh_project_update.sh <project_org> <project_number> <issue_number> <status> <story_points> [priority_label] [iteration_title] [--repo-owner OWNER] [--repo-name NAME]
set -euo pipefail

if [[ $# -lt 5 ]]; then
  echo "Usage: $0 <project_org> <project_number> <issue_number> <status> <story_points> [priority_label] [iteration_title] [--repo-owner OWNER] [--repo-name NAME]"
  exit 1
fi

ORG="$1"; shift
PROJECT_NUMBER="$1"; shift
ISSUE_NUMBER="$1"; shift
STATUS="$1"; shift
STORY_POINTS="$1"; shift
PRIORITY_LABEL="${1:-}"; [[ $# -gt 0 ]] && shift || true
ITERATION_TITLE="${1:-}"; [[ $# -gt 0 ]] && shift || true

REPO_OWNER="${REPO_OWNER:-}"
REPO_NAME="${REPO_NAME:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-owner) REPO_OWNER="$2"; shift 2 ;;
    --repo-name) REPO_NAME="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$REPO_OWNER" || -z "$REPO_NAME" ]]; then
  # Fallback to repo from git if not provided
  REPO_NAME=${REPO_NAME:-$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" )}
  # Use current repo owner via gh context when possible
  REPO_OWNER=${REPO_OWNER:-$(gh repo view --json owner -q .owner.login 2>/dev/null || echo "$ORG")}
fi

# Fetch node IDs
issueId=$(gh api graphql -f query='query($own:String!,$repo:String!,$number:Int!){repository(owner:$own,name:$repo){issue(number:$number){id}}}' -f own="$REPO_OWNER" -f repo="$REPO_NAME" -F number=$ISSUE_NUMBER --jq '.data.repository.issue.id' 2>/dev/null || true)
if [[ -z "$issueId" ]]; then
  echo "Error: cannot resolve issue node id. Ensure repo context is correct." >&2
  exit 1
fi

projectId=$(gh api graphql -f query='query($org:String!,$number:Int!){organization(login:$org){projectV2(number:$number){id title}}}' -f org="$ORG" -F number=$PROJECT_NUMBER --jq '.data.organization.projectV2.id')

# Add issue to project (idempotent)
itemId=$(gh api graphql -f query='mutation($project:ID!,$item:ID!){addProjectV2ItemById(input:{projectId:$project, contentId:$item}){item{id}}}' -f project=$projectId -f item=$issueId --jq '.data.addProjectV2ItemById.item.id')

# Resolve field IDs
FIELDS_JSON=$(gh api graphql -f query='query($project:ID!){node(id:$project){... on ProjectV2{fields(first:100){nodes{__typename ... on ProjectV2FieldCommon{id name} ... on ProjectV2SingleSelectField{id name options{id name}} ... on ProjectV2IterationField{id name configuration{iterations{title id}}}}}}}}' -f project=$projectId --jq '.data.node.fields.nodes')
statusFieldId=$(echo "$FIELDS_JSON" | jq -r '.[] | select(.name=="Status") | .id')
storyFieldId=$(echo "$FIELDS_JSON" | jq -r '.[] | select(.name=="Story Points") | .id')
priorityFieldId=$(echo "$FIELDS_JSON" | jq -r '.[] | select(.name=="Priority") | .id')
iterationFieldId=$(echo "$FIELDS_JSON" | jq -r '.[] | select(.name=="Iteration") | .id')

# Map status name to option ID
statusOptionId=$(gh api graphql -f query='query($project:ID!){node(id:$project){... on ProjectV2{fields(first:100){nodes{... on ProjectV2SingleSelectField{id name options{id name}}}}}}}' -f project=$projectId --jq \
  --raw-field status_name="$STATUS" \
  '[.data.node.fields.nodes[] | select(.name=="Status") | .options[] | select(.name==env.status_name) | .id] | first')

# Update Status
if [[ -n "$statusFieldId" && -n "$statusOptionId" ]]; then
  gh api graphql -f query='mutation($project:ID!,$item:ID!,$field:ID!,$opt: String!){updateProjectV2ItemFieldValue(input:{projectId:$project, itemId:$item, fieldId:$field, value:{singleSelectOptionId:$opt}}){clientMutationId}}' \
    -f project=$projectId -f item=$itemId -f field=$statusFieldId -f opt=$statusOptionId >/dev/null
  echo "Status set to $STATUS"
else
  echo "Warning: could not resolve Status field/option." >&2
fi

# Update Story Points
if [[ -n "$storyFieldId" ]]; then
  gh api graphql -f query='mutation($project:ID!,$item:ID!,$field:ID!,$sp:Float!){updateProjectV2ItemFieldValue(input:{projectId:$project, itemId:$item, fieldId:$field, value:{number:$sp}}){clientMutationId}}' \
    -f project=$projectId -f item=$itemId -f field=$storyFieldId -F sp=$STORY_POINTS >/dev/null
  echo "Story Points set to $STORY_POINTS"
else
  echo "Warning: could not resolve Story Points field." >&2
fi

# Update Priority (single select)
if [[ -n "$priorityFieldId" && -n "$PRIORITY_LABEL" ]]; then
  priorityOptionId=$(gh api graphql -f query='query($project:ID!){node(id:$project){... on ProjectV2{fields(first:100){nodes{... on ProjectV2SingleSelectField{id name options{id name}}}}}}}' -f project=$projectId --jq \
    --raw-field prio_name="$PRIORITY_LABEL" \
    '[.data.node.fields.nodes[] | select(.name=="Priority") | .options[] | select(.name==env.prio_name) | .id] | first')
  if [[ -n "$priorityOptionId" ]]; then
    gh api graphql -f query='mutation($project:ID!,$item:ID!,$field:ID!,$opt: String!){updateProjectV2ItemFieldValue(input:{projectId:$project, itemId:$item, fieldId:$field, value:{singleSelectOptionId:$opt}}){clientMutationId}}' \
      -f project=$projectId -f item=$itemId -f field=$priorityFieldId -f opt=$priorityOptionId >/dev/null
    echo "Priority set to $PRIORITY_LABEL"
  else
    echo "Warning: could not resolve Priority option: $PRIORITY_LABEL" >&2
  fi
fi

# Update Iteration
if [[ -n "$iterationFieldId" && -n "$ITERATION_TITLE" ]]; then
  iterationId=$(echo "$FIELDS_JSON" | jq -r --arg title "$ITERATION_TITLE" '.[] | select(.name=="Iteration") | .configuration.iterations[] | select(.title==$title) | .id' | head -n1)
  if [[ -n "$iterationId" ]]; then
    gh api graphql -f query='mutation($project:ID!,$item:ID!,$field:ID!,$iter: String!){updateProjectV2ItemFieldValue(input:{projectId:$project, itemId:$item, fieldId:$field, value:{iterationId:$iter}}){clientMutationId}}' \
      -f project=$projectId -f item=$itemId -f field=$iterationFieldId -f iter=$iterationId >/dev/null
    echo "Iteration set to $ITERATION_TITLE"
  else
    echo "Warning: Iteration title not found: $ITERATION_TITLE" >&2
  fi
fi

echo "Done."