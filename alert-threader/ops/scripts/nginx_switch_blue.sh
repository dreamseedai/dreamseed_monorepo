#!/usr/bin/env bash
set -euo pipefail

# One-touch auto rollback: Switch Nginx upstream to Blue on failure
# Usage: sudo ./nginx_switch_blue.sh

BLUE=${BLUE:-/etc/nginx/upstreams/threader_blue.conf}
GREEN=${GREEN:-/etc/nginx/upstreams/threader_green.conf}
ACTIVE=${ACTIVE:-/etc/nginx/upstreams/threader_active.conf}

# Ensure upstream directories exist
mkdir -p /etc/nginx/upstreams

# Create Blue upstream if it doesn't exist (fallback to localhost:9009)
if [ ! -f "$BLUE" ]; then
    cat > "$BLUE" << 'EOF'
# Blue upstream (stable version)
upstream threader_blue {
    server 127.0.0.1:9009 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
EOF
    echo "Created Blue upstream: $BLUE"
fi

# Create Green upstream if it doesn't exist (fallback to localhost:9010)
if [ ! -f "$GREEN" ]; then
    cat > "$GREEN" << 'EOF'
# Green upstream (new version)
upstream threader_green {
    server 127.0.0.1:9010 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
EOF
    echo "Created Green upstream: $GREEN"
fi

# Switch to Blue
echo "🔄 Switching Nginx upstream to BLUE..."
ln -sfn "$BLUE" "$ACTIVE"

# Validate and reload
if nginx -t; then
    systemctl reload nginx
    echo "✅ Successfully switched to BLUE upstream"
    echo "   Active: $ACTIVE -> $BLUE"
    
    # Health check the Blue upstream
    sleep 2
    if curl -sf http://127.0.0.1:9009/healthz >/dev/null 2>&1; then
        echo "✅ Blue upstream health check passed"
    else
        echo "⚠️  Blue upstream health check failed - may need manual intervention"
    fi
else
    echo "❌ Nginx configuration test failed - rollback aborted"
    exit 1
fi

# Log the rollback event
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Auto rollback to BLUE executed" >> /var/log/nginx-rollback.log


