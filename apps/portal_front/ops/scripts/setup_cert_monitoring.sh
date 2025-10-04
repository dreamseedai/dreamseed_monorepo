#!/usr/bin/env bash
set -euo pipefail

# Setup certificate expiry monitoring with cron
DOMAIN=${1:?"domain"}

echo "🔔 Setting up certificate monitoring for $DOMAIN"

# Create cron job for daily certificate check
CRON_JOB="0 8 * * * root /bin/bash $(pwd)/ops/scripts/check_cert_expiry.sh $DOMAIN || true"

# Add to crontab
echo "$CRON_JOB" | sudo tee /etc/cron.d/ds-cert-check

# Set proper permissions
sudo chmod 644 /etc/cron.d/ds-cert-check

echo "✅ Certificate monitoring setup complete"
echo "📅 Daily check at 8:00 AM"
echo "📧 Configure email alerts in /etc/cron.d/ds-cert-check if needed"

# Test the script
echo "🧪 Testing certificate check..."
ops/scripts/check_cert_expiry.sh "$DOMAIN"
