# Alertmanager Slack 전용 빠른 배포 가이드

**총 소요 시간: 10분**

---

## 🎯 Step 1: Slack Webhook 발급 (5분)

### 1-1. Slack App 생성

1. **브라우저에서 열기**
   ```
   https://api.slack.com/apps
   ```

2. **Create New App** 클릭
   - **From scratch** 선택
   - App Name: `Alertmanager` 입력
   - Workspace: 워크스페이스 선택
   - **Create App** 클릭

### 1-2. Incoming Webhooks 활성화

1. **좌측 메뉴**: Features → **Incoming Webhooks**

2. **Activate Incoming Webhooks**: **ON** 전환

3. **Add New Webhook to Workspace** 클릭

4. **채널 선택**: `#seedtest-alerts` (또는 알림받을 채널)

5. **Allow** 클릭

### 1-3. Webhook URL 복사

```
형식: https://hooks.slack.com/services/T.../B.../XXX...
```

**📋 복사한 URL을 메모장에 임시 저장!**

---

## ✅ Step 2: Webhook 테스트 (1분)

터미널에서 실행:

```bash
# Webhook URL 테스트
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🧪 Alertmanager Webhook 테스트"}' \
  'YOUR_SLACK_WEBHOOK_URL_HERE'
```

**성공 응답**: `ok`

**Slack 채널에서 메시지 확인!** ✅

---

## 🔐 Step 3: Kubernetes Secret 생성 (1분)

```bash
# 자동화 스크립트 사용 (권장)
bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \
  'YOUR_SLACK_WEBHOOK_URL'

# 또는 kubectl 직접 사용
kubectl -n monitoring create secret generic alertmanager-secrets \
  --from-literal=slack_webhook_url='YOUR_SLACK_WEBHOOK_URL'
```

**Secret 확인**:
```bash
kubectl -n monitoring get secret alertmanager-secrets
```

---

## 🚀 Step 4: Alertmanager 배포 (1분)

```bash
# Kustomize 배포
kubectl apply -k infra/monitoring/alertmanager/

# Pod 시작 확인
kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager
```

---

## 🎯 Step 5: 자동 검증 (1분)

```bash
# 7단계 자동 검증
bash infra/monitoring/alertmanager/validate-alertmanager.sh monitoring
```

**예상 출력**:
```
✅ Secret 존재: alertmanager-main
✅ Alertmanager Pod 실행 중
✅ /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url
✅ 검증 완료
```

---

## 🧪 Step 6: 종단 테스트 (1분)

### 6-1. Port-forward

```bash
ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n monitoring port-forward "$ALERTM" 9093:9093 &
```

### 6-2. Critical 알림 테스트

```bash
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestCritical \
  service=seedtest-api \
  severity=critical \
  summary="🧪 Critical 테스트"
```

**Slack #seedtest-alerts에서 빨간색 메시지 수신 확인 (즉시)** 🔴

### 6-3. Warning 알림 테스트

```bash
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestWarning \
  service=seedtest-api \
  severity=warning \
  summary="🧪 Warning 테스트"
```

**Slack #seedtest-alerts에서 주황색 메시지 수신 확인 (30초 이내)** 🟠

---

## ✅ 완료 체크리스트

- [ ] Slack Webhook 발급
- [ ] Webhook 단독 테스트 (curl)
- [ ] Kubernetes Secret 생성
- [ ] Alertmanager 배포
- [ ] 자동 검증 통과
- [ ] Critical 알림 Slack 수신
- [ ] Warning 알림 Slack 수신

---

## 📊 알림 라우팅 규칙

| 심각도 | 채널 | 지연 | 색상 |
|--------|------|------|------|
| **Critical** | #seedtest-alerts | 즉시 (0s) | 🔴 빨강 |
| **Warning** | #seedtest-alerts | 30초 | 🟠 주황 |
| **Info** | #seedtest-alerts | 30초 | 🟢 초록 |

**Inhibit Rule**: Critical 활성 시 동일한 alertname의 Warning 억제

---

## 🔧 트러블슈팅

### Slack 메시지 미수신

1. **Webhook URL 확인**
   ```bash
   kubectl -n monitoring get secret alertmanager-secrets \
     -o jsonpath='{.data.slack_webhook_url}' | base64 -d
   ```

2. **Alertmanager 로그**
   ```bash
   kubectl -n monitoring logs "$ALERTM" --tail=50 | grep -i slack
   ```

3. **Private 채널인 경우**
   - Slack 채널 → Integrations → Alertmanager App 초대 확인

### amtool 없을 경우

```bash
# macOS
brew install amtool

# Linux
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xzf alertmanager-0.26.0.linux-amd64.tar.gz
sudo cp alertmanager-0.26.0.linux-amd64/amtool /usr/local/bin/
```

---

## 📚 상세 문서

- **SETUP_CREDENTIALS.md**: Slack Webhook 상세 발급 가이드
- **OPERATIONS_RUNBOOK.md**: 운영 절차 (키 회전, 장애 대응)
- **ALERTMANAGER_ROUTING_GUIDE.md**: 고급 설정 (보안, 멀티 채널)
- **README.md**: 전체 구성 개요

---

## 🎉 성공!

이제 Alertmanager가 모든 알림을 Slack으로 전송합니다.

**Alertmanager UI 접속**:
```
http://127.0.0.1:9093
```

- **Status → Config**: 전체 설정 확인
- **Status → Routes**: 라우팅 트리 시각화
- **Alerts**: 활성 알림 목록

---

**작성일**: 2025-11-08  
**버전**: 2.0 (Slack Only)
