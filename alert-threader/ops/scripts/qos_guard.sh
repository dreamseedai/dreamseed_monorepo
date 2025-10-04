#!/usr/bin/env bash
# qos_guard.sh lock|unlock|status [minutes]
# Manages a Quality of Service guard-window to prevent deployments during instability
set -euo pipefail

LOCK=/run/threader.qos.guard
CMD=${1:-status}
MINS=${2:-15}

case "$CMD" in
    lock)
        date -u +%s > "$LOCK"
        echo "🔒 QoS guard-window locked for ${MINS} minutes"
        ;;
    unlock)
        rm -f "$LOCK"
        echo "🔓 QoS guard-window unlocked"
        ;;
    status)
        if [ -f "$LOCK" ]; then
            ts=$(cat "$LOCK")
            now=$(date -u +%s)
            age=$(( (now-ts)/60 ))
            
            if [ $age -lt $MINS ]; then
                echo "🔒 QoS guard-window locked (${age}m/<${MINS}m remaining)"
                exit 1
            else
                echo "⚠️ QoS guard-window expired (${age}m), removing stale lock"
                rm -f "$LOCK"
            fi
        fi
        echo "🔓 QoS guard-window unlocked"
        ;;
    *)
        echo "Usage: qos_guard.sh lock|unlock|status [minutes]"
        echo "  lock   - Lock the guard-window for specified minutes (default: 15)"
        echo "  unlock - Unlock the guard-window immediately"
        echo "  status - Check if guard-window is locked (exit 1 if locked)"
        exit 2
        ;;
esac


