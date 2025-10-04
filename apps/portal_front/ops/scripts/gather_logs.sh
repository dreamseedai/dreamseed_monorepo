#!/usr/bin/env bash
set -euo pipefail

OUT=/tmp/dreamseed_logs_$(date +%Y%m%d_%H%M%S).tgz

echo "📦 Collecting logs to $OUT"

tar czf "$OUT" \
  /var/log/nginx \
  /var/log/syslog \
  /var/log/letsencrypt 2>/dev/null || true

echo "✅ Logs archived: $OUT"
echo "📊 Archive size: $(du -h "$OUT" | cut -f1)"
