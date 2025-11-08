# Monitoring Stack Verification Guide

## 🎯 Current Configuration

**ServiceMonitor**: `seedtest-api`  
**Namespace**: `seedtest`  
**Prometheus Release Label**: `prometheus`  
**Scrape Endpoint**: `http://seedtest-api:8000/metrics`  
**Interval**: 30s  
**Timeout**: 10s  

---

## ✅ Immediate Verification

### 1. Declarative Validation (Local, No Cluster Access)

```bash
# ServiceMonitor labels/namespace/endpoints
kustomize build ops/k8s/governance/base | \
  yq '. | select(.kind=="ServiceMonitor") 
      | {ns:.metadata.namespace, labels:.metadata.labels, nsSel:.spec.namespaceSelector, endpoints:.spec.endpoints}'

# Expected output:
# ns: seedtest
# labels:
#   app: seedtest-api
#   governance: enabled
#   release: prometheus
# nsSel:
#   matchNames: [seedtest]
# endpoints:
#   - port: http
#     path: /metrics
#     interval: 30s
```

### 2. Prometheus Target Registration (Cluster Access Required)

```bash
# Check ServiceMonitor exists
kubectl -n seedtest get servicemonitor seedtest-api -o wide --show-labels

# Expected output:
# NAME           AGE   LABELS
# seedtest-api   ...   app=seedtest-api,governance=enabled,release=prometheus

# Verify Prometheus discovered the target
# (Assuming Prometheus in 'monitoring' namespace)
PROM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}')

# Port-forward and check targets
kubectl -n monitoring port-forward $PROM 9090:9090 >/dev/null 2>&1 &
sleep 2
curl -s 'http://127.0.0.1:9090/api/v1/targets?state=active' | jq '.data.activeTargets[] | select(.labels.job=="seedtest-api")'
```

### 3. Metrics Endpoint Validation

```bash
# Check app exposes /metrics
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest exec "$POD" -- curl -s http://localhost:8000/metrics | head -20

# Expected: Prometheus-format metrics
# Example:
# # HELP http_requests_total Total HTTP requests
# # TYPE http_requests_total counter
# http_requests_total{method="GET",status="200"} 1234
```

---

## 🛠️ Troubleshooting

### Issue 1: Target Not Appearing in Prometheus

**Check ServiceMonitor label**:
```bash
kubectl -n seedtest get servicemonitor seedtest-api -o jsonpath='{.metadata.labels.release}{"\n"}'
# Expected: prometheus (or kube-prometheus-stack)
```

**Verify Prometheus Operator CRD**:
```bash
kubectl get crd servicemonitors.monitoring.coreos.com
# Should exist
```

**Check Prometheus ServiceMonitor selector** (in Helm values or Prometheus CR):
```bash
# Prometheus instance should have serviceMonitorSelector matching release label
kubectl -n monitoring get prometheus -o yaml | grep -A 5 serviceMonitorSelector
```

### Issue 2: Cross-Namespace Scraping

**If Prometheus is in different namespace** (e.g., `monitoring`):

Update NetworkPolicy:
```yaml
# ops/k8s/governance/base/networkpolicy.yaml
ingress:
  # Add this rule (currently commented)
  - from:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: monitoring
    ports:
      - protocol: TCP
        port: 8000
```

**Verify namespace label**:
```bash
kubectl get namespace monitoring --show-labels
# Should have: kubernetes.io/metadata.name=monitoring
```

### Issue 3: Path/Port Mismatch

**Verify Service port name**:
```bash
kubectl -n seedtest get svc seedtest-api -o yaml | grep -A 5 "ports:"
# Expected:
#   - name: http
#     port: 8000
#     targetPort: 8000
```

**Test metrics endpoint directly**:
```bash
kubectl -n seedtest exec deployment/seedtest-api -- curl -v http://localhost:8000/metrics
# Should return 200 OK with metrics
```

### Issue 4: DNS Resolution

**Verify NetworkPolicy allows DNS**:
```bash
kubectl -n seedtest get networkpolicy seedtest-api-netpol -o yaml | grep -A 10 "egress:"
# Should include:
#   - to:
#       - namespaceSelector:
#           matchLabels:
#             kubernetes.io/metadata.name: kube-system
#     ports:
#       - port: 53
```

### Issue 5: Label Conflict (Multiple Prometheus Instances)

**If using both `prometheus` and `kube-prometheus-stack`**:

Check existing ServiceMonitors:
```bash
kubectl get servicemonitor --all-namespaces -o jsonpath='{range .items[*]}{.metadata.labels.release}{"\n"}{end}' | sort -u
```

**Solution**: Use overlay to change release label for different environments:
```yaml
# ops/k8s/governance/overlays/prod/kustomization.yaml
patches:
  - target:
      kind: ServiceMonitor
      name: seedtest-api
    patch: |-
      - op: replace
        path: /metadata/labels/release
        value: "kube-prometheus-stack"
```

---

## 📈 Optional Enhancements

### A) Alerting Rules (PrometheusRule)

Create `ops/k8s/governance/base/prometheusrule.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: seedtest-api-rules
  namespace: seedtest
  labels:
    release: prometheus
    app: seedtest-api
    governance: enabled
spec:
  groups:
    - name: seedtest-api.availability
      interval: 30s
      rules:
        - alert: SeedtestApiDown
          expr: up{job="seedtest-api"} == 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "seedtest-api is down"
            description: "seedtest-api has been down for more than 5 minutes"
        
        - alert: SeedtestApiHighLatency
          expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job="seedtest-api"}[5m])) > 1
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "seedtest-api high latency"
            description: "P99 latency > 1s for 10 minutes"

    - name: seedtest-api.governance
      interval: 30s
      rules:
        - alert: GovernancePolicyDenyRate
          expr: rate(policy_deny_total{job="seedtest-api"}[5m]) > 0.1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High policy denial rate"
            description: "Policy denying >10% of requests (phase={{ $labels.phase }}, strict_mode={{ $labels.strict_mode }})"
```

Add to `kustomization.yaml`:
```yaml
resources:
  # ...existing...
  - prometheusrule.yaml
```

### B) Metric Relabeling (Reduce Cardinality)

Update ServiceMonitor endpoints:

```yaml
endpoints:
  - port: http
    interval: 30s
    scrapeTimeout: 10s
    path: /metrics
    scheme: http
    # Drop high-cardinality metrics
    metricRelabelings:
      - sourceLabels: [__name__]
        regex: "go_gc_.*|process_.*"
        action: drop
      # Keep only important metrics
      - sourceLabels: [__name__]
        regex: "http_requests_total|policy_deny_total|policy_allow_total|governance_.*"
        action: keep
    # Relabel job name
    relabelings:
      - sourceLabels: [__meta_kubernetes_service_name]
        targetLabel: job
```

### C) Grafana Dashboard Labels

If using Grafana sidecar for auto-import:

```yaml
# configmap with dashboard JSON
apiVersion: v1
kind: ConfigMap
metadata:
  name: seedtest-api-dashboard
  namespace: seedtest
  labels:
    grafana_dashboard: "1"  # Grafana sidecar selector
    app: seedtest-api
    governance: enabled
data:
  seedtest-api.json: |
    {
      "dashboard": {
        "title": "SeedTest API - Governance",
        "panels": [...]
      }
    }
```

---

## 🔍 Quick Validation Commands

### One-Liner: Full Stack Check

```bash
# Check ServiceMonitor → Service → Pods → Metrics
echo "=== ServiceMonitor ===" && \
kubectl -n seedtest get servicemonitor seedtest-api -o jsonpath='{.metadata.labels.release}{"\n"}' && \
echo "=== Service ===" && \
kubectl -n seedtest get svc seedtest-api -o jsonpath='{.spec.ports[0].name}:{.spec.ports[0].port}{"\n"}' && \
echo "=== Pods ===" && \
kubectl -n seedtest get pods -l app=seedtest-api && \
echo "=== Metrics ===" && \
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}') && \
kubectl -n seedtest exec $POD -- curl -s http://localhost:8000/metrics | head -5
```

### Prometheus Query Examples

```promql
# Request rate
rate(http_requests_total{job="seedtest-api"}[5m])

# Policy denials
sum(rate(policy_deny_total{job="seedtest-api"}[5m])) by (action, phase)

# Uptime
up{job="seedtest-api"}

# Pod count
count(up{job="seedtest-api"})
```

---

## 📦 Overlay-Specific Configuration

### Staging: Prometheus (default)

```yaml
# ops/k8s/governance/overlays/staging/kustomization.yaml
# No changes needed - uses base release: prometheus
```

### Production: Different Prometheus Instance

```yaml
# ops/k8s/governance/overlays/prod/kustomization.yaml
patches:
  - target:
      kind: ServiceMonitor
      name: seedtest-api
    patch: |-
      - op: replace
        path: /metadata/labels/release
        value: "kube-prometheus-stack"
      - op: replace
        path: /spec/endpoints/0/interval
        value: "15s"  # More frequent in prod
```

---

## 🧪 Fast Search (Monitoring Keywords)

```bash
# Create index (once)
rg --files infra ops -g '*.y*ml' > .monitoring_yaml_index.txt

# Search for monitoring resources
rg -n -F -e 'ServiceMonitor' -e 'prometheus' -e 'grafana' -f .monitoring_yaml_index.txt

# Search for specific patterns
rg -n --pcre2 'release:\s*(prometheus|kube-prometheus-stack)' -f .monitoring_yaml_index.txt
```

---

## ✅ Success Criteria

- [x] ServiceMonitor has `release: prometheus` label
- [x] ServiceMonitor appears in Prometheus UI → Status → Targets
- [x] Target state is `UP` (green)
- [x] Metrics accessible at `http://seedtest-api:8000/metrics`
- [x] Queries return data in Prometheus graph view
- [ ] Grafana dashboard shows metrics (optional)
- [ ] Alerts firing correctly (optional)

---

## 📞 Support

**Prometheus Not Discovering**:
- Check Prometheus Operator logs: `kubectl -n monitoring logs -l app.kubernetes.io/name=prometheus-operator`
- Verify ServiceMonitor selector in Prometheus CR
- Ensure `release` label matches Helm release name

**Metrics Not Appearing**:
- Verify app actually exposes `/metrics`
- Check NetworkPolicy allows Prometheus → app traffic
- Review Prometheus scrape logs

**Contact**: Platform Team / #monitoring-alerts Slack channel
