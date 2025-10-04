# Auto-Retry and QoS Guard-Window System

This document describes the auto-retry (backoff) mechanism and post-rollback QoS stability monitoring (guard-window) routine implemented in the Alert Threader CI/CD pipeline.

## Overview

The system provides two key resilience features:

1. **Auto-Retry with Exponential Backoff**: Automatically retries failed operations with increasing delays
2. **QoS Guard-Window**: Prevents deployments during system instability periods after rollbacks

## Components

### 1. Retry Backoff Script (`ops/scripts/retry_backoff.sh`)

A generic retry script that implements exponential backoff for any command.

**Usage:**
```bash
retry_backoff.sh <max_attempts> <base_seconds> -- <command...>
```

**Example:**
```bash
retry_backoff.sh 3 5 -- ansible-playbook deploy.yaml
```

**Features:**
- Configurable maximum attempts (default: 3)
- Configurable base delay in seconds (default: 5)
- Exponential backoff: delay = base_seconds * 2^(attempt-1)
- Clear logging of each attempt
- Exit codes: 0 on success, 1 on final failure

### 2. QoS Guard Script (`ops/scripts/qos_guard.sh`)

Manages a Quality of Service guard-window to prevent deployments during instability.

**Usage:**
```bash
qos_guard.sh lock|unlock|status [minutes]
```

**Commands:**
- `lock [minutes]`: Lock the guard-window for specified minutes (default: 15)
- `unlock`: Unlock the guard-window immediately
- `status`: Check if guard-window is locked (exit 1 if locked)

**Features:**
- Persistent lock file at `/run/threader.qos.guard`
- Automatic cleanup of expired locks
- Clear status reporting
- Integration with CI/CD pipelines

### 3. QoS Guard Release Playbook (`ansible/playbooks/qos_guard_release.yaml`)

Ansible playbook that releases the QoS guard-window when SLOs are stable.

**Variables:**
- `prom_url`: Prometheus URL (default: `http://prometheus.local:9090`)
- `loki_url`: Loki URL (default: `http://loki.local:3100`)
- `job`: Threader job name (default: `threader`)
- `max_5xx_ratio`: Maximum 5xx error ratio (default: 0.01)
- `min_health_ratio`: Minimum health ratio (default: 0.995)
- `max_error_logs_per_min`: Maximum error logs per minute (default: 1)
- `window`: Stability window duration (default: `15m`)

**SLO Checks:**
1. 5xx error ratio over the stability window
2. Health ratio over the stability window
3. Error log rate over the stability window

### 4. Promotion Guards Playbook (`ansible/playbooks/promo_with_guards.yaml`)

Enhanced promotion playbook that includes QoS guard-window checks and metric/log guards.

**Features:**
- Pre-deployment QoS guard-window check
- Real-time metric validation (5xx ratio, health ratio, error logs)
- Automatic QoS guard-window locking after successful promotion
- Integration with Prometheus and Loki

## Integration Points

### GitHub Actions

The auto-retry mechanism is integrated into the `auto-rollback` job:

```yaml
- name: Install retry backoff script
  run: |
    sudo cp alert-threader/ops/scripts/retry_backoff.sh /usr/local/sbin/
    sudo chmod +x /usr/local/sbin/retry_backoff.sh

- name: Execute auto rollback with retry
  run: |
    /usr/local/sbin/retry_backoff.sh 3 5 -- ansible-playbook -i alert-threader/ansible/inventory/hosts.yaml alert-threader/ansible/playbooks/auto_rollback_on_failure.yaml
```

### GitLab CI

Similar integration in the `auto_rollback` job:

```yaml
script:
  - cp ops/scripts/retry_backoff.sh /usr/local/sbin/ && chmod +x /usr/local/sbin/retry_backoff.sh
  - /usr/local/sbin/retry_backoff.sh 3 5 -- ansible-playbook -i ansible/inventory/hosts.yaml ansible/playbooks/auto_rollback_on_failure.yaml
```

### Ansible Playbooks

The auto-rollback playbook now includes QoS guard-window locking:

```yaml
- name: Lock QoS guard-window after rollback
  shell: "{{ qos_guard_script | default('/usr/local/sbin/qos_guard.sh') }} lock {{ qos_guard_window | default(15) }}"
  when: rollback_status == 'SUCCESS'
```

## Workflow

### 1. Normal Deployment

1. **Pre-deployment**: Check QoS guard-window status
2. **Deployment**: Execute deployment with retry backoff
3. **Post-deployment**: Lock QoS guard-window for stability monitoring

### 2. Rollback Scenario

1. **Failure Detection**: CI/CD pipeline detects failure
2. **Auto-Rollback**: Execute rollback with retry backoff
3. **QoS Lock**: Lock guard-window to prevent further deployments
4. **Stability Monitoring**: Monitor SLOs over the guard-window period
5. **Release**: Unlock guard-window when SLOs are stable

### 3. Guard-Window Management

1. **Lock**: Set guard-window lock with expiration time
2. **Monitor**: Continuously check SLOs during guard-window
3. **Release**: Unlock when stability criteria are met
4. **Cleanup**: Automatic cleanup of expired locks

## Configuration

### Environment Variables

```bash
# Retry configuration
MAX_RETRY_ATTEMPTS=3
BASE_RETRY_DELAY=5

# QoS guard-window configuration
QOS_GUARD_WINDOW=15  # minutes
QOS_GUARD_SCRIPT=/usr/local/sbin/qos_guard.sh

# SLO thresholds
MAX_5XX_RATIO=0.01
MIN_HEALTH_RATIO=0.995
MAX_ERROR_LOGS_PER_MIN=1
STABILITY_WINDOW=15m

# Monitoring endpoints
PROMETHEUS_URL=http://prometheus.local:9090
LOKI_URL=http://loki.local:3100
THREADER_JOB=threader
```

### Ansible Variables

```yaml
# In group_vars or host_vars
qos_guard_script: /usr/local/sbin/qos_guard.sh
qos_guard_window: 15
retry_script: /usr/local/sbin/retry_backoff.sh
max_5xx_ratio: 0.01
min_health_ratio: 0.995
max_error_logs_per_min: 1
stability_window: 15m
prometheus_url: http://prometheus.local:9090
loki_url: http://loki.local:3100
threader_job: threader
```

## Monitoring and Alerting

### Metrics

The system monitors the following metrics:

1. **5xx Error Ratio**: `avg_over_time(job:http_5xx_ratio_1m{job="threader"}[15m])`
2. **Health Ratio**: `avg_over_time(job:health_ok_ratio_1m{job="threader"}[15m])`
3. **Error Log Rate**: `sum(rate({job="threader"} |~ "ERROR|Exception|Traceback"[1m]))`

### Alerts

- QoS guard-window locked for extended periods
- SLO violations during guard-window
- Failed rollback attempts
- Excessive retry attempts

### Logs

- Retry attempts and delays
- QoS guard-window state changes
- SLO check results
- Rollback execution details

## Troubleshooting

### Common Issues

1. **Guard-Window Stuck**: Check for stale lock files in `/run/threader.qos.guard`
2. **Retry Failures**: Verify command syntax and permissions
3. **SLO Check Failures**: Ensure Prometheus/Loki connectivity
4. **Permission Issues**: Check script permissions and ownership

### Debug Commands

```bash
# Check QoS guard-window status
/usr/local/sbin/qos_guard.sh status

# Manually unlock guard-window
/usr/local/sbin/qos_guard.sh unlock

# Test retry mechanism
/usr/local/sbin/retry_backoff.sh 2 3 -- echo "test"

# Check lock file
ls -la /run/threader.qos.guard

# View rollback logs
tail -f /var/log/nginx-rollback.log
```

### Manual Recovery

```bash
# Force unlock guard-window
rm -f /run/threader.qos.guard

# Manual rollback
ansible-playbook -i ansible/inventory/hosts.yaml ansible/playbooks/bluegreen_rollback.yaml

# Check system health
curl -f http://localhost:9009/healthz
```

## Best Practices

1. **Monitor Guard-Windows**: Set up alerts for extended guard-window periods
2. **Tune SLO Thresholds**: Adjust thresholds based on system behavior
3. **Test Retry Logic**: Regularly test retry mechanisms in staging
4. **Document Incidents**: Track rollback patterns and root causes
5. **Review Metrics**: Regularly review SLO metrics and adjust thresholds

## Future Enhancements

1. **Adaptive Retry**: Adjust retry delays based on error types
2. **Machine Learning**: Use ML to predict system stability
3. **Advanced SLOs**: Add more sophisticated stability criteria
4. **Integration**: Better integration with monitoring dashboards
5. **Automation**: Fully automated guard-window management


