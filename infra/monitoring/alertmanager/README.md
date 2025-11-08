# Alertmanager Configuration - Slack Only

이 디렉토리는 Prometheus Operator 환경에서 Alertmanager 설정을 GitOps로 관리합니다.
**Slack 전용 구성**으로 모든 알림이 Slack으로 전송됩니다.

## 📁 파일 구조

```
infra/monitoring/alertmanager/
├── alertmanager-cr.yaml               # Alertmanager CR (Secret 마운트 설정)
├── alertmanager-cr-patch.yaml         # Kustomize 패치 (spec.secrets 보장)
├── alertmanager-secret.yaml           # Alertmanager 설정 (Slack 전용)
├── kustomization.yaml                 # Kustomize 설정
├── setup-secrets.sh                   # Slack Webhook Secret 생성 스크립트
├── validate-alertmanager.sh           # 검증 스크립트
├── SETUP_CREDENTIALS.md               # ⭐ Slack Webhook 발급 가이드
├── ALERTMANAGER_ROUTING_GUIDE.md      # 상세 설정 가이드 (보안, 트러블슈팅)
└── OPERATIONS_RUNBOOK.md              # 운영 런북 (키 회전, 장애 대응, ArgoCD 통합)
```

## 🚀 빠른 시작

### Option A: Kustomize 사용 (권장)

```bash
# 0. Slack Webhook 발급 (SETUP_CREDENTIALS.md 참고)
# - https://api.slack.com/apps → Create App → Incoming Webhooks

# 1. Secret 생성
bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \
  'https://hooks.slack.com/services/T실제값/B실제값/실제토큰'

# 2. Kustomize로 전체 적용
kubectl apply -k infra/monitoring/alertmanager/

# 3. 검증
bash infra/monitoring/alertmanager/validate-alertmanager.sh monitoring

# 4. 테스트 알림 전송 (SETUP_CREDENTIALS.md 참고)
```

### Option B: 개별 적용

### 1. 보안 설정 (필수)

**Slack Webhook URL 주입:**

```bash
# Option A: 스크립트 사용 (권장)
bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \
  'https://hooks.slack.com/services/T실제값/B실제값/실제토큰'

# Option B: kubectl로 직접 생성
kubectl -n monitoring create secret generic alertmanager-secrets \
  --from-literal=slack_webhook_url='https://hooks.slack.com/services/T실제값/B실제값/실제토큰'

# Option C: External Secrets Operator (프로덕션 권장)
# infra/monitoring/alertmanager/external-secret.yaml 참고
```

### 2. Alertmanager CR 적용 (Secret 마운트)

```bash
# Prometheus Operator가 Secret을 /etc/alertmanager/secrets/에 자동 마운트
kubectl apply -f infra/monitoring/alertmanager/alertmanager-cr.yaml
```

### 3. Alertmanager 설정 적용

```bash
# 설정 Secret 적용 (api_url_file 사용)
kubectl apply -f infra/monitoring/alertmanager/alertmanager-secret.yaml

# Prometheus Operator가 자동으로 Alertmanager 재시작
# 수동 재시작이 필요한 경우:
kubectl -n monitoring rollout restart statefulset alertmanager-main
```

### 4. 검증

```bash
# 자동 검증 스크립트
bash infra/monitoring/alertmanager/validate-alertmanager.sh monitoring

# 수동 검증
kubectl -n monitoring get secret alertmanager-main alertmanager-secrets
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

- **SETUP_CREDENTIALS.md**: ⭐ **먼저 읽으세요!**
  - Slack Webhook 발급 (단계별 스크린샷)
  - PagerDuty Routing Key 발급 (Events API v2)
  - Secret 생성 및 동작 확인
  - 키 회전 절차
  - 트러블슈팅 (Slack/PagerDuty/라우팅 오류)

- **OPERATIONS_RUNBOOK.md**:
  - 적용 & 검증 치트시트
  - 운영 작업 (키 회전, 라우팅 변경)
  - 장애 대응 체크리스트 (Slack/PagerDuty/라우팅 오류)
  - ArgoCD 통합 및 환경 분리 (Staging/Production)

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
