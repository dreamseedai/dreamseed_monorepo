# 전체 파이프라인 배포 가이드 (4-5단계 포함)

**작성일**: 2025-11-01  
**버전**: V1 Complete

## 배포 완료 현황

### ✅ 1-3단계 (즉시 배포 가능)
1. **compute-daily-kpis** - 일일 KPI 계산
2. **aggregate-features-daily** - 토픽별 피처 집계
3. **mirt-calibrate** - IRT 주간 캘리브레이션

### ✅ 4단계 (θ 온라인 업데이트)
- **API 엔드포인트**: `POST /api/seedtest/analysis/irt/update-theta`
- **세션 훅**: `on_session_complete()` 자동 트리거
- **서비스**: `irt_update_service.py` 구현 완료

### ✅ 5단계 (Quarto 리포팅)
- **템플릿**: `reports/quarto/weekly_report.qmd`
- **Dockerfile**: `Dockerfile.quarto-runner`
- **CronJob**: `generate-weekly-report.yaml`
- **Job 코드**: `jobs/generate_weekly_report.py`

---

## 즉시 배포 (1-3단계)

### 1. 배포 명령어

```bash
# 모든 CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# 확인
kubectl -n seedtest get cronjob
```

### 2. 수동 테스트

```bash
# 1. KPI 계산 (즉시 실행 가능)
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis \
  compute-daily-kpis-test-$(date +%s)

# 2. 피처 집계 (즉시 실행 가능)
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily \
  aggregate-features-test-$(date +%s)

# 3. IRT 캘리브레이션 (R IRT 서비스 필요)
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-test-$(date +%s)

# 로그 확인
kubectl -n seedtest get jobs --watch
kubectl -n seedtest logs -f job/<job-name>
```

### 3. 검증

```sql
-- 1-2단계 검증
SELECT user_id, week_start,
       kpis->>'I_t' AS improvement,
       kpis->>'P' AS goal_prob,
       kpis->>'S' AS churn_risk
FROM weekly_kpi
WHERE week_start >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY updated_at DESC
LIMIT 10;

SELECT user_id, topic_id, date, attempts, correct, rt_median
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC
LIMIT 20;

-- 3단계 검증 (R IRT 서비스 배포 후)
SELECT item_id, params->>'a' AS discrimination, params->>'b' AS difficulty
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 20;

SELECT user_id, theta, se
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 20;
```

---

## 4단계: θ 온라인 업데이트 배포

### 전제 조건
- R IRT Plumber 서비스 배포 완료
- `r-irt-credentials` Secret 생성

### 1. 환경 변수 설정

```bash
# seedtest-api Deployment에 환경 변수 추가
kubectl -n seedtest edit deployment seedtest-api

# 추가할 env:
env:
  - name: ENABLE_IRT_ONLINE_UPDATE
    value: "true"
  - name: R_IRT_BASE_URL
    value: "http://r-irt-plumber.seedtest.svc.cluster.local:80"
  - name: R_IRT_INTERNAL_TOKEN
    valueFrom:
      secretKeyRef:
        name: r-irt-credentials
        key: token
        optional: true
```

또는 ConfigMap/Patch 사용:

```bash
# ConfigMap 생성
kubectl -n seedtest create configmap irt-config \
  --from-literal=ENABLE_IRT_ONLINE_UPDATE=true \
  --from-literal=R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80 \
  --dry-run=client -o yaml | kubectl apply -f -

# Deployment 업데이트
kubectl -n seedtest rollout restart deployment/seedtest-api
kubectl -n seedtest rollout status deployment/seedtest-api
```

### 2. API 테스트

```bash
# 수동 θ 업데이트 테스트
curl -X POST http://<api-url>/api/seedtest/analysis/irt/update-theta \
  -H "Authorization: Bearer <token>" \
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

### 3. 세션 종료 통합 (코드 예시)

```python
# 세션 종료 엔드포인트에 추가
from apps.seedtest_api.services.session_hooks import on_session_complete

@router.post("/sessions/{session_id}/complete")
async def complete_session(session_id: str, user=Depends(require_scopes("exam:write"))):
    user_id = user.get("sub")
    
    # 세션 종료 처리
    # ... (기존 로직) ...
    
    # θ 업데이트 트리거 (백그라운드)
    on_session_complete(user_id, session_id)
    
    return {"status": "completed"}
```

### 4. 검증

```sql
-- θ 업데이트 확인
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour'
ORDER BY fitted_at DESC;

-- 업데이트 빈도
SELECT DATE(fitted_at) AS date, COUNT(*) AS updates
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(fitted_at)
ORDER BY date DESC;
```

---

## 5단계: Quarto 리포팅 배포

### 전제 조건
- S3 버킷 생성
- AWS 자격증명 준비
- `report_artifacts` 테이블 마이그레이션 완료

### 1. Quarto 런너 이미지 빌드

```bash
# 이미지 빌드
docker build -f Dockerfile.quarto-runner \
  -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest .

# 푸시
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest
```

### 2. ConfigMap 및 Secret 생성

```bash
# S3 버킷 ConfigMap
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET='dreamseed-reports' \
  --dry-run=client -o yaml | kubectl apply -f -

# AWS 자격증명 Secret
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<your-access-key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<your-secret-key>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. CronJob 배포

```bash
# 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# 확인
kubectl -n seedtest get cronjob generate-weekly-report
kubectl -n seedtest describe cronjob generate-weekly-report
```

### 4. 수동 테스트

```bash
# 테스트 실행
kubectl -n seedtest create job --from=cronjob/generate-weekly-report \
  generate-weekly-report-test-$(date +%s)

# 로그 확인 (5-10분 소요 가능)
kubectl -n seedtest logs -f job/generate-weekly-report-test-<timestamp>
```

### 5. 검증

```sql
-- 리포트 생성 확인
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

| 시간 (UTC) | CronJob | 설명 |
|-----------|---------|------|
| 01:15 | aggregate-features-daily | 토픽별 피처 집계 |
| 02:10 | compute-daily-kpis | 일일 KPI 계산 |
| 03:00 | mirt-calibrate | IRT 캘리브레이션 |
| 04:00 (월) | generate-weekly-report | 주간 리포트 생성 |
| 05:00 | detect-inactivity | 비활성 사용자 감지 |
| 실시간 | θ 온라인 업데이트 | 세션 종료 시 트리거 |

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

### Prometheus 메트릭 (선택 사항)

```yaml
# Example ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: seedtest-cronjobs
  namespace: seedtest
spec:
  selector:
    matchLabels:
      app: seedtest-api
  endpoints:
    - port: metrics
      interval: 30s
```

---

## 문제 해결

### 1. CronJob이 실행되지 않음

```bash
# CronJob 상태 확인
kubectl -n seedtest describe cronjob <cronjob-name>

# 이벤트 확인
kubectl -n seedtest get events --sort-by='.lastTimestamp' | grep <cronjob-name>

# 스케줄 확인 (UTC 기준)
kubectl -n seedtest get cronjob <cronjob-name> -o jsonpath='{.spec.schedule}'
```

### 2. Job 실패

```bash
# Pod 로그
kubectl -n seedtest logs <pod-name>

# Pod 상세 정보
kubectl -n seedtest describe pod <pod-name>

# 재시도
kubectl -n seedtest delete job <job-name>
kubectl -n seedtest create job --from=cronjob/<cronjob-name> <job-name>-retry
```

### 3. θ 업데이트 실패

```bash
# R IRT 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/health

# API 로그
kubectl -n seedtest logs -l app=seedtest-api --tail=100 | grep theta
```

### 4. Quarto 리포트 생성 실패

```bash
# Job 로그 확인
kubectl -n seedtest logs job/<report-job-name>

# Quarto 설치 확인
kubectl -n seedtest run quarto-test \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest \
  --rm -it --restart=Never -- quarto --version

# S3 자격증명 확인
kubectl -n seedtest get secret aws-s3-credentials -o yaml
```

---

## 체크리스트

### Phase 1-3 (즉시 배포)
- [ ] `seedtest` namespace 존재
- [ ] `seedtest-db-credentials` Secret 생성
- [ ] `seedtest-api:f830ff9c2-with-env` 이미지 배포
- [ ] DB 마이그레이션 완료 (features_topic_daily, weekly_kpi)
- [ ] CronJob 3개 배포 (compute-daily-kpis, aggregate-features-daily, mirt-calibrate)
- [ ] 수동 테스트 실행 및 검증

### Phase 4 (θ 온라인 업데이트)
- [ ] R IRT Plumber 서비스 배포
- [ ] `r-irt-credentials` Secret 생성
- [ ] `ENABLE_IRT_ONLINE_UPDATE=true` 환경 변수 설정
- [ ] API 배포 (θ 업데이트 엔드포인트 포함)
- [ ] 세션 종료 훅 통합
- [ ] 수동 API 테스트
- [ ] θ 업데이트 검증

### Phase 5 (Quarto 리포팅)
- [ ] Quarto 런너 이미지 빌드 및 푸시
- [ ] S3 버킷 생성 및 권한 설정
- [ ] `report-config` ConfigMap 생성
- [ ] `aws-s3-credentials` Secret 생성
- [ ] `report_artifacts` 테이블 마이그레이션
- [ ] `generate-weekly-report` CronJob 배포
- [ ] 수동 테스트 실행
- [ ] S3 및 DB 검증

---

## 참고 문서

### 배치 작업
- `/portal_front/ops/k8s/cron/DEPLOYMENT_GUIDE.md` - 통합 배포 가이드
- `/portal_front/apps/seedtest_api/jobs/README_compute_daily_kpis.md`
- `/portal_front/apps/seedtest_api/jobs/README_aggregate_features_daily.md`
- `/portal_front/apps/seedtest_api/jobs/README_mirt_calibrate.md`
- `/portal_front/apps/seedtest_api/jobs/README_detect_inactivity.md`

### θ 온라인 업데이트
- `/apps/seedtest_api/docs/IRT_ONLINE_UPDATE_GUIDE.md` - θ 업데이트 가이드
- `/apps/seedtest_api/services/irt_update_service.py` - 서비스 구현
- `/apps/seedtest_api/services/session_hooks.py` - 세션 훅
- `/apps/seedtest_api/routers/analysis.py` - API 엔드포인트

### Quarto 리포팅
- `/apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md` - 리포팅 가이드
- `/apps/seedtest_api/jobs/generate_weekly_report.py` - Job 구현
- `/reports/quarto/weekly_report.qmd` - 템플릿
- `/Dockerfile.quarto-runner` - 런너 이미지

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**버전**: 1.0 Complete
