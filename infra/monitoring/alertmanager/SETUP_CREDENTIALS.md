# Slack & PagerDuty 키 발급 및 설정 가이드

## 📋 목차

1. [Slack Webhook 발급](#1-slack-webhook-발급)
2. [PagerDuty Routing Key 발급](#2-pagerduty-routing-key-발급)
3. [Kubernetes Secret 생성](#3-kubernetes-secret-생성)
4. [동작 확인](#4-동작-확인)
5. [키 회전 (운영 절차)](#5-키-회전-운영-절차)
6. [트러블슈팅](#6-트러블슈팅)

---

## 1. Slack Webhook 발급

### A. Slack 앱 생성 & Webhook 활성화

**필수 조건**: Slack 워크스페이스 관리자 권한

#### Step 1: Slack 앱 생성

1. **Slack API 페이지 접속**
   ```
   https://api.slack.com/apps
   ```

2. **Create New App 클릭**
   - "From scratch" 선택
   - App Name: `Alertmanager` (또는 원하는 이름)
   - Workspace: 알림을 받을 워크스페이스 선택
   - **Create App** 클릭

#### Step 2: Incoming Webhooks 활성화

1. **좌측 메뉴에서 "Features" → "Incoming Webhooks" 선택**

2. **Activate Incoming Webhooks → ON 전환**

3. **Add New Webhook to Workspace 클릭**

4. **채널 선택**
   - `#seedtest-alerts` (Critical/Warning 알림용)
   - **Allow** 클릭

5. **Webhook URL 복사**
   ```
   형식: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   ```

#### Step 3: 추가 채널 Webhook 생성 (선택)

**저우선 알림용 채널**:
- "Add New Webhook to Workspace" 다시 클릭
- `#seedtest-notify` 선택
- 두 번째 Webhook URL 복사

**참고**: 
- Webhook은 채널당 하나씩 발급됩니다
- 동일한 Webhook URL을 여러 채널에 공유할 수 있지만, 채널별 분리 권장
- Private 채널의 경우 Webhook App을 채널에 초대해야 합니다

---

## 2. PagerDuty Routing Key 발급

### A. PagerDuty Service Integration 생성

**필수 조건**: PagerDuty 계정 및 Service 생성 권한

#### Step 1: Service 선택 또는 생성

1. **PagerDuty 로그인**
   ```
   https://yourcompany.pagerduty.com
   ```

2. **Services → Service Directory**

3. **기존 서비스 선택 또는 "New Service" 생성**
   - Service Name: `seedtest-api` (또는 원하는 이름)
   - Escalation Policy: 알림 받을 정책 선택
   - **Create Service** 클릭

#### Step 2: Events API v2 Integration 추가

1. **Service 페이지에서 "Integrations" 탭 클릭**

2. **Add Integration 클릭**

3. **Integration 검색**
   - 검색어: `Events API v2` 입력
   - **Events API v2** 선택 (⚠️ v1이 아닌 v2 확인!)

4. **Add** 클릭

5. **Integration Key (=Routing Key) 복사**
   ```
   형식: R00000000000000000000000000000000 (32자 영숫자)
   ```

**중요 체크사항**:
- ✅ Integration Name이 "Events API v2"인지 확인
- ✅ Integration Key 길이가 32자인지 확인
- ❌ Generic API v1 키는 사용 불가

---

## 3. Kubernetes Secret 생성

### Option A: 자동화 스크립트 사용 (권장)

```bash
# 발급받은 키를 사용하여 Secret 생성
bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \
  'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX' \
  'R00000000000000000000000000000000'

# 출력 예시:
# ✅ Secret 생성: alertmanager-secrets
#    키: slack_webhook_url
#    마운트 경로: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
# ✅ Secret 생성: pagerduty-routing-key
#    키: routing_key
#    마운트 경로: /etc/alertmanager/secrets/pagerduty-routing-key/routing_key
```

### Option B: kubectl 직접 사용

#### Slack Webhook Secret 생성

```bash
kubectl -n monitoring create secret generic alertmanager-secrets \
  --from-literal=slack_webhook_url='https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX'

# 확인
kubectl -n monitoring get secret alertmanager-secrets -o yaml
```

#### PagerDuty Routing Key Secret 생성

```bash
kubectl -n monitoring create secret generic pagerduty-routing-key \
  --from-literal=routing_key='R00000000000000000000000000000000'

# 확인
kubectl -n monitoring get secret pagerduty-routing-key -o yaml
```

### Option C: External Secrets Operator (프로덕션 권장)

```yaml
# external-secret-slack.yaml
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
```

```yaml
# external-secret-pagerduty.yaml
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

## 4. 동작 확인

### A. Slack Webhook 단독 테스트 (직접 호출)

```bash
# Webhook URL 테스트
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"[TEST] Alertmanager Slack Webhook 연결 확인"}' \
  'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX'

# 성공 시 응답: ok
# 실패 시: invalid_token, channel_not_found 등
```

**확인 사항**:
- ✅ 지정한 Slack 채널에 메시지 수신 확인
- ✅ 응답 코드 200 확인

### B. PagerDuty Events API v2 단독 테스트

```bash
# PagerDuty Events API 테스트
curl -X POST 'https://events.pagerduty.com/v2/enqueue' \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key": "R00000000000000000000000000000000",
    "event_action": "trigger",
    "payload": {
      "summary": "TEST – Alertmanager PagerDuty 연결 확인",
      "severity": "critical",
      "source": "seedtest-api",
      "component": "manual-test",
      "group": "monitoring",
      "class": "test"
    }
  }'

# 성공 응답:
# {"status":"success","message":"Event processed","dedup_key":"..."}

# 실패 응답:
# {"status":"invalid","message":"Invalid routing_key","errors":["..."]}
```

**확인 사항**:
- ✅ 응답 status가 "success"인지 확인
- ✅ PagerDuty Service → Incidents 페이지에서 새 인시던트 생성 확인
- ✅ dedup_key 값 받음 확인

### C. Alertmanager를 통한 종단 테스트 (amtool)

#### 1️⃣ Alertmanager 포트포워드

```bash
# Alertmanager Pod 이름 가져오기
ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')

# 포트포워드 (백그라운드)
kubectl -n monitoring port-forward "$ALERTM" 9093:9093 >/dev/null 2>&1 &

# UI 접속 확인
open http://127.0.0.1:9093
```

#### 2️⃣ Critical → PagerDuty 라우팅 테스트

```bash
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=SeedtestRouteTest \
  service=seedtest-api \
  severity=critical \
  summary="[TEST] PagerDuty 라우팅 확인" \
  description="이 알림은 pagerduty-seedtest receiver로 라우팅되어야 합니다"

# 확인:
# 1. Alertmanager UI → Alerts에서 firing 상태 확인
# 2. PagerDuty Incidents에서 새 인시던트 생성 확인 (30초 이내)
```

#### 3️⃣ Warning → Slack 라우팅 테스트

```bash
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=SeedtestRouteTest \
  service=seedtest-api \
  severity=warning \
  summary="[TEST] Slack 라우팅 확인" \
  description="이 알림은 slack-seedtest receiver (#seedtest-alerts)로 라우팅되어야 합니다"

# 확인:
# 1. Alertmanager UI → Alerts에서 firing 상태 확인
# 2. Slack #seedtest-alerts 채널에서 메시지 수신 확인 (30초 이내)
```

#### 4️⃣ Info → Slack 저우선 라우팅 테스트

```bash
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=SeedtestRouteTest \
  namespace=seedtest \
  severity=info \
  summary="[TEST] Slack 저우선 라우팅 확인" \
  description="이 알림은 slack-lowprio receiver (#seedtest-notify)로 라우팅되어야 합니다"

# 확인:
# 1. Alertmanager UI → Alerts에서 firing 상태 확인
# 2. Slack #seedtest-notify 채널에서 메시지 수신 확인 (30초 이내)
```

#### 5️⃣ Alert 삭제 (테스트 종료)

```bash
# 모든 테스트 알림 삭제
amtool --alertmanager.url=http://127.0.0.1:9093 silence add \
  alertname=SeedtestRouteTest \
  --duration=1m \
  --author="test" \
  --comment="테스트 종료"

# 또는 Alertmanager UI에서 수동 삭제
# http://127.0.0.1:9093/#/alerts → 각 Alert 클릭 → Silence
```

---

## 5. 키 회전 (운영 절차)

### A. Slack Webhook 회전

#### Step 1: 새 Webhook 발급

1. Slack API 페이지 접속
   ```
   https://api.slack.com/apps → 기존 Alertmanager App 선택
   ```

2. Features → Incoming Webhooks

3. **Revoke** (기존 Webhook 무효화) 또는 **Add New Webhook to Workspace**

4. 새 Webhook URL 복사

#### Step 2: Kubernetes Secret 갱신

```bash
# Secret 갱신 (기존 Secret 덮어쓰기)
kubectl -n monitoring create secret generic alertmanager-secrets \
  --from-literal=slack_webhook_url='https://hooks.slack.com/services/NEW/WEBHOOK/URL' \
  -o yaml --dry-run=client | kubectl apply -f -

# 확인
kubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.slack_webhook_url}' | base64 -d
```

#### Step 3: Alertmanager 재시작

```bash
# StatefulSet 롤아웃 재시작
kubectl -n monitoring rollout restart statefulset/alertmanager-main

# Pod 재시작 확인
kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -w
```

#### Step 4: 검증

```bash
# Secret 마운트 확인
ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')
kubectl -n monitoring exec "$ALERTM" -- cat /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url

# 테스트 알림 전송
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=WebhookRotationTest service=seedtest-api severity=warning \
  summary="Webhook 회전 테스트"

# Slack 채널에서 메시지 수신 확인
```

### B. PagerDuty Routing Key 회전

#### Step 1: 새 Routing Key 발급

1. PagerDuty → Services → seedtest-api

2. Integrations 탭

3. 기존 Events API v2 Integration → **Edit**

4. **Regenerate Key** 클릭 (또는 새 Integration 추가)

5. 새 Routing Key 복사

#### Step 2: Kubernetes Secret 갱신

```bash
# Secret 갱신
kubectl -n monitoring create secret generic pagerduty-routing-key \
  --from-literal=routing_key='NEW_PD_ROUTING_KEY_XXXXXXXXXXXX' \
  -o yaml --dry-run=client | kubectl apply -f -

# 확인
kubectl -n monitoring get secret pagerduty-routing-key -o jsonpath='{.data.routing_key}' | base64 -d
```

#### Step 3: Alertmanager 재시작

```bash
kubectl -n monitoring rollout restart statefulset/alertmanager-main
```

#### Step 4: 검증

```bash
# Secret 마운트 확인
kubectl -n monitoring exec "$ALERTM" -- cat /etc/alertmanager/secrets/pagerduty-routing-key/routing_key

# 테스트 알림 전송
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=PDKeyRotationTest service=seedtest-api severity=critical \
  summary="PD 키 회전 테스트"

# PagerDuty Incidents에서 수신 확인
```

---

## 6. 트러블슈팅

### 🚨 Slack 메시지 미수신

#### 체크리스트

**1. Webhook URL 유효성**
```bash
# Webhook 직접 테스트
WEBHOOK=$(kubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.slack_webhook_url}' | base64 -d)

curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Direct test"}' \
  "$WEBHOOK"

# 응답 확인:
# - "ok" → Webhook 정상
# - "invalid_token" → Webhook URL 오류
# - "channel_not_found" → 채널 삭제됨 또는 App 초대 안됨
```

**2. 채널 권한**
- Private 채널의 경우: Alertmanager App이 채널에 초대되어 있는지 확인
- Slack에서 채널 → Integrations → Alertmanager App 확인

**3. Alertmanager 라우팅**
```bash
# Alertmanager 로그에서 Slack 전송 확인
kubectl -n monitoring logs "$ALERTM" --tail=100 | grep -i slack

# 에러 예시:
# - "context deadline exceeded" → 네트워크 타임아웃
# - "invalid_token" → Webhook URL 오류
# - "channel_not_found" → 채널 문제
```

**4. NetworkPolicy**
```bash
# Alertmanager에서 Slack(HTTPS 443) egress 허용 확인
kubectl -n monitoring get networkpolicy -o yaml | grep -A 20 egress

# 필요 시 egress 추가 (OPERATIONS_RUNBOOK.md 참고)
```

**5. Alert 라벨 확인**
```bash
# Alertmanager UI에서 Alert 클릭 → Labels 확인
# service=seedtest-api, severity=warning 있는지 확인
# Receiver가 "slack-seedtest"인지 확인
```

---

### 🚨 PagerDuty Incident 미생성

#### 체크리스트

**1. Routing Key 유효성**
```bash
# Routing Key 직접 테스트
PD_KEY=$(kubectl -n monitoring get secret pagerduty-routing-key -o jsonpath='{.data.routing_key}' | base64 -d)

curl -X POST 'https://events.pagerduty.com/v2/enqueue' \
  -H 'Content-Type: application/json' \
  -d "{
    \"routing_key\": \"$PD_KEY\",
    \"event_action\": \"trigger\",
    \"payload\": {
      \"summary\": \"Direct test\",
      \"severity\": \"critical\",
      \"source\": \"manual\"
    }
  }"

# 응답 확인:
# - {"status":"success",...} → Key 정상
# - {"status":"invalid","message":"Invalid routing_key"} → Key 오류
```

**2. Integration 타입 확인**
- PagerDuty → Services → seedtest-api → Integrations
- Integration Name이 **"Events API v2"**인지 확인 (v1 아님!)
- Integration Key 길이가 32자인지 확인

**3. Service 설정**
- Service 상태가 **Active**인지 확인
- Escalation Policy에 On-call Engineer가 있는지 확인
- Integration이 **Enabled** 상태인지 확인

**4. Alertmanager 라우팅**
```bash
# Alertmanager 로그에서 PagerDuty 전송 확인
kubectl -n monitoring logs "$ALERTM" --tail=100 | grep -i pagerduty

# 에러 예시:
# - "403 Forbidden" → Integration 비활성화 또는 권한 문제
# - "Invalid routing_key" → Key 오류
# - "context deadline exceeded" → 네트워크 타임아웃
```

**5. Alert 라벨 확인**
```bash
# Alertmanager UI에서 Alert 클릭 → Labels 확인
# service=seedtest-api, severity=critical 있는지 확인
# Receiver가 "pagerduty-seedtest"인지 확인
```

---

### 🚨 Alert 라우팅 오작동

#### 문제: Alert가 잘못된 receiver로 라우팅됨

**1. PrometheusRule 라벨 확인**
```bash
# PrometheusRule에서 알림 정의 확인
kubectl -n monitoring get prometheusrule -o yaml | grep -A 10 "HTTPHighErrorRate"

# labels:
#   severity: critical      ← 이 라벨이 route matcher와 일치해야 함
#   service: seedtest-api   ← 이 라벨 필수
```

**2. Firing Alert 라벨 확인**
```bash
# Prometheus UI → Alerts
kubectl -n monitoring port-forward svc/prometheus-k8s 9090:9090 &
open http://127.0.0.1:9090/alerts

# ALERTS{alertname="HTTPHighErrorRate"} 쿼리로 라벨 확인
```

**3. Route Matchers 확인**
```bash
# Alertmanager UI → Status → Routes
open http://127.0.0.1:9093/#/status

# Route 트리에서 matchers 확인:
# - service="seedtest-api"
# - severity="critical"
# - severity=~"warning|info"
```

**4. amtool로 라우팅 시뮬레이션**
```bash
# 실제 전송 없이 라우팅만 테스트
amtool --alertmanager.url=http://127.0.0.1:9093 config routes test \
  service=seedtest-api \
  severity=critical

# 출력 예상: pagerduty-seedtest

amtool --alertmanager.url=http://127.0.0.1:9093 config routes test \
  service=seedtest-api \
  severity=warning

# 출력 예상: slack-seedtest
```

---

### 🚨 Secret 마운트 누락

#### 문제: /etc/alertmanager/secrets/ 디렉토리가 비어있음

**1. Alertmanager CR 확인**
```bash
kubectl -n monitoring get alertmanager main -o yaml | yq '.spec.secrets'

# 출력 예상:
# - alertmanager-secrets
# - pagerduty-routing-key

# 출력이 null이거나 빈 배열이면 문제!
```

**2. Kustomize 패치 재적용**
```bash
# alertmanager-cr-patch.yaml 포함 확인
kubectl kustomize infra/monitoring/alertmanager/ | grep -A 5 "spec.secrets"

# 전체 재적용
kubectl apply -k infra/monitoring/alertmanager/
```

**3. Pod 재시작**
```bash
kubectl -n monitoring rollout restart statefulset/alertmanager-main
```

**4. 마운트 검증**
```bash
ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')
kubectl -n monitoring exec "$ALERTM" -- ls -R /etc/alertmanager/secrets/

# 출력 예상:
# /etc/alertmanager/secrets/alertmanager-secrets:
# slack_webhook_url
#
# /etc/alertmanager/secrets/pagerduty-routing-key:
# routing_key
```

---

## 📅 운영 체크리스트

### 정기 점검 (월 1회)

- [ ] Slack Webhook 유효성 테스트 (curl)
- [ ] PagerDuty Routing Key 유효성 테스트 (curl)
- [ ] Alertmanager 테스트 알림 전송 (amtool)
- [ ] PagerDuty Incidents 수신 확인
- [ ] Slack 채널 메시지 수신 확인
- [ ] Alertmanager UI에서 라우팅 확인

### 키 회전 (분기 1회 권장)

- [ ] 새 Slack Webhook 발급
- [ ] 새 PagerDuty Routing Key 발급
- [ ] Kubernetes Secret 갱신
- [ ] Alertmanager 재시작
- [ ] 테스트 알림으로 검증
- [ ] 이전 키 무효화 (Slack/PD UI)

### 보안 점검

- [ ] 키가 Git에 커밋되지 않았는지 확인 (`git log -S "hooks.slack.com"`)
- [ ] Secret에 적절한 RBAC 적용 확인
- [ ] External Secrets Operator 사용 여부 검토
- [ ] Audit Log에서 Secret 접근 기록 확인

---

## 📚 관련 문서

- **OPERATIONS_RUNBOOK.md**: 운영 절차 (키 회전, 장애 대응, ArgoCD 통합)
- **ALERTMANAGER_ROUTING_GUIDE.md**: 라우팅 설정 (보안, 트러블슈팅)
- **validate-alertmanager.sh**: 자동 검증 스크립트
- **setup-secrets.sh**: Secret 생성 자동화 스크립트

---

**작성일**: 2025-11-08  
**버전**: 1.0  
**최종 업데이트**: 2025-11-08
