# Changelog: Auto-Retry and QoS Guard-Window System

## Overview

This changelog documents the implementation of the auto-retry (backoff) mechanism and post-rollback QoS stability monitoring (guard-window) routine for the Alert Threader CI/CD pipeline.

## New Features

### 1. Auto-Retry Mechanism

#### Scripts
- **`ops/scripts/retry_backoff.sh`**: Generic retry script with exponential backoff
  - Configurable maximum attempts and base delay
  - Exponential backoff: delay = base_seconds * 2^(attempt-1)
  - Clear logging of each attempt
  - Exit codes: 0 on success, 1 on final failure

#### Integration
- **GitHub Actions**: Updated `auto-rollback` job to use retry backoff
- **GitLab CI**: Updated `auto_rollback` job to use retry backoff
- **Ansible**: Integrated into deployment playbooks

### 2. QoS Guard-Window System

#### Scripts
- **`ops/scripts/qos_guard.sh`**: QoS guard-window management
  - Lock/unlock/status commands
  - Persistent lock file at `/run/threader.qos.guard`
  - Automatic cleanup of expired locks
  - Clear status reporting

#### Ansible Playbooks
- **`ansible/playbooks/qos_guard_release.yaml`**: Release guard-window when SLOs are stable
  - Prometheus integration for 5xx error ratio
  - Loki integration for error log rate
  - Health ratio monitoring
  - Configurable SLO thresholds

- **`ansible/playbooks/promo_with_guards.yaml`**: Enhanced promotion with guards
  - Pre-deployment QoS guard-window check
  - Real-time metric validation
  - Automatic guard-window locking after promotion

#### Updated Playbooks
- **`ansible/playbooks/auto_rollback_on_failure.yaml`**: Added QoS guard-window locking after rollback
- **`ansible/playbooks/bluegreen_deploy.yaml`**: Enhanced with guard integration

### 3. Testing Infrastructure

#### Test Scripts
- **`ops/scripts/test_retry_backoff.sh`**: Tests retry backoff mechanism
- **`ops/scripts/test_qos_guard.sh`**: Tests QoS guard mechanism
- **`ops/scripts/test_resilience_system.sh`**: Comprehensive integration tests

#### Test Coverage
- Successful command execution
- Failing command handling
- Eventually successful commands
- Guard-window lock/unlock cycles
- Expired lock cleanup
- Integration scenarios

### 4. Documentation

#### New Documentation
- **`README-Auto-Retry-QoS.md`**: Comprehensive guide for the resilience system
  - Component descriptions
  - Usage examples
  - Configuration options
  - Troubleshooting guide
  - Best practices

#### Updated Documentation
- **`README-CI-CD-Complete.md`**: Added resilience system section
  - Feature overview
  - Integration points
  - Testing instructions
  - Troubleshooting information

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

## Workflow Changes

### 1. Normal Deployment
1. Pre-deployment: Check QoS guard-window status
2. Deployment: Execute with retry backoff
3. Post-deployment: Lock QoS guard-window for monitoring

### 2. Rollback Scenario
1. Failure detection: CI/CD pipeline detects failure
2. Auto-rollback: Execute with retry backoff
3. QoS lock: Lock guard-window to prevent further deployments
4. Stability monitoring: Monitor SLOs over guard-window period
5. Release: Unlock guard-window when SLOs are stable

### 3. Guard-Window Management
1. Lock: Set guard-window lock with expiration time
2. Monitor: Continuously check SLOs during guard-window
3. Release: Unlock when stability criteria are met
4. Cleanup: Automatic cleanup of expired locks

## Monitoring and Alerting

### Metrics
- 5xx error ratio over stability window
- Health ratio over stability window
- Error log rate over stability window

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

## Breaking Changes

None. This is a purely additive feature that enhances existing functionality without breaking changes.

## Migration Guide

### 1. Install Scripts
```bash
# Copy scripts to system location
sudo cp ops/scripts/retry_backoff.sh /usr/local/sbin/
sudo cp ops/scripts/qos_guard.sh /usr/local/sbin/
sudo chmod +x /usr/local/sbin/retry_backoff.sh
sudo chmod +x /usr/local/sbin/qos_guard.sh
```

### 2. Update Ansible Variables
Add the new variables to your Ansible inventory or group_vars files.

### 3. Test the System
```bash
# Run comprehensive tests
./ops/scripts/test_resilience_system.sh
```

### 4. Monitor Integration
Ensure Prometheus and Loki are properly configured and accessible.

## Future Enhancements

1. **Adaptive Retry**: Adjust retry delays based on error types
2. **Machine Learning**: Use ML to predict system stability
3. **Advanced SLOs**: Add more sophisticated stability criteria
4. **Integration**: Better integration with monitoring dashboards
5. **Automation**: Fully automated guard-window management

## Support

For issues or questions about the resilience system:

1. Check the troubleshooting section in `README-Auto-Retry-QoS.md`
2. Run the test scripts to verify functionality
3. Check logs for detailed error information
4. Review configuration variables and environment setup

## Contributors

- Implemented auto-retry mechanism with exponential backoff
- Created QoS guard-window system for stability monitoring
- Integrated with existing CI/CD pipelines
- Added comprehensive testing infrastructure
- Created detailed documentation and troubleshooting guides


