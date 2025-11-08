# ⚡ Governance 모니터링 빠른 시작 가이드

## 🎯 5분 안에 배포하기

### 전제 조건
- ✅ Slack Webhook URL 발급 완료
- ✅ PagerDuty Routing Key 발급 완료
- ✅ Kubernetes 클러스터 접근 가능

---

## 🚀 배포 명령어 (복사 & 붙여넣기)

### Step 1: Secret 생성 (1분)

```bash
cd /home/won/projects/dreamseed_monorepo

# 실제 값으로 교체하세요
export SLACK_WEBHOOK='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
export PAGERDUTY_KEY='R0XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

# Secret 생성
bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \
  "$SLACK_WEBHOOK" \
  "$PAGERDUTY_KEY"
```

### Step 2: 모니터링 스택 배포 (2분)

```bash
# Alertmanager 설정
kubectl apply -k infra/monitoring/alertmanager/

# Prometheus 알림 규칙
kubectl apply -f infra/argocd/apps/monitoring/prometheus-rule-seedtest.yaml

# Grafana Dashboard
kubectl apply -f infra/argocd/apps/monitoring/grafana-dashboard-seedtest.yaml
```

### Step 3: 검증 (1분)

```bash
# Alertmanager 검증
bash infra/monitoring/alertmanager/validate-alertmanager.sh monitoring

# 예상 출력:
# ✅ Secret exists
# ✅ Alertmanager CR exists
# ✅ Alertmanager Pod is Running
# ✅ Slack webhook configured
# ✅ PagerDuty routing key configured
```

### Step 4: 테스트 알림 (1분)

```bash
# Slack 테스트
curl -X POST "$SLACK_WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d '{"text": "🧪 SeedTest 모니터링 테스트 - Slack 연동 성공!"}'

# PagerDuty 테스트
curl -X POST 'https://events.pagerduty.com/v2/enqueue' \
  -H 'Content-Type: application/json' \
  -d "{
    \"routing_key\": \"$PAGERDUTY_KEY\",
    \"event_action\": \"trigger\",
    \"payload\": {
      \"summary\": \"🧪 SeedTest 모니터링 테스트\",
      \"severity\": \"info\",
      \"source\": \"seedtest-api\"
    }
  }"
```

---

## 📊 대시보드 접속

### Prometheus
```bash
kubectl -n monitoring port-forward svc/prometheus-k8s 9090:9090
# http://localhost:9090/alerts
```

### Grafana
```bash
kubectl -n monitoring port-forward svc/grafana 3000:3000
# http://localhost:3000
# 검색: "SeedTest API Dashboard"
```

### Alertmanager
```bash
kubectl -n monitoring port-forward svc/alertmanager-main 9093:9093
# http://localhost:9093
```

---

## 🎉 완료!

이제 다음 항목이 자동으로 모니터링됩니다:

### 알림 (15개)
- 🔴 **Critical**: API Down, Bundle Failure, Pod Restarting
- 🟡 **Warning**: High Latency, High Error Rate, High Deny Rate

### 메트릭 (19개)
- HTTP 요청 (3개)
- Governance 정책 (7개)
- IRT 드리프트 (3개)
- 데이터베이스 (3개)
- Feature Flags (2개)
- 애플리케이션 (1개)

### 알림 채널
- 📱 Slack: `#seedtest-alerts`
- 📟 PagerDuty: `seedtest-api` service

---

## 🔍 다음 단계

상세 가이드는 다음 문서를 참고하세요:
- `/docs/GOVERNANCE_MONITORING_DEPLOYMENT.md` - 전체 배포 가이드
- `/docs/MONITORING_VERIFICATION.md` - 메트릭 검증
- `/infra/monitoring/alertmanager/OPERATIONS_RUNBOOK.md` - 운영 가이드
