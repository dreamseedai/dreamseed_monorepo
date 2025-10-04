#!/usr/bin/env bash
# Guard-Window Slack Briefing Script
# Queries Prometheus/Loki for SLO metrics and posts to Slack thread
set -euo pipefail

# Required environment variables
: "${PROM_URL:?PROM_URL required}"
: "${LOKI_URL:?LOKI_URL required}"
: "${SLACK_BOT_TOKEN:?SLACK_BOT_TOKEN required}"
: "${SLACK_CHANNEL_ID:?SLACK_CHANNEL_ID required}"
: "${THREAD_TS:?THREAD_TS required}"

# Optional parameters with defaults
WINDOW=${WINDOW:-15m}
JOB=${JOB:-threader}
MAX_5XX_RATIO=${MAX_5XX_RATIO:-0.01}
MIN_HEALTH_RATIO=${MIN_HEALTH_RATIO:-0.995}
MAX_ERROR_LOGS_PER_MIN=${MAX_ERROR_LOGS_PER_MIN:-1}

# Optional dashboard links (plain URLs). If set, appended to message.
GRAFANA_PANEL_URL=${GRAFANA_PANEL_URL:-}
PROM_DASH_URL=${PROM_DASH_URL:-}
LOKI_EXPLORE_URL=${LOKI_EXPLORE_URL:-}
SLO_DASH_URL=${SLO_DASH_URL:-}
SLA_DASH_URL=${SLA_DASH_URL:-}
JVM_DASH_URL=${JVM_DASH_URL:-}
DB_DASH_URL=${DB_DASH_URL:-}

# Helper function for JSON parsing
jq() { command jq -r "$@"; }

echo "🔍 Querying SLO metrics for Guard-Window briefing..."

# Query Prometheus - 5xx error ratio over window
echo "Querying 5xx error ratio..."
fx=$(curl -s "${PROM_URL}/api/v1/query?query=avg_over_time(job:http_5xx_ratio_1m%7Bjob%3D%22${JOB}%22%7D[${WINDOW}])" | jq '.data.result[0].value[1] // 0')

# Query Prometheus - health ratio over window
echo "Querying health ratio..."
hr=$(curl -s "${PROM_URL}/api/v1/query?query=avg_over_time(job:health_ok_ratio_1m%7Bjob%3D%22${JOB}%22%7D[${WINDOW}])" | jq '.data.result[0].value[1] // 1')

# Query Loki - error log rate over window
echo "Querying error log rate..."
le=$(curl -s "${LOKI_URL}/loki/api/v1/query?query=avg_over_time(sum(rate({job%3D%22${JOB}%22}%7C~%22ERROR%7CException%7CTraceback%22%5B1m%5D))[${WINDOW}])" | jq '.data.result[0].value[1] // 0')

# Format numbers
FX=$(printf '%.4f' "${fx}")
HR=$(printf '%.4f' "${hr}")
LE=$(printf '%.2f' "${le}")

# Determine status indicators
FX_STATUS="✅"
if (( $(echo "$fx > $MAX_5XX_RATIO" | bc -l) )); then
    FX_STATUS="❌"
elif (( $(echo "$fx > $MAX_5XX_RATIO * 0.5" | bc -l) )); then
    FX_STATUS="⚠️"
fi

HR_STATUS="✅"
if (( $(echo "$hr < $MIN_HEALTH_RATIO" | bc -l) )); then
    HR_STATUS="❌"
elif (( $(echo "$hr < $MIN_HEALTH_RATIO + 0.005" | bc -l) )); then
    HR_STATUS="⚠️"
fi

LE_STATUS="✅"
if (( $(echo "$le > $MAX_ERROR_LOGS_PER_MIN" | bc -l) )); then
    LE_STATUS="❌"
elif (( $(echo "$le > $MAX_ERROR_LOGS_PER_MIN * 0.5" | bc -l) )); then
    LE_STATUS="⚠️"
fi

# Check if Guard-Window is locked
GUARD_STATUS="🔓 Unlocked"
if [ -f "/run/threader.qos.guard" ]; then
    ts=$(cat "/run/threader.qos.guard")
    now=$(date -u +%s)
    age=$(( (now-ts)/60 ))
    GUARD_STATUS="🔒 Locked (${age}m)"
fi

# Create Slack message
TEXT="*🛡️ Guard-Window Brief* (window=${WINDOW})
• 5xx avg ratio: \`${FX}\` ${FX_STATUS} (threshold: ${MAX_5XX_RATIO})
• health ok avg: \`${HR}\` ${HR_STATUS} (threshold: ${MIN_HEALTH_RATIO})
• error logs/min: \`${LE}\` ${LE_STATUS} (threshold: ${MAX_ERROR_LOGS_PER_MIN})
• Guard status: ${GUARD_STATUS}
• Job: \`${JOB}\`
• Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# Add dashboard links if configured
links=""
[ -n "$GRAFANA_PANEL_URL" ] && links+=$'\n• Grafana: <'"$GRAFANA_PANEL_URL"'|panel>'
[ -n "$PROM_DASH_URL" ]    && links+=$'\n• Prometheus: <'"$PROM_DASH_URL"'|query>'
[ -n "$LOKI_EXPLORE_URL" ] && links+=$'\n• Loki: <'"$LOKI_EXPLORE_URL"'|explore>'
[ -n "$SLO_DASH_URL" ]     && links+=$'\n• SLO: <'"$SLO_DASH_URL"'|SLO Dashboard>'
[ -n "$SLA_DASH_URL" ]     && links+=$'\n• SLA: <'"$SLA_DASH_URL"'|SLA Dashboard>'
[ -n "$JVM_DASH_URL" ]     && links+=$'\n• JVM: <'"$JVM_DASH_URL"'|JVM Metrics>'
[ -n "$DB_DASH_URL" ]      && links+=$'\n• DB: <'"$DB_DASH_URL"'|DB Performance>'
TEXT+="$links"

# Send to Slack thread
echo "📤 Sending briefing to Slack thread..."
payload=$(cat <<JSON
{
  "channel": "${SLACK_CHANNEL_ID}",
  "thread_ts": "${THREAD_TS}",
  "text": "${TEXT}",
  "unfurl_links": false,
  "unfurl_media": false
}
JSON
)

response=$(curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
  -H 'Content-Type: application/json' \
  --data "${payload}")

# Check response
ok=$(echo "$response" | jq '.ok')
if [ "$ok" = "true" ]; then
    echo "✅ Guard-Window briefing sent successfully"
else
    echo "❌ Failed to send briefing: $response" >&2
    exit 1
fi

# Log metrics for monitoring
echo "📊 Metrics logged: 5xx=${FX}, health=${HR}, errors=${LE}"
