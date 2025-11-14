# 운영 배포 가이드 (Production Ready)

**작성일**: 2025-11-01  
**환경**: GCP Cloud SQL + GKE  
**상태**: 전체 파이프라인 배포 준비 완료

---

## ✅ 구현 완료 현황

### Phase 1-3: 일일 배치 작업
- ✅ `compute-daily-kpis` - 주간 KPI 계산 (02:10 UTC)
- ✅ `aggregate-features-daily` - 토픽별 피처 집계 (02:25 UTC)
- ✅ `mirt-calibrate` - IRT 캘리브레이션 (03:00 UTC)

### Phase 4: θ 온라인 업데이트
- ✅ API 엔드포인트: `POST /analysis/irt/update-theta`
- ✅ JWT/JWKS 스코프 검사: `analysis:run` 또는 `exam:write`
- ✅ 세션 훅: `on_session_complete()`
- ✅ 구조화된 로깅 및 에러 처리

### Phase 5: Quarto 리포팅
- ✅ Quarto 템플릿: `weekly_report.qmd`
- ✅ 리포트 생성 Job: `generate_weekly_report.py`
- ✅ Dockerfile: `Dockerfile.quarto-runner`
- ✅ CronJob: `generate-weekly-report.yaml` (매주 월요일 04:00 UTC)

---

## 🔧 운영 환경 설정

### Cloud SQL Proxy 사이드카

모든 CronJob에 Cloud SQL Proxy 사이드카가 추가되었습니다:

```yaml
serviceAccountName: seedtest-api
containers:
  - name: <job-name>
    command:
      - /bin/sh
      - -c
      - |
        echo "Waiting for Cloud SQL Proxy to be ready..."
        sleep 5
        python3 -m seedtest_api.jobs.<job_name>
  
  - name: cloud-sql-proxy
    image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.11.3
    args:
      - --structured-logs
      - --port=5432
      - univprepai:asia-northeast3:seedtest-staging
```

### 이미지 레지스트리

- **배치 작업**: `gcr.io/univprepai/seedtest-api:latest`
- **Quarto 런너**: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest`

---

## 📋 사전 준비 체크리스트

### 1. GCP 리소스

```bash
# ServiceAccount 생성 (Cloud SQL 접근 권한)
gcloud iam service-accounts create seedtest-api \
  --display-name="Seedtest API Service Account"

# Cloud SQL Client 역할 부여
gcloud projects add-iam-policy-binding univprepai \
  --member="serviceAccount:seedtest-api@univprepai.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Workload Identity 바인딩
gcloud iam service-accounts add-iam-policy-binding \
  seedtest-api@univprepai.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:univprepai.svc.id.goog[seedtest/seedtest-api]"
```

### 2. Kubernetes Secrets

```bash
# DB 자격증명
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:pass@localhost:5432/seedtest'

# R IRT 서비스 토큰 (선택사항)
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<internal-token>'

# AWS S3 자격증명 (리포팅용)
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<secret>'
```

### 3. Kubernetes ServiceAccount

```bash
# ServiceAccount 생성 및 Workload Identity 연결
kubectl -n seedtest create serviceaccount seedtest-api

kubectl annotate serviceaccount seedtest-api \
  --namespace seedtest \
  iam.gke.io/gcp-service-account=seedtest-api@univprepai.iam.gserviceaccount.com
```

### 4. JWT/JWKS 설정

```bash
# seedtest-api Deployment 환경 변수
kubectl -n seedtest set env deployment/seedtest-api \
  JWKS_URL='https://your-auth-server/.well-known/jwks.json' \
  JWT_AUD='seedtest-api' \
  JWT_ISS='https://your-auth-server'
```

### 5. R IRT Plumber 서비스

```bash
# R IRT 서비스 배포 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/health
```

---

## 🚀 배포 명령어

### 1단계: 이미지 빌드 및 푸시

```bash
# seedtest-api 이미지
docker build -t gcr.io/univprepai/seedtest-api:latest .
docker push gcr.io/univprepai/seedtest-api:latest

# Quarto 런너 이미지
docker build -f Dockerfile.quarto-runner \
  -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest
```

### 2단계: CronJob 배포

```bash
# 모든 배치 작업 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# 배포 확인
kubectl -n seedtest get cronjob
```

### 3단계: θ 온라인 업데이트 활성화

```bash
# seedtest-api Deployment 환경 변수 추가
kubectl -n seedtest set env deployment/seedtest-api \
  ENABLE_IRT_ONLINE_UPDATE=true \
  R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80

# 배포 확인
kubectl -n seedtest rollout status deployment/seedtest-api
```

---

## 🧪 수동 테스트

### 1-3단계: 배치 작업 테스트

```bash
# 1. KPI 계산
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis \
  compute-daily-kpis-test-$(date +%s)

# 2. 피처 집계
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily \
  aggregate-features-test-$(date +%s)

# 3. IRT 캘리브레이션
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-test-$(date +%s)

# 로그 확인
kubectl -n seedtest get jobs --watch
kubectl -n seedtest logs -f job/<job-name>
```

### 4단계: θ 업데이트 API 테스트

```bash
# JWT 토큰 획득 (실제 인증 서버에서)
TOKEN=$(curl -X POST https://your-auth-server/token \
  -d "grant_type=client_credentials" \
  -d "scope=analysis:run" | jq -r .access_token)

# API 호출
curl -X POST "https://api.example.com/api/seedtest/analysis/irt/update-theta" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "lookback_days": 30
  }'

# 예상 응답 (성공)
{
  "status": "ok",
  "user_id": "test-user-123",
  "theta": 0.85,
  "se": 0.12,
  "model": "2PL",
  "version": "v1",
  "updated_at": "2025-11-01T12:34:56Z"
}

# 예상 응답 (데이터 없음)
{
  "status": "noop",
  "user_id": "test-user-123",
  "message": "theta_update_failed: no attempts found or R IRT service unavailable"
}
```

### 5단계: Quarto 리포트 테스트

```bash
# 수동 Job 실행
kubectl -n seedtest create job --from=cronjob/generate-weekly-report \
  generate-weekly-report-test-$(date +%s)

# 로그 확인 (5-10분 소요)
kubectl -n seedtest logs -f job/generate-weekly-report-test-<timestamp>

# 로컬 테스트 (dry-run)
docker run --rm \
  -e DATABASE_URL='postgresql://...' \
  -e REPORT_FORMAT='pdf' \
  -e S3_BUCKET='seedtest-reports' \
  asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest \
  python3 -m apps.seedtest_api.jobs.generate_weekly_report --dry-run
```

---

## 🔍 검증 쿼리

### 1-2단계: KPI 및 피처 검증

```sql
-- weekly_kpi 확인
SELECT 
    user_id, 
    week_start,
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
SELECT 
    user_id, 
    topic_id, 
    date,
    attempts, 
    correct,
    ROUND((correct::float / NULLIF(attempts, 0) * 100)::numeric, 1) AS accuracy_pct,
    rt_median,
    hints,
    improvement
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, user_id
LIMIT 20;
```

### 3단계: IRT 캘리브레이션 검증

```sql
-- mirt_item_params 확인
SELECT 
    item_id, 
    model,
    params->>'a' AS discrimination,
    params->>'b' AS difficulty,
    params->>'c' AS guessing,
    fitted_at
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 20;

-- mirt_ability 확인
SELECT 
    user_id, 
    theta, 
    se, 
    model, 
    version,
    fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 20;
```

### 4단계: θ 온라인 업데이트 검증

```sql
-- 최근 1시간 θ 업데이트
SELECT 
    user_id, 
    theta, 
    se, 
    version,
    fitted_at
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour'
ORDER BY fitted_at DESC;

-- 일별 업데이트 빈도
SELECT 
    DATE(fitted_at) AS date, 
    COUNT(*) AS updates,
    COUNT(DISTINCT user_id) AS unique_users
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(fitted_at)
ORDER BY date DESC;
```

### 5단계: 리포트 생성 검증

```sql
-- 생성된 리포트 확인
SELECT 
    user_id, 
    week_start, 
    format, 
    url, 
    generated_at,
    file_size_bytes
FROM report_artifacts
ORDER BY generated_at DESC
LIMIT 10;

-- 주간 리포트 커버리지
SELECT 
    week_start, 
    COUNT(DISTINCT user_id) AS users_with_report,
    COUNT(*) AS total_reports
FROM report_artifacts
WHERE generated_at >= NOW() - INTERVAL '30 days'
GROUP BY week_start
ORDER BY week_start DESC;
```

```bash
# S3 확인
aws s3 ls s3://seedtest-reports/reports/ --recursive --region ap-northeast-2 | head -20
```

---

## 📊 모니터링

### CronJob 상태 확인

```bash
# 모든 CronJob 상태
kubectl -n seedtest get cronjob

# 최근 Job 실행 이력
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -20

# 실패한 Job
kubectl -n seedtest get jobs --field-selector status.successful!=1

# 특정 CronJob의 최근 실행
kubectl -n seedtest get jobs -l cronjob=compute-daily-kpis --sort-by=.metadata.creationTimestamp
```

### 로그 조회

```bash
# 특정 CronJob 최근 로그
CRONJOB=compute-daily-kpis
LATEST_JOB=$(kubectl -n seedtest get jobs -l cronjob=$CRONJOB \
  --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl -n seedtest logs job/$LATEST_JOB --tail=100

# Cloud SQL Proxy 로그
kubectl -n seedtest logs job/$LATEST_JOB -c cloud-sql-proxy --tail=50

# 에러 필터링
kubectl -n seedtest logs job/$LATEST_JOB | grep -i "error\|exception\|failed"
```

### 메트릭 (Prometheus/Grafana)

```promql
# Job 실행 성공률
sum(rate(kube_job_status_succeeded{namespace="seedtest"}[1h])) 
/ 
sum(rate(kube_job_status_failed{namespace="seedtest"}[1h]))

# Job 실행 시간
histogram_quantile(0.95, 
  rate(kube_job_complete_duration_seconds_bucket{namespace="seedtest"}[1h])
)

# θ 업데이트 성공률 (커스텀 메트릭)
rate(theta_update_total{status="ok"}[5m]) 
/ 
rate(theta_update_total[5m])
```

---

## 🔧 문제 해결

### Cloud SQL Proxy 연결 실패

```bash
# ServiceAccount 확인
kubectl -n seedtest get sa seedtest-api -o yaml

# Workload Identity 바인딩 확인
gcloud iam service-accounts get-iam-policy \
  seedtest-api@univprepai.iam.gserviceaccount.com

# Proxy 로그 확인
kubectl -n seedtest logs <pod-name> -c cloud-sql-proxy

# 수동 연결 테스트
kubectl -n seedtest run sql-test --image=postgres:15 --rm -it --restart=Never -- \
  psql -h localhost -p 5432 -U <user> -d seedtest
```

### R IRT 서비스 연결 실패

```bash
# 서비스 상태
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 엔드포인트 확인
kubectl -n seedtest get endpoints r-irt-plumber

# 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/health
```

### JWT 인증 실패

```bash
# seedtest-api 로그 확인
kubectl -n seedtest logs -l app=seedtest-api --tail=100 | grep -i "jwt\|auth\|token"

# JWKS 엔드포인트 테스트
curl -v https://your-auth-server/.well-known/jwks.json

# 토큰 디코딩 (jwt.io 또는)
echo $TOKEN | cut -d. -f2 | base64 -d | jq .
```

### S3 업로드 실패

```bash
# Secret 확인
kubectl -n seedtest get secret aws-s3-credentials -o yaml

# 권한 테스트 (로컬)
aws s3 ls s3://seedtest-reports/ --region ap-northeast-2

# Job 로그 확인
kubectl -n seedtest logs job/<report-job-name> | grep -i "s3\|boto\|upload"
```

### Job 실패 (일반)

```bash
# Pod 상세 정보
kubectl -n seedtest describe pod <pod-name>

# 이벤트 확인
kubectl -n seedtest get events --sort-by='.lastTimestamp' | grep <job-name>

# 재시도
kubectl -n seedtest delete job <job-name>
kubectl -n seedtest create job --from=cronjob/<cronjob-name> <job-name>-retry
```

---

## 🔄 롤백 절차

### CronJob 롤백

```bash
# 이전 버전으로 롤백
kubectl -n seedtest rollout undo cronjob/<cronjob-name>

# 특정 리비전으로 롤백
kubectl -n seedtest rollout undo cronjob/<cronjob-name> --to-revision=2

# 이미지 변경
kubectl -n seedtest set image cronjob/<cronjob-name> \
  <container-name>=gcr.io/univprepai/seedtest-api:<previous-tag>
```

### θ 온라인 업데이트 비활성화

```bash
# 환경 변수 제거
kubectl -n seedtest set env deployment/seedtest-api \
  ENABLE_IRT_ONLINE_UPDATE=false

# 또는 완전 제거
kubectl -n seedtest set env deployment/seedtest-api \
  ENABLE_IRT_ONLINE_UPDATE-
```

---

## 📈 성능 최적화

### 리소스 조정

```bash
# CPU/메모리 증가
kubectl -n seedtest set resources cronjob/compute-daily-kpis \
  --requests=cpu=1000m,memory=1Gi \
  --limits=cpu=2000m,memory=2Gi
```

### 동시성 제어

```yaml
# CronJob에서 동시 실행 방지
spec:
  concurrencyPolicy: Forbid  # 또는 Replace, Allow
```

### 타임아웃 설정

```yaml
spec:
  jobTemplate:
    spec:
      activeDeadlineSeconds: 7200  # 2시간
      backoffLimit: 1  # 재시도 횟수
```

---

## 📚 참고 문서

### 배치 작업
- `/portal_front/ops/k8s/cron/FINAL_DEPLOYMENT_SUMMARY.md`
- `/portal_front/apps/seedtest_api/jobs/README_compute_daily_kpis.md`
- `/portal_front/apps/seedtest_api/jobs/README_aggregate_features_daily.md`
- `/portal_front/apps/seedtest_api/jobs/README_mirt_calibrate.md`

### θ 온라인 업데이트
- `/apps/seedtest_api/docs/IRT_ONLINE_UPDATE_GUIDE.md`
- `/apps/seedtest_api/services/irt_update_service.py`
- `/apps/seedtest_api/services/session_hooks.py`

### Quarto 리포팅
- `/apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md`
- `/apps/seedtest_api/jobs/generate_weekly_report.py`
- `/reports/quarto/weekly_report.qmd`

### GCP/Kubernetes
- [Cloud SQL Proxy for GKE](https://cloud.google.com/sql/docs/postgres/connect-kubernetes-engine)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Kubernetes CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**상태**: Production Ready - 즉시 배포 가능
