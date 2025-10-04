#!/usr/bin/env bash
set -euo pipefail

# Blue-Green upstream switch script
# Usage: sudo ./dreamseed_upstream_switch.sh [blue|green]

BLUE=/etc/nginx/upstreams/threader_blue.conf
GREEN=/etc/nginx/upstreams/threader_green.conf
ACTIVE=/etc/nginx/upstreams/threader_active.conf

TARGET=${1:-green}  # blue|green

case "$TARGET" in
  blue)
    echo "🔄 Switching to BLUE upstream..."
    ln -sfn "$BLUE" "$ACTIVE"
    ;;
  green)
    echo "🔄 Switching to GREEN upstream..."
    ln -sfn "$GREEN" "$ACTIVE"
    ;;
  *)
    echo "Usage: $0 [blue|green]"
    exit 1
    ;;
esac

# Validate and reload
if nginx -t; then
    systemctl reload nginx
    echo "✅ Successfully switched to $TARGET upstream"
    echo "   Active: $ACTIVE -> $([ "$TARGET" = "blue" ] && echo "$BLUE" || echo "$GREEN")"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# Log the switch event
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Switched to $TARGET upstream" >> /var/log/nginx-deploy.log


