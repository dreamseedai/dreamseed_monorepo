# SeedTest API 모니터링 빠른 참조

## 📊 PrometheusRule & Grafana 즉시 확인

### 1분 검증 (Kustomize 렌더링)

```bash
# 룰 그룹 확인
kubectl kustomize ops/k8s/governance/base \
  | grep 'name: seedtest-api\.'

# 출력 예상:
#   name: seedtest-api.http
#   name: seedtest-api.governance
#   name: seedtest-api.featureflags
#   name: seedtest-api.irt
#   name: seedtest-api.db
#   name: seedtest-api.app
```

### 배포 확인 (클러스터)

```bash
# 자동 검증 스크립트
bash ops/k8s/governance/MONITORING_VALIDATION.sh seedtest prometheus

# 수동 확인
kubectl -n seedtest get prometheusrule seedtest-api-rules
kubectl -n seedtest get servicemonitor seedtest-api
kubectl -n seedtest get cm seedtest-api-dashboard
```

---

## 🎯 레코딩 룰 (Recording Rules)

성능 최적화를 위한 사전 계산 메트릭

| 레코딩 룰 | 설명 | 사용처 |
|----------|------|--------|
| `job:http_error_rate_5m` | 5분 HTTP 5xx 에러율 | 대시보드, 알림 |
| `job:http_error_rate_30m` | 30분 HTTP 5xx 에러율 | 기준선 비교 |
| `job:http_request_duration_seconds:p90_5m` | HTTP p90 지연 | 대시보드 |
| `job:http_request_duration_seconds:p95_5m` | HTTP p95 지연 | 알림, 대시보드 |
| `job:policy_evaluation_duration_seconds:p95_5m` | 정책 평가 p95 | 대시보드 |
| `job:db_query_duration_seconds:p95_5m` | DB 쿼리 p95 | 알림, 대시보드 |

**Grafana에서 사용 예시:**
```promql
# 단순화된 쿼리 (레코딩 룰 활용)
job:http_error_rate_5m{endpoint="/api/v1/exams"}

# vs 원본 쿼리 (매번 계산)
sum by (endpoint, method) (rate(http_requests_total{status=~"5.."}[5m]))
/
sum by (endpoint, method) (rate(http_requests_total[5m]))
```

---

## 🚨 알림 룰 (Alert Rules) - 15개

### HTTP (4개)

| 알림 | 조건 | 심각도 | 설명 |
|------|------|--------|------|
| `SeedtestApiHighErrorRate` | 5m > 5% AND 30m > 3% | warning | 에러율 급증 (기준선 대비) |
| `SeedtestApiHighLatencyP95` | p95 > 1s | warning | 응답 지연 상승 |
| `SeedtestApiRequestsInProgressHigh` | in-flight > 200 | warning | 동시 요청 폭증 |
| `SeedtestApiMetricsAbsent` | 메트릭 결측 10분 | critical | ServiceMonitor 실패 |

### Governance (4개)

| 알림 | 조건 | 심각도 |
|------|------|--------|
| `GovernancePolicyDenySpike` | 10분 내 deny > 50 | warning |
| `GovernancePolicyEvalLatencyHigh` | p95 > 200ms | warning |
| `GovernanceBundleLoadFailed` | bundle_loaded < 1 | critical |
| `GovernanceBundleReloadErrors` | 15분 내 reload error | warning |

### Feature Flags (2개)

| 알림 | 조건 | 심각도 |
|------|------|--------|
| `FeatureFlagCriticalDisabled` | risk_engine 비활성 | critical |
| `FeatureFlagCheckErrors` | 10분 내 에러 > 10 | warning |

### IRT (2개)

| 알림 | 조건 | 심각도 |
|------|------|--------|
| `IrtDriftDetectedSpike` | 30분 내 감지 > 5 | warning |
| `IrtDriftFlaggedItemsHigh` | flagged > 50 | warning |

### DB (3개)

| 알림 | 조건 | 심각도 |
|------|------|--------|
| `DbLatencyHigh` | p95 > 200ms | warning |
| `DbErrorsSpike` | 10분 내 > 20 | warning |
| `DbConnectionsHigh` | active > 200 | warning |

### App (1개)

| 알림 | 조건 | 심각도 |
|------|------|--------|
| `AppVersionChanged` | 버전 변경 감지 | info |

---

## 📈 Grafana 대시보드

### 임포트 방법

**자동 (Sidecar):**
- Grafana 사이드카가 `grafana_dashboard="1"` 라벨 감지
- ConfigMap 자동 임포트
- 네임스페이스: `seedtest`

**수동 (UI):**
1. Grafana → Dashboards → Import
2. ConfigMap에서 JSON 추출:
   ```bash
   kubectl -n seedtest get cm seedtest-api-dashboard \
     -o jsonpath='{.data.seedtest-api-governance\.json}' \
     > /tmp/dashboard.json
   ```
3. `/tmp/dashboard.json` 업로드

### 대시보드 구조 (6개 Row, 16개 패널)

**1. HTTP**
- Error Rate (5m/30m) - 시계열
- p95 Latency - 시계열
- In-Flight Requests - 시계열

**2. Governance**
- Policy Deny / Allow Rate - 시계열
- Policy Eval p95 - 시계열
- Bundle Loaded - Stat
- Bundle Reload (success/error) - 시계열

**3. Feature Flags**
- risk_engine enabled - Stat
- Flag Checks (rate) - 시계열

**4. IRT / Content**
- IRT Drift Detections - 시계열
- Flagged Items - Stat

**5. Database**
- DB p95 - 시계열
- DB Errors - 시계열
- Active DB Connections - Stat

**6. App**
- App Version - Stat

### 템플릿 변수

| 변수 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `namespace` | query | seedtest | K8s 네임스페이스 |
| `app` | textbox | seedtest-api | 앱 이름 필터 |

---

## 🔧 빠른 트러블슈팅

### PrometheusRule 로드 안 됨

```bash
# 1. 라벨 확인 (release: prometheus)
kubectl -n seedtest get prometheusrule seedtest-api-rules -o yaml \
  | grep 'release:'

# 2. Prometheus Operator 로그
PROM_OP=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=prometheus-operator -o jsonpath='{.items[0].metadata.name}')
kubectl -n monitoring logs "$PROM_OP" | grep -i prometheusrule

# 3. Prometheus ConfigMap 확인
kubectl -n monitoring get prometheus -o yaml | grep ruleSelector
```

### ServiceMonitor 타겟 미등록

```bash
# 1. 타겟 확인 (Prometheus UI)
kubectl -n monitoring port-forward svc/prometheus-operated 9090:9090 &
curl -s 'http://127.0.0.1:9090/api/v1/targets' | jq '.data.activeTargets[] | select(.labels.job=="seedtest-api")'

# 2. 라벨 일치 확인
kubectl -n seedtest get servicemonitor seedtest-api -o yaml | grep -A5 labels
kubectl -n monitoring get prometheus -o yaml | grep -A10 serviceMonitorSelector
```

### Grafana 대시보드 임포트 실패

```bash
# 1. 사이드카 확인
kubectl -n monitoring get deploy -l app.kubernetes.io/name=grafana -o yaml \
  | grep -i sidecar

# 2. ConfigMap 라벨 확인
kubectl -n seedtest get cm seedtest-api-dashboard -o yaml | grep grafana_dashboard

# 3. Grafana 재시작 (사이드카 재스캔)
kubectl -n monitoring rollout restart deploy/grafana
```

### 히스토그램 메트릭 없음

```bash
# 1. 메트릭 엔드포인트 확인
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest exec "$POD" -- curl -s http://localhost:8000/metrics \
  | grep -E '(http_request_duration_seconds_bucket|policy_evaluation_duration_seconds_bucket|db_query_duration_seconds_bucket)'

# 2. 없으면 Python 코드에서 Histogram 생성 필요
# apps/seedtest_api/routers/prometheus_metrics.py 확인
```

---

## 📖 추가 리소스

- **DEPLOYMENT_RUNBOOK.md**: 전체 배포/검증 절차
- **MONITORING_VERIFICATION.md**: 모니터링 상세 가이드 (389줄)
- **VALIDATION_CHEATSHEET.sh**: 자동화 검증 스크립트

---

## 🎯 운영 팁

### 문턱값 조정

실제 트래픽 확인 후 조정 권장:

```bash
# 현재 p95 확인
kubectl -n monitoring port-forward svc/prometheus-operated 9090:9090 &
curl -s 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=job:http_request_duration_seconds:p95_5m' \
  | jq '.data.result[] | {endpoint: .metric.endpoint, value: .value[1]}'

# 알림 문턱값 수정
# ops/k8s/governance/base/prometheusrule.yaml
# expr: job:http_request_duration_seconds:p95_5m > 1.0  # ← 조정
```

### 알림 라우팅 (Alertmanager)

```yaml
# Alertmanager config 예시
route:
  routes:
    - matchers:
        - service = "seedtest-api"
        - severity =~ "critical|warning"
      receiver: seedtest-team
      continue: true

receivers:
  - name: seedtest-team
    slack_configs:
      - channel: '#seedtest-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### SLO 목표 설정 예시

```promql
# 28일 99.9% 가용성 (에러 예산)
# 에러 예산 = (1 - 0.999) * 28일 = 40.32분

# 소진율 확인
sum(increase(http_requests_total{status=~"5.."}[28d]))
/
sum(increase(http_requests_total[28d]))
```

---

**문서 업데이트**: 2025-11-08  
**버전**: v2.0 (SLO-기반 레코딩/알림 룰)
