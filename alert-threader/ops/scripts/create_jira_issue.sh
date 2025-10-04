#!/usr/bin/env bash
# Create Jira Issue for SLO Breach
# Usage: env JIRA_BASE=..., JIRA_USER=..., JIRA_TOKEN=..., JIRA_PROJECT=PRJ, JIRA_ISSUE_TYPE=Bug, SUMMARY=..., DESC=...
set -euo pipefail

# Required environment variables
: "${JIRA_BASE:?JIRA_BASE required}"
: "${JIRA_USER:?JIRA_USER required}"
: "${JIRA_TOKEN:?JIRA_TOKEN required}"
: "${JIRA_PROJECT:?JIRA_PROJECT required}"

# Optional parameters with defaults
ISSUE_TYPE=${JIRA_ISSUE_TYPE:-Bug}
SUMMARY=${SUMMARY:-"SLO breach detected"}
DESC=${DESC:-"See Slack thread and Prometheus/Loki dashboards."}
PRIORITY=${JIRA_PRIORITY:-High}
LABELS=${JIRA_LABELS:-"slo-breach,auto-generated"}

echo "🎫 Creating Jira issue for SLO breach..."

# Create issue payload
payload=$(cat <<JSON
{
  "fields": {
    "project": {"key": "${JIRA_PROJECT}"},
    "summary": "${SUMMARY}",
    "issuetype": {"name": "${ISSUE_TYPE}"},
    "description": "${DESC}",
    "priority": {"name": "${PRIORITY}"},
    "labels": [$(echo "${LABELS}" | tr ',' '\n' | sed 's/^/"/;s/$/"/' | tr '\n' ',' | sed 's/,$//')]
  }
}
JSON
)

# Send request to Jira API
response=$(curl -s -u "${JIRA_USER}:${JIRA_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "$payload" \
  "${JIRA_BASE}/rest/api/2/issue")

# Parse response
issue_key=$(echo "$response" | jq -r '.key // empty')
issue_id=$(echo "$response" | jq -r '.id // empty')
error_message=$(echo "$response" | jq -r '.errorMessages[]? // .errors | to_entries[] | "\(.key): \(.value)"' 2>/dev/null || echo "")

if [ -n "$issue_key" ]; then
    echo "✅ Jira issue created: ${issue_key}"
    echo "🔗 URL: ${JIRA_BASE}/browse/${issue_key}"
    echo "${issue_key}"
else
    echo "❌ Failed to create Jira issue: $error_message" >&2
    echo "Response: $response" >&2
    exit 1
fi


