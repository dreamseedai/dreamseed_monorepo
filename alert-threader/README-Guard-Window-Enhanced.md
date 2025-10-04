# 🛡️ Enhanced Guard-Window System

## Overview

The Enhanced Guard-Window System provides comprehensive monitoring and automated response capabilities for the Alert Threader CI/CD pipeline. It includes periodic Slack thread briefings, automatic ticket creation on SLO violations, and intelligent guard-window management.

## 🚀 Features

### 1. Periodic Slack Thread Briefings
- **Frequency**: Every 5 minutes during Guard-Window lock
- **Metrics**: 5xx error ratio, health ratio, error log rate
- **Status Indicators**: Visual indicators (✅❌⚠️) for each metric
- **Guard Status**: Shows current lock status and duration
- **Dashboard Links**: Optional clickable links to Grafana, Prometheus, Loki, SLO, SLA, JVM, and DB dashboards

### 2. Automatic Ticket Creation
- **Jira Integration**: Creates high-priority issues on SLO violations
- **GitHub Issues**: Creates labeled issues with detailed metrics
- **Smart Routing**: Different channels for different environments
- **Rich Context**: Includes host, environment, timestamp, and metrics

### 3. Enhanced SLO Monitoring
- **Multi-Source**: Prometheus + Loki integration
- **Configurable Thresholds**: Customizable SLO parameters
- **Window-Based**: Averages metrics over configurable time windows
- **Real-Time Alerts**: Immediate Slack notifications on violations

## 📁 File Structure

```
alert-threader/
├── ops/
│   ├── scripts/
│   │   ├── guard_window_brief.sh          # Main briefing script
│   │   ├── create_jira_issue.sh           # Jira ticket creation
│   │   ├── create_github_issue.sh         # GitHub issue creation
│   │   └── test_guard_briefing.sh         # Test script
│   ├── services/
│   │   ├── guard-brief.service            # Systemd service
│   │   └── guard-brief.timer              # Systemd timer
│   └── templates/
│       └── guard-brief.env.j2             # Environment template
├── ansible/
│   └── playbooks/
│       ├── setup_guard_briefing.yaml      # Setup playbook
│       └── qos_guard_release.yaml         # Enhanced release playbook
└── .github/
    └── workflows/
        └── qos_guard_release.yml          # GitHub Actions workflow
```

## 🔧 Setup

### 1. Install the Briefing System

```bash
# Run the Ansible playbook
ansible-playbook -i ansible/inventory/hosts.yaml ansible/playbooks/setup_guard_briefing.yaml \
  -e "slack_bot_token=xoxb-YOUR-TOKEN" \
  -e "slack_channel_id=C0123456789" \
  -e "thread_ts=1699999999.000000" \
  -e "prometheus_url=http://prometheus.local:9090" \
  -e "loki_url=http://loki.local:3100" \
  -e "jira_enabled=true" \
  -e "jira_base=https://your.atlassian.net" \
  -e "jira_user=email@domain.com" \
  -e "jira_token=YOUR-JIRA-TOKEN" \
  -e "jira_project=OPS" \
  -e "github_issue_enabled=true" \
  -e "gh_repo=owner/repo" \
  -e "gh_token=YOUR-GH-TOKEN"
```

### 2. Configure Environment Variables

The system uses `/etc/guard-brief.env` for configuration:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-YOUR-TOKEN
SLACK_CHANNEL_ID=C0123456789
THREAD_TS=1699999999.000000

# Monitoring Endpoints
PROM_URL=http://prometheus.local:9090
LOKI_URL=http://loki.local:3100

# SLO Configuration
WINDOW=15m
JOB=threader
MAX_5XX_RATIO=0.01
MIN_HEALTH_RATIO=0.995
MAX_ERROR_LOGS_PER_MIN=1

# Ticket Creation
JIRA_ENABLED=true
JIRA_BASE=https://your.atlassian.net
JIRA_USER=email@domain.com
JIRA_TOKEN=YOUR-JIRA-TOKEN
JIRA_PROJECT=OPS
JIRA_PRIORITY=High
JIRA_LABELS=slo-breach,auto-generated

GITHUB_ISSUE_ENABLED=true
GH_REPO=owner/repo
GH_TOKEN=YOUR-GH-TOKEN
GH_LABELS=slo-breach,auto-generated

# Optional Dashboard Links (plain URLs)
GRAFANA_PANEL_URL=https://grafana.example.com/d/threader-dashboard/threader-overview
PROM_DASH_URL=https://prometheus.example.com/graph?g0.expr=up%7Bjob%3D%22threader%22%7D
LOKI_EXPLORE_URL=https://loki.example.com/explore?left=%5B%22now-1h%22%2C%22now%22%2C%22Loki%22%2C%7B%22expr%22%3A%22%7Bjob%3D%5C%22threader%5C%22%7D%22%7D%5D
SLO_DASH_URL=https://grafana.example.com/d/slo123/slo-dashboard
SLA_DASH_URL=https://grafana.example.com/d/sla456/sla-dashboard
JVM_DASH_URL=https://grafana.example.com/d/jvm789/jvm-dashboard
DB_DASH_URL=https://grafana.example.com/d/db012/db-dashboard
```

### 3. Enable the Timer

```bash
# Enable and start the briefing timer
sudo systemctl enable --now guard-brief.timer

# Check status
sudo systemctl status guard-brief.timer
```

## 🎯 Usage

### Manual Guard Release

```bash
# Release guard with ticket creation
ansible-playbook -i ansible/inventory/hosts.yaml ansible/playbooks/qos_guard_release.yaml \
  -e "jira_enabled=true" \
  -e "github_issue_enabled=true" \
  -e "slack_thread_ts=1699999999.000000"
```

### GitHub Actions Workflow

```yaml
# Trigger guard release with ticket creation
- name: Release Guard
  uses: ./.github/workflows/qos_guard_release.yml
  with:
    create_ticket: true
    jira_enabled: true
    github_issue_enabled: true
    thread_ts: "1699999999.000000"
```

### Environment-Specific Dashboard URLs

```yaml
# Resolve dashboard URLs based on environment
- name: Resolve Dashboard Links
  uses: ./.github/workflows/_resolve_dashboard_links.yml
  with:
    environment: production  # or staging
  secrets:
    GRAFANA_BASE_STG: ${{ secrets.GRAFANA_BASE_STG }}
    GRAFANA_BASE_PROD: ${{ secrets.GRAFANA_BASE_PROD }}

# Use resolved URLs in Slack notifications
- name: Notify Slack
  uses: ./.github/workflows/_slack_thread_reply.yml
  with:
    thread_ts: ${{ needs.open_thread.outputs.thread_ts }}
    text: "Deployment completed"
    grafana_panel_url: ${{ needs.resolve_links.outputs.grafana_panel_url }}
    slo_dash_url: ${{ needs.resolve_links.outputs.slo_dash_url }}
    sla_dash_url: ${{ needs.resolve_links.outputs.sla_dash_url }}
    jvm_dash_url: ${{ needs.resolve_links.outputs.jvm_dash_url }}
    db_dash_url: ${{ needs.resolve_links.outputs.db_dash_url }}
```

### Testing the System

```bash
# Run comprehensive tests
sudo /usr/local/sbin/test_guard_briefing.sh

# Test briefing script manually
sudo /usr/local/sbin/guard_window_brief.sh

# Test ticket creation (dry run)
JIRA_BASE=https://your.atlassian.net \
JIRA_USER=email@domain.com \
JIRA_TOKEN=YOUR-TOKEN \
JIRA_PROJECT=OPS \
SUMMARY="Test Issue" \
DESC="Test Description" \
/usr/local/sbin/create_jira_issue.sh
```

## 📊 Monitoring

### Slack Thread Briefings

The system posts periodic updates to the Slack thread:

```
🛡️ Guard-Window Brief (window=15m)
• 5xx avg ratio: 0.0023 ✅ (threshold: 0.01)
• health ok avg: 0.9987 ✅ (threshold: 0.995)
• error logs/min: 0.15 ✅ (threshold: 1)
• Guard status: 🔒 Locked (12m)
• Job: threader
• Time: 2024-01-15 14:30:00 UTC
• Grafana: <https://grafana.example.com/d/threader-dashboard/threader-overview|panel>
• Prometheus: <https://prometheus.example.com/graph?g0.expr=up%7Bjob%3D%22threader%22%7D|query>
• Loki: <https://loki.example.com/explore?left=%5B%22now-1h%22%2C%22now%22%2C%22Loki%22%2C%7B%22expr%22%3A%22%7Bjob%3D%5C%22threader%5C%22%7D%22%7D%5D|explore>
• SLO: <https://grafana.example.com/d/slo123/slo-dashboard|SLO Dashboard>
• SLA: <https://grafana.example.com/d/sla456/sla-dashboard|SLA Dashboard>
• JVM: <https://grafana.example.com/d/jvm789/jvm-dashboard|JVM Metrics>
• DB: <https://grafana.example.com/d/db012/db-dashboard|DB Performance>
```

### SLO Violation Alerts

When SLOs are violated, the system:

1. **Creates Tickets**: Jira issues and/or GitHub issues
2. **Notifies Slack**: Posts violation details to the thread
3. **Maintains Guard**: Keeps the guard-window locked
4. **Provides Context**: Includes host, environment, and metrics

### Ticket Examples

#### Jira Issue
- **Project**: OPS
- **Type**: Bug
- **Priority**: High
- **Labels**: slo-breach, auto-generated
- **Description**: Detailed metrics and context

#### GitHub Issue
- **Title**: SLO breach detected on hostname
- **Labels**: slo-breach, auto-generated
- **Body**: Comprehensive metrics and investigation guidance

## 🔧 Configuration

### SLO Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_5XX_RATIO` | 0.01 | Maximum 5xx error ratio (1%) |
| `MIN_HEALTH_RATIO` | 0.995 | Minimum health check success rate (99.5%) |
| `MAX_ERROR_LOGS_PER_MIN` | 1 | Maximum error logs per minute |
| `WINDOW` | 15m | Time window for metric averaging |

### Briefing Frequency

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OnBootSec` | 2m | Delay after boot before first briefing |
| `OnUnitActiveSec` | 5m | Interval between briefings |
| `RandomizedDelaySec` | 30s | Random delay to prevent thundering herd |

### Ticket Configuration

#### Jira
- **Priority**: High (configurable)
- **Labels**: slo-breach, auto-generated
- **Project**: OPS (configurable)
- **Type**: Bug (configurable)

#### GitHub
- **Labels**: slo-breach, auto-generated
- **Assignees**: Configurable
- **Repository**: Current repository

### Dashboard URL Configuration

#### Grafana Panel
- **Variable**: `GRAFANA_PANEL_URL`
- **Format**: Full URL to Grafana dashboard panel
- **Example**: `https://grafana.example.com/d/threader-dashboard/threader-overview?orgId=1&refresh=5m`

#### Prometheus Query
- **Variable**: `PROM_DASH_URL`
- **Format**: Full URL to Prometheus query interface
- **Example**: `https://prometheus.example.com/graph?g0.expr=up%7Bjob%3D%22threader%22%7D&g0.tab=0`

#### Loki Explore
- **Variable**: `LOKI_EXPLORE_URL`
- **Format**: Full URL to Loki explore interface
- **Example**: `https://loki.example.com/explore?left=%5B%22now-1h%22%2C%22now%22%2C%22Loki%22%2C%7B%22expr%22%3A%22%7Bjob%3D%5C%22threader%5C%22%7D%22%7D%5D`

#### SLO Dashboard
- **Variable**: `SLO_DASH_URL`
- **Format**: Full URL to SLO dashboard
- **Example**: `https://grafana.example.com/d/slo123/slo-dashboard`

#### SLA Dashboard
- **Variable**: `SLA_DASH_URL`
- **Format**: Full URL to SLA dashboard
- **Example**: `https://grafana.example.com/d/sla456/sla-dashboard`

#### JVM Metrics
- **Variable**: `JVM_DASH_URL`
- **Format**: Full URL to JVM metrics dashboard
- **Example**: `https://grafana.example.com/d/jvm789/jvm-dashboard`

#### DB Performance
- **Variable**: `DB_DASH_URL`
- **Format**: Full URL to database performance dashboard
- **Example**: `https://grafana.example.com/d/db012/db-dashboard`

#### URL Encoding
- **Prometheus**: Use URL encoding for special characters (`%7B` for `{`, `%22` for `"`)
- **Loki**: Use URL encoding for complex query parameters
- **Grafana**: Include refresh parameters and time ranges as needed

## 🚨 Troubleshooting

### Common Issues

1. **Briefing Script Fails**
   ```bash
   # Check environment variables
   sudo systemctl status guard-brief.service
   journalctl -u guard-brief.service -f
   ```

2. **Ticket Creation Fails**
   ```bash
   # Test individual scripts
   /usr/local/sbin/create_jira_issue.sh
   /usr/local/sbin/create_github_issue.sh
   ```

3. **Timer Not Running**
   ```bash
   # Check timer status
   sudo systemctl status guard-brief.timer
   sudo systemctl list-timers | grep guard
   ```

4. **Environment File Issues**
   ```bash
   # Check file permissions and content
   ls -la /etc/guard-brief.env
   sudo cat /etc/guard-brief.env
   ```

### Debug Commands

```bash
# Test briefing script with debug output
sudo -E /usr/local/sbin/guard_window_brief.sh

# Check systemd timer logs
journalctl -u guard-brief.timer -f

# Verify environment file
sudo systemd-analyze verify /etc/systemd/system/guard-brief.service

# Test ticket creation with verbose output
JIRA_BASE=https://your.atlassian.net \
JIRA_USER=email@domain.com \
JIRA_TOKEN=YOUR-TOKEN \
JIRA_PROJECT=OPS \
SUMMARY="Debug Test" \
DESC="Debug Description" \
/usr/local/sbin/create_jira_issue.sh
```

## 🔒 Security Considerations

1. **Environment File**: Store sensitive tokens in `/etc/guard-brief.env` with restricted permissions (640)
2. **SOPS/Vault**: Use secret management for production deployments
3. **Network Access**: Ensure monitoring endpoints are accessible
4. **Token Rotation**: Regularly rotate Slack, Jira, and GitHub tokens
5. **Audit Logs**: Monitor ticket creation and briefing activities

## 📈 Performance

- **Resource Usage**: Minimal CPU and memory overhead
- **Network Impact**: Lightweight API calls every 5 minutes
- **Storage**: No persistent data storage required
- **Scalability**: Supports multiple environments and channels

## 🔄 Maintenance

### Regular Tasks

1. **Monitor Briefings**: Check Slack threads for system health
2. **Review Tickets**: Ensure SLO violations are addressed
3. **Update Thresholds**: Adjust SLO parameters as needed
4. **Rotate Tokens**: Update authentication credentials
5. **Test System**: Run test scripts periodically

### Updates

1. **Script Updates**: Deploy new versions via Ansible
2. **Configuration Changes**: Update environment files
3. **Service Restart**: Reload systemd services after changes
4. **Validation**: Test all components after updates

## 📚 Related Documentation

- [README-Auto-Retry-QoS.md](README-Auto-Retry-QoS.md) - Core resilience system
- [README-CI-CD-Complete.md](README-CI-CD-Complete.md) - Complete CI/CD setup
- [Slack-Bot-Setup.md](docs/Slack-Bot-Setup.md) - Slack integration guide
- [GitHub-Environments-Setup.md](docs/GitHub-Environments-Setup.md) - Environment configuration

## 🎉 Success Metrics

- **MTTR Reduction**: Faster incident response through automated alerts
- **Visibility**: Clear system health status in Slack threads
- **Accountability**: Automatic ticket creation for SLO violations
- **Reliability**: Proactive monitoring and guard-window management
- **Efficiency**: Reduced manual monitoring overhead

The Enhanced Guard-Window System provides comprehensive monitoring, alerting, and response capabilities that significantly improve the reliability and observability of the Alert Threader CI/CD pipeline.
