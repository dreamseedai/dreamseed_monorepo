# SeedTest API 모니터링 검증 가이드

## 📊 개요

SeedTest API의 Prometheus 메트릭 및 Grafana 대시보드 설정 가이드입니다.

---

## 🎯 메트릭 목록

### HTTP 요청 메트릭
```promql
# 총 HTTP 요청 수
http_requests_total{method, endpoint, status}

# HTTP 요청 지연시간
http_request_duration_seconds{method, endpoint}

# 진행 중인 HTTP 요청 수
http_requests_in_progress{method, endpoint}
```

### Governance 정책 메트릭
```promql
# 총 정책 평가 수
policy_evaluations_total{action, role, phase, result}

# 정책 평가 지연시간
policy_evaluation_duration_seconds{action, phase}

# 정책 거부 수
policy_deny_total{action, role, phase, reason}

# 정책 허용 수
policy_allow_total{action, role, phase}
```

### Governance 번들 메트릭
```promql
# 번들 로드 상태 (0=실패, 1=성공)
governance_bundle_loaded{bundle_id, phase}

# 번들 리로드 횟수
governance_bundle_reload_total{bundle_id, phase, status}

# 번들 리로드 지연시간
governance_bundle_reload_duration_seconds{bundle_id, phase}
```

### Feature Flag 메트릭
```promql
# Feature Flag 체크 횟수
feature_flag_checks_total{flag_name, result}

# Feature Flag 활성화 상태
feature_flag_enabled{flag_name, phase}
```

### IRT 드리프트 메트릭
```promql
# IRT 드리프트 감지 횟수
irt_drift_detections_total{status}

# 플래그된 문항 수
irt_drift_flagged_items

# 드리프트 감지 지연시간
irt_drift_detection_duration_seconds
```

### 데이터베이스 메트릭
```promql
# 활성 DB 연결 수
db_connections_active

# DB 쿼리 지연시간
db_query_duration_seconds{query_type}

# DB 오류 수
db_errors_total{error_type}
```

### 애플리케이션 메트릭
```promql
# 애플리케이션 정보
app_info{version, environment}
```

---

## 🔍 메트릭 확인 방법

### 1. 로컬 개발 환경

```bash
# 1. FastAPI 서버 실행
cd /home/won/projects/dreamseed_monorepo/apps/seedtest_api
uvicorn app.main:app --reload --port 8000

# 2. 메트릭 엔드포인트 확인
curl http://localhost:8000/metrics

# 3. 특정 메트릭만 필터링
curl http://localhost:8000/metrics | grep 'http_requests_total'
curl http://localhost:8000/metrics | grep 'policy_'
curl http://localhost:8000/metrics | grep 'governance_'
curl http://localhost:8000/metrics | grep 'irt_drift_'
```

### 2. Kubernetes 클러스터

```bash
# 1. Pod 확인
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')

# 2. Pod에서 직접 메트릭 확인
kubectl -n seedtest exec "$POD" -- curl -s http://localhost:8000/metrics

# 3. 메트릭 타입 확인
kubectl -n seedtest exec "$POD" -- curl -s http://localhost:8000/metrics | grep '^# TYPE'

# 4. Governance 관련 메트릭만
kubectl -n seedtest exec "$POD" -- curl -s http://localhost:8000/metrics | grep -i 'policy\|governance'

# 5. IRT 드리프트 관련 메트릭만
kubectl -n seedtest exec "$POD" -- curl -s http://localhost:8000/metrics | grep -i 'irt_drift'

# 6. Port-forward로 로컬에서 확인
kubectl -n seedtest port-forward svc/seedtest-api 8000:8000 &
curl -s http://localhost:8000/metrics
```

---

## 📈 Prometheus 쿼리 예제

### HTTP 트래픽 분석

```promql
# 초당 요청 수
rate(http_requests_total{job="seedtest-api"}[5m])

# 엔드포인트별 요청 수
sum by (endpoint) (rate(http_requests_total{job="seedtest-api"}[5m]))

# 에러율 (5xx)
rate(http_requests_total{job="seedtest-api",status=~"5.."}[5m]) 
  / rate(http_requests_total{job="seedtest-api"}[5m])

# 95th percentile 지연시간
histogram_quantile(0.95, 
  rate(http_request_duration_seconds_bucket{job="seedtest-api"}[5m]))

# 50th percentile 지연시간
histogram_quantile(0.50, 
  rate(http_request_duration_seconds_bucket{job="seedtest-api"}[5m]))
```

### Governance 정책 분석

```promql
# 정책 거부율
rate(policy_deny_total{job="seedtest-api"}[5m]) 
  / rate(policy_evaluations_total{job="seedtest-api"}[5m])

# Phase별 정책 평가 수
sum by (phase) (rate(policy_evaluations_total{job="seedtest-api"}[5m]))

# Action별 거부 수
sum by (action) (rate(policy_deny_total{job="seedtest-api"}[5m]))

# 번들 로드 상태 (0=실패, 1=성공)
governance_bundle_loaded{job="seedtest-api"}

# 번들 리로드 실패율
rate(governance_bundle_reload_total{job="seedtest-api",status="failure"}[5m])
  / rate(governance_bundle_reload_total{job="seedtest-api"}[5m])
```

### IRT 드리프트 분석

```promql
# 드리프트 감지 성공률
rate(irt_drift_detections_total{job="seedtest-api",status="success"}[10m])
  / rate(irt_drift_detections_total{job="seedtest-api"}[10m])

# 플래그된 문항 수
irt_drift_flagged_items{job="seedtest-api"}

# 드리프트 감지 지연시간 (95th percentile)
histogram_quantile(0.95, 
  rate(irt_drift_detection_duration_seconds_bucket{job="seedtest-api"}[10m]))
```

### 데이터베이스 분석

```promql
# 활성 연결 수
db_connections_active{job="seedtest-api"}

# 쿼리 지연시간 (95th percentile)
histogram_quantile(0.95, 
  rate(db_query_duration_seconds_bucket{job="seedtest-api"}[5m]))

# 쿼리 타입별 오류율
rate(db_errors_total{job="seedtest-api"}[5m])
```

---

## 🚨 알림 규칙

### 가용성 알림

#### SeedTestAPIDown
```yaml
alert: SeedTestAPIDown
expr: up{job="seedtest-api"} == 0
for: 2m
severity: critical
```

#### SeedTestAPIHighLatency
```yaml
alert: SeedTestAPIHighLatency
expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="seedtest-api"}[5m])) > 1
for: 5m
severity: warning
```

#### SeedTestAPIHighErrorRate
```yaml
alert: SeedTestAPIHighErrorRate
expr: rate(http_requests_total{job="seedtest-api",status=~"5.."}[5m]) / rate(http_requests_total{job="seedtest-api"}[5m]) > 0.05
for: 5m
severity: warning
```

### Governance 알림

#### GovernanceHighDenyRate
```yaml
alert: GovernanceHighDenyRate
expr: rate(policy_deny_total{job="seedtest-api"}[5m]) / rate(policy_evaluations_total{job="seedtest-api"}[5m]) > 0.3
for: 10m
severity: warning
```

#### GovernanceBundleReloadFailure
```yaml
alert: GovernanceBundleReloadFailure
expr: rate(governance_bundle_reload_total{job="seedtest-api",status="failure"}[5m]) > 0
for: 2m
severity: critical
```

#### GovernanceBundleNotLoaded
```yaml
alert: GovernanceBundleNotLoaded
expr: governance_bundle_loaded{job="seedtest-api"} == 0
for: 5m
severity: critical
```

### IRT 드리프트 알림

#### IRTDriftDetectionFailure
```yaml
alert: IRTDriftDetectionFailure
expr: rate(irt_drift_detections_total{job="seedtest-api",status="failure"}[10m]) > 0
for: 5m
severity: warning
```

#### IRTDriftHighFlaggedItems
```yaml
alert: IRTDriftHighFlaggedItems
expr: irt_drift_flagged_items{job="seedtest-api"} > 100
for: 10m
severity: warning
```

---

## 📊 Grafana 대시보드

### 패널 구성

1. **HTTP Request Rate** - 초당 요청 수
2. **HTTP Request Latency** - p50, p95 지연시간
3. **Error Rate** - 5xx 에러율
4. **Policy Deny Rate** - 정책 거부율
5. **Governance Bundle Status** - 번들 로드 상태
6. **IRT Drift Flagged Items** - 플래그된 문항 수
7. **Policy Evaluations by Action & Phase** - Action/Phase별 정책 평가
8. **Database Connections** - 활성 DB 연결 수

### 대시보드 접속

```bash
# Port-forward Grafana
kubectl -n monitoring port-forward svc/grafana 3000:3000

# 브라우저에서 접속
http://localhost:3000

# 대시보드 검색
"SeedTest API Dashboard"
```

---

## 🔧 설정 파일

### ServiceMonitor
```yaml
# infra/argocd/apps/monitoring/servicemonitor-seedtest.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: seedtest-api
  namespace: seedtest
spec:
  selector:
    matchLabels:
      app: seedtest-api
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

### PrometheusRule
```yaml
# infra/argocd/apps/monitoring/prometheus-rule-seedtest.yaml
# 위에서 생성한 파일 참조
```

### Grafana Dashboard
```yaml
# infra/argocd/apps/monitoring/grafana-dashboard-seedtest.yaml
# 위에서 생성한 파일 참조
```

---

## 🧪 테스트

### 1. 메트릭 생성 테스트

```bash
# HTTP 요청 생성
for i in {1..100}; do
  curl http://localhost:8000/healthz
done

# 메트릭 확인
curl http://localhost:8000/metrics | grep 'http_requests_total{.*healthz'
```

### 2. Governance 메트릭 테스트

```python
# Python 코드에서 메트릭 기록
from apps.seedtest_api.routers.prometheus_metrics import record_policy_evaluation

record_policy_evaluation(
    action="read_student_data",
    role="teacher",
    phase="phase0",
    result="allow",
    duration=0.05
)
```

### 3. IRT 드리프트 메트릭 테스트

```python
from apps.seedtest_api.routers.prometheus_metrics import record_irt_drift_detection

record_irt_drift_detection(
    status="success",
    flagged_items=15,
    duration=120.5
)
```

---

## 📝 다음 단계

### 1. FastAPI 앱에 Prometheus 메트릭 통합
```bash
# requirements.txt에 추가
prometheus-client==0.19.0

# main.py에 라우터 추가
from .routers.prometheus_metrics import router as prometheus_router
app.include_router(prometheus_router)
```

### 2. ServiceMonitor 배포
```bash
kubectl apply -f infra/argocd/apps/monitoring/servicemonitor-seedtest.yaml
```

### 3. PrometheusRule 배포
```bash
kubectl apply -f infra/argocd/apps/monitoring/prometheus-rule-seedtest.yaml
```

### 4. Grafana Dashboard 배포
```bash
kubectl apply -f infra/argocd/apps/monitoring/grafana-dashboard-seedtest.yaml
```

### 5. 메트릭 확인
```bash
# Prometheus에서 타겟 확인
kubectl -n monitoring port-forward svc/prometheus 9090:9090
# http://localhost:9090/targets

# Grafana에서 대시보드 확인
kubectl -n monitoring port-forward svc/grafana 3000:3000
# http://localhost:3000
```

---

## 🎯 요약

### 생성된 파일
1. ✅ `/apps/seedtest_api/routers/prometheus_metrics.py` - Prometheus 메트릭 엔드포인트
2. ✅ `/infra/argocd/apps/monitoring/prometheus-rule-seedtest.yaml` - Prometheus 알림 규칙
3. ✅ `/infra/argocd/apps/monitoring/grafana-dashboard-seedtest.yaml` - Grafana 대시보드
4. ✅ `/docs/MONITORING_VERIFICATION.md` - 이 문서

### 메트릭 카테고리
- HTTP 요청 (3개 메트릭)
- Governance 정책 (7개 메트릭)
- Feature Flags (2개 메트릭)
- IRT 드리프트 (3개 메트릭)
- 데이터베이스 (3개 메트릭)
- 애플리케이션 (1개 메트릭)

### 알림 규칙
- 가용성 (3개)
- Governance (3개)
- IRT 드리프트 (3개)
- 데이터베이스 (3개)
- 리소스 (3개)

**총 19개 메트릭, 15개 알림 규칙, 8개 Grafana 패널**
