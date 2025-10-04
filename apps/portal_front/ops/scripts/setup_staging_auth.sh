#!/usr/bin/env bash
set -euo pipefail

# Setup Basic Auth for staging environment
echo "🔐 Setting up Basic Auth for staging environment"

# Create htpasswd file for staging
echo "📝 Creating .htpasswd file for staging..."
printf 'won:$(openssl passwd -crypt change-me)\n' > /tmp/.htpasswd_staging

# Move to nginx directory
sudo mv /tmp/.htpasswd_staging /etc/nginx/.htpasswd_staging
sudo chown root:root /etc/nginx/.htpasswd_staging
sudo chmod 644 /etc/nginx/.htpasswd_staging

echo "✅ Basic Auth setup complete"
echo "👤 Username: won"
echo "🔑 Password: change-me"
echo "🌐 Apply to staging domains only"

# Test nginx config
echo "🔍 Testing nginx configuration..."
nginx -t && systemctl reload nginx

echo "✅ Staging Basic Auth is now active"
echo "⚠️ Remember to change the password in production!"
