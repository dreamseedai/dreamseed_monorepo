# Alertmanager 운영 런북 (Operations Runbook)

## 📋 목차

1. [적용 & 검증 치트시트](#적용--검증-치트시트)
2. [운영 작업 (Rotation & Changes)](#운영-작업-rotation--changes)
3. [장애 대응 체크리스트](#장애-대응-체크리스트)
4. [ArgoCD 통합](#argocd-통합)
5. [환경 분리 (Staging/Production)](#환경-분리-stagingproduction)

---

## 적용 & 검증 치트시트

### 1️⃣ Kustomize 빌드 & 적용

```bash
# Kustomize 빌드 확인
kubectl kustomize infra/monitoring/alertmanager/

# 적용 (ArgoCD 미사용 시)
kubectl apply -k infra/monitoring/alertmanager/

# ArgoCD 사용 시 (Git push 후 Sync)
git add infra/monitoring/alertmanager/
git commit -m "chore(monitoring): Update Alertmanager configuration"
git push
argocd app sync monitoring-alertmanager  # App 이름은 환경에 따라 다름
```

### 2️⃣ 리소스 확인

```bash
# Alertmanager CR 확인
kubectl -n monitoring get alertmanager main -o yaml | yq '.spec.secrets'
# 출력 예상:
# - alertmanager-secrets
# - pagerduty-routing-key

# StatefulSet 확인
kubectl -n monitoring get statefulset alertmanager-main -o wide

# Pod 확인
kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o wide
```

### 3️⃣ Secret 마운트 검증

```bash
# Alertmanager Pod 이름 가져오기
ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')

# Secret 마운트 경로 확인
kubectl -n monitoring exec "$ALERTM" -- ls -R /etc/alertmanager/secrets

# 출력 예상:
# /etc/alertmanager/secrets/alertmanager-secrets:
# slack_webhook_url
#
# /etc/alertmanager/secrets/pagerduty-routing-key:
# routing_key

# 파일 내용 확인 (첫 20자만)
kubectl -n monitoring exec "$ALERTM" -- sh -c 'head -c 20 /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url'
```

### 4️⃣ Alertmanager UI 확인

```bash
# 포트포워드 (백그라운드)
kubectl -n monitoring port-forward "$ALERTM" 9093:9093 >/dev/null 2>&1 &

# UI 접속
sleep 2 && open http://127.0.0.1:9093

# 확인 사항:
# - Status → Config: alertmanager.yaml 내용 확인
# - Status → Routes: 3개 route 확인 (pagerduty-seedtest, slack-seedtest, slack-lowprio)
# - Alerts: 현재 발화 중인 알림 확인
```

### 5️⃣ 테스트 알림 전송 (amtool)

```bash
# amtool 설치 (없을 경우)
# macOS: brew install alertmanager
# Linux: wget https://github.com/prometheus/alertmanager/releases/download/v0.27.0/alertmanager-0.27.0.linux-amd64.tar.gz

# Critical → PagerDuty
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestCritical \
  service=seedtest-api \
  severity=critical \
  summary="PagerDuty 라우팅 테스트" \
  description="이 알림은 pagerduty-seedtest receiver로 라우팅되어야 합니다"

# Warning → Slack #seedtest-alerts
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestWarning \
  service=seedtest-api \
  severity=warning \
  summary="Slack 라우팅 테스트" \
  description="이 알림은 slack-seedtest receiver (#seedtest-alerts)로 라우팅되어야 합니다"

# Info → Slack #seedtest-notify
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestInfo \
  namespace=seedtest \
  severity=info \
  summary="Slack 저우선 테스트" \
  description="이 알림은 slack-lowprio receiver (#seedtest-notify)로 라우팅되어야 합니다"
```

### 6️⃣ 수신 확인

**Slack:**
- `#seedtest-alerts`: Warning/Info 알림 수신 (service=seedtest-api)
- `#seedtest-notify`: 저우선 알림 수신 (namespace=seedtest, service 없음)

**PagerDuty:**
- Incidents 페이지에서 Critical 인시던트 생성 확인
- Service: seedtest-api
- Severity: critical

---

## 운영 작업 (Rotation & Changes)

### A) 키 회전 (Key Rotation)

#### Slack Webhook URL 변경

```bash
# 1. Slack에서 새 Webhook URL 생성
# https://api.slack.com/messaging/webhooks
# Workspace → Apps → Incoming Webhooks → Add New Webhook to Workspace

# 2. Secret 갱신
kubectl -n monitoring create secret generic alertmanager-secrets \
  --from-literal=slack_webhook_url='https://hooks.slack.com/services/NEW/WEBHOOK/URL' \
  -o yaml --dry-run=client | kubectl apply -f -

# 3. Alertmanager 재시작 (Secret 볼륨 갱신)
kubectl -n monitoring rollout restart statefulset/alertmanager-main

# 4. 검증
kubectl -n monitoring exec "$ALERTM" -- cat /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
```

#### PagerDuty Routing Key 변경

```bash
# 1. PagerDuty에서 새 Integration Key 생성
# Services → 선택 → Integrations → Add Integration → Events API v2

# 2. Secret 갱신
kubectl -n monitoring create secret generic pagerduty-routing-key \
  --from-literal=routing_key='NEW_PD_ROUTING_KEY' \
  -o yaml --dry-run=client | kubectl apply -f -

# 3. Alertmanager 재시작
kubectl -n monitoring rollout restart statefulset/alertmanager-main

# 4. 검증
kubectl -n monitoring exec "$ALERTM" -- cat /etc/alertmanager/secrets/pagerduty-routing-key/routing_key
```

### B) 라우팅 설정 변경

#### Alertmanager 설정 수정

```bash
# 1. alertmanager-secret.yaml 수정
vim infra/monitoring/alertmanager/alertmanager-secret.yaml

# 2. 적용
kubectl apply -f infra/monitoring/alertmanager/alertmanager-secret.yaml

# 또는 Kustomize 사용
kubectl apply -k infra/monitoring/alertmanager/

# 3. Prometheus Operator가 자동으로 Alertmanager 재로드
# (Config Hash 변경 감지 후 Hot Reload)

# 4. 설정 반영 확인 (UI)
kubectl -n monitoring port-forward "$ALERTM" 9093:9093 &
open http://127.0.0.1:9093/#/status

# Status → Config Hash 변경 확인
```

#### 라우팅 규칙 추가 예시

```yaml
# alertmanager-secret.yaml의 alertmanager.yaml 섹션
route:
  receiver: 'null'
  group_by: ['alertname', 'cluster', 'service']
  routes:
    # 기존 routes...
    
    # 새 route 추가 (예: phase1 환경)
    - receiver: slack-phase1
      matchers:
        - namespace="phase1"
        - severity=~"warning|info"
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      continue: false

receivers:
  # 기존 receivers...
  
  # 새 receiver 추가
  - name: slack-phase1
    slack_configs:
      - channel: '#phase1-alerts'
        send_resolved: true
        api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
```

### C) Inhibit Rules 변경

```yaml
# Critical 알림 발생 시 Warning 억제 (현재 설정)
inhibit_rules:
  - source_matchers:
      - severity="critical"
    target_matchers:
      - severity="warning"
    equal: ['alertname', 'namespace', 'service']

# 추가 예시: Page 알림 발생 시 모든 하위 알림 억제
  - source_matchers:
      - severity="page"
    target_matchers:
      - severity=~"critical|warning|info"
    equal: ['alertname', 'cluster']
```

---

## 장애 대응 체크리스트

### 🚨 Slack 알림 미수신

#### 1단계: Secret 파일 확인

```bash
# api_url_file 경로 확인
ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')
kubectl -n monitoring exec "$ALERTM" -- test -f /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url && echo "✅ 파일 존재" || echo "❌ 파일 없음"

# 파일 내용 확인 (앞 50자만)
kubectl -n monitoring exec "$ALERTM" -- sh -c 'head -c 50 /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url'
# 예상 출력: https://hooks.slack.com/services/T00000000/B00
```

#### 2단계: Slack Webhook 유효성 확인

```bash
# Webhook URL 직접 테스트
WEBHOOK=$(kubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.slack_webhook_url}' | base64 -d)

curl -X POST "$WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d '{"text": "Alertmanager Webhook 테스트"}'

# 성공 시: ok
# 실패 시: invalid_token, channel_not_found 등
```

#### 3단계: Alertmanager 라우팅 로그 확인

```bash
# Alertmanager 로그에서 Slack 관련 에러 검색
kubectl -n monitoring logs "$ALERTM" --tail=100 | grep -i slack

# 일반적인 에러:
# - "Post \"https://hooks.slack.com/...\": dial tcp: i/o timeout" → NetworkPolicy 차단
# - "invalid_token" → Webhook URL 오류
# - "channel_not_found" → 채널 이름 오타 (#seedtest-alerts 확인)
```

#### 4단계: NetworkPolicy 확인

```bash
# Alertmanager에서 Slack으로 egress 허용 확인
kubectl -n monitoring get networkpolicy -o yaml | grep -A 10 "egress"

# 필요 시 egress 추가
cat <<EOF | kubectl apply -f -
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
      ports:
        - protocol: TCP
          port: 443  # Slack HTTPS
        - protocol: TCP
          port: 53   # DNS
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53   # DNS
EOF
```

#### 5단계: Alertmanager UI에서 라우팅 확인

```bash
# UI 접속
kubectl -n monitoring port-forward "$ALERTM" 9093:9093 &
open http://127.0.0.1:9093/#/alerts

# 확인 사항:
# 1. Alert가 "Firing" 상태인지 확인
# 2. Alert 클릭 → Labels에 service=seedtest-api, severity=warning 있는지 확인
# 3. "Receiver" 필드가 "slack-seedtest"인지 확인
# 4. "State" → "Active" 확인
```

---

### 🚨 PagerDuty 인시던트 미생성

#### 1단계: Routing Key 확인

```bash
# routing_key_file 파일 존재 확인
kubectl -n monitoring exec "$ALERTM" -- test -f /etc/alertmanager/secrets/pagerduty-routing-key/routing_key && echo "✅ 파일 존재" || echo "❌ 파일 없음"

# Routing Key 확인
kubectl -n monitoring get secret pagerduty-routing-key -o jsonpath='{.data.routing_key}' | base64 -d
# 예상 길이: 32자 영숫자
```

#### 2단계: PagerDuty Events API 직접 테스트

```bash
# Routing Key 가져오기
PD_KEY=$(kubectl -n monitoring get secret pagerduty-routing-key -o jsonpath='{.data.routing_key}' | base64 -d)

# Events API v2 테스트
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H 'Content-Type: application/json' \
  -d "{
    \"routing_key\": \"$PD_KEY\",
    \"event_action\": \"trigger\",
    \"payload\": {
      \"summary\": \"Alertmanager 테스트\",
      \"severity\": \"critical\",
      \"source\": \"manual-curl-test\"
    }
  }"

# 성공 응답:
# {"status":"success","message":"Event processed","dedup_key":"..."}

# 실패 응답:
# {"status":"invalid","message":"Invalid routing_key","errors":["..."]}
```

#### 3단계: PagerDuty Integration 설정 확인

1. PagerDuty 웹 콘솔 접속
2. Services → seedtest-api (또는 해당 서비스)
3. Integrations 탭
4. Events API v2 Integration 존재 확인
5. Integration Key가 Kubernetes Secret의 routing_key와 일치하는지 확인

#### 4단계: Alertmanager 로그 확인

```bash
kubectl -n monitoring logs "$ALERTM" --tail=100 | grep -i pagerduty

# 일반적인 에러:
# - "Post \"https://events.pagerduty.com/v2/enqueue\": context deadline exceeded" → 네트워크 타임아웃
# - "Invalid routing_key" → Key 오류
# - "403 Forbidden" → Integration 비활성화
```

---

### 🚨 Alert 라우팅 오작동

#### 1단계: PrometheusRule에서 라벨 확인

```bash
# PrometheusRule에서 알림 정의 확인
kubectl -n monitoring get prometheusrule -o yaml | grep -A 30 "HTTPHighErrorRate"

# 출력 예시:
# - alert: HTTPHighErrorRate
#   expr: ...
#   labels:
#     severity: critical      # ← 이 라벨이 Alertmanager route matcher와 일치해야 함
#     service: seedtest-api   # ← 이 라벨이 있어야 함
#   annotations:
#     summary: "..."
```

#### 2단계: Firing Alert 라벨 확인

```bash
# Prometheus UI에서 Alerts 페이지 접속
kubectl -n monitoring port-forward svc/prometheus-k8s 9090:9090 &
open http://127.0.0.1:9090/alerts

# 또는 PromQL로 확인
# ALERTS{alertname="HTTPHighErrorRate"}

# 확인 사항:
# - service 라벨이 "seedtest-api"인지 확인
# - severity 라벨이 "critical" 또는 "warning"인지 확인
# - namespace 라벨 존재 여부 확인
```

#### 3단계: Alertmanager Route Matchers 확인

```bash
# Alertmanager UI → Status → Routes
kubectl -n monitoring port-forward "$ALERTM" 9093:9093 &
open http://127.0.0.1:9093/#/status

# Route 트리 확인:
# route:
#   receiver: 'null'
#   routes:
#     - receiver: pagerduty-seedtest
#       matchers:
#         - service="seedtest-api"
#         - severity="critical"
#     - receiver: slack-seedtest
#       matchers:
#         - service="seedtest-api"
#         - severity=~"warning|info"
#     - receiver: slack-lowprio
#       matchers:
#         - namespace="seedtest"
```

#### 4단계: amtool로 라우팅 테스트

```bash
# Alertmanager route 테스트 (실제 전송 없이 라우팅만 확인)
amtool --alertmanager.url=http://127.0.0.1:9093 config routes test \
  service=seedtest-api \
  severity=critical

# 출력 예상:
# pagerduty-seedtest

amtool --alertmanager.url=http://127.0.0.1:9093 config routes test \
  service=seedtest-api \
  severity=warning

# 출력 예상:
# slack-seedtest
```

---

### 🚨 재배포 후 Secret 마운트 누락

#### 원인: Alertmanager CR의 spec.secrets 누락

```bash
# CR 확인
kubectl -n monitoring get alertmanager main -o yaml | yq '.spec.secrets'

# 출력이 null이거나 빈 배열이면 문제
```

#### 해결: CR Patch 재적용

```bash
# 1. Kustomize로 재적용
kubectl apply -k infra/monitoring/alertmanager/

# 2. 또는 직접 패치
kubectl -n monitoring patch alertmanager main --type merge -p '
spec:
  secrets:
    - alertmanager-secrets
    - pagerduty-routing-key
'

# 3. StatefulSet 롤아웃 (필요 시)
kubectl -n monitoring rollout restart statefulset/alertmanager-main

# 4. 검증
kubectl -n monitoring exec "$ALERTM" -- ls -R /etc/alertmanager/secrets
```

---

## ArgoCD 통합

### Application 정의 예시

```yaml
# infra/argocd/apps/monitoring/alertmanager.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: monitoring-alertmanager
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
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=false  # monitoring namespace는 별도 생성
```

### Secret 관리 (External Secrets Operator 권장)

```yaml
# infra/monitoring/alertmanager/externalsecret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: alertmanager-secrets
  namespace: monitoring
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: alertmanager-secrets
    creationPolicy: Owner
  data:
    - secretKey: slack_webhook_url
      remoteRef:
        key: alertmanager/slack
        property: webhook_url

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: pagerduty-routing-key
  namespace: monitoring
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: pagerduty-routing-key
    creationPolicy: Owner
  data:
    - secretKey: routing_key
      remoteRef:
        key: alertmanager/pagerduty
        property: routing_key
```

---

## 환경 분리 (Staging/Production)

### Overlay 구조

```
infra/monitoring/alertmanager/
├── base/
│   ├── alertmanager-cr.yaml
│   ├── alertmanager-secret.yaml
│   ├── alertmanager-cr-patch.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── alertmanager-config-patch.yaml
│   └── production/
│       ├── kustomization.yaml
│       └── alertmanager-config-patch.yaml
```

### Staging Overlay

```yaml
# overlays/staging/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: monitoring

bases:
  - ../../base

patchesStrategicMerge:
  - alertmanager-config-patch.yaml

# Staging Secret은 ExternalSecret으로 관리
resources:
  - externalsecret-staging.yaml
```

```yaml
# overlays/staging/alertmanager-config-patch.yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-main
  namespace: monitoring
stringData:
  alertmanager.yaml: |
    global:
      slack_api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
    
    route:
      receiver: 'null'
      group_by: ['alertname', 'cluster', 'service']
      routes:
        # Staging: #seedtest-staging-alerts
        - receiver: slack-staging
          matchers:
            - service="seedtest-api"
            - severity=~"critical|warning|info"
          group_wait: 10s
          group_interval: 5m
          repeat_interval: 12h
    
    receivers:
      - name: 'null'
      - name: slack-staging
        slack_configs:
          - channel: '#seedtest-staging-alerts'
            send_resolved: true
            api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
```

### Production Overlay

```yaml
# overlays/production/alertmanager-config-patch.yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-main
  namespace: monitoring
stringData:
  alertmanager.yaml: |
    global:
      slack_api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
    
    route:
      receiver: 'null'
      group_by: ['alertname', 'cluster', 'service']
      routes:
        # Production: Critical → PagerDuty
        - receiver: pagerduty-production
          matchers:
            - service="seedtest-api"
            - severity="critical"
          group_wait: 0s
          group_interval: 5m
          repeat_interval: 4h
          continue: false
        
        # Production: Warning/Info → Slack
        - receiver: slack-production
          matchers:
            - service="seedtest-api"
            - severity=~"warning|info"
          group_wait: 30s
          group_interval: 5m
          repeat_interval: 4h
          continue: false
    
    inhibit_rules:
      - source_matchers:
          - severity="critical"
        target_matchers:
          - severity="warning"
        equal: ['alertname', 'namespace', 'service']
    
    receivers:
      - name: 'null'
      - name: pagerduty-production
        pagerduty_configs:
          - routing_key_file: /etc/alertmanager/secrets/pagerduty-routing-key/routing_key
            send_resolved: true
      - name: slack-production
        slack_configs:
          - channel: '#seedtest-prod-alerts'
            send_resolved: true
            api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
```

---

## 📚 참고 자료

- **Prometheus Operator API**: https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api.md#alertmanagerspec
- **Alertmanager 설정**: https://prometheus.io/docs/alerting/latest/configuration/
- **Slack Incoming Webhooks**: https://api.slack.com/messaging/webhooks
- **PagerDuty Events API v2**: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview

---

**작성일**: 2025-11-08  
**버전**: 1.0  
**관련 파일**:
- `alertmanager-cr.yaml`
- `alertmanager-secret.yaml`
- `alertmanager-cr-patch.yaml`
- `kustomization.yaml`
- `setup-secrets.sh`
- `validate-alertmanager.sh`
