#!/usr/bin/env bash
# Verify that a Projects V2 board has an Iteration field; print its name and id if present.
# Usage: ./scripts/gh_project_assert_iteration_field.sh <org> <project_number>
# Exit codes: 0 if iteration field present, 2 if missing, 1 on other errors
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <org> <project_number>" >&2
  exit 1
fi
ORG="$1"; PROJECT_NUMBER="$2"

GQL='query($org: String!, $number: Int!) {
  organization(login: $org) {
    projectV2(number: $number) {
      id
      title
      fields(first: 100) {
        nodes {
          __typename
          ... on ProjectV2Field {
            id
            name
          }
          ... on ProjectV2IterationField {
            id
            name
            configuration {
              iterations {
                title
              }
            }
          }
        }
      }
    }
  }
}'

RESP=$(gh api graphql -f query="$GQL" -F org="$ORG" -F number="$PROJECT_NUMBER" 2>&1 || true)
if [[ -z "$RESP" ]]; then
  echo "Error: failed to query project fields. Ensure gh is authenticated and you have access." >&2
  exit 1
fi

# Check for GraphQL errors
if echo "$RESP" | jq -e '.errors' >/dev/null 2>&1; then
  echo "GraphQL errors:" >&2
  echo "$RESP" | jq -r '.errors[].message' >&2
  exit 1
fi

TITLE=$(echo "$RESP" | jq -r '.data.organization.projectV2.title // empty')
if [[ -z "$TITLE" ]]; then
  echo "Error: project not found (org=$ORG number=$PROJECT_NUMBER)" >&2
  exit 1
fi

ITER=$(echo "$RESP" | jq -c '.data.organization.projectV2.fields.nodes[] | select(.__typename=="ProjectV2IterationField")' || true)
if [[ -n "$ITER" ]]; then
  NAME=$(echo "$ITER" | jq -r '.name')
  ID=$(echo "$ITER" | jq -r '.id')
  echo "Project '$TITLE' has Iteration field: name='$NAME' id=$ID"
  exit 0
else
  echo "Iteration field is missing on project '$TITLE'." >&2
  echo "Add it via UI: https://github.com/orgs/$ORG/projects/$PROJECT_NUMBER/settings/fields" >&2
  exit 2
fi
