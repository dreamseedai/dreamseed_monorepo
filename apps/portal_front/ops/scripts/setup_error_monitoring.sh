#!/usr/bin/env bash
set -euo pipefail

# Setup error monitoring and alerting
echo "📊 Setting up error monitoring and alerting"

# Create error monitoring script
cat > /tmp/nginx-error-monitor.sh << 'MONITOR_EOF'
#!/usr/bin/env bash
# Monitor nginx 5xx errors and send alerts

LOG_FILE="/var/log/nginx/error.log"
ALERT_THRESHOLD=10  # Alert if more than 10 errors in 5 minutes
TIME_WINDOW=300     # 5 minutes in seconds

# Count 5xx errors in the last 5 minutes
ERROR_COUNT=$(tail -n 1000 "$LOG_FILE" | \
    awk -v threshold=$(date -d "5 minutes ago" +%s) '
    {
        # Parse timestamp and convert to epoch
        gsub(/\[/, "", $4)
        gsub(/:/, " ", $4)
        timestamp = mktime($4)
        if (timestamp > threshold && $0 ~ /5[0-9][0-9]/) {
            count++
        }
    }
    END { print count+0 }')

if [ "$ERROR_COUNT" -gt "$ALERT_THRESHOLD" ]; then
    echo "ALERT: $ERROR_COUNT 5xx errors detected in the last 5 minutes"
    # Add your alerting mechanism here (email, Slack, etc.)
    # Example: curl -X POST -H 'Content-type: application/json' \
    #   --data '{"text":"Nginx 5xx Alert: '$ERROR_COUNT' errors"}' \
    #   $SLACK_WEBHOOK_URL
fi
MONITOR_EOF

# Make executable and install
chmod +x /tmp/nginx-error-monitor.sh
sudo mv /tmp/nginx-error-monitor.sh /usr/local/bin/nginx-error-monitor.sh

# Add to crontab (run every 5 minutes)
echo "*/5 * * * * root /usr/local/bin/nginx-error-monitor.sh" | sudo tee /etc/cron.d/nginx-error-monitor

echo "✅ Error monitoring setup complete"
echo "📊 Monitors 5xx errors every 5 minutes"
echo "🚨 Alerts when threshold exceeded"
echo "🔧 Configure alerting mechanism in /usr/local/bin/nginx-error-monitor.sh"
