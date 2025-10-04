#!/usr/bin/env bash
# retry_backoff.sh <max_attempts> <base_seconds> -- <command...>
# Example: retry_backoff.sh 3 5 -- ansible-playbook deploy.yaml
set -euo pipefail

MAX=${1:-3}
BASE=${2:-5}
shift 2

# Validate arguments
if [ "$1" != "--" ]; then
    echo "Usage: retry_backoff.sh <max_attempts> <base_seconds> -- <command...>"
    echo "Example: retry_backoff.sh 3 5 -- ansible-playbook deploy.yaml"
    exit 2
fi
shift

echo "🔄 Retry backoff: max_attempts=$MAX, base_delay=${BASE}s"
echo "Command: $*"

for i in $(seq 1 "$MAX"); do
    echo "[retry] attempt $i/$MAX: $*"
    
    if "$@"; then
        echo "✅ Command succeeded on attempt $i"
        exit 0
    fi
    
    if [ $i -lt $MAX ]; then
        delay=$((BASE * 2**(i-1)))
        echo "❌ Command failed, waiting ${delay}s before retry..."
        sleep $delay
    fi
done

echo "❌ Command failed after $MAX attempts"
exit 1


