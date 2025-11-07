# R Analytics 통합 가이드

**최종 업데이트**: 2025-11-02  
**상태**: Production Ready

---

## 🎯 개요

r-analytics는 통합 분석 API 서비스(Plumber, 포트 8010)로, 다음 기능을 제공합니다:

- **Topic Theta Scoring**: IRT 기반 주제별 능력 추정
- **Improvement Index**: 성장 추적 (I_t 메트릭)
- **Goal Attainment**: 목표 달성 확률 예측
- **Topic Recommendations**: 다음 학습 주제 추천
- **Churn Risk**: 14일 이탈 위험 평가
- **Report Generation**: 종합 분석 리포트 생성

---

## 🏗️ 아키텍처

```
Frontend/Client
    ↓ (HTTP + JWT)
FastAPI (/analytics/* endpoints)
    ↓ (analytics_proxy router)
RAnalyticsClient (Python)
    ↓ (HTTP + X-Internal-Token)
r-analytics (Plumber on K8s, port 8010)
    ↓ (Cloud SQL Proxy)
PostgreSQL
```

---

## 📦 구현 완료 컴포넌트

### 1. Python 클라이언트

**파일**: `apps/seedtest_api/app/clients/r_analytics.py`

```python
from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient

# 환경 변수에서 자동 로드
client = RAnalyticsClient()

# 또는 명시적 설정
client = RAnalyticsClient(
    base_url="http://r-analytics.seedtest.svc.cluster.local:80",
    timeout=60.0,
    token="your-token",
    auth_header="X-Internal-Token"
)

# 사용 예시
health = client.health()
theta = client.score_topic_theta("student-123", ["topic-A", "topic-B"])
risk = client.risk_churn("student-123")
```

**환경 변수**:
- `R_ANALYTICS_BASE_URL`: 서비스 URL (기본: 필수)
- `R_ANALYTICS_TOKEN`: 인증 토큰 (선택)
- `R_ANALYTICS_TIMEOUT_SECS`: 타임아웃 (기본: 20초)

---

### 2. FastAPI 프록시 라우터

**파일**: `apps/seedtest_api/routers/analytics_proxy.py`

**엔드포인트**:

| 메서드 | 경로 | 스코프 | 설명 |
|--------|------|--------|------|
| GET | `/analytics/health` | `reports:view` | 헬스 체크 |
| POST | `/analytics/score/topic-theta` | `analysis:run`, `reports:view` | 주제별 θ 점수 |
| POST | `/analytics/improvement/index` | `analysis:run`, `reports:view` | 개선 지수 (I_t) |
| POST | `/analytics/goal/attainment` | `analysis:run`, `reports:view` | 목표 달성 확률 |
| POST | `/analytics/recommend/next-topics` | `recommend:plan`, `reports:view` | 추천 주제 |
| POST | `/analytics/risk/churn` | `analysis:run`, `reports:view` | 이탈 위험 |
| POST | `/analytics/report/generate` | `reports:generate`, `reports:view` | 리포트 생성 |

**요청 예시**:

```bash
# Health check
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://api.example.com/analytics/health

# Topic theta scoring
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "student-123", "topic_ids": ["topic-A", "topic-B"]}' \
  https://api.example.com/analytics/score/topic-theta

# Churn risk
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "student-123"}' \
  https://api.example.com/analytics/risk/churn
```

---

### 3. K8s 매니페스트

**위치**: `portal_front/ops/k8s/r-analytics/`

- **deployment.yaml**: 2 replicas, 2Gi~8Gi 메모리, anti-affinity
- **service.yaml**: ClusterIP, port 80 → targetPort 8010
- **externalsecret.yaml**: GCP Secret Manager 연동
- **servicemonitor.yaml**: Prometheus 메트릭 수집

---

## 🚀 배포 절차

### 1. 사전 준비

```bash
# 1. Docker 이미지 빌드 및 푸시
cd /path/to/r-analytics
docker build -t gcr.io/univprepai/r-analytics:latest .
docker push gcr.io/univprepai/r-analytics:latest

# 2. GCP Secret Manager에 토큰 생성
TOKEN=$(openssl rand -base64 32)
echo -n "$TOKEN" | gcloud secrets create r-analytics-internal-token \
  --data-file=- \
  --project=univprepai
```

---

### 2. K8s 배포

```bash
cd /home/won/projects/dreamseed_monorepo

# ExternalSecret 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml

# Deployment 및 Service 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/service.yaml

# ServiceMonitor 적용 (Prometheus)
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/servicemonitor.yaml

# 배포 상태 확인
kubectl -n seedtest rollout status deployment/r-analytics --timeout=5m
kubectl -n seedtest get pods -l app=r-analytics
```

---

### 3. 검증

```bash
# 1. Pod 상태 확인
kubectl -n seedtest get pods -l app=r-analytics

# 2. 로그 확인
kubectl -n seedtest logs -l app=r-analytics --tail=50

# 3. 헬스 체크
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://r-analytics.seedtest.svc.cluster.local:80/health

# 4. Secret 확인
kubectl -n seedtest get secret r-analytics-credentials
```

**예상 결과**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2025-11-02T10:30:00Z"
}
```

---

## 🔧 환경 설정

### seedtest-api 환경 변수

**K8s Deployment** (`apps/seedtest_api`):

```yaml
env:
  - name: R_ANALYTICS_BASE_URL
    value: "http://r-analytics.seedtest.svc.cluster.local:80"
  - name: R_ANALYTICS_TOKEN
    valueFrom:
      secretKeyRef:
        name: r-analytics-credentials
        key: token
        optional: true
  - name: R_ANALYTICS_TIMEOUT_SECS
    value: "60"
```

**로컬 개발** (`.env.local`):

```bash
R_ANALYTICS_BASE_URL=http://localhost:8010
R_ANALYTICS_TOKEN=your-local-token
R_ANALYTICS_TIMEOUT_SECS=20
```

---

## 📊 모니터링

### Prometheus 메트릭

ServiceMonitor가 다음 메트릭을 수집합니다:

- `r_analytics_up`: 서비스 상태 (1=up, 0=down)
- `r_analytics_request_duration_seconds`: 요청 처리 시간
- `r_analytics_request_total`: 총 요청 수
- `r_analytics_error_total`: 에러 수

### 로그 모니터링

```bash
# 실시간 로그
kubectl -n seedtest logs -f deployment/r-analytics

# 에러 로그
kubectl -n seedtest logs -l app=r-analytics --tail=100 | grep -i error

# 특정 시간대 로그
kubectl -n seedtest logs -l app=r-analytics --since=1h
```

### 리소스 사용량

```bash
# Pod 리소스 사용량
kubectl -n seedtest top pods -l app=r-analytics

# Deployment 상태
kubectl -n seedtest describe deployment r-analytics
```

---

## 🔍 트러블슈팅

### 문제 1: 연결 실패 (502 Bad Gateway)

**증상**:
```
HTTPException: 502 Bad Gateway - r-analytics error: Connection refused
```

**해결**:
```bash
# 1. Pod 상태 확인
kubectl -n seedtest get pods -l app=r-analytics

# 2. Service 확인
kubectl -n seedtest get svc r-analytics

# 3. DNS 확인
kubectl -n seedtest run -it --rm debug --image=busybox --restart=Never -- \
  nslookup r-analytics.seedtest.svc.cluster.local

# 4. 재시작
kubectl -n seedtest rollout restart deployment/r-analytics
```

---

### 문제 2: 인증 실패 (401 Unauthorized)

**증상**:
```
HTTPException: 401 Unauthorized - Invalid token
```

**해결**:
```bash
# 1. Secret 확인
kubectl -n seedtest get secret r-analytics-credentials -o yaml

# 2. ExternalSecret 상태 확인
kubectl -n seedtest describe externalsecret r-analytics-credentials

# 3. GCP Secret Manager 확인
gcloud secrets versions access latest --secret=r-analytics-internal-token --project=univprepai

# 4. Secret 재동기화
kubectl -n seedtest delete secret r-analytics-credentials
kubectl -n seedtest delete externalsecret r-analytics-credentials
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml
```

---

### 문제 3: 타임아웃 (504 Gateway Timeout)

**증상**:
```
HTTPException: 504 Gateway Timeout - Request timeout
```

**해결**:
```bash
# 1. 타임아웃 증가
kubectl -n seedtest set env deployment/seedtest-api R_ANALYTICS_TIMEOUT_SECS=120

# 2. Pod 리소스 확인
kubectl -n seedtest top pods -l app=r-analytics

# 3. 리소스 증가 (필요 시)
kubectl -n seedtest patch deployment r-analytics --type=json -p='[
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/cpu", "value": "8000m"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "16Gi"}
]'
```

---

### 문제 4: Pod 시작 실패

**증상**:
```
kubectl get pods -l app=r-analytics
NAME                           READY   STATUS             RESTARTS   AGE
r-analytics-xxx                0/1     CrashLoopBackOff   5          5m
```

**해결**:
```bash
# 1. Pod 로그 확인
kubectl -n seedtest logs -l app=r-analytics --tail=100

# 2. Pod 이벤트 확인
kubectl -n seedtest describe pod -l app=r-analytics

# 3. 이미지 확인
kubectl -n seedtest get deployment r-analytics -o jsonpath='{.spec.template.spec.containers[0].image}'

# 4. 이미지 재빌드 및 푸시
docker build -t gcr.io/univprepai/r-analytics:latest .
docker push gcr.io/univprepai/r-analytics:latest
kubectl -n seedtest rollout restart deployment/r-analytics
```

---

## 🔄 스케일링

### 수동 스케일링

```bash
# 스케일 업
kubectl -n seedtest scale deployment r-analytics --replicas=4

# 스케일 다운
kubectl -n seedtest scale deployment r-analytics --replicas=1
```

### HPA (Horizontal Pod Autoscaler)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: r-analytics-hpa
  namespace: seedtest
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: r-analytics
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

```bash
# HPA 적용
kubectl -n seedtest apply -f r-analytics-hpa.yaml

# HPA 상태 확인
kubectl -n seedtest get hpa r-analytics-hpa
```

---

## 🎯 사용 예시

### Python (Job/Script)

```python
from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient

client = RAnalyticsClient()

# 1. 주제별 능력 추정
result = client.score_topic_theta(
    student_id="student-123",
    topic_ids=["algebra", "geometry", "calculus"]
)
print(f"Theta scores: {result['theta_scores']}")

# 2. 개선 지수 계산
improvement = client.improvement_index(
    student_id="student-123",
    window_days=14
)
print(f"I_t: {improvement['I_t']}, trend: {improvement['trend']}")

# 3. 목표 달성 확률
goal = client.goal_attainment(
    student_id="student-123",
    subject_id="math",
    target_score=85.0,
    target_date="2025-12-31"
)
print(f"P(goal): {goal['probability']}")

# 4. 추천 주제
recommendations = client.recommend_next_topics(
    student_id="student-123",
    k=5
)
print(f"Next topics: {recommendations['topics']}")

# 5. 이탈 위험
risk = client.risk_churn(student_id="student-123")
print(f"Churn risk: {risk['risk_score']}, alert: {risk['alert']}")

# 6. 리포트 생성
report = client.report_generate(
    student_id="student-123",
    period="weekly"
)
print(f"Report URL: {report['url']}")
```

### FastAPI (Endpoint)

```python
from fastapi import APIRouter, Depends
from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient
from apps.seedtest_api.security.jwt import require_scopes

router = APIRouter()

@router.get("/student/{student_id}/analytics")
async def get_student_analytics(
    student_id: str,
    client: RAnalyticsClient = Depends(lambda: RAnalyticsClient()),
    payload: dict = Depends(require_scopes("analysis:run"))
):
    """Get comprehensive analytics for a student."""
    
    # 1. Topic theta
    theta = client.score_topic_theta(student_id, [])
    
    # 2. Improvement index
    improvement = client.improvement_index(student_id, window_days=14)
    
    # 3. Churn risk
    risk = client.risk_churn(student_id)
    
    # 4. Recommendations
    recommendations = client.recommend_next_topics(student_id, k=5)
    
    return {
        "student_id": student_id,
        "theta": theta,
        "improvement": improvement,
        "churn_risk": risk,
        "recommendations": recommendations
    }
```

---

## 📚 관련 문서

- **K8s 매니페스트**: `portal_front/ops/k8s/r-analytics/`
- **Python 클라이언트**: `apps/seedtest_api/app/clients/r_analytics.py`
- **FastAPI 라우터**: `apps/seedtest_api/routers/analytics_proxy.py`
- **배포 가이드**: `portal_front/ops/k8s/r-analytics/README.md`
- **배포 스크립트**: `portal_front/ops/k8s/deploy-advanced-analytics.sh`

---

## ✅ 체크리스트

### 배포 전
- [ ] Docker 이미지 빌드 및 푸시
- [ ] GCP Secret Manager에 토큰 생성
- [ ] SecretStore 확인 (gcpsm-secret-store)
- [ ] PostgreSQL 스키마 확인

### 배포
- [ ] ExternalSecret 적용
- [ ] Deployment 적용
- [ ] Service 적용
- [ ] ServiceMonitor 적용 (선택)

### 검증
- [ ] Pod Running 상태 확인
- [ ] 헬스 체크 (200 OK)
- [ ] Secret 동기화 확인
- [ ] FastAPI 엔드포인트 테스트

### 통합
- [ ] seedtest-api 환경 변수 설정
- [ ] JWT 스코프 확인
- [ ] 로그 모니터링 설정
- [ ] 알림 설정 (선택)

---

**최종 업데이트**: 2025-11-02  
**작성자**: Cascade AI  
**상태**: Production Ready - 즉시 배포 가능
