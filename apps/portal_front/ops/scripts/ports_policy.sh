#!/usr/bin/env bash
# Fail CI if dangerous browser-blocked ports are used
set -euo pipefail

CONF_DIR=${1:-ops/nginx}

echo "🔍 Checking for blocked browser ports in $CONF_DIR..."

# Check for blocked ports in nginx configs
if grep -R --line-number -E ":(6000|6665|6666|6667|6668|6669|10080)" "$CONF_DIR"; then
  echo "❌ Blocked browser port found in configs" >&2
  echo "🚫 Blocked ports: 6000, 6665-6669, 10080" >&2
  echo "✅ Safe ports: 80, 443, 8000, 8080, 3000, 5173" >&2
  exit 1
fi

echo "✅ No blocked ports detected"
echo "📋 Safe ports used: 80, 443, 8000, 8080, 3000, 5173"
