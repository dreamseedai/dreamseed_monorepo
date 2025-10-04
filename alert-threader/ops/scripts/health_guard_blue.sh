#!/usr/bin/env bash
set -euo pipefail

# Health Guard: Switch to Blue after consecutive failures
# Usage: ./health_guard_blue.sh [max_failures] [health_url]

SENTINEL=/run/threader.health.failures
MAX_FAIL=${1:-5}
HEALTH_URL=${2:-http://127.0.0.1:9009/healthz}
SWITCH_SCRIPT=/usr/local/sbin/nginx_switch_blue.sh

# Check if health check passes
if curl -sf --max-time 10 "$HEALTH_URL" >/dev/null 2>&1; then
    # Health check passed - reset failure counter
    rm -f "$SENTINEL"
    echo "[health-guard] Health check passed - reset failure counter"
    exit 0
fi

# Health check failed - increment counter
cnt=0
if [ -f "$SENTINEL" ]; then
    cnt=$(cat "$SENTINEL" 2>/dev/null || echo 0)
fi

cnt=$((cnt + 1))
echo "$cnt" > "$SENTINEL"

echo "[health-guard] Health check failed - consecutive failures: $cnt/$MAX_FAIL"

if [ "$cnt" -ge "$MAX_FAIL" ]; then
    echo "[health-guard] Max failures ($MAX_FAIL) reached - switching to BLUE upstream"
    
    # Execute rollback
    if [ -x "$SWITCH_SCRIPT" ]; then
        "$SWITCH_SCRIPT"
        echo "[health-guard] Rollback to BLUE completed"
    else
        echo "[health-guard] ERROR: Switch script not found at $SWITCH_SCRIPT"
        exit 1
    fi
    
    # Reset counter after rollback
    rm -f "$SENTINEL"
    
    # Log the event
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Health guard triggered rollback to BLUE (failures: $cnt)" >> /var/log/nginx-rollback.log
else
    echo "[health-guard] Waiting for more failures before rollback (need $((MAX_FAIL - cnt)) more)"
fi


