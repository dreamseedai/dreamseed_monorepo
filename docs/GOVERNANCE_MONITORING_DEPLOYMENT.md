# 🚀 Governance 모니터링 시스템 배포 가이드

## 📋 개요

SeedTest API의 Governance 시스템 모니터링을 위한 완전한 배포 가이드입니다.

**현재 상태**: 
- ✅ Prometheus 메트릭 엔드포인트 구현 완료
- ✅ PrometheusRule (알림 규칙) 작성 완료
- ✅ Grafana Dashboard 작성 완료
- ✅ Alertmanager 설정 완료
- ⏳ Slack/PagerDuty 키 발급 대기

**브랜치**: `feat/governance-production-ready`  
**커밋**: `a0ad14a11`

---

## 🎯 배포 순서

### Phase 1: 로컬 검증 (10분)
### Phase 2: Credentials 발급 (10분)
### Phase 3: Kubernetes 배포 (5분)
### Phase 4: 검증 및 테스트 (10분)

---

## 📦 Phase 1: 로컬 검증

### 1.1 패키지 설치

```bash
cd /home/won/projects/dreamseed_monorepo/apps/seedtest_api

# 가상환경 활성화 (선택)
# python -m venv venv
# source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 1.2 서버 실행

```bash
# FastAPI 서버 실행
uvicorn app.main:app --reload --port 8000
```

### 1.3 메트릭 확인

```bash
# 새 터미널에서 실행

# 1. Health check
curl http://localhost:8000/health

# 2. 전체 메트릭 확인
curl http://localhost:8000/metrics

# 3. 메트릭 타입 확인
curl http://localhost:8000/metrics | grep '^# TYPE'

# 4. HTTP 메트릭
curl http://localhost:8000/metrics | grep 'http_requests'

# 5. Governance 메트릭
curl http://localhost:8000/metrics | grep -E 'policy_|governance_'

# 6. IRT 드리프트 메트릭
curl http://localhost:8000/metrics | grep 'irt_drift'

# 7. DB 메트릭
curl http://localhost:8000/metrics | grep 'db_'
```

**예상 출력**:
```promql
# TYPE http_requests_total counter
# TYPE http_request_duration_seconds histogram
# TYPE policy_evaluations_total counter
# TYPE governance_bundle_loaded gauge
# TYPE irt_drift_flagged_items gauge
# TYPE db_connections_active gauge
...
```

---

## 🔑 Phase 2: Credentials 발급

### 2.1 Slack Webhook 발급 (5분)

#### Step 1: Slack App 생성
1. https://api.slack.com/apps 접속
2. **Create New App** 클릭
3. **From scratch** 선택
4. App Name: `SeedTest Alerts`
5. Workspace 선택 → **Create App**

#### Step 2: Incoming Webhooks 활성화
1. 좌측 메뉴 **Incoming Webhooks** 클릭
2. **Activate Incoming Webhooks** 토글 ON
3. **Add New Webhook to Workspace** 클릭
4. 채널 선택: `#seedtest-alerts` (없으면 생성)
5. **Allow** 클릭

#### Step 3: Webhook URL 복사
```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

**저장 위치**: 메모장에 임시 저장

### 2.2 PagerDuty Routing Key 발급 (5분)

#### Step 1: PagerDuty Service 생성
1. PagerDuty 로그인
2. **Services** → **Service Directory**
3. **New Service** 클릭
4. Service Name: `seedtest-api`
5. Escalation Policy 선택
6. **Create Service**

#### Step 2: Integration 추가
1. 생성된 Service 클릭
2. **Integrations** 탭
3. **Add Integration** 클릭
4. Integration Type: **Events API v2** 선택
5. **Add**

#### Step 3: Routing Key 복사
```
R0XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
(32자 문자열)

**저장 위치**: 메모장에 임시 저장

---

## ☸️ Phase 3: Kubernetes 배포

### 3.1 Secret 생성

```bash
cd /home/won/projects/dreamseed_monorepo

# Alertmanager Secret 생성
bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \
  'https://hooks.slack.com/services/실제Webhook' \
  'R0실제PagerDutyRoutingKey'
```

**예상 출력**:
```
✅ Secret 'alertmanager-secrets' created in namespace 'monitoring'
```

### 3.2 Alertmanager 배포

```bash
# Kustomize로 Alertmanager 설정 적용
kubectl apply -k infra/monitoring/alertmanager/
```

**예상 출력**:
```
secret/alertmanager-secrets configured
alertmanager.monitoring.coreos.com/main configured
```

### 3.3 PrometheusRule 배포

```bash
# Prometheus 알림 규칙 배포
kubectl apply -f infra/argocd/apps/monitoring/prometheus-rule-seedtest.yaml
```

**예상 출력**:
```
prometheusrule.monitoring.coreos.com/seedtest-api-alerts created
```

### 3.4 Grafana Dashboard 배포

```bash
# Grafana Dashboard ConfigMap 배포
kubectl apply -f infra/argocd/apps/monitoring/grafana-dashboard-seedtest.yaml
```

**예상 출력**:
```
configmap/grafana-dashboard-seedtest created
```

### 3.5 SeedTest API 배포 (메트릭 포함)

```bash
# ArgoCD로 배포하거나 직접 배포
# Option 1: ArgoCD (권장)
argocd app sync seedtest-api

# Option 2: 직접 배포
kubectl apply -f ops/k8s/seedtest-api/
```

---

## ✅ Phase 4: 검증 및 테스트

### 4.1 Alertmanager 검증

```bash
# Alertmanager 검증 스크립트 실행
bash infra/monitoring/alertmanager/validate-alertmanager.sh monitoring
```

**예상 출력**:
```
✅ Secret exists
✅ Alertmanager CR exists
✅ Alertmanager Pod is Running
✅ Slack webhook configured
✅ PagerDuty routing key configured
```

### 4.2 Prometheus 타겟 확인

```bash
# Prometheus UI 접속
kubectl -n monitoring port-forward svc/prometheus-k8s 9090:9090

# 브라우저에서 확인
# http://localhost:9090/targets
# → "seedtest-api" 타겟이 UP 상태인지 확인
```

### 4.3 메트릭 수집 확인

```bash
# Prometheus에서 메트릭 쿼리
# http://localhost:9090/graph

# 쿼리 예제:
up{job="seedtest-api"}
http_requests_total{job="seedtest-api"}
policy_evaluations_total{job="seedtest-api"}
governance_bundle_loaded{job="seedtest-api"}
```

### 4.4 Grafana Dashboard 확인

```bash
# Grafana UI 접속
kubectl -n monitoring port-forward svc/grafana 3000:3000

# 브라우저에서 확인
# http://localhost:3000
# → 검색: "SeedTest API Dashboard"
```

### 4.5 Slack 알림 테스트

```bash
# Slack Webhook 직접 테스트
curl -X POST 'https://hooks.slack.com/services/실제Webhook' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🧪 SeedTest API 모니터링 테스트",
    "attachments": [{
      "color": "good",
      "fields": [{
        "title": "Status",
        "value": "Alertmanager 설정 완료",
        "short": true
      }]
    }]
  }'
```

**예상 결과**: `#seedtest-alerts` 채널에 메시지 수신

### 4.6 PagerDuty 알림 테스트

```bash
# PagerDuty Events API 직접 테스트
curl -X POST 'https://events.pagerduty.com/v2/enqueue' \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key": "R0실제PagerDutyRoutingKey",
    "event_action": "trigger",
    "payload": {
      "summary": "🧪 SeedTest API 모니터링 테스트",
      "severity": "info",
      "source": "seedtest-api",
      "custom_details": {
        "message": "Alertmanager 설정 완료"
      }
    }
  }'
```

**예상 결과**: PagerDuty에 Incident 생성

### 4.7 Alertmanager 종단 테스트

```bash
# amtool 설치 (필요시)
# brew install alertmanager  # macOS
# apt-get install prometheus-alertmanager  # Ubuntu

# Alertmanager에 테스트 알림 전송
kubectl -n monitoring port-forward svc/alertmanager-main 9093:9093 &

amtool alert add test_alert \
  alertname=TestAlert \
  severity=warning \
  summary="Alertmanager 테스트" \
  --alertmanager.url=http://localhost:9093
```

**예상 결과**: 
- Slack에 알림 수신
- PagerDuty에 Incident 생성

---

## 🔍 트러블슈팅

### 문제 1: 메트릭 엔드포인트 404

**증상**:
```bash
curl http://localhost:8000/metrics
# 404 Not Found
```

**해결**:
```bash
# 1. prometheus_router가 main.py에 추가되었는지 확인
grep "prometheus_router" apps/seedtest_api/app/main.py

# 2. prometheus-client 설치 확인
pip list | grep prometheus-client

# 3. 서버 재시작
pkill -f uvicorn
uvicorn app.main:app --reload --port 8000
```

### 문제 2: Prometheus 타겟 DOWN

**증상**:
```
Prometheus UI → Targets → seedtest-api: DOWN
```

**해결**:
```bash
# 1. Pod 상태 확인
kubectl -n seedtest get pods -l app=seedtest-api

# 2. Service 확인
kubectl -n seedtest get svc seedtest-api

# 3. ServiceMonitor 확인
kubectl -n seedtest get servicemonitor seedtest-api -o yaml

# 4. Pod 로그 확인
kubectl -n seedtest logs -l app=seedtest-api --tail=50
```

### 문제 3: Slack 알림 미수신

**증상**: Alertmanager에서 알림이 발생했지만 Slack에 메시지가 없음

**해결**:
```bash
# 1. Secret 확인
kubectl -n monitoring get secret alertmanager-secrets -o yaml

# 2. Alertmanager 로그 확인
kubectl -n monitoring logs -l app.kubernetes.io/name=alertmanager --tail=100

# 3. Webhook URL 재확인
# - https://hooks.slack.com/services/... 형식인지 확인
# - 채널 권한 확인

# 4. Alertmanager 재시작
kubectl -n monitoring delete pod -l app.kubernetes.io/name=alertmanager
```

### 문제 4: PagerDuty Incident 미생성

**증상**: Alertmanager에서 알림이 발생했지만 PagerDuty에 Incident가 없음

**해결**:
```bash
# 1. Routing Key 확인 (32자)
kubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.pagerduty_routing_key}' | base64 -d

# 2. PagerDuty Service 상태 확인
# - Service가 활성화되어 있는지
# - Integration이 Events API v2인지

# 3. Alertmanager 로그에서 PagerDuty 관련 오류 확인
kubectl -n monitoring logs -l app.kubernetes.io/name=alertmanager | grep -i pagerduty
```

---

## 📊 모니터링 대시보드

### Prometheus Alerts
```
http://localhost:9090/alerts
```

**주요 알림**:
- `SeedTestAPIDown`: API 서버 다운
- `SeedTestAPIHighLatency`: 높은 지연시간
- `GovernanceHighDenyRate`: 높은 정책 거부율
- `GovernanceBundleNotLoaded`: 번들 로드 실패
- `IRTDriftHighFlaggedItems`: 높은 드리프트 문항 수

### Grafana Dashboard
```
http://localhost:3000
```

**패널**:
1. HTTP Request Rate
2. HTTP Request Latency (p50, p95)
3. Error Rate
4. Policy Deny Rate
5. Governance Bundle Status
6. IRT Drift Flagged Items
7. Policy Evaluations by Action & Phase
8. Database Connections

### Alertmanager UI
```
http://localhost:9093
```

**기능**:
- 활성 알림 확인
- 알림 Silence (일시 중지)
- 알림 히스토리

---

## 📝 배포 체크리스트

### 사전 준비
- [ ] Slack Workspace 접근 권한
- [ ] PagerDuty 계정 및 Service 생성 권한
- [ ] Kubernetes 클러스터 접근 권한
- [ ] `kubectl`, `argocd` CLI 설치

### Phase 1: 로컬 검증
- [ ] `prometheus-client` 패키지 설치
- [ ] FastAPI 서버 실행
- [ ] `/metrics` 엔드포인트 확인
- [ ] `/health` 엔드포인트 확인
- [ ] 메트릭 타입 확인 (19개)

### Phase 2: Credentials
- [ ] Slack Webhook URL 발급
- [ ] PagerDuty Routing Key 발급
- [ ] Credentials 안전하게 저장

### Phase 3: Kubernetes 배포
- [ ] Alertmanager Secret 생성
- [ ] Alertmanager 설정 적용
- [ ] PrometheusRule 배포
- [ ] Grafana Dashboard 배포
- [ ] SeedTest API 배포

### Phase 4: 검증
- [ ] Alertmanager 검증 스크립트 실행
- [ ] Prometheus 타겟 UP 확인
- [ ] 메트릭 수집 확인
- [ ] Grafana Dashboard 확인
- [ ] Slack 알림 테스트
- [ ] PagerDuty 알림 테스트
- [ ] Alertmanager 종단 테스트

---

## 🎯 다음 단계

### 1. 실제 알림 발생 시나리오

#### 시나리오 1: API Down
```bash
# SeedTest API Pod 삭제
kubectl -n seedtest delete pod -l app=seedtest-api

# 예상 결과 (2분 후):
# - Prometheus Alert: SeedTestAPIDown (FIRING)
# - Slack: #seedtest-alerts에 알림
# - PagerDuty: Critical Incident 생성
```

#### 시나리오 2: High Latency
```python
# 의도적으로 느린 엔드포인트 호출
import time
import requests

for _ in range(100):
    requests.get("http://seedtest-api/slow-endpoint")
    time.sleep(0.1)

# 예상 결과 (5분 후):
# - Prometheus Alert: SeedTestAPIHighLatency (FIRING)
# - Slack: Warning 알림
```

#### 시나리오 3: Governance Bundle Failure
```python
# Governance 번들 리로드 실패 시뮬레이션
from apps.seedtest_api.routers.prometheus_metrics import record_bundle_reload

record_bundle_reload(
    bundle_id="phase0-bundle",
    phase="phase0",
    status="failure",
    duration=5.0
)

# 예상 결과 (2분 후):
# - Prometheus Alert: GovernanceBundleReloadFailure (FIRING)
# - Slack: Critical 알림
# - PagerDuty: Critical Incident
```

### 2. 알림 임계값 튜닝

```yaml
# infra/argocd/apps/monitoring/prometheus-rule-seedtest.yaml

# 예: Latency 임계값 조정
- alert: SeedTestAPIHighLatency
  expr: histogram_quantile(0.95, ...) > 2  # 1초 → 2초로 변경
  for: 10m  # 5분 → 10분으로 변경
```

### 3. 추가 알림 채널

```yaml
# infra/monitoring/alertmanager/alertmanager-cr.yaml

receivers:
  - name: 'seedtest-team'
    slack_configs: [...]
    pagerduty_configs: [...]
    # 추가 채널
    email_configs:
      - to: 'team@dreamseed.ai'
        from: 'alerts@dreamseed.ai'
    webhook_configs:
      - url: 'https://custom-webhook.example.com'
```

---

## 📚 참고 문서

### 프로젝트 문서
- `/docs/MONITORING_VERIFICATION.md` - 메트릭 검증 가이드
- `/infra/monitoring/alertmanager/SETUP_CREDENTIALS.md` - Credentials 발급 상세
- `/infra/monitoring/alertmanager/OPERATIONS_RUNBOOK.md` - 운영 Runbook
- `/infra/monitoring/alertmanager/ALERTMANAGER_ROUTING_GUIDE.md` - 라우팅 가이드

### 외부 문서
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [PagerDuty Events API v2](https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview)

---

## 🎉 완료!

모든 단계를 완료하면:
- ✅ SeedTest API 메트릭 수집 (19개 메트릭)
- ✅ Prometheus 알림 규칙 (15개 알림)
- ✅ Grafana 대시보드 (8개 패널)
- ✅ Slack 알림 자동화
- ✅ PagerDuty Incident 자동 생성

**현재 상태**: 🎯 Slack/PD 키만 발급하면 즉시 배포 가능!
