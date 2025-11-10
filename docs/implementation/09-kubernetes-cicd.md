# Kubernetes Deployment & CI/CD

## Table of Contents

- [Overview](#overview)
- [Kubernetes Architecture](#kubernetes-architecture)
- [Helm vs Kustomize](#helm-vs-kustomize)
- [Service Mesh](#service-mesh)
- [Secrets Management](#secrets-management)
- [Database Migrations](#database-migrations)
- [Auto-Scaling](#auto-scaling)
- [Monitoring Stack](#monitoring-stack)
- [CI/CD Pipeline](#cicd-pipeline)
- [Cost Optimization](#cost-optimization)

## Overview

Production Kubernetes deployment with:

- **7+ microservices**: Assessment, Content, Analytics, AI Tutor, User, Auth, Payment
- **Infrastructure services**: PostgreSQL, Redis, Kafka, MinIO
- **Auto-scaling**: HPA based on CPU/memory and custom metrics
- **Blue-green deployments**: Zero-downtime releases
- **Monitoring**: Prometheus, Grafana, ELK stack

**Platform**: GKE, EKS, or AKS (cloud-agnostic manifests)

## Kubernetes Architecture

### Namespace Organization

```yaml
# namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dreamseed-production
  labels:
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: dreamseed-staging
  labels:
    environment: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: dreamseed-monitoring
  labels:
    environment: shared
```

### Microservices Deployment

```yaml
# deployments/assessment-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: assessment-service
  namespace: dreamseed-production
  labels:
    app: assessment-service
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: assessment-service
  template:
    metadata:
      labels:
        app: assessment-service
        version: v1
    spec:
      serviceAccountName: assessment-service-sa
      containers:
        - name: assessment-service
          image: gcr.io/dreamseed/assessment-service:latest
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: url
            - name: REDIS_URL
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: redis_url
            - name: KAFKA_BOOTSTRAP_SERVERS
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: kafka_bootstrap_servers
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: config
              mountPath: /app/config
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: app-config
---
apiVersion: v1
kind: Service
metadata:
  name: assessment-service
  namespace: dreamseed-production
spec:
  selector:
    app: assessment-service
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
  type: ClusterIP
```

## Helm vs Kustomize

### Decision Matrix

| Factor             | Helm                    | Kustomize             |
| ------------------ | ----------------------- | --------------------- |
| Templating         | Go templates (powerful) | YAML patches (simple) |
| Package management | Charts, repositories    | No packaging          |
| Learning curve     | Moderate                | Gentle                |
| Complexity         | Can get complex         | Straightforward       |
| Community          | Large ecosystem         | Growing               |
| Kubernetes-native  | External tool           | Built into kubectl    |

**Decision**: **Kustomize** for simplicity and Kubernetes-native approach

### Kustomize Structure

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── deployments/
│   │   ├── assessment-service.yaml
│   │   ├── content-service.yaml
│   │   └── ...
│   ├── services/
│   ├── configmaps/
│   └── secrets/
├── overlays/
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   ├── replicas.yaml
│   │   └── resources.yaml
│   └── production/
│       ├── kustomization.yaml
│       ├── replicas.yaml
│       ├── resources.yaml
│       └── hpa.yaml
```

```yaml
# k8s/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployments/assessment-service.yaml
  - deployments/content-service.yaml
  - services/assessment-service.yaml
  - services/content-service.yaml
  - configmaps/app-config.yaml

commonLabels:
  app.kubernetes.io/name: dreamseed
  app.kubernetes.io/managed-by: kustomize
```

```yaml
# k8s/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

namespace: dreamseed-production

replicas:
  - name: assessment-service
    count: 5
  - name: content-service
    count: 3

patchesStrategicMerge:
  - resources.yaml
  - hpa.yaml

configMapGenerator:
  - name: app-config
    behavior: merge
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
```

## Service Mesh

### Istio vs Linkerd

| Factor            | Istio       | Linkerd | None    |
| ----------------- | ----------- | ------- | ------- |
| Features          | Extensive   | Focused | Minimal |
| Complexity        | High        | Low     | None    |
| Resource overhead | Significant | Minimal | None    |
| Observability     | Excellent   | Good    | Manual  |
| mTLS              | Yes         | Yes     | Manual  |

**Decision**: **Start without service mesh**, add Linkerd if needed

### Nginx Ingress Controller

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dreamseed-ingress
  namespace: dreamseed-production
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - api.dreamseed.ai
      secretName: dreamseed-tls
  rules:
    - host: api.dreamseed.ai
      http:
        paths:
          - path: /api/assessments
            pathType: Prefix
            backend:
              service:
                name: assessment-service
                port:
                  number: 80
          - path: /api/content
            pathType: Prefix
            backend:
              service:
                name: content-service
                port:
                  number: 80
          - path: /api/auth
            pathType: Prefix
            backend:
              service:
                name: auth-service
                port:
                  number: 80
```

## Secrets Management

### Sealed Secrets (Chosen Approach)

```yaml
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Encrypt secret
echo -n 'super-secret-password' | kubectl create secret generic db-password \
  --dry-run=client --from-file=password=/dev/stdin -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml
```

```yaml
# sealed-secrets/database.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: database-secrets
  namespace: dreamseed-production
spec:
  encryptedData:
    url: AgA7K8... # Encrypted value
    username: AgBxN9...
    password: AgC4T2...
```

### External Secrets Operator (Alternative)

```yaml
# For production: sync from cloud secret managers (AWS Secrets Manager, GCP Secret Manager)
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secret-store
  namespace: dreamseed-production
spec:
  provider:
    gcpsm:
      projectID: "dreamseed-prod"
      auth:
        workloadIdentity:
          clusterLocation: us-central1
          clusterName: dreamseed-cluster
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-secrets
  namespace: dreamseed-production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcp-secret-store
    kind: SecretStore
  target:
    name: database-secrets
  data:
    - secretKey: url
      remoteRef:
        key: database-url
    - secretKey: username
      remoteRef:
        key: database-username
    - secretKey: password
      remoteRef:
        key: database-password
```

## Database Migrations

### Alembic Job

```yaml
# jobs/db-migration.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-{{ .Values.version }}
  namespace: dreamseed-production
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: alembic
          image: gcr.io/dreamseed/assessment-service:{{ .Values.version }}
          command: ["alembic", "upgrade", "head"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: url
      backoffLimit: 3
```

### Migration Strategy

```bash
# scripts/deploy.sh
#!/bin/bash

# 1. Run database migrations
kubectl apply -f k8s/jobs/db-migration.yaml
kubectl wait --for=condition=complete --timeout=300s job/db-migration-$VERSION

# 2. Deploy new version
kubectl apply -k k8s/overlays/production

# 3. Wait for rollout
kubectl rollout status deployment/assessment-service -n dreamseed-production
```

## Auto-Scaling

### Horizontal Pod Autoscaler

```yaml
# hpa/assessment-service.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: assessment-service-hpa
  namespace: dreamseed-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: assessment-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
```

### Cluster Autoscaler

```yaml
# For GKE
resource "google_container_node_pool" "primary_nodes" {
name       = "primary-node-pool"
cluster    = google_container_cluster.primary.name
node_count = 3

autoscaling {
min_node_count = 3
max_node_count = 10
}

node_config {
machine_type = "n1-standard-4"

oauth_scopes = [
"https://www.googleapis.com/auth/cloud-platform"
]
}
}
```

## Monitoring Stack

### Prometheus

```yaml
# monitoring/prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: dreamseed-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: dreamseed-monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
        - name: prometheus
          image: prom/prometheus:v2.45.0
          ports:
            - containerPort: 9090
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
            - name: storage
              mountPath: /prometheus
      volumes:
        - name: config
          configMap:
            name: prometheus-config
        - name: storage
          persistentVolumeClaim:
            claimName: prometheus-pvc
```

### Grafana Dashboards

```yaml
# monitoring/grafana-dashboard-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: dreamseed-monitoring
data:
  assessment-service.json: |
    {
      "dashboard": {
        "title": "Assessment Service Metrics",
        "panels": [
          {
            "title": "Request Rate",
            "targets": [
              {
                "expr": "rate(http_requests_total{service=\"assessment-service\"}[5m])"
              }
            ]
          },
          {
            "title": "Error Rate",
            "targets": [
              {
                "expr": "rate(http_requests_total{service=\"assessment-service\",status=~\"5..\"}[5m])"
              }
            ]
          }
        ]
      }
    }
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

env:
  GCP_PROJECT_ID: dreamseed-prod
  GKE_CLUSTER: dreamseed-cluster
  GKE_ZONE: us-central1-a

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest tests/ -v --cov=app

      - name: Lint
        run: |
          ruff check app/
          mypy app/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ env.GCP_PROJECT_ID }}

      - name: Configure Docker
        run: gcloud auth configure-docker

      - name: Build Docker image
        run: |
          docker build -t gcr.io/$GCP_PROJECT_ID/assessment-service:$GITHUB_SHA .
          docker tag gcr.io/$GCP_PROJECT_ID/assessment-service:$GITHUB_SHA \
                     gcr.io/$GCP_PROJECT_ID/assessment-service:latest

      - name: Push to GCR
        run: |
          docker push gcr.io/$GCP_PROJECT_ID/assessment-service:$GITHUB_SHA
          docker push gcr.io/$GCP_PROJECT_ID/assessment-service:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ env.GCP_PROJECT_ID }}

      - name: Get GKE credentials
        run: |
          gcloud container clusters get-credentials $GKE_CLUSTER \
            --zone $GKE_ZONE --project $GCP_PROJECT_ID

      - name: Run database migrations
        run: |
          kubectl apply -f k8s/jobs/db-migration.yaml
          kubectl wait --for=condition=complete --timeout=300s \
            job/db-migration-$GITHUB_SHA -n dreamseed-production

      - name: Deploy to Kubernetes
        run: |
          cd k8s/overlays/production
          kustomize edit set image \
            assessment-service=gcr.io/$GCP_PROJECT_ID/assessment-service:$GITHUB_SHA
          kubectl apply -k .

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/assessment-service \
            -n dreamseed-production --timeout=5m

      - name: Smoke test
        run: |
          curl -f https://api.dreamseed.ai/health || exit 1
```

## Cost Optimization

### Resource Requests/Limits

```yaml
# Right-size based on actual usage (use metrics)
resources:
  requests:
    memory: "256Mi" # Minimum guaranteed
    cpu: "100m" # 0.1 CPU core
  limits:
    memory: "512Mi" # Maximum allowed
    cpu: "500m" # 0.5 CPU core
```

### Cluster Autoscaler + Spot Instances

```yaml
# GKE with spot VMs (70% cheaper)
resource "google_container_node_pool" "spot_pool" {
  name    = "spot-pool"
  cluster = google_container_cluster.primary.name

  autoscaling {
    min_node_count = 0
    max_node_count = 10
  }

  node_config {
    preemptible  = true  # Spot instances
    machine_type = "n1-standard-2"

    taint {
      key    = "cloud.google.com/gke-preemptible"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
}
```

### Pod Disruption Budgets

```yaml
# Ensure availability during node preemption
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: assessment-service-pdb
  namespace: dreamseed-production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: assessment-service
```

## Summary

Kubernetes deployment provides:

1. **Microservices orchestration**: 7+ services with auto-scaling
2. **Zero-downtime deployments**: Rolling updates with health checks
3. **Secrets management**: Sealed Secrets or External Secrets Operator
4. **Database migrations**: Automated Alembic jobs
5. **Monitoring**: Prometheus + Grafana stack
6. **CI/CD**: GitHub Actions with automated testing and deployment
7. **Cost optimization**: Spot instances, right-sizing, autoscaling

**Key Metrics**:

- Deployment time: <5 minutes
- Rollback time: <2 minutes
- Auto-scale response: <1 minute
- Infrastructure cost: <$5K/month for 10K users

**Next Steps**:

- Implement GitOps with ArgoCD
- Add canary deployments
- Set up disaster recovery
- Multi-region deployment
