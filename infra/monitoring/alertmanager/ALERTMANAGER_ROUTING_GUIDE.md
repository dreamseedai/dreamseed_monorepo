# Alertmanager 설정 및 알림 라우팅 가이드

## 📋 개요

Prometheus Operator 환경에서 Alertmanager 설정을 GitOps로 관리하는 방법입니다.

**네임스페이스**: `monitoring` (Prometheus Operator 배포 위치)  
**관리 방식**: Kubernetes Secret (`alertmanager-main`)  
**적용 방법**: ArgoCD 자동 동기화 또는 kubectl apply

---

## 🎯 알림 라우팅 전략

### 라벨 기반 라우팅

모든 PrometheusRule 알림은 다음 라벨을 포함해야 합니다:

| 라벨 | 값 | 용도 |
|------|-----|------|
| `service` | `seedtest-api` | 서비스 식별 |
| `severity` | `critical`, `warning`, `info` | 중요도 분류 |
| `namespace` | `seedtest` | 네임스페이스 |

### 라우팅 규칙

```
┌─────────────────────────────────────────────────────────────┐
│ service=seedtest-api + severity=critical                    │
│ → PagerDuty (즉시, group_wait=0s)                          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ service=seedtest-api + severity=warning|info                │
│ → Slack #seedtest-alerts (group_wait=30s)                  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ namespace=seedtest (기타 앱)                                │
│ → Slack #seedtest-notify (저우선)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 보안 설정

### Slack Webhook URL 주입 (권장 방법)

**Option 1: External Secrets Operator (ESO)**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: alertmanager-slack-webhook
  namespace: monitoring
spec:
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: alertmanager-secrets
    template:
      type: Opaque
      data:
        slack_webhook_url: "{{ .slack_webhook_url }}"
  data:
    - secretKey: slack_webhook_url
      remoteRef:
        key: monitoring/alertmanager/slack
        property: webhook_url
```

**Option 2: Sealed Secrets**

```bash
# 시크릿 생성
kubectl create secret generic alertmanager-secrets \
  --from-literal=slack_webhook_url='https://hooks.slack.com/services/XXX/YYY/ZZZ' \
  --namespace=monitoring \
  --dry-run=client -o yaml \
  | kubeseal --format=yaml > sealed-alertmanager-secrets.yaml

# 적용
kubectl apply -f sealed-alertmanager-secrets.yaml
```

**Option 3: SOPS (Simple)**

```bash
# 암호화
sops -e infra/monitoring/alertmanager/alertmanager-secret.yaml \
  > infra/monitoring/alertmanager/alertmanager-secret.enc.yaml

# 복호화 후 적용 (CI/CD)
sops -d infra/monitoring/alertmanager/alertmanager-secret.enc.yaml \
  | kubectl apply -f -
```

### PagerDuty Routing Key 주입

PagerDuty Integration → Events API v2 → Routing Key 복사 후:

```bash
# Secret 수동 생성 (임시)
kubectl -n monitoring create secret generic pagerduty-routing-key \
  --from-literal=routing_key='YOUR_PAGERDUTY_ROUTING_KEY'

# 또는 External Secret으로 관리
```

alertmanager-secret.yaml에서 참조:

```yaml
pagerduty_configs:
  - routing_key_file: /etc/alertmanager/secrets/pagerduty-routing-key/routing_key
```

---

## 📦 배포

### ArgoCD Application (권장)

```yaml
# infra/argocd/apps/monitoring/alertmanager-config.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: alertmanager-config
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/dreamseedai/dreamseed_monorepo.git
    targetRevision: main
    path: infra/monitoring/alertmanager
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    automated:
      prune: false       # Secret 삭제 방지
      selfHeal: true
```

### 수동 적용

```bash
# Secret 적용
kubectl apply -f infra/monitoring/alertmanager/alertmanager-secret.yaml

# Prometheus Operator가 자동으로 Alertmanager 재시작
# 수동 재시작이 필요한 경우:
kubectl -n monitoring rollout restart statefulset alertmanager-main
```

---

## ✅ 검증

### 1. Secret 확인

```bash
# Secret 존재 확인
kubectl -n monitoring get secret alertmanager-main

# 설정 내용 확인 (복호화)
kubectl -n monitoring get secret alertmanager-main \
  -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d | head -50
```

### 2. Alertmanager 상태 확인

```bash
# Pod 상태
kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager

# 포트포워드
ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n monitoring port-forward "$ALERTM" 9093:9093 &

# 브라우저: http://127.0.0.1:9093
# - Status → Config: 설정 확인
# - Status → Routes: 라우팅 트리 확인
```

### 3. 라우팅 테스트

```bash
# amtool 설치 (macOS)
brew install amtool

# 테스트 알림 발송 (Critical → PagerDuty)
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestCritical \
  service=seedtest-api \
  severity=critical \
  summary="PagerDuty 라우팅 테스트" \
  description="Critical 알림이 PagerDuty로 전송되어야 합니다"

# 테스트 알림 발송 (Warning → Slack)
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestWarning \
  service=seedtest-api \
  severity=warning \
  summary="Slack 라우팅 테스트" \
  description="Warning 알림이 #seedtest-alerts로 전송되어야 합니다"

# 활성 알림 확인
amtool --alertmanager.url=http://127.0.0.1:9093 alert query
```

### 4. 수신 확인

**Slack:**
- `#seedtest-alerts`: Warning/Info 알림 수신 확인
- `#seedtest-notify`: 기타 seedtest 네임스페이스 알림

**PagerDuty:**
- Incidents 페이지에서 Critical 알림 인시던트 생성 확인

---

## 🔧 트러블슈팅

### Alertmanager가 설정을 읽지 못함

```bash
# Prometheus Operator 로그 확인
PROM_OP=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=prometheus-operator \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n monitoring logs "$PROM_OP" | grep -i alertmanager

# Alertmanager 로그 확인
kubectl -n monitoring logs "$ALERTM" | grep -i "error\|failed"
```

**원인**: Secret 이름 불일치
**해결**: Prometheus Operator가 기대하는 Secret 이름 확인

```bash
kubectl -n monitoring get prometheus -o yaml \
  | grep -A5 alertmanager
```

### Slack 알림이 전송되지 않음

```bash
# Alertmanager 로그에서 Slack 전송 실패 확인
kubectl -n monitoring logs "$ALERTM" | grep -i slack

# 일반적인 원인:
# 1. Webhook URL 오류 → Secret 재확인
# 2. 채널 이름 오타 → #seedtest-alerts 확인
# 3. 네트워크 정책 차단 → egress 허용 확인
```

**NetworkPolicy 수정 (Alertmanager egress 허용):**

```yaml
# infra/monitoring/alertmanager/networkpolicy.yaml (필요 시)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: alertmanager-egress
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: alertmanager
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector: {}
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443  # Slack/PagerDuty HTTPS
```

### PagerDuty 인시던트 생성 안 됨

```bash
# PagerDuty Events API v2 엔드포인트 확인
kubectl -n monitoring logs "$ALERTM" | grep -i pagerduty

# Routing Key 확인
kubectl -n monitoring get secret alertmanager-main \
  -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d \
  | grep routing_key
```

**원인**: Routing Key 오류  
**해결**: PagerDuty UI → Services → Integration → Events API v2 → Routing Key 재확인

### 알림 중복 수신

**원인**: `continue: true`로 설정된 route가 여러 receiver로 전송  
**해결**: Critical 알림은 `continue: false` 확인

```yaml
routes:
  - matchers:
      - 'service = seedtest-api'
      - 'severity = critical'
    receiver: 'pagerduty-seedtest'
    continue: false  # ← 이후 route 무시
```

### 억제 규칙이 작동하지 않음

**원인**: `equal` 라벨이 일치하지 않음  
**해결**: PrometheusRule의 알림이 `alertname`, `service`, `namespace` 라벨을 포함하는지 확인

```bash
# Prometheus UI에서 활성 알림 라벨 확인
kubectl -n monitoring port-forward svc/prometheus-operated 9090:9090 &
curl -s 'http://127.0.0.1:9090/api/v1/alerts' \
  | jq '.data.alerts[] | {name: .labels.alertname, labels: .labels}'
```

---

## 🎯 운영 모범 사례

### 1. 라벨 표준화

모든 PrometheusRule에서 일관된 라벨 사용:

```yaml
# ops/k8s/governance/base/prometheusrule.yaml
- alert: SeedtestApiHighErrorRate
  expr: job:http_error_rate_5m > 0.05
  labels:
    severity: warning      # ← 필수
    service: seedtest-api  # ← 필수
    component: api         # ← 선택
```

### 2. 알림 피로 방지

```yaml
# 그룹화로 알림 묶음
route:
  group_by: ['alertname', 'service', 'namespace']
  group_wait: 30s        # 첫 알림 전 대기 (같은 그룹 묶기)
  group_interval: 5m     # 같은 그룹 추가 알림 전 대기
  repeat_interval: 2h    # 해결되지 않은 알림 재전송 간격
```

### 3. 유지보수 창 설정

```yaml
time_intervals:
  - name: business-hours
    time_intervals:
      - weekdays: ['monday:friday']
        times:
          - start_time: '09:00'
            end_time: '18:00'
        location: 'Asia/Seoul'

route:
  routes:
    - matchers: ['severity = info']
      mute_time_intervals: ['business-hours']  # 근무 시간에만 알림
      receiver: 'slack-lowprio'
```

### 4. SLO 기반 알림 (향후)

에러 예산 기반 알림 예시:

```promql
# 28일 99.9% 가용성 목표 (에러 예산: 40.32분)
# 6시간 내 에러 예산 25% 소진 시 알림
(
  1 - (
    sum(increase(http_requests_total{status=~"5.."}[6h]))
    /
    sum(increase(http_requests_total[6h]))
  )
) < 0.9975  # 99.9% - (0.1% * 0.25) = 99.75%
```

### 5. 다중 환경 관리

Kustomize overlay로 환경별 Alertmanager 설정:

```
infra/monitoring/alertmanager/
├── base/
│   ├── kustomization.yaml
│   └── alertmanager-secret.yaml (기본 템플릿)
├── overlays/
│   ├── staging/
│   │   └── kustomization.yaml (Slack만 사용)
│   └── production/
│       └── kustomization.yaml (Slack + PagerDuty)
```

---

## 📚 참고 자료

- **Alertmanager 공식 문서**: https://prometheus.io/docs/alerting/latest/configuration/
- **PagerDuty Events API v2**: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview
- **Slack Incoming Webhooks**: https://api.slack.com/messaging/webhooks
- **Prometheus Operator**: https://github.com/prometheus-operator/prometheus-operator

---

**문서 업데이트**: 2025-11-08  
**버전**: v1.0 (초안)
