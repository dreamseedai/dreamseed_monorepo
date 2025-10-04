# Alert Threader Automation System

This document describes the comprehensive automation system for the Alert Threader service, including health checks, deployment strategies, monitoring, and CI/CD pipelines.

## Overview

The automation system provides:

- **Health Check Automation**: Automatic monitoring and restart on failure
- **Advanced Deployment Strategies**: Canary, Rolling, Blue-Green deployments
- **Monitoring & Alerting**: Prometheus, Alertmanager, Grafana integration
- **CI/CD Pipeline**: GitHub Actions workflow for automated deployment
- **Unified Management**: Single interface for all automation features

## Architecture

### Health Check System

The health check system uses systemd timers and custom scripts:

- **Health Check Scripts**: Per-instance health monitoring
- **Systemd Timers**: Automated health checks every minute
- **Auto-restart**: Automatic service restart on health check failure
- **Escalation**: Alertmanager integration for persistent failures

### Deployment Strategies

#### 1. Canary Deployment
- Deploy to a small subset of instances
- Monitor metrics and logs
- Manual approval for full rollout
- Automatic rollback on failure

#### 2. Rolling Update
- Update instances one at a time
- Health check between updates
- Automatic rollback on failure
- Zero-downtime deployment

#### 3. Blue-Green Deployment
- Maintain two identical environments
- Switch traffic between Blue and Green
- Instant rollback capability
- Full environment testing

### Monitoring Stack

- **Prometheus**: Metrics collection and alerting
- **Alertmanager**: Alert routing and notification
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation and analysis

## Usage

### Quick Start

```bash
# Deploy all services
./automation_manager.sh deploy

# Run health checks
./automation_manager.sh health

# Start canary deployment
./automation_manager.sh canary

# Set up monitoring
./automation_manager.sh monitor
```

### Health Check Management

```bash
# Check health of all instances
./automation_manager.sh health

# View logs for specific instance
./automation_manager.sh logs py-a

# Check status of all instances
./automation_manager.sh status
```

### Deployment Management

```bash
# Canary deployment
./automation_manager.sh canary

# Rolling update
./automation_manager.sh rolling

# Blue-Green deployment
ansible-playbook -i inventory/hosts.yaml playbooks/bluegreen_deploy.yaml

# Rollback
./automation_manager.sh rollback
```

### Monitoring Setup

```bash
# Set up monitoring stack
./automation_manager.sh monitor

# Access Grafana
open http://localhost:3000

# Access Prometheus
open http://localhost:9090

# Access Alertmanager
open http://localhost:9093
```

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# Vault configuration
export VAULT_ADDR="https://vault.example.com"
export VAULT_TOKEN="your-token"

# Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Redis configuration
export REDIS_URL="redis://localhost:6379"
```

### Instance Configuration

Configure instances in the Ansible inventory:

```yaml
threader_instances:
  - name: py-a
    impl: python
    port: 9009
    env_file: /etc/alert-threader.d/py-a.env
  - name: node-a
    impl: node
    port: 9010
    env_file: /etc/alert-threader.d/node-a.env
  - name: go-a
    impl: go
    port: 9011
    env_file: /etc/alert-threader.d/go-a.env
```

### Alert Rules

Configure alert rules in Prometheus:

```yaml
groups:
  - name: threader.alerts
    rules:
      - alert: ThreaderInstanceDown
        expr: up{job=~"alert_threader_.*"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Alert Threader instance is down"
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline includes:

1. **Build & Test**: Linting, security scanning, unit tests
2. **Staging Deployment**: Automated deployment to staging
3. **Production Deployment**: Manual approval for production
4. **Monitoring**: Health checks and alerting

### Pipeline Stages

```yaml
# Build and test
- name: Build and test
  run: |
    ansible-lint .
    trivy fs --severity HIGH,CRITICAL .

# Deploy to staging
- name: Deploy to staging
  run: |
    ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml

# Deploy to production
- name: Deploy to production
  if: github.ref == 'refs/heads/main'
  run: |
    ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml
```

## Monitoring & Alerting

### Prometheus Metrics

The system exposes the following metrics:

- `http_requests_total`: HTTP request counter
- `http_request_duration_seconds`: Request duration histogram
- `threader_health_status`: Health check status
- `threader_errors_total`: Error counter

### Alert Rules

Key alert rules:

- **Instance Down**: Service not responding
- **High Error Rate**: 5xx errors > 5%
- **Health Check Failed**: Health endpoint failing
- **Log Error Spike**: Error logs > 5/min

### Slack Integration

Alerts are sent to Slack channels:

- `#alerts-critical`: Critical alerts
- `#alerts-warning`: Warning alerts
- `#alerts-info`: Informational alerts

## Troubleshooting

### Common Issues

1. **Health Check Failures**
   - Check service logs
   - Verify health endpoint
   - Check network connectivity

2. **Deployment Failures**
   - Check Ansible logs
   - Verify inventory configuration
   - Check target host connectivity

3. **Monitoring Issues**
   - Check Prometheus configuration
   - Verify Alertmanager setup
   - Check Slack webhook configuration

### Debug Commands

```bash
# Check service status
systemctl status alert-threader@py-a

# View service logs
journalctl -u alert-threader@py-a -f

# Test health endpoint
curl http://localhost:9009/health

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test Alertmanager
curl http://localhost:9093/api/v1/alerts
```

## Best Practices

### Deployment

1. **Always test in staging first**
2. **Use canary deployments for risky changes**
3. **Monitor metrics during deployment**
4. **Have rollback plan ready**

### Monitoring

1. **Set up comprehensive alerting**
2. **Monitor key business metrics**
3. **Use dashboards for visualization**
4. **Regular alert rule review**

### Security

1. **Use Vault for secrets management**
2. **Rotate credentials regularly**
3. **Monitor for security issues**
4. **Keep dependencies updated**

## Advanced Features

### Auto-scaling

The system supports auto-scaling based on metrics:

```yaml
# Auto-scale based on CPU usage
- name: Scale up on high CPU
  when: cpu_usage > 80
  systemd:
    name: "alert-threader@{{ item }}"
    state: started
  loop: "{{ additional_instances }}"
```

### Multi-region Deployment

Support for multi-region deployments:

```yaml
# Deploy to multiple regions
- name: Deploy to all regions
  hosts: "{{ groups['all_regions'] }}"
  tasks:
    - name: Deploy threader
      include_tasks: deploy_threader.yml
```

### Disaster Recovery

Automated disaster recovery procedures:

```yaml
# Disaster recovery playbook
- name: Disaster recovery
  hosts: backup_servers
  tasks:
    - name: Restore from backup
      include_tasks: restore_backup.yml
    - name: Start services
      include_tasks: start_services.yml
```

## Contributing

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

### Code Standards

- Use Ansible best practices
- Follow naming conventions
- Add comprehensive comments
- Include error handling

### Testing

- Test in staging environment
- Use automated testing
- Verify all scenarios
- Document test results