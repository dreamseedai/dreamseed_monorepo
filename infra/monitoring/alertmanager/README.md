# Alertmanager Configuration

이 디렉토리는 Prometheus Operator 환경에서 Alertmanager 설정을 GitOps로 관리합니다.

## 📁 파일 구조

```
infra/monitoring/alertmanager/
├── alertmanager-secret.yaml          # Alertmanager 설정 (Secret)
├── ALERTMANAGER_ROUTING_GUIDE.md     # 상세 설정 가이드 (보안, 트러블슈팅)
└── validate-alertmanager.sh          # 검증 스크립트
```

## 🚀 빠른 시작

### 1. 보안 설정 (필수)

**Slack Webhook URL 주입:**

```bash
# Option A: kubectl로 Secret 생성 (임시)
kubectl -n monitoring create secret generic alertmanager-secrets \
  --from-literal=slack_webhook_url='https://hooks.slack.com/services/XXX/YYY/ZZZ'

# Option B: External Secrets Operator (권장)
# infra/monitoring/alertmanager/external-secret.yaml 참고
```

**PagerDuty Routing Key 주입:**

```bash
# PagerDuty UI → Services → Integrations → Events API v2 → Routing Key 복사
kubectl -n monitoring create secret generic pagerduty-routing-key \
  --from-literal=routing_key='YOUR_PAGERDUTY_ROUTING_KEY'
```

**alertmanager-secret.yaml 수정:**

```yaml
# 1. Slack webhook URL 참조 (실제 값 대신)
slack_configs:
  - api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url

# 2. PagerDuty routing key 참조
pagerduty_configs:
  - routing_key_file: /etc/alertmanager/secrets/pagerduty-routing-key/routing_key
```

### 2. 배포

```bash
# ArgoCD (권장)
kubectl apply -f infra/argocd/apps/monitoring/alertmanager-config.yaml

# 또는 직접 적용
kubectl apply -f infra/monitoring/alertmanager/alertmanager-secret.yaml
```

### 3. 검증

```bash
# 자동 검증 스크립트
bash infra/monitoring/alertmanager/validate-alertmanager.sh monitoring

# 수동 검증
kubectl -n monitoring get secret alertmanager-main
kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager
```

---

## 🎯 알림 라우팅 규칙

| 조건 | 수신자 | 채널/서비스 | 지연 |
|------|--------|-------------|------|
| `service=seedtest-api` + `severity=critical` | PagerDuty | Incidents | 즉시 (0s) |
| `service=seedtest-api` + `severity=warning\|info` | Slack | #seedtest-alerts | 30s |
| `namespace=seedtest` (기타) | Slack | #seedtest-notify | 30s |

**억제 규칙**: Critical 활성 시 동일 alertname의 Warning 억제

---

## 🔧 트러블슈팅

### Secret 적용 후 반영 안 됨

```bash
# Alertmanager 재시작
kubectl -n monitoring rollout restart statefulset alertmanager-main

# 로그 확인
kubectl -n monitoring logs -l app.kubernetes.io/name=alertmanager | tail -50
```

### Slack 알림 전송 실패

```bash
# Webhook URL 테스트 (Pod 내부)
kubectl -n monitoring exec -it alertmanager-main-0 -- \
  curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test from Alertmanager"}' \
  https://hooks.slack.com/services/XXX/YYY/ZZZ

# NetworkPolicy 확인 (egress 443 허용 필요)
kubectl -n monitoring get networkpolicy
```

### PagerDuty 인시던트 생성 안 됨

```bash
# Routing Key 검증
kubectl -n monitoring get secret alertmanager-main \
  -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d | grep routing_key

# Events API v2 엔드포인트 테스트
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key": "YOUR_ROUTING_KEY",
    "event_action": "trigger",
    "payload": {
      "summary": "Test from Alertmanager",
      "severity": "critical",
      "source": "manual-test"
    }
  }'
```

---

## 📚 상세 문서

- **ALERTMANAGER_ROUTING_GUIDE.md**: 
  - 보안 설정 (ESO, Sealed Secrets, SOPS)
  - 트러블슈팅 (10+ 시나리오)
  - 운영 모범 사례 (라벨 표준화, SLO 알림)
  
- **validate-alertmanager.sh**:
  - Secret 확인
  - Alertmanager Pod 상태
  - 라우팅/수신자/억제 규칙 검증
  - 테스트 알림 전송 가이드

---

## 🔗 관련 리소스

- **PrometheusRule**: `ops/k8s/governance/base/prometheusrule.yaml`
- **ServiceMonitor**: `ops/k8s/governance/base/servicemonitor.yaml`
- **모니터링 가이드**: `ops/k8s/governance/MONITORING_QUICKREF.md`

---

**업데이트**: 2025-11-08  
**관리**: DevOps Team
