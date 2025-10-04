#!/usr/bin/env bash
set -euo pipefail

# Setup log rotation for nginx site logs
echo "📋 Setting up log rotation for nginx site logs"

# Create logrotate configuration for site-specific logs
cat > /tmp/nginx-dreamseed << 'LOGROTATE_EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}
LOGROTATE_EOF

# Install logrotate configuration
sudo mv /tmp/nginx-dreamseed /etc/logrotate.d/nginx-dreamseed
sudo chmod 644 /etc/logrotate.d/nginx-dreamseed

echo "✅ Log rotation setup complete"
echo "📅 Daily rotation, 14 days retention, compression enabled"
echo "🔄 Test with: sudo logrotate -d /etc/logrotate.d/nginx-dreamseed"
