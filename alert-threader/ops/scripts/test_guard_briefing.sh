#!/usr/bin/env bash
# Test script for Guard-Window Briefing System
set -euo pipefail

echo "🧪 Testing Guard-Window Briefing System..."

# Test environment variables
REQUIRED_VARS=(
    "PROM_URL"
    "LOKI_URL" 
    "SLACK_BOT_TOKEN"
    "SLACK_CHANNEL_ID"
    "THREAD_TS"
)

# Optional dashboard URL variables
OPTIONAL_VARS=(
    "GRAFANA_PANEL_URL"
    "PROM_DASH_URL"
    "LOKI_EXPLORE_URL"
    "SLO_DASH_URL"
    "SLA_DASH_URL"
    "JVM_DASH_URL"
    "DB_DASH_URL"
)

echo "📋 Checking required environment variables..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "❌ Missing required variable: $var"
        exit 1
    else
        echo "✅ $var is set"
    fi
done

echo "📋 Checking optional dashboard URL variables..."
for var in "${OPTIONAL_VARS[@]}"; do
    if [ -n "${!var:-}" ]; then
        echo "✅ $var is set: ${!var}"
    else
        echo "ℹ️ $var is not set (optional)"
    fi
done

# Test script execution
echo "🔧 Testing briefing script..."
if [ -f "/usr/local/sbin/guard_window_brief.sh" ]; then
    echo "✅ Briefing script exists"
    chmod +x /usr/local/sbin/guard_window_brief.sh
else
    echo "❌ Briefing script not found"
    exit 1
fi

# Test ticket creation scripts
echo "🎫 Testing ticket creation scripts..."
for script in "create_jira_issue.sh" "create_github_issue.sh"; do
    if [ -f "/usr/local/sbin/$script" ]; then
        echo "✅ $script exists"
        chmod +x "/usr/local/sbin/$script"
    else
        echo "❌ $script not found"
        exit 1
    fi
done

# Test systemd services
echo "⚙️ Testing systemd services..."
if systemctl is-enabled guard-brief.timer >/dev/null 2>&1; then
    echo "✅ Guard briefing timer is enabled"
else
    echo "⚠️ Guard briefing timer is not enabled"
fi

if systemctl is-active guard-brief.timer >/dev/null 2>&1; then
    echo "✅ Guard briefing timer is active"
else
    echo "⚠️ Guard briefing timer is not active"
fi

# Test environment file
echo "📄 Testing environment file..."
if [ -f "/etc/guard-brief.env" ]; then
    echo "✅ Environment file exists"
    if [ -r "/etc/guard-brief.env" ]; then
        echo "✅ Environment file is readable"
    else
        echo "❌ Environment file is not readable"
        exit 1
    fi
else
    echo "❌ Environment file not found"
    exit 1
fi

# Test dry run (without actually sending to Slack)
echo "🧪 Testing briefing script (dry run)..."
export DRY_RUN=true
if /usr/local/sbin/guard_window_brief.sh >/dev/null 2>&1; then
    echo "✅ Briefing script executes successfully"
else
    echo "❌ Briefing script execution failed"
    exit 1
fi

# Test QoS guard status
echo "🛡️ Testing QoS guard status..."
if [ -f "/usr/local/sbin/qos_guard.sh" ]; then
    if /usr/local/sbin/qos_guard.sh status >/dev/null 2>&1; then
        echo "✅ QoS guard is unlocked"
    else
        echo "🔒 QoS guard is locked"
    fi
else
    echo "⚠️ QoS guard script not found"
fi

echo "🎉 All tests completed successfully!"
echo ""
echo "📊 System Status:"
echo "• Briefing script: ✅"
echo "• Ticket scripts: ✅"
echo "• Systemd timer: $(systemctl is-active guard-brief.timer 2>/dev/null || echo 'unknown')"
echo "• Environment file: ✅"
echo "• QoS guard: $(/usr/local/sbin/qos_guard.sh status 2>/dev/null || echo 'unknown')"
