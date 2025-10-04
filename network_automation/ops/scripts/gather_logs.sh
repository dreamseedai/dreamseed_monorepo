#!/usr/bin/env bash
set -euo pipefail
OUT=/tmp/dreamseed_logs_$(date +%Y%m%d_%H%M%S).tgz

TMPDIR=$(mktemp -d)

# Snapshots of networking & firewall
ss -lntp > "$TMPDIR/ss_lntp.txt" 2>&1 || true
ufw status verbose > "$TMPDIR/ufw_status.txt" 2>&1 || true
ip addr show > "$TMPDIR/ip_addr.txt" 2>&1 || true
ip route show > "$TMPDIR/ip_route.txt" 2>&1 || true
nginx -T > "$TMPDIR/nginx_T.txt" 2>&1 || true

tar czf "$OUT" \
  /var/log/nginx \
  /var/log/syslog \
  /var/log/letsencrypt \
  "$TMPDIR" 2>/dev/null || true

echo "Logs archived: $OUT"