# r-analytics Service Deployment

## Overview

The r-analytics service is a unified R plumber API (port 8010) that consolidates analytics capabilities:

- **Topic Theta Scoring**: IRT-based ability estimation
- **Improvement Index**: Growth tracking (I_t metric)
- **Goal Attainment**: Probability estimation for target achievement
- **Topic Recommendations**: Next-best-topic suggestions
- **Churn Risk**: 14-day churn probability assessment
- **Report Generation**: Comprehensive analytics report creation

## Architecture

```
FastAPI (analytics_proxy router)
    ↓ (HTTP + JWT)
RAnalyticsClient (Python)
    ↓ (HTTP + Internal Token)
r-analytics (Plumber on K8s)
    ↓
PostgreSQL (via Cloud SQL Proxy)
```

## Prerequisites

1. **Docker Image**: Build and push r-analytics image
2. **Secrets**: Create `r-analytics-internal-token` in Google Secret Manager
3. **Kubernetes**: `gcpsm-secret-store` SecretStore must exist in seedtest namespace
4. **Dependencies**: PostgreSQL with required schemas, R packages installed

## Deployment

### 1. Build and Push Image

```bash
cd /home/won/projects/dreamseed_monorepo/portal_front

# Build the image (assuming r-analytics directory exists with Dockerfile)
docker build -t gcr.io/univprepai/r-analytics:latest \
  -f r-analytics/Dockerfile \
  r-analytics/

# Push to GCR
docker push gcr.io/univprepai/r-analytics:latest
```

### 2. Create Secret in GSM

```bash
# Generate a random token
TOKEN=$(openssl rand -base64 32)

# Create secret in Google Secret Manager
echo -n "$TOKEN" | gcloud secrets create r-analytics-internal-token \
  --data-file=- \
  --project=univprepai

# Or update existing secret
echo -n "$TOKEN" | gcloud secrets versions add r-analytics-internal-token \
  --data-file=- \
  --project=univprepai

# Store token securely for use in R_ANALYTICS_TOKEN environment variable
echo "R_ANALYTICS_TOKEN=$TOKEN" >> .env.local
```

### 3. Deploy to Kubernetes

```bash
# Apply manifests
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/service.yaml

# Wait for rollout
kubectl -n seedtest rollout status deployment/r-analytics --timeout=5m

# Check pods
kubectl -n seedtest get pods -l app=r-analytics
```

### 4. Verify Deployment

```bash
# Check pod logs
kubectl -n seedtest logs -l app=r-analytics --tail=50

# Port-forward for local testing
kubectl -n seedtest port-forward svc/r-analytics 8010:80

# Test health endpoint
curl http://localhost:8010/health

# Test with internal token
curl -H "X-Internal-Token: YOUR_TOKEN" \
  http://localhost:8010/health
```

## Configuration

### Environment Variables

The r-analytics service expects the following environment variables (configured in Deployment):

- `R_ANALYTICS_INTERNAL_TOKEN`: Internal authentication token (from ExternalSecret)

### Client Configuration

Python clients using `RAnalyticsClient` need:

```bash
# Required
R_ANALYTICS_BASE_URL=http://r-analytics.seedtest.svc.cluster.local:80

# Required (must match GSM secret)
R_ANALYTICS_TOKEN=<your-token-here>

# Optional (default: 60)
R_ANALYTICS_TIMEOUT_SECS=60
```

### FastAPI Configuration

The analytics_proxy router is configured with JWT scopes:

- `analysis:run` - Execute analytics operations
- `reports:view` - View analytics results
- `reports:generate` - Generate comprehensive reports
- `recommend:plan` - Access recommendation features

## Monitoring

### Health Checks

```bash
# Kubernetes health probes
kubectl -n seedtest get pods -l app=r-analytics -o wide

# Manual health check
curl http://r-analytics.seedtest.svc.cluster.local:80/health
```

### Logs

```bash
# Stream logs
kubectl -n seedtest logs -f deployment/r-analytics

# Recent logs with errors
kubectl -n seedtest logs -l app=r-analytics --tail=100 | grep -i error
```

### Resource Usage

```bash
# Pod resource usage
kubectl -n seedtest top pods -l app=r-analytics

# Describe for events and status
kubectl -n seedtest describe deployment r-analytics
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status and events
kubectl -n seedtest describe pod -l app=r-analytics

# Check image pull
kubectl -n seedtest get events --sort-by='.lastTimestamp' | grep r-analytics
```

### Secret Issues

```bash
# Verify ExternalSecret
kubectl -n seedtest get externalsecret r-analytics-credentials

# Check Secret creation
kubectl -n seedtest get secret r-analytics-credentials

# Describe for errors
kubectl -n seedtest describe externalsecret r-analytics-credentials
```

### Health Check Failures

```bash
# Check if service is responsive
kubectl -n seedtest port-forward svc/r-analytics 8010:80 &
curl -v http://localhost:8010/health

# Check container logs
kubectl -n seedtest logs -l app=r-analytics --tail=100
```

### Connection Issues from FastAPI

```bash
# Test DNS resolution
kubectl -n seedtest run -it --rm debug --image=busybox --restart=Never -- \
  nslookup r-analytics.seedtest.svc.cluster.local

# Test connectivity
kubectl -n seedtest run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -v http://r-analytics.seedtest.svc.cluster.local:80/health
```

## Scaling

### Manual Scaling

```bash
# Scale up
kubectl -n seedtest scale deployment r-analytics --replicas=3

# Scale down
kubectl -n seedtest scale deployment r-analytics --replicas=1
```

### Auto-scaling (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: r-analytics-hpa
  namespace: seedtest
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: r-analytics
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Rollback

```bash
# View deployment history
kubectl -n seedtest rollout history deployment/r-analytics

# Rollback to previous version
kubectl -n seedtest rollout undo deployment/r-analytics

# Rollback to specific revision
kubectl -n seedtest rollout undo deployment/r-analytics --to-revision=2
```

## Integration

### From Python (RAnalyticsClient)

```python
from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient

client = RAnalyticsClient()

# Health check
health = client.health()

# Score topic theta
result = client.score_topic_theta("student-123", ["topic-A", "topic-B"])

# Churn risk
risk = client.risk_churn("student-123")
```

### From FastAPI (analytics_proxy router)

```python
# In main.py
from portal_front.apps.seedtest_api.routers.analytics_proxy import router as analytics_router

app.include_router(analytics_router, prefix="/api/v1")

# Endpoints available:
# GET  /api/v1/analytics/health
# POST /api/v1/analytics/score/topic-theta
# POST /api/v1/analytics/improvement/index
# POST /api/v1/analytics/goal/attainment
# POST /api/v1/analytics/recommend/next-topics
# POST /api/v1/analytics/risk/churn
# POST /api/v1/analytics/report/generate
```

## Related Documentation

- [DEPLOYMENT_CHECKLIST.md](../../../DEPLOYMENT_CHECKLIST.md) - Complete deployment guide
- [ANALYTICS_QUICKSTART.md](../../../ANALYTICS_QUICKSTART.md) - Quick reference
- [deploy_analytics.sh](../../../deploy_analytics.sh) - Automated deployment script
- [RAnalyticsClient](../../../apps/seedtest_api/app/clients/r_analytics.py) - Python client implementation
- [analytics_proxy router](../../apps/seedtest_api/routers/analytics_proxy.py) - FastAPI integration
