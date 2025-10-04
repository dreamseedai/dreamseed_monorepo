# Alert Threader Template-based Multi-Instance Management

This document describes the template-based multi-instance management system for the Alert Threader service.

## Overview

The system uses systemd template units (`@`) to manage multiple instances of the Alert Threader service, allowing for:

- **Multi-instance deployment**: Run multiple instances on different ports
- **Independent management**: Start, stop, restart individual instances
- **Health monitoring**: Per-instance health checks and monitoring
- **Scalability**: Easy horizontal scaling by adding more instances

## Architecture

### Systemd Template Units

The system uses systemd template units with the pattern `alert-threader@<instance>.service`:

- `alert-threader@py-a.service` - Python instance A
- `alert-threader@py-b.service` - Python instance B  
- `alert-threader@node-a.service` - Node.js instance A
- `alert-threader@go-a.service` - Go instance A

### Instance Configuration

Each instance is configured via:

1. **Environment files**: `/etc/alert-threader.d/<instance>.env`
2. **Port assignment**: Each instance runs on a unique port
3. **Health endpoints**: `/health` endpoint for monitoring

## Usage

### Deploying Instances

```bash
# Deploy all configured instances
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_template_instances.yaml

# Or use the convenience script
./scripts/deploy_template_instances.sh
```

### Managing Individual Instances

```bash
# Start an instance
./scripts/manage_instances.sh start py-a

# Stop an instance
./scripts/manage_instances.sh stop py-a

# Restart an instance
./scripts/manage_instances.sh restart py-a

# Check status
./scripts/manage_instances.sh status py-a

# View logs
./scripts/manage_instances.sh logs py-a

# List all running instances
./scripts/manage_instances.sh list
```

### Health Monitoring

```bash
# Run health checks for all instances
ansible-playbook -i inventory/hosts.yaml playbooks/test_threader.yaml
```

## Configuration

### Instance Definition

Instances are defined in the Ansible inventory or group_vars:

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

### Environment Files

Each instance has its own environment file:

```bash
# /etc/alert-threader.d/py-a.env
THREADER_PORT=9009
THREADER_IMPL=python
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
REDIS_URL=redis://localhost:6379
```

## Benefits

1. **Isolation**: Each instance runs independently
2. **Scalability**: Easy to add/remove instances
3. **Fault Tolerance**: Failure of one instance doesn't affect others
4. **Load Distribution**: Can distribute load across multiple instances
5. **A/B Testing**: Run different versions simultaneously
6. **Rolling Updates**: Update instances one at a time

## Monitoring

The system includes comprehensive monitoring:

- **Health checks**: Per-instance health endpoints
- **Logging**: Centralized logging via journald
- **Metrics**: Prometheus metrics collection
- **Alerting**: Alertmanager integration for failures

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure each instance uses a unique port
2. **Environment file missing**: Check `/etc/alert-threader.d/` directory
3. **Permission issues**: Verify systemd service permissions
4. **Health check failures**: Check service logs and configuration

### Debugging Commands

```bash
# Check systemd status
systemctl status alert-threader@py-a

# View detailed logs
journalctl -u alert-threader@py-a -f

# Test health endpoint
curl http://localhost:9009/health

# Check port usage
netstat -tlnp | grep :9009
```

## Best Practices

1. **Resource limits**: Set appropriate memory/CPU limits per instance
2. **Health checks**: Implement robust health check endpoints
3. **Logging**: Use structured logging for better observability
4. **Monitoring**: Set up comprehensive monitoring and alerting
5. **Backup**: Regular backup of configuration and data
6. **Documentation**: Keep instance configuration documented