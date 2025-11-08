# R Analytics 빠른 시작 가이드

**최종 업데이트**: 2025-11-02  
**상태**: Production Ready

---

## 🎯 r-analytics란?

통합 분석 API 서비스(Plumber, 포트 8010)로 7가지 핵심 분석 기능을 제공합니다:

1. **Topic Theta Scoring** - IRT 기반 주제별 능력 추정
2. **Improvement Index** - 성장 추적 (I_t 메트릭)
3. **Goal Attainment** - 목표 달성 확률 예측
4. **Topic Recommendations** - 다음 학습 주제 추천
5. **Churn Risk** - 14일 이탈 위험 평가
6. **Report Generation** - 종합 분석 리포트 생성
7. **Health Check** - 서비스 상태 확인

---

## 🚀 5분 안에 시작하기

### 1. 배포 (K8s)

```bash
cd /home/won/projects/dreamseed_monorepo

# 전체 배포 (r-analytics 포함)
./portal_front/ops/k8s/deploy-advanced-analytics.sh

# 또는 r-analytics만 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/service.yaml
```

### 2. 검증

```bash
# Pod 상태 확인
kubectl -n seedtest get pods -l app=r-analytics

# 헬스 체크
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl http://r-analytics.seedtest.svc.cluster.local:80/health
```

### 3. Python에서 사용

```python
from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient

# 클라이언트 생성 (환경 변수에서 자동 로드)
client = RAnalyticsClient()

# 헬스 체크
health = client.health()
print(health)  # {"status": "ok", "version": "1.0.0"}

# 주제별 능력 추정
theta = client.score_topic_theta("student-123", ["algebra", "geometry"])
print(theta)  # {"student_id": "student-123", "theta_scores": {...}}

# 이탈 위험 평가
risk = client.risk_churn("student-123")
print(risk)  # {"student_id": "student-123", "risk_score": 0.75, "alert": true}
```

### 4. FastAPI에서 사용

```bash
# 엔드포인트는 이미 등록되어 있음 (main.py)
# GET  /analytics/health
# POST /analytics/score/topic-theta
# POST /analytics/improvement/index
# POST /analytics/goal/attainment
# POST /analytics/recommend/next-topics
# POST /analytics/risk/churn
# POST /analytics/report/generate

# 테스트 (JWT 토큰 필요)
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://api.example.com/analytics/health
```

---

## 📦 구현 완료 컴포넌트

### ✅ Python 클라이언트
- **파일**: `apps/seedtest_api/app/clients/r_analytics.py`
- **환경 변수**: `R_ANALYTICS_BASE_URL`, `R_ANALYTICS_TOKEN`, `R_ANALYTICS_TIMEOUT_SECS`

### ✅ FastAPI 프록시 라우터
- **파일**: `apps/seedtest_api/routers/analytics_proxy.py`
- **보안**: JWT/JWKS 스코프 보호 (`analysis:run`, `reports:view`, etc.)

### ✅ K8s 매니페스트
- **위치**: `portal_front/ops/k8s/r-analytics/`
- **파일**: `deployment.yaml`, `service.yaml`, `externalsecret.yaml`, `servicemonitor.yaml`

### ✅ 배포 스크립트
- **파일**: `portal_front/ops/k8s/deploy-advanced-analytics.sh`
- **기능**: r-analytics 자동 배포 포함

---

## 🔧 환경 설정

### K8s (seedtest-api Deployment)

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

### 로컬 개발 (.env.local)

```bash
R_ANALYTICS_BASE_URL=http://localhost:8010
R_ANALYTICS_TOKEN=your-local-token
R_ANALYTICS_TIMEOUT_SECS=20
```

---

## 📊 API 엔드포인트

### 1. Health Check

```bash
GET /health

# 응답
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2025-11-02T10:30:00Z"
}
```

### 2. Topic Theta Scoring

```bash
POST /score/topic-theta
{
  "student_id": "student-123",
  "topic_ids": ["algebra", "geometry"]
}

# 응답
{
  "student_id": "student-123",
  "theta_scores": {
    "algebra": 1.2,
    "geometry": 0.8
  },
  "timestamp": "2025-11-02T10:30:00Z"
}
```

### 3. Improvement Index

```bash
POST /improvement/index
{
  "student_id": "student-123",
  "window_days": 14
}

# 응답
{
  "student_id": "student-123",
  "I_t": 0.75,
  "trend": "improving",
  "window_days": 14,
  "timestamp": "2025-11-02T10:30:00Z"
}
```

### 4. Goal Attainment

```bash
POST /goal/attainment
{
  "student_id": "student-123",
  "subject_id": "math",
  "target_score": 85.0,
  "target_date": "2025-12-31"
}

# 응답
{
  "student_id": "student-123",
  "subject_id": "math",
  "probability": 0.82,
  "confidence_interval": [0.75, 0.89],
  "timestamp": "2025-11-02T10:30:00Z"
}
```

### 5. Topic Recommendations

```bash
POST /recommend/next-topics
{
  "student_id": "student-123",
  "k": 5
}

# 응답
{
  "student_id": "student-123",
  "topics": [
    {"topic_id": "calculus", "score": 0.95, "reason": "high_potential"},
    {"topic_id": "statistics", "score": 0.88, "reason": "prerequisite_met"},
    ...
  ],
  "timestamp": "2025-11-02T10:30:00Z"
}
```

### 6. Churn Risk

```bash
POST /risk/churn
{
  "student_id": "student-123"
}

# 응답
{
  "student_id": "student-123",
  "risk_score": 0.75,
  "risk_percentile": 85,
  "alert": true,
  "threshold": 0.7,
  "timestamp": "2025-11-02T10:30:00Z"
}
```

### 7. Report Generation

```bash
POST /report/generate
{
  "student_id": "student-123",
  "period": "weekly"
}

# 응답
{
  "student_id": "student-123",
  "period": "weekly",
  "url": "https://s3.../report-student-123-2025-11-02.pdf",
  "generated_at": "2025-11-02T10:30:00Z"
}
```

---

## 🔍 트러블슈팅

### 연결 실패 (502 Bad Gateway)

```bash
# Pod 상태 확인
kubectl -n seedtest get pods -l app=r-analytics

# 재시작
kubectl -n seedtest rollout restart deployment/r-analytics
```

### 인증 실패 (401 Unauthorized)

```bash
# Secret 확인
kubectl -n seedtest get secret r-analytics-credentials

# Secret 재동기화
kubectl -n seedtest delete secret r-analytics-credentials
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml
```

### 타임아웃 (504 Gateway Timeout)

```bash
# 타임아웃 증가
kubectl -n seedtest set env deployment/seedtest-api R_ANALYTICS_TIMEOUT_SECS=120
```

---

## 📚 상세 문서

- **통합 가이드**: `R_ANALYTICS_INTEGRATION.md`
- **K8s 배포**: `portal_front/ops/k8s/r-analytics/README.md`
- **Python 클라이언트**: `apps/seedtest_api/app/clients/r_analytics.py`
- **FastAPI 라우터**: `apps/seedtest_api/routers/analytics_proxy.py`

---

## ✅ 체크리스트

### 배포 전
- [ ] Docker 이미지 빌드 및 푸시
- [ ] GCP Secret Manager에 토큰 생성
- [ ] SecretStore 확인

### 배포
- [ ] ExternalSecret 적용
- [ ] Deployment 적용
- [ ] Service 적용

### 검증
- [ ] Pod Running 상태
- [ ] 헬스 체크 (200 OK)
- [ ] Python 클라이언트 테스트
- [ ] FastAPI 엔드포인트 테스트

---

**r-analytics는 이미 구현되어 있으며, 배포 스크립트로 즉시 배포 가능합니다!** 🚀

```bash
./portal_front/ops/k8s/deploy-advanced-analytics.sh
```
