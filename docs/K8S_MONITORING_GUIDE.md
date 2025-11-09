# K8s Audit·Prometheus 모니터링 가이드

**FastAPI → 감사 로그 & Prometheus → Argo Rollouts → Grafana** 전체 흐름 구축 가이드

## 📋 개요

### 목표
- trace_id 기반 요청 계보 추적
- Prometheus 메트릭 (요청 수, 지연시간 히스토그램)
- Grafana 대시보드 (P50/P95/P99, 에러율)
- Argo Rollouts 자동 카나리 판단

### 핵심 원칙
1. **최소 라벨 정책**: Cardinality 폭발 방지
2. **trace_id 전파**: 로그/메트릭/응답 헤더 일관성
3. **설정 드리프트 최소화**: 공통 Helm 값 템플릿화

## 🚀 빠른 시작 (5분)

### 1단계: FastAPI 미들웨어 추가

```python
# apps/seedtest_api/app/main.py
from fastapi import FastAPI
from shared.monitoring.middleware import AuditMetricsMiddleware, setup_structlog
from shared.monitoring.metrics import router as metrics_router

# structlog 설정
setup_structlog()

app = FastAPI()

# 감사 로그 + Prometheus 미들웨어
app.add_middleware(
    AuditMetricsMiddleware,
    service_name="seedtest-api",
    service_version="v1"
)

# 메트릭 엔드포인트
app.include_router(metrics_router)
```

### 2단계: 환경 변수 설정

```bash
# .env
SERVICE_NAME=seedtest-api
SERVICE_VERSION=v1
```

### 3단계: K8s ServiceMonitor 배포

```bash
kubectl apply -f ops/k8s/monitoring/servicemonitor.yaml
```

### 4단계: Grafana 대시보드 import

```bash
# ops/grafana/dashboards/api-monitoring.json 파일을
# Grafana UI에서 Import
```

## 📊 아키텍처

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ X-Trace-ID (생성 또는 전파)
       ↓
┌─────────────────────────────────────┐
│  FastAPI (AuditMetricsMiddleware)   │
│  - trace_id 생성/전파                │
│  - 지연시간 측정                      │
│  - Prometheus 메트릭 기록             │
│  - 구조화된 감사 로그                 │
└──────┬──────────────────────────────┘
       │
       ├─→ /metrics (Prometheus)
       │   └─→ http_requests_total
       │       http_request_duration_seconds
       │
       ├─→ stdout (감사 로그)
       │   └─→ {"trace_id": "...", "latency_s": 0.123, ...}
       │
       └─→ Response (X-Trace-ID 헤더)
           
┌─────────────┐
│ Prometheus  │ ← ServiceMonitor (15s 간격 스크랩)
└──────┬──────┘
       │
       ├─→ Grafana (대시보드)
       │   └─→ P50/P95/P99, 에러율, RPS
       │
       └─→ Argo Rollouts (AnalysisTemplate)
           └─→ 카나리 자동 승격/중단
```

## 🔧 상세 설정

### FastAPI 미들웨어

#### 기본 사용

```python
from shared.monitoring.middleware import AuditMetricsMiddleware

app.add_middleware(
    AuditMetricsMiddleware,
    service_name="univprepai-api",
    service_version="v1"
)
```

#### 경로 템플릿 비활성화 (동적 ID 많은 경우)

```python
app.add_middleware(
    AuditMetricsMiddleware,
    service_name="univprepai-api",
    service_version="v1",
    path_template_enabled=False  # /users/123 그대로 사용
)
```

### Prometheus 메트릭

#### http_requests_total (Counter)

```promql
# 요청 수
sum by (service, version) (rate(http_requests_total[5m]))

# 에러율
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m]))
```

#### http_request_duration_seconds (Histogram)

```promql
# P95 지연시간
histogram_quantile(0.95,
  sum by (le, service) (rate(http_request_duration_seconds_bucket[5m]))
)

# P99 지연시간
histogram_quantile(0.99,
  sum by (le, service) (rate(http_request_duration_seconds_bucket[5m]))
)
```

### Argo Rollouts 카나리 배포

#### 1. AnalysisTemplate 배포

```bash
kubectl apply -f ops/k8s/monitoring/analysistemplate.yaml
```

#### 2. Rollout 리소스 배포

```bash
kubectl apply -f ops/k8s/monitoring/rollout-example.yaml
```

#### 3. 카나리 배포 시작

```bash
# 새 이미지로 업데이트
kubectl argo rollouts set image univprepai-api \
  api=your.registry/univprepai-api:v2.0

# 진행 상황 확인
kubectl argo rollouts status univprepai-api

# 수동 승격
kubectl argo rollouts promote univprepai-api

# 중단 (롤백)
kubectl argo rollouts abort univprepai-api
```

## 📈 Grafana 대시보드

### 주요 패널

#### 1. 요청 수 (RPS)

```promql
sum by (service, version) (rate(http_requests_total[5m]))
```

#### 2. 에러율 (%)

```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m]))
* 100
```

#### 3. P50/P95/P99 지연시간

```promql
histogram_quantile(0.50, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m])))
histogram_quantile(0.95, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m])))
```

#### 4. 카나리 vs 스테이블 비교

```promql
histogram_quantile(0.95,
  sum by (le, version) (
    rate(http_request_duration_seconds_bucket{service="$service"}[5m])
  )
)
```

#### 5. 엔드포인트별 Top 10 지연

```promql
topk(10,
  histogram_quantile(0.95,
    sum by (le, path) (rate(http_request_duration_seconds_bucket[5m]))
  )
)
```

### 대시보드 Import

1. Grafana UI → Dashboards → Import
2. `ops/grafana/dashboards/api-monitoring.json` 업로드
3. Prometheus 데이터 소스 선택

## 🔍 trace_id 기반 계보 추적

### 1. 요청 시 trace_id 전달

```bash
curl -H "X-Trace-ID: abc123" http://api.example.com/v1/chat
```

### 2. 응답 헤더 확인

```bash
curl -v http://api.example.com/v1/chat
# < X-Trace-ID: abc123
```

### 3. 로그에서 검색

```bash
# JSON 로그에서 trace_id 검색
kubectl logs -l app=univprepai-api | jq 'select(.trace_id=="abc123")'
```

### 4. Grafana Explore (Loki 연동 시)

```logql
{app="univprepai-api"} |= "abc123"
```

## ⚙️ 운영 체크리스트 (5분 점검)

### 메트릭 확인

- [ ] `/metrics` 엔드포인트 200 OK
- [ ] Prometheus에서 `http_requests_total` 시계열 생성 확인
- [ ] Grafana에서 `histogram_quantile()` 쿼리 값 반환 확인

### trace_id 확인

- [ ] 요청 헤더 → 응답 헤더 전파 확인
- [ ] 로그에 trace_id 포함 확인
- [ ] 게이트웨이 → API → 로그 일관성 확인

### Rollouts 확인

- [ ] AnalysisTemplate 배포 확인
- [ ] Rollout 이벤트에서 Analysis 성공/실패 확인
- [ ] Prometheus 쿼리 결과와 임계치 일치 확인

## 🐛 문제 해결

### Q1: 메트릭이 안 잡혀요

**A**: ServiceMonitor 라벨 확인

```bash
# ServiceMonitor 확인
kubectl get servicemonitor

# Service 라벨 확인
kubectl get svc univprepai-api -o yaml | grep -A5 labels

# Prometheus targets 확인
# Prometheus UI → Status → Targets
```

### Q2: Cardinality 폭발

**A**: 경로 템플릿 사용

```python
# 동적 ID를 템플릿으로 변환
# /users/123 → /users/{id}
app.add_middleware(
    AuditMetricsMiddleware,
    path_template_enabled=True  # 기본값
)
```

### Q3: Rollout이 중단돼요

**A**: Grafana에서 같은 쿼리 실행

```promql
# AnalysisTemplate과 동일한 쿼리 실행
histogram_quantile(0.95,
  sum by (le) (
    rate(http_request_duration_seconds_bucket{
      service="univprepai-api",
      version="canary"
    }[1m])
  )
)

# 결과가 임계치(0.3)보다 높으면 중단됨
```

### Q4: trace_id가 전파 안 돼요

**A**: 게이트웨이 설정 확인

```nginx
# Nginx 예시
proxy_set_header X-Trace-ID $http_x_trace_id;

# 또는 생성
set $trace_id $http_x_trace_id;
if ($trace_id = "") {
    set $trace_id $request_id;
}
proxy_set_header X-Trace-ID $trace_id;
```

## 📚 DreamSeedAI 적용 팁

### 1. 공통 Helm 값 템플릿

```yaml
# values.yaml (공통)
monitoring:
  enabled: true
  serviceName: "{{ .Release.Name }}"
  serviceVersion: "{{ .Chart.Version }}"
  metricsPath: /metrics
  metricsPort: 8000
```

### 2. 서비스별 적용

| 서비스 | 포트 | 상태 |
|--------|------|------|
| seedtest_api | 8000 | 🔄 적용 대기 |
| univprepai_api | 8006 | 🔄 적용 대기 |
| governance | 8002 | 🔄 적용 대기 |

### 3. Grafana 폴더 구조

```
DreamSeedAI/
├── API Monitoring/
│   ├── SeedTest API
│   ├── UnivPrep API
│   └── Governance API
├── Dashboard/
│   ├── Teacher Dashboard
│   └── Admin Dashboard
└── Infrastructure/
    ├── Kubernetes
    └── Database
```

## 📖 참고 문서

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Argo Rollouts](https://argoproj.github.io/argo-rollouts/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

## 🎯 다음 단계

1. **OpenTelemetry 통합** (선택)
   - Tempo/Jaeger로 분산 트레이싱
   - Grafana에서 trace_id 점프

2. **알림 설정**
   - Prometheus AlertManager
   - Slack/PagerDuty 통합

3. **SLO 정의**
   - P95 < 300ms
   - 에러율 < 2%
   - 가용성 > 99.9%
