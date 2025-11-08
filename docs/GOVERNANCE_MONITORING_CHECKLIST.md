# ✅ Governance 모니터링 배포 체크리스트

## 📋 사전 준비

- [ ] Slack Workspace 접근 권한 확보
- [ ] PagerDuty 계정 및 Service 생성 권한 확보
- [ ] Kubernetes 클러스터 접근 권한 확인
- [ ] `kubectl` CLI 설치 및 설정 완료
- [ ] 터미널 2개 준비 (하나는 명령어 실행, 하나는 로그 확인)

---

## 🔑 Step 1: Credentials 발급 (10분)

### 1.1 Slack Webhook 발급 (5분)

#### 실행 단계
1. https://api.slack.com/apps 접속
2. **Create New App** 클릭
3. **From scratch** 선택
4. App Name: `SeedTest Alerts` 입력
5. Workspace 선택 → **Create App**
6. 좌측 메뉴 **Incoming Webhooks** 클릭
7. **Activate Incoming Webhooks** 토글 ON
8. **Add New Webhook to Workspace** 클릭
9. 채널: `#seedtest-alerts` 선택 (없으면 먼저 생성)
10. **Allow** 클릭
11. Webhook URL 복사

#### 체크포인트
- [ ] Slack App 생성 완료
- [ ] Incoming Webhooks 활성화
- [ ] Webhook URL 복사 완료
- [ ] URL 형식 확인: `https://hooks.slack.com/services/T.../B.../XXX...`

#### Webhook URL 저장
```bash
# 환경 변수로 저장 (터미널 세션 동안 유지)
export SLACK_WEBHOOK='https://hooks.slack.com/services/실제값으로교체'

# 확인
echo $SLACK_WEBHOOK
```

---

### 1.2 PagerDuty Routing Key 발급 (5분)

#### 실행 단계
1. PagerDuty 로그인
2. **Services** → **Service Directory** 이동
3. **New Service** 클릭
4. Service Name: `seedtest-api` 입력
5. Escalation Policy 선택 (기존 또는 신규 생성)
6. **Create Service** 클릭
7. 생성된 Service 클릭
8. **Integrations** 탭 선택
9. **Add Integration** 클릭
10. Integration Type: **Events API v2** 선택
11. **Add** 클릭
12. Integration Key (Routing Key) 복사

#### 체크포인트
- [ ] PagerDuty Service 생성 완료
- [ ] Events API v2 Integration 추가
- [ ] Routing Key 복사 완료
- [ ] Key 형식 확인: 32자 영숫자 (예: `R0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5`)

#### Routing Key 저장
```bash
# 환경 변수로 저장
export PAGERDUTY_KEY='R0실제키32자로교체'

# 확인
echo $PAGERDUTY_KEY
```

---

## 🚀 Step 2: Kubernetes Secret 생성 (2분)

### 2.1 Secret 생성 스크립트 실행

```bash
cd /home/won/projects/dreamseed_monorepo

# Secret 생성
bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \
  "$SLACK_WEBHOOK" \
  "$PAGERDUTY_KEY"
```

#### 예상 출력
```
✅ Secret 'alertmanager-secrets' created in namespace 'monitoring'
```

#### 체크포인트
- [ ] 스크립트 실행 성공
- [ ] Secret 생성 확인 메시지 출력
- [ ] 에러 없음

### 2.2 Secret 검증

```bash
# Secret 존재 확인
kubectl -n monitoring get secret alertmanager-secrets

# Secret 내용 확인 (base64 인코딩됨)
kubectl -n monitoring get secret alertmanager-secrets -o yaml
```

#### 예상 출력
```
NAME                    TYPE     DATA   AGE
alertmanager-secrets    Opaque   2      5s
```

#### 체크포인트
- [ ] Secret 존재 확인
- [ ] DATA 필드 = 2 (slack_webhook, pagerduty_routing_key)

---

## ☸️ Step 3: Kubernetes 리소스 배포 (3분)

### 3.1 Alertmanager 설정 배포

```bash
# Kustomize로 Alertmanager 설정 적용
kubectl apply -k infra/monitoring/alertmanager/
```

#### 예상 출력
```
secret/alertmanager-secrets configured
alertmanager.monitoring.coreos.com/main configured
```

#### 체크포인트
- [ ] Secret configured
- [ ] Alertmanager CR configured
- [ ] 에러 없음

### 3.2 PrometheusRule 배포

```bash
# Prometheus 알림 규칙 배포
kubectl apply -f infra/argocd/apps/monitoring/prometheus-rule-seedtest.yaml
```

#### 예상 출력
```
prometheusrule.monitoring.coreos.com/seedtest-api-alerts created
```

#### 체크포인트
- [ ] PrometheusRule 생성 완료
- [ ] 에러 없음

### 3.3 Grafana Dashboard 배포

```bash
# Grafana Dashboard ConfigMap 배포
kubectl apply -f infra/argocd/apps/monitoring/grafana-dashboard-seedtest.yaml
```

#### 예상 출력
```
configmap/grafana-dashboard-seedtest created
```

#### 체크포인트
- [ ] ConfigMap 생성 완료
- [ ] 에러 없음

### 3.4 Governance 설정 배포 (선택사항)

```bash
# Governance 설정이 있는 경우
kubectl apply -k ops/k8s/governance/overlays/staging
```

#### 체크포인트
- [ ] Governance 리소스 배포 완료 (해당하는 경우)

---

## ✅ Step 4: 검증 (2분)

### 4.1 Alertmanager 검증

```bash
# Alertmanager 검증 스크립트 실행
bash infra/monitoring/alertmanager/validate-alertmanager.sh monitoring
```

#### 예상 출력
```
✅ Secret exists
✅ Alertmanager CR exists
✅ Alertmanager Pod is Running
✅ Slack webhook configured
✅ PagerDuty routing key configured
```

#### 체크포인트
- [ ] 모든 항목 ✅ 표시
- [ ] Pod 상태 Running
- [ ] Webhook 및 Routing Key 설정 확인

### 4.2 Prometheus 타겟 확인

```bash
# Prometheus UI 접속
kubectl -n monitoring port-forward svc/prometheus-k8s 9090:9090 &

# 브라우저에서 확인
# http://localhost:9090/targets
```

#### 체크포인트
- [ ] Prometheus UI 접속 성공
- [ ] `seedtest-api` 타겟 존재
- [ ] 타겟 상태 UP (또는 배포 후 UP으로 변경 예정)

### 4.3 PrometheusRule 확인

```bash
# Prometheus Alerts 페이지 확인
# http://localhost:9090/alerts
```

#### 체크포인트
- [ ] `seedtest-api-availability` 그룹 존재
- [ ] `seedtest-api-governance` 그룹 존재
- [ ] `seedtest-api-irt-drift` 그룹 존재
- [ ] `seedtest-api-database` 그룹 존재
- [ ] `seedtest-api-resources` 그룹 존재
- [ ] 총 15개 알림 규칙 확인

### 4.4 Grafana Dashboard 확인

```bash
# Grafana UI 접속
kubectl -n monitoring port-forward svc/grafana 3000:3000 &

# 브라우저에서 확인
# http://localhost:3000
# 검색: "SeedTest API Dashboard"
```

#### 체크포인트
- [ ] Grafana UI 접속 성공
- [ ] "SeedTest API Dashboard" 검색 결과 존재
- [ ] Dashboard 열기 성공
- [ ] 8개 패널 확인

### 4.5 Governance 모니터링 검증 (선택사항)

```bash
# Governance 검증 스크립트 (있는 경우)
bash ops/k8s/governance/monitoring-validation.sh seedtest
```

#### 체크포인트
- [ ] Governance 검증 완료 (해당하는 경우)

---

## 🧪 Step 5: 테스트 알림 (3분)

### 5.1 Slack 알림 테스트

```bash
# Slack Webhook 직접 테스트
curl -X POST "$SLACK_WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🧪 SeedTest API 모니터링 테스트",
    "attachments": [{
      "color": "good",
      "title": "테스트 알림",
      "fields": [{
        "title": "Status",
        "value": "Alertmanager 설정 완료",
        "short": true
      }, {
        "title": "Timestamp",
        "value": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
        "short": true
      }]
    }]
  }'
```

#### 예상 결과
- Slack `#seedtest-alerts` 채널에 테스트 메시지 수신

#### 체크포인트
- [ ] Slack 채널에 메시지 도착
- [ ] 메시지 형식 정상
- [ ] 타임스탬프 정확

### 5.2 PagerDuty 알림 테스트

```bash
# PagerDuty Events API 직접 테스트
curl -X POST 'https://events.pagerduty.com/v2/enqueue' \
  -H 'Content-Type: application/json' \
  -d "{
    \"routing_key\": \"$PAGERDUTY_KEY\",
    \"event_action\": \"trigger\",
    \"payload\": {
      \"summary\": \"🧪 SeedTest API 모니터링 테스트\",
      \"severity\": \"info\",
      \"source\": \"seedtest-api\",
      \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
      \"custom_details\": {
        \"message\": \"Alertmanager 설정 완료\",
        \"environment\": \"staging\"
      }
    }
  }"
```

#### 예상 결과
- PagerDuty에 Incident 생성
- Status: Triggered
- Severity: Info

#### 체크포인트
- [ ] PagerDuty Incident 생성 확인
- [ ] Incident 상세 정보 정확
- [ ] Escalation Policy 적용 확인

### 5.3 Alertmanager 종단 테스트

```bash
# Alertmanager UI 접속
kubectl -n monitoring port-forward svc/alertmanager-main 9093:9093 &

# amtool 설치 확인 (없으면 설치)
# macOS: brew install alertmanager
# Ubuntu: apt-get install prometheus-alertmanager

# 테스트 알림 전송
amtool alert add test_alert \
  alertname=TestAlert \
  severity=warning \
  summary="Alertmanager 종단 테스트" \
  description="모든 알림 채널 테스트" \
  --alertmanager.url=http://localhost:9093
```

#### 예상 결과
- Alertmanager UI에 알림 표시
- Slack에 알림 수신
- PagerDuty에 Incident 생성

#### 체크포인트
- [ ] Alertmanager UI에서 알림 확인
- [ ] Slack 알림 수신
- [ ] PagerDuty Incident 생성
- [ ] 모든 채널 정상 작동

### 5.4 알림 해제 테스트

```bash
# PagerDuty Incident 해제
curl -X POST 'https://events.pagerduty.com/v2/enqueue' \
  -H 'Content-Type: application/json' \
  -d "{
    \"routing_key\": \"$PAGERDUTY_KEY\",
    \"event_action\": \"resolve\",
    \"payload\": {
      \"summary\": \"🧪 SeedTest API 모니터링 테스트\",
      \"severity\": \"info\",
      \"source\": \"seedtest-api\"
    }
  }"
```

#### 체크포인트
- [ ] PagerDuty Incident 상태 Resolved로 변경

---

## 📊 Step 6: 메트릭 수집 확인 (선택사항)

### 6.1 SeedTest API Pod 확인

```bash
# Pod 상태 확인
kubectl -n seedtest get pods -l app=seedtest-api

# Pod 로그 확인
kubectl -n seedtest logs -l app=seedtest-api --tail=50
```

#### 체크포인트
- [ ] Pod 상태 Running
- [ ] 로그에 에러 없음

### 6.2 메트릭 엔드포인트 확인

```bash
# Pod에서 메트릭 확인
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest exec "$POD" -- curl -s http://localhost:8000/metrics | head -50
```

#### 체크포인트
- [ ] `/metrics` 엔드포인트 응답
- [ ] Prometheus 형식 메트릭 출력
- [ ] 메트릭 타입 확인 (`# TYPE`)

### 6.3 Prometheus 메트릭 쿼리

```bash
# Prometheus UI에서 쿼리 실행
# http://localhost:9090/graph

# 쿼리 예제:
# up{job="seedtest-api"}
# http_requests_total{job="seedtest-api"}
# policy_evaluations_total{job="seedtest-api"}
```

#### 체크포인트
- [ ] 메트릭 쿼리 결과 반환
- [ ] 데이터 수집 확인

---

## 🎯 배포 완료 확인

### 최종 체크리스트

#### Credentials
- [ ] Slack Webhook URL 발급 완료
- [ ] PagerDuty Routing Key 발급 완료
- [ ] 환경 변수 설정 완료

#### Kubernetes 리소스
- [ ] Alertmanager Secret 생성
- [ ] Alertmanager CR 배포
- [ ] PrometheusRule 배포
- [ ] Grafana Dashboard 배포

#### 검증
- [ ] Alertmanager 검증 스크립트 통과
- [ ] Prometheus 타겟 UP
- [ ] PrometheusRule 15개 확인
- [ ] Grafana Dashboard 8개 패널 확인

#### 테스트
- [ ] Slack 알림 테스트 성공
- [ ] PagerDuty 알림 테스트 성공
- [ ] Alertmanager 종단 테스트 성공
- [ ] 알림 해제 테스트 성공

#### 메트릭 (선택사항)
- [ ] SeedTest API Pod Running
- [ ] `/metrics` 엔드포인트 응답
- [ ] Prometheus 메트릭 수집 확인

---

## 📝 배포 후 작업

### 1. 문서 업데이트
- [ ] 실제 Webhook URL을 안전한 곳에 저장 (1Password, Vault 등)
- [ ] 실제 Routing Key를 안전한 곳에 저장
- [ ] 배포 날짜 및 담당자 기록

### 2. 팀 공유
- [ ] Slack `#seedtest-alerts` 채널에 팀원 초대
- [ ] PagerDuty Escalation Policy에 팀원 추가
- [ ] 모니터링 대시보드 URL 공유

### 3. 알림 임계값 튜닝 (1주일 후)
- [ ] 실제 트래픽 패턴 분석
- [ ] False Positive 알림 확인
- [ ] 임계값 조정 (필요시)

### 4. 정기 점검 설정
- [ ] 주간 대시보드 리뷰 일정 설정
- [ ] 월간 알림 규칙 검토 일정 설정
- [ ] 분기별 Runbook 업데이트 일정 설정

---

## 🚨 트러블슈팅

### 문제: Secret 생성 실패
```bash
# 네임스페이스 확인
kubectl get namespace monitoring

# 네임스페이스 없으면 생성
kubectl create namespace monitoring
```

### 문제: Alertmanager Pod 시작 안됨
```bash
# Pod 상태 확인
kubectl -n monitoring get pods -l app.kubernetes.io/name=alertmanager

# Pod 로그 확인
kubectl -n monitoring logs -l app.kubernetes.io/name=alertmanager --tail=100

# Pod 재시작
kubectl -n monitoring delete pod -l app.kubernetes.io/name=alertmanager
```

### 문제: Slack 알림 미수신
```bash
# Webhook URL 재확인
echo $SLACK_WEBHOOK

# Secret 확인
kubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.slack_webhook}' | base64 -d

# Alertmanager 로그 확인
kubectl -n monitoring logs -l app.kubernetes.io/name=alertmanager | grep -i slack
```

### 문제: PagerDuty Incident 미생성
```bash
# Routing Key 재확인
echo $PAGERDUTY_KEY

# Secret 확인
kubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.pagerduty_routing_key}' | base64 -d

# Alertmanager 로그 확인
kubectl -n monitoring logs -l app.kubernetes.io/name=alertmanager | grep -i pagerduty
```

---

## 📚 참고 문서

- **빠른 시작**: `/docs/GOVERNANCE_MONITORING_QUICKSTART.md`
- **전체 가이드**: `/docs/GOVERNANCE_MONITORING_DEPLOYMENT.md`
- **메트릭 검증**: `/docs/MONITORING_VERIFICATION.md`
- **Alertmanager 설정**: `/infra/monitoring/alertmanager/SETUP_CREDENTIALS.md`
- **운영 Runbook**: `/infra/monitoring/alertmanager/OPERATIONS_RUNBOOK.md`

---

## ✅ 배포 완료!

모든 체크리스트 항목이 완료되면 Governance 모니터링 시스템이 정상 작동합니다.

**다음 단계**: 실제 알림 발생 시나리오 테스트 및 임계값 튜닝
