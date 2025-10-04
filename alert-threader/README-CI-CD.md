# CI/CD Pipeline Documentation

This document describes the comprehensive CI/CD pipeline for the Alert Threader automation system, including GitHub Actions and GitLab CI integration.

## Overview

The CI/CD pipeline provides:

- **Automated Testing**: Security scanning, performance testing, end-to-end testing
- **Deployment Automation**: SOPS/Vault environment setup, multi-instance deployment
- **Advanced Deployment Strategies**: Canary, Rolling, Blue-Green deployments
- **Monitoring Integration**: Prometheus, Alertmanager, Grafana setup
- **Backup & Recovery**: Automated SQLite backup and restore
- **Release Management**: Automated release creation and deployment

## GitHub Actions Workflows

### 1. Reusable Ansible Runner (`_ansible-runner.yml`)

A reusable workflow that provides a common interface for running Ansible playbooks with proper authentication and environment setup.

**Features:**
- SSH key management
- Vault/AWS credentials injection
- Python and Ansible installation
- Host key verification

**Usage:**
```yaml
uses: ./.github/workflows/_ansible-runner.yml
with:
  playbook: ansible/playbooks/deploy_threader.yaml
  extra_vars: "threader_impl=multi"
secrets: inherit
```

### 2. Environment & Threader Deployment (`deploy_env_and_threader.yml`)

Deploys the environment (SOPS/Vault) and Alert Threader services.

**Inputs:**
- `mode`: Environment mode (sops|vault)
- `impl`: Threader implementation (python|node|go|multi)

**Jobs:**
1. **env**: Deploy environment configuration
2. **app**: Deploy threader services

### 3. Canary + Blue-Green Deployment (`deploy_canary_bluegreen.yml`)

Implements advanced deployment strategies with automated promotion.

**Inputs:**
- `canary`: Instance name for canary deployment

**Jobs:**
1. **canary**: Deploy to selected instance
2. **guards**: Run metric/log-based validation
3. **bluegreen**: Switch traffic to new version

### 4. Rolling Update (`rolling_update.yml`)

Performs rolling updates across all instances.

**Features:**
- Serial deployment (one instance at a time)
- Health check validation between updates
- Automatic rollback on failure

### 5. Security Scanning (`security_scan.yml`)

Comprehensive security scanning and vulnerability assessment.

**Tools:**
- Trivy (vulnerability scanner)
- Bandit (Python security linter)
- Safety (dependency vulnerability check)
- Ansible Lint (configuration security)

**Triggers:**
- Push to main/develop branches
- Pull requests
- Weekly schedule

### 6. Performance Testing (`performance_test.yml`)

Load testing using Locust for performance validation.

**Inputs:**
- `target_url`: Target URL for testing
- `duration`: Test duration in seconds
- `users`: Number of concurrent users

**Features:**
- Configurable load parameters
- HTML report generation
- Artifact upload

### 7. Monitoring Setup (`monitoring_setup.yml`)

Deploys and configures the monitoring stack.

**Inputs:**
- `environment`: Target environment (staging|production)
- `slack_webhook`: Slack webhook URL

**Components:**
- Prometheus (metrics collection)
- Alertmanager (alert routing)
- Grafana (visualization)

### 8. Backup & Restore (`backup_restore.yml`)

Automated backup and restore operations.

**Inputs:**
- `action`: Operation type (backup|restore)
- `backup_name`: Backup name for restore

**Features:**
- SQLite database backup
- S3 upload (optional)
- Automatic cleanup
- Health verification

### 9. End-to-End Testing (`end_to_end_test.yml`)

Comprehensive end-to-end testing of the Alert Threader system.

**Test Coverage:**
- Health endpoint validation
- Alert processing
- Metrics collection
- Thread persistence
- Error handling
- Concurrent request handling

### 10. Release Management (`release.yml`)

Automated release creation and deployment.

**Features:**
- Multi-platform binary builds
- Staging deployment
- Production deployment (main branch only)
- Release notes generation

## GitLab CI Pipeline

### Pipeline Stages

1. **env**: Environment setup (SOPS/Vault)
2. **deploy**: Threader service deployment
3. **canary**: Canary deployment
4. **guard**: Metric/log validation
5. **switch**: Blue-Green traffic switch

### Configuration

The GitLab CI pipeline uses a single `.gitlab-ci.yml` file with reusable job templates.

**Variables:**
- `MODE`: Environment mode (sops|vault)
- `IMPL`: Threader implementation
- `CANARY`: Canary instance name
- `SSH_PRIVATE_KEY`: SSH private key for deployment

## Required Secrets

### GitHub Secrets

- `SSH_PRIVATE_KEY`: SSH private key for server access
- `VAULT_ADDR`: Vault server address
- `VAULT_ROLE_ID`: Vault AppRole role ID
- `VAULT_SECRET_ID`: Vault AppRole secret ID
- `AWS_ACCESS_KEY_ID`: AWS access key (for S3 backup)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

### GitLab CI Variables

- `SSH_PRIVATE_KEY`: SSH private key
- `VAULT_ADDR`: Vault server address
- `VAULT_ROLE_ID`: Vault AppRole role ID
- `VAULT_SECRET_ID`: Vault AppRole secret ID
- `MODE`: Environment mode
- `IMPL`: Threader implementation
- `CANARY`: Canary instance name

## Usage Examples

### GitHub Actions

#### Deploy Environment and Services
```bash
# Manual trigger
gh workflow run deploy_env_and_threader.yml \
  -f mode=sops \
  -f impl=multi
```

#### Run Canary Deployment
```bash
# Manual trigger
gh workflow run deploy_canary_bluegreen.yml \
  -f canary=py-a
```

#### Performance Testing
```bash
# Manual trigger
gh workflow run performance_test.yml \
  -f target_url=http://192.168.68.116:9009 \
  -f duration=120 \
  -f users=20
```

### GitLab CI

#### Trigger Pipeline
```bash
# Using GitLab CLI
glab ci run --variable MODE=sops --variable IMPL=multi
```

#### Manual Pipeline
```bash
# Using GitLab web interface
# Go to CI/CD > Pipelines > Run Pipeline
# Set variables: MODE=sops, IMPL=multi, CANARY=py-a
```

## Best Practices

### Security

1. **Secret Management**: Use GitHub Secrets or GitLab CI Variables for sensitive data
2. **Access Control**: Limit SSH key access to necessary servers only
3. **Audit Logging**: Monitor all deployment activities
4. **Regular Rotation**: Rotate SSH keys and API tokens regularly

### Deployment

1. **Staging First**: Always test in staging before production
2. **Canary Strategy**: Use canary deployments for risky changes
3. **Rollback Plan**: Always have a rollback strategy ready
4. **Health Monitoring**: Monitor services during and after deployment

### Testing

1. **Comprehensive Coverage**: Run all test suites before deployment
2. **Performance Validation**: Include performance testing in CI
3. **Security Scanning**: Regular vulnerability assessments
4. **End-to-End Testing**: Validate complete workflows

### Monitoring

1. **Alert Configuration**: Set up proper alerting rules
2. **Dashboard Setup**: Create monitoring dashboards
3. **Log Aggregation**: Centralize log collection
4. **Metrics Collection**: Monitor key performance indicators

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Check SSH key permissions
   - Verify host key in known_hosts
   - Ensure server is accessible

2. **Ansible Playbook Failed**
   - Check inventory configuration
   - Verify target server state
   - Review Ansible logs

3. **Service Health Check Failed**
   - Check service logs
   - Verify port availability
   - Check firewall rules

4. **Vault Authentication Failed**
   - Verify Vault credentials
   - Check Vault server connectivity
   - Validate AppRole configuration

### Debug Commands

```bash
# Check GitHub Actions logs
gh run view <run-id> --log

# Check GitLab CI logs
glab ci view <pipeline-id>

# Test Ansible connectivity
ansible all -i inventory/hosts.yaml -m ping

# Check service status
systemctl status alert-threader-python
journalctl -u alert-threader-python -f
```

## Integration with Existing Systems

### Slack Integration

The pipeline integrates with Slack for notifications:

- **Deployment Status**: Success/failure notifications
- **Alert Routing**: Severity-based channel routing
- **Thread Management**: Persistent alert threads

### Monitoring Integration

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification

### Backup Integration

- **S3 Storage**: Automated backup upload
- **Retention Policy**: Automatic cleanup of old backups
- **Restore Validation**: Health check after restore

This comprehensive CI/CD pipeline ensures reliable, secure, and automated deployment of the Alert Threader system with full monitoring and backup capabilities.


