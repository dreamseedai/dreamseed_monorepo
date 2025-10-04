#!/usr/bin/env bash
# Create GitHub Issue for SLO Breach
# Usage: env GH_REPO=owner/name, GH_TOKEN=..., TITLE=..., BODY=...
set -euo pipefail

# Required environment variables
: "${GH_REPO:?GH_REPO required}"
: "${GH_TOKEN:?GH_TOKEN required}"

# Optional parameters with defaults
TITLE=${TITLE:-"SLO breach detected"}
BODY=${BODY:-"See Slack thread and Prometheus/Loki dashboards."}
LABELS=${GH_LABELS:-"slo-breach,auto-generated"}
ASSIGNEES=${GH_ASSIGNEES:-""}

echo "🎫 Creating GitHub issue for SLO breach..."

# Create issue payload
payload=$(cat <<JSON
{
  "title": "${TITLE}",
  "body": "${BODY}",
  "labels": [$(echo "${LABELS}" | tr ',' '\n' | sed 's/^/"/;s/$/"/' | tr '\n' ',' | sed 's/,$//')],
  "assignees": [$(if [ -n "${ASSIGNEES}" ]; then echo "${ASSIGNEES}" | tr ',' '\n' | sed 's/^/"/;s/$/"/' | tr '\n' ',' | sed 's/,$//'; fi)]
}
JSON
)

# Send request to GitHub API
response=$(curl -s -H "Authorization: Bearer ${GH_TOKEN}" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  -d "$payload" \
  "https://api.github.com/repos/${GH_REPO}/issues")

# Parse response
issue_number=$(echo "$response" | jq -r '.number // empty')
issue_url=$(echo "$response" | jq -r '.html_url // empty')
error_message=$(echo "$response" | jq -r '.message // empty')

if [ -n "$issue_number" ]; then
    echo "✅ GitHub issue created: #${issue_number}"
    echo "🔗 URL: ${issue_url}"
    echo "#${issue_number}"
else
    echo "❌ Failed to create GitHub issue: $error_message" >&2
    echo "Response: $response" >&2
    exit 1
fi


