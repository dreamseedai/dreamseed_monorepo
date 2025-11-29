# K8s Audit·Prometheus 모니터링 - 최종 요약

**복붙-커밋-배포 Ready!** 🚀

## ✅ 완성된 파일

### 1. shared/monitoring/ (공용 모듈)
```
shared/monitoring/
├── __init__.py
├── middleware.py          # AuditMetricsMiddleware
├── metrics.py             # /metrics, /healthz 엔드포인트
└── requirements.txt       # prometheus-client, structlog
```

### 2. ops/k8s/monitoring/ (K8s 설정)
```
ops/k8s/monitoring/
├── servicemonitor.yaml        # Prometheus 스크랩 설정
├── analysistemplate.yaml      # Argo Rollouts 분석
└── rollout-example.yaml       # 카나리 배포 예시
```

### 3. ops/grafana/dashboards/ (대시보드)
```
ops/grafana/dashboards/
└── api-monitoring.json        # API 모니터링 대시보드
```

### 4. docs/ (문서)
```
docs/
├── K8S_MONITORING_GUIDE.md    # 상세 가이드
└── K8S_MONITORING_SUMMARY.md  # 이 파일
```

### 5. apps/seedtest_api/ (적용 예시)
```
apps/seedtest_api/app/
└── main_monitoring_example.py # 통합 예시
```

## 🚀 즉시 적용 (3단계)

### 1단계: 미들웨어 추가 (2줄!)

```python
from shared.monitoring.middleware import AuditMetricsMiddleware, setup_structlog
from shared.monitoring.metrics import router as metrics_router

setup_structlog()  # 앱 시작 시 한 번

app.add_middleware(
    AuditMetricsMiddleware,
    service_name="seedtest-api",
    service_version="v1"
)

app.include_router(metrics_router)  # /metrics, /healthz
```

### 2단계: K8s 배포

```bash
# ServiceMonitor 배포
kubectl apply -f ops/k8s/monitoring/servicemonitor.yaml

# AnalysisTemplate 배포 (카나리 사용 시)
kubectl apply -f ops/k8s/monitoring/analysistemplate.yaml
```

### 3단계: Grafana 대시보드 Import

```bash
# ops/grafana/dashboards/api-monitoring.json
# Grafana UI → Import
```

## 📊 핵심 기능

### 1. **trace_id 자동 전파**

```
Client → API (X-Trace-ID 생성) → 로그 → 응답 헤더
```

```bash
# 요청
curl -H "X-Trace-ID: abc123" http://api/v1/test

# 응답 헤더
X-Trace-ID: abc123

# 로그
{"trace_id": "abc123", "latency_s": 0.123, ...}
```

### 2. **Prometheus 메트릭**

```python
# 자동 수집
http_requests_total{method, path, status, service, version}
http_request_duration_seconds{method, path, status, service, version}
```

### 3. **Grafana 대시보드**

- 요청 수 (RPS)
- 에러율 (%)
- P50/P95/P99 지연시간
- 카나리 vs 스테이블 비교
- 엔드포인트별 Top 10 지연

### 4. **Argo Rollouts 자동 판단**

```yaml
# P95 < 300ms, 에러율 < 2%
# 조건 만족 → 자동 승격
# 조건 실패 → 자동 중단 (롤백)
```

## 📈 Prometheus 쿼리 예시

### 요청 수 (RPS)

```promql
sum by (service, version) (rate(http_requests_total[5m]))
```

### 에러율 (%)

```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m]))
* 100
```

### P95 지연시간

```promql
histogram_quantile(0.95,
  sum by (le, service) (rate(http_request_duration_seconds_bucket[5m]))
)
```

### 카나리 vs 스테이블

```promql
histogram_quantile(0.95,
  sum by (le, version) (
    rate(http_request_duration_seconds_bucket{service="$service"}[5m])
  )
)
```

## 🎯 라벨 정책 (Cardinality 방지)

### ✅ 최소 라벨 (5개)

- `method`: GET, POST, PUT, DELETE
- `path`: 템플릿 경로 (/users/{id})
- `status`: 200, 400, 500
- `service`: seedtest-api, univprepai-api
- `version`: v1, canary, stable

### ❌ 금지 라벨

- `user_id`: 사용자별 (Cardinality 폭발)
- `trace_id`: 요청별 (로그에만 사용)
- `timestamp`: 시간별 (불필요)

## 🔧 서비스별 적용

| 서비스 | 포트 | 미들웨어 | ServiceMonitor | 상태 |
|--------|------|---------|----------------|------|
| seedtest_api | 8000 | ✅ 예시 완성 | 🔄 대기 | 🔄 적용 대기 |
| analytics_api | 8006 | 🔄 대기 | 🔄 대기 | ⏳ 대기 |
| governance | 8002 | 🔄 대기 | 🔄 대기 | ⏳ 대기 |

## ✅ 운영 체크리스트

### 메트릭 확인 (1분)

```bash
# 1. /metrics 엔드포인트 확인
curl http://localhost:8000/metrics

# 2. Prometheus targets 확인
# Prometheus UI → Status → Targets

# 3. Grafana 쿼리 테스트
# histogram_quantile(0.95, ...)
```

### trace_id 확인 (1분)

```bash
# 1. 요청 → 응답 헤더 확인
curl -v -H "X-Trace-ID: test123" http://localhost:8000/

# 2. 로그 확인
kubectl logs -l app=seedtest-api | jq 'select(.trace_id=="test123")'
```

### Rollouts 확인 (1분)

```bash
# 1. AnalysisTemplate 확인
kubectl get analysistemplate

# 2. Rollout 상태 확인
kubectl argo rollouts status univprepai-api

# 3. Analysis 결과 확인
kubectl argo rollouts get rollout univprepai-api
```

## 🐛 문제 해결 (5분)

### Q1: 메트릭이 안 잡혀요

```bash
# ServiceMonitor 라벨 확인
kubectl get servicemonitor -o yaml | grep -A5 selector

# Service 라벨 확인
kubectl get svc seedtest-api -o yaml | grep -A5 labels

# 일치하지 않으면 수정
```

### Q2: Cardinality 폭발

```python
# 경로 템플릿 사용
app.add_middleware(
    AuditMetricsMiddleware,
    path_template_enabled=True  # /users/123 → /users/{id}
)
```

### Q3: Rollout 중단

```promql
# Grafana에서 같은 쿼리 실행
histogram_quantile(0.95,
  sum by (le) (
    rate(http_request_duration_seconds_bucket{
      service="univprepai-api",
      version="canary"
    }[1m])
  )
)

# 결과 > 0.3 (임계치) → 중단됨
# 히스토그램 버킷 조정 또는 임계치 완화
```

## 📚 참고 문서

- **상세 가이드**: `docs/K8S_MONITORING_GUIDE.md`
- **Prometheus 쿼리**: [Prometheus Docs](https://prometheus.io/docs/)
- **Argo Rollouts**: [Argo Docs](https://argoproj.github.io/argo-rollouts/)

## 🎉 완료!

**이제 복붙-커밋-배포만 하면 됩니다!**

```bash
# 1. 의존성 설치
pip install -r shared/monitoring/requirements.txt

# 2. 미들웨어 추가 (2줄)
# app/main.py 참고

# 3. K8s 배포
kubectl apply -f ops/k8s/monitoring/

# 4. Grafana 대시보드 Import
# ops/grafana/dashboards/api-monitoring.json

# 5. 테스트
curl http://localhost:8000/metrics
```

---

**모든 파일이 준비되었습니다!** 각 FastAPI 서비스에 미들웨어 2줄만 추가하면 즉시 작동합니다! 🚀
