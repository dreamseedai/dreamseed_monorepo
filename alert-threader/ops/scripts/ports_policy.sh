#!/usr/bin/env bash
# Fail CI if dangerous browser-blocked ports are used
set -euo pipefail
CONF_DIR=${1:-ops/nginx}
if grep -R --line-number -E ":(6000|6665|6666|6667|6668|6669|10080)" "$CONF_DIR"; then
  echo "❌ Blocked browser port found in configs" >&2
  exit 1
fi
echo "✅ No blocked ports detected"

# Warn if non‑recommended ports are used (allowlist)
ALLOWLIST=':80|:443|:8000|:8080|:3000|:5173'
if grep -R -E ":[0-9]{2,5}" "$CONF_DIR" | grep -Ev "$ALLOWLIST" | grep -vE "(6000|6665|6666|6667|6668|6669|10080)"; then
  echo "⚠️  Non‑recommended ports detected (not blocked, but review). Allowed: 80, 443, 8000, 8080, 3000, 5173" >&2
fi


