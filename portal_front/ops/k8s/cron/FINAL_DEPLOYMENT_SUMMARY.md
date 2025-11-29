# 전체 파이프라인 최종 배포 요약

**작성일**: 2025-11-01  
**상태**: 4-5단계 포함 완료

---

## ✅ 구현 완료 현황

### Phase 1-3: 일일 배치 작업 (즉시 배포 가능)

| CronJob | 스케줄 | 설명 | 파일 |
|---------|--------|------|------|
| compute-daily-kpis | 02:10 UTC | 주간 KPI 계산 (I_t, E_t, R_t, A_t, P, S) | `jobs/compute_daily_kpis.py` |
| aggregate-features-daily | 02:25 UTC | 토픽별 일일 피처 집계 | `jobs/aggregate_features_daily.py` |
| mirt-calibrate | 03:00 UTC | IRT 주간 캘리브레이션 | `jobs/mirt_calibrate.py` |

**이미지**: `gcr.io/univprepai/seedtest-api:latest`

### Phase 4: θ 온라인 업데이트 (완료)

**구현 파일:**
- `services/irt_update_service.py` - IRT 업데이트 서비스
- `services/session_hooks.py` - 세션 종료 훅
- `routers/analysis.py` - API 엔드포인트 추가
- `docs/IRT_ONLINE_UPDATE_GUIDE.md` - 가이드 문서

**API 엔드포인트:**
```
POST /api/seedtest/analysis/irt/update-theta
Body: {user_id, session_id?, lookback_days=30}
Response: {user_id, theta, se, model, version, updated_at}
```

**환경 변수:**
```bash
ENABLE_IRT_ONLINE_UPDATE=true
R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80
R_IRT_INTERNAL_TOKEN=<optional>
```

### Phase 5: Quarto 리포팅 (완료)

**구현 파일:**
- `jobs/generate_weekly_report.py` - 리포트 생성 Job
- `reports/quarto/weekly_report.qmd` - Quarto 템플릿
- `Dockerfile.quarto-runner` - Quarto 런너 이미지
- `ops/k8s/cron/generate-weekly-report.yaml` - CronJob 매니페스트
- `docs/QUARTO_REPORTING_GUIDE.md` - 가이드 문서

**CronJob**: 매주 월요일 04:00 UTC  
**이미지**: `gcr.io/univprepai/seedtest-report-runner:latest`

---

## 즉시 배포 명령어

### 1단계: 일일 배치 작업 배포

```bash
# 모든 CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# 확인
kubectl -n seedtest get cronjob
```

### 2단계: θ 온라인 업데이트 활성화

```bash
# seedtest-api Deployment에 환경 변수 추가
kubectl -n seedtest set env deployment/seedtest-api \
  ENABLE_IRT_ONLINE_UPDATE=true \
  R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80

# 배포 확인
kubectl -n seedtest rollout status deployment/seedtest-api

# API 테스트
curl -X POST "https://api.example.com/api/seedtest/analysis/irt/update-theta" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-123"}'
```

### 3단계: Quarto 리포팅 배포

```bash
# 1. Quarto 런너 이미지 빌드
docker build -f Dockerfile.quarto-runner \
  -t gcr.io/univprepai/seedtest-report-runner:latest .

# 2. 이미지 푸시
docker push gcr.io/univprepai/seedtest-report-runner:latest

# 3. ConfigMap 생성
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET='dreamseed-reports' \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Secret 생성
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<secret>' \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# 6. 수동 테스트
kubectl -n seedtest create job --from=cronjob/generate-weekly-report \
  generate-weekly-report-test-$(date +%s)
```

---

## 수동 테스트

### 1-3단계 테스트

```bash
# 1. KPI 계산
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis \
  compute-daily-kpis-test-$(date +%s)

# 2. 피처 집계
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily \
  aggregate-features-test-$(date +%s)

# 3. IRT 캘리브레이션 (R IRT 서비스 필요)
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-test-$(date +%s)

# 로그 확인
kubectl -n seedtest get jobs --watch
kubectl -n seedtest logs -f job/<job-name>
```

### 4단계 테스트 (θ 업데이트)

```bash
# API 호출
curl -X POST "http://localhost:8000/api/seedtest/analysis/irt/update-theta" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "lookback_days": 30
  }'

# 예상 응답
{
  "user_id": "test-user-123",
  "theta": 0.85,
  "se": 0.12,
  "model": "2PL",
  "version": "v1",
  "updated_at": "2025-11-01T12:34:56Z"
}
```

### 5단계 테스트 (리포트 생성)

```bash
# Job 실행
kubectl -n seedtest create job --from=cronjob/generate-weekly-report \
  generate-weekly-report-test-$(date +%s)

# 로그 확인 (5-10분 소요)
kubectl -n seedtest logs -f job/generate-weekly-report-test-<timestamp>
```

---

## 검증 쿼리

### 1-2단계 검증

```sql
-- weekly_kpi 확인
SELECT user_id, week_start,
       kpis->>'I_t' AS improvement,
       kpis->>'E_t' AS efficiency,
       kpis->>'P' AS goal_prob,
       kpis->>'S' AS churn_risk,
       updated_at
FROM weekly_kpi
WHERE week_start >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY updated_at DESC
LIMIT 10;

-- features_topic_daily 확인
SELECT user_id, topic_id, date,
       attempts, correct,
       ROUND((correct::float / NULLIF(attempts, 0) * 100)::numeric, 1) AS accuracy_pct,
       rt_median, hints, improvement
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC
LIMIT 20;
```

### 3단계 검증 (IRT 캘리브레이션)

```sql
-- mirt_item_params 확인
SELECT item_id, model,
       params->>'a' AS discrimination,
       params->>'b' AS difficulty,
       fitted_at
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 20;

-- mirt_ability 확인
SELECT user_id, theta, se, model, fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 20;
```

### 4단계 검증 (θ 온라인 업데이트)

```sql
-- 최근 θ 업데이트 확인
SELECT user_id, theta, se, version, fitted_at
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour'
ORDER BY fitted_at DESC
LIMIT 10;

-- 업데이트 빈도
SELECT DATE(fitted_at) AS date, COUNT(*) AS updates
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(fitted_at)
ORDER BY date DESC;
```

### 5단계 검증 (리포트 생성)

```sql
-- 생성된 리포트 확인
SELECT user_id, week_start, format, url, generated_at
FROM report_artifacts
ORDER BY generated_at DESC
LIMIT 10;

-- 주간 리포트 커버리지
SELECT week_start, COUNT(DISTINCT user_id) AS users_with_report
FROM report_artifacts
WHERE generated_at >= NOW() - INTERVAL '30 days'
GROUP BY week_start
ORDER BY week_start DESC;
```

```bash
# S3 확인
aws s3 ls s3://dreamseed-reports/reports/ --recursive | head -20
```

---

## 전체 파이프라인 스케줄

| 시간 (UTC) | CronJob | 설명 | 의존성 |
|-----------|---------|------|--------|
| 02:10 | compute-daily-kpis | 주간 KPI 계산 | exam_results, attempt |
| 02:25 | aggregate-features-daily | 토픽별 피처 집계 | attempt, question |
| 03:00 | mirt-calibrate | IRT 캘리브레이션 | attempt, R IRT 서비스 |
| 04:00 (월) | generate-weekly-report | 주간 리포트 생성 | weekly_kpi, mirt_ability, S3 |
| 실시간 | θ 온라인 업데이트 | 세션 종료 시 | R IRT 서비스 |

---

## 세션 훅 통합

세션 종료 처리 코드에 다음을 추가하여 자동 θ 업데이트를 활성화하세요:

```python
# 예: apps/seedtest_api/routers/exams.py 또는 services/result_service.py
from apps.seedtest_api.services.session_hooks import on_session_complete

@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    user=Depends(require_scopes("exam:write")),
):
    user_id = user.get("sub")
    
    # 기존 세션 종료 로직
    # ... (결과 저장, 상태 업데이트 등) ...
    
    # θ 업데이트 트리거 (백그라운드, non-blocking)
    on_session_complete(user_id, session_id)
    
    return {"status": "completed", "session_id": session_id}
```

---

## 전제 조건 체크리스트

### Phase 1-3
- [ ] `seedtest` namespace 존재
- [ ] `seedtest-db-credentials` Secret 생성
- [ ] `gcr.io/univprepai/seedtest-api:latest` 이미지 빌드 및 푸시
- [ ] DB 마이그레이션 완료 (features_topic_daily, weekly_kpi, mirt_item_params, mirt_ability)
- [ ] `attempt` VIEW 생성

### Phase 4 (θ 온라인 업데이트)
- [ ] R IRT Plumber 서비스 배포 (`r-irt-plumber.seedtest.svc.cluster.local:80`)
- [ ] `r-irt-credentials` Secret 생성 (선택사항)
- [ ] `ENABLE_IRT_ONLINE_UPDATE=true` 환경 변수 설정
- [ ] 세션 종료 훅 통합

### Phase 5 (Quarto 리포팅)
- [ ] Quarto 런너 이미지 빌드 (`gcr.io/univprepai/seedtest-report-runner:latest`)
- [ ] S3 버킷 생성 및 권한 설정
- [ ] `report-config` ConfigMap 생성
- [ ] `aws-s3-credentials` Secret 생성
- [ ] `report_artifacts` 테이블 마이그레이션

---

## 모니터링

### 전체 상태 확인

```bash
# 모든 CronJob 상태
kubectl -n seedtest get cronjob

# 최근 Job 실행
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -20

# 실패한 Job
kubectl -n seedtest get jobs --field-selector status.successful!=1
```

### 로그 조회

```bash
# 특정 CronJob 최근 로그
CRONJOB=compute-daily-kpis
LATEST_JOB=$(kubectl -n seedtest get jobs -l cronjob=$CRONJOB \
  --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl -n seedtest logs job/$LATEST_JOB --tail=100
```

---

## 문제 해결

### R IRT 서비스 연결 실패

```bash
# 서비스 상태 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/health
```

### S3 업로드 실패

```bash
# Secret 확인
kubectl -n seedtest get secret aws-s3-credentials -o yaml

# 권한 테스트
aws s3 ls s3://dreamseed-reports/ --profile <profile>
```

### Job 실패

```bash
# Pod 로그
kubectl -n seedtest logs <pod-name>

# Pod 상세 정보
kubectl -n seedtest describe pod <pod-name>

# 재시도
kubectl -n seedtest delete job <job-name>
kubectl -n seedtest create job --from=cronjob/<cronjob-name> <job-name>-retry
```

---

## 참고 문서

### 배치 작업
- `/portal_front/ops/k8s/cron/DEPLOYMENT_GUIDE.md` - 통합 배포 가이드
- `/portal_front/apps/seedtest_api/jobs/README_compute_daily_kpis.md`
- `/portal_front/apps/seedtest_api/jobs/README_aggregate_features_daily.md`
- `/portal_front/apps/seedtest_api/jobs/README_mirt_calibrate.md`

### θ 온라인 업데이트
- `/apps/seedtest_api/docs/IRT_ONLINE_UPDATE_GUIDE.md` - θ 업데이트 가이드
- `/apps/seedtest_api/services/irt_update_service.py` - 서비스 구현
- `/apps/seedtest_api/services/session_hooks.py` - 세션 훅

### Quarto 리포팅
- `/apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md` - 리포팅 가이드
- `/apps/seedtest_api/jobs/generate_weekly_report.py` - Job 구현
- `/reports/quarto/weekly_report.qmd` - 템플릿

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**상태**: 전체 파이프라인 구현 완료 (1-5단계)
