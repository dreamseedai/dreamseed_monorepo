# 최종 배포 체크리스트

**작성일**: 2025-11-01  
**상태**: Production Ready - 즉시 배포 가능

---

## ✅ 구현 완료 현황

### Phase 1-3: 일일 배치 작업
- ✅ `compute-daily-kpis.yaml` - 주간 KPI 계산
- ✅ `aggregate-features-daily.yaml` - 토픽별 피처 집계
- ✅ `mirt-calibrate.yaml` - IRT 캘리브레이션
- ✅ Cloud SQL Proxy 사이드카 적용
- ✅ `serviceAccountName: seedtest-api` 설정

### Phase 4: θ 온라인 업데이트
- ✅ API 엔드포인트: `POST /analysis/irt/update-theta`
- ✅ JWT/JWKS 스코프 검사: `require_scopes("analysis:run", "exam:write")`
- ✅ 세션 훅: `on_session_complete()`
- ✅ 구조화된 로깅 및 에러 처리
- ✅ 안전한 응답: `{status: "ok"/"noop"}`

### Phase 5: Quarto 리포팅
- ✅ Quarto 템플릿: `reports/quarto/weekly_report.qmd`
- ✅ 런너 Dockerfile: `tools/quarto-runner/Dockerfile`
- ✅ 생성 Job: `apps/seedtest_api/jobs/generate_weekly_report.py`
- ✅ CronJob: `ops/k8s/cron/generate-weekly-report.yaml`
- ✅ Cloud SQL Proxy 사이드카 적용
- ✅ S3 설정: `seedtest-reports` (ap-northeast-2)

---

## 📋 배포 전 체크리스트

### 1. GCP 리소스 준비

```bash
# [ ] ServiceAccount 생성
gcloud iam service-accounts create seedtest-api \
  --display-name="Seedtest API Service Account"

# [ ] Cloud SQL Client 역할 부여
gcloud projects add-iam-policy-binding univprepai \
  --member="serviceAccount:seedtest-api@univprepai.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# [ ] Workload Identity 바인딩
gcloud iam service-accounts add-iam-policy-binding \
  seedtest-api@univprepai.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:univprepai.svc.id.goog[seedtest/seedtest-api]"

# [ ] Kubernetes ServiceAccount 생성
kubectl -n seedtest create serviceaccount seedtest-api

# [ ] ServiceAccount에 Workload Identity 어노테이션
kubectl annotate serviceaccount seedtest-api \
  --namespace seedtest \
  iam.gke.io/gcp-service-account=seedtest-api@univprepai.iam.gserviceaccount.com
```

### 2. Kubernetes Secrets 생성

```bash
# [ ] DB 자격증명
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:pass@localhost:5432/seedtest'

# [ ] R IRT 서비스 토큰 (선택사항)
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<internal-token>'

# [ ] AWS S3 자격증명
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<secret>'

# [ ] Secrets 확인
kubectl -n seedtest get secrets
```

### 3. 이미지 빌드 및 푸시

```bash
# [ ] seedtest-api 이미지 빌드
docker build -t gcr.io/univprepai/seedtest-api:latest .

# [ ] seedtest-api 이미지 푸시
docker push gcr.io/univprepai/seedtest-api:latest

# [ ] Quarto 런너 이미지 빌드
docker build -f Dockerfile.quarto-runner \
  -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest .

# [ ] Quarto 런너 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest

# [ ] 이미지 확인
gcloud container images list --repository=gcr.io/univprepai
gcloud artifacts docker images list asia-northeast3-docker.pkg.dev/univprepai/seedtest
```

### 4. R IRT Plumber 서비스 확인

```bash
# [ ] R IRT 서비스 상태 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# [ ] 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/health

# 예상 응답: {"status": "ok"}
```

### 5. JWT/JWKS 설정

```bash
# [ ] seedtest-api Deployment 환경 변수 설정
kubectl -n seedtest set env deployment/seedtest-api \
  JWKS_URL='https://your-auth-server/.well-known/jwks.json' \
  JWT_AUD='seedtest-api' \
  JWT_ISS='https://your-auth-server'

# [ ] JWKS 엔드포인트 테스트
curl -v https://your-auth-server/.well-known/jwks.json

# [ ] 배포 확인
kubectl -n seedtest rollout status deployment/seedtest-api
```

### 6. S3 버킷 준비

```bash
# [ ] S3 버킷 생성 (이미 존재하면 스킵)
aws s3 mb s3://seedtest-reports --region ap-northeast-2

# [ ] 버킷 정책 설정 (필요시)
aws s3api put-bucket-policy --bucket seedtest-reports --policy file://bucket-policy.json

# [ ] 버킷 확인
aws s3 ls s3://seedtest-reports/ --region ap-northeast-2
```

---

## 🚀 배포 실행

### Step 1: CronJob 배포

```bash
# [ ] compute-daily-kpis 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml

# [ ] aggregate-features-daily 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml

# [ ] mirt-calibrate 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# [ ] generate-weekly-report 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# [ ] 배포 확인
kubectl -n seedtest get cronjob
```

### Step 2: θ 온라인 업데이트 활성화

```bash
# [ ] 환경 변수 설정
kubectl -n seedtest set env deployment/seedtest-api \
  ENABLE_IRT_ONLINE_UPDATE=true \
  R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80

# [ ] 배포 확인
kubectl -n seedtest rollout status deployment/seedtest-api

# [ ] Pod 로그 확인
kubectl -n seedtest logs -l app=seedtest-api --tail=50
```

---

## 🧪 배포 후 검증

### 1. 배치 작업 수동 테스트

```bash
# [ ] KPI 계산 테스트
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis \
  compute-daily-kpis-test-$(date +%s)

# [ ] 피처 집계 테스트
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily \
  aggregate-features-test-$(date +%s)

# [ ] IRT 캘리브레이션 테스트
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-test-$(date +%s)

# [ ] 리포트 생성 테스트
kubectl -n seedtest create job --from=cronjob/generate-weekly-report \
  generate-weekly-report-test-$(date +%s)

# [ ] Job 상태 확인
kubectl -n seedtest get jobs --watch

# [ ] 로그 확인
kubectl -n seedtest logs -f job/<job-name>
kubectl -n seedtest logs -f job/<job-name> -c cloud-sql-proxy
```

### 2. θ 업데이트 API 테스트

```bash
# [ ] JWT 토큰 획득
TOKEN=$(curl -X POST https://your-auth-server/token \
  -d "grant_type=client_credentials" \
  -d "scope=analysis:run" | jq -r .access_token)

# [ ] API 호출
curl -X POST "https://api.example.com/api/seedtest/analysis/irt/update-theta" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "lookback_days": 30
  }'

# 예상 응답 (성공):
# {
#   "status": "ok",
#   "user_id": "test-user-123",
#   "theta": 0.85,
#   "se": 0.12,
#   "model": "2PL",
#   "version": "v1",
#   "updated_at": "2025-11-01T12:34:56Z"
# }

# 예상 응답 (데이터 없음):
# {
#   "status": "noop",
#   "user_id": "test-user-123",
#   "message": "theta_update_failed: no attempts found or R IRT service unavailable"
# }
```

### 3. 데이터베이스 검증

```sql
-- [ ] weekly_kpi 확인
SELECT user_id, week_start,
       kpis->>'I_t' AS improvement,
       kpis->>'P' AS goal_prob,
       kpis->>'S' AS churn_risk,
       updated_at
FROM weekly_kpi
WHERE week_start >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY updated_at DESC
LIMIT 10;

-- [ ] features_topic_daily 확인
SELECT user_id, topic_id, date,
       attempts, correct,
       ROUND((correct::float / NULLIF(attempts, 0) * 100)::numeric, 1) AS accuracy_pct
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC
LIMIT 20;

-- [ ] mirt_item_params 확인
SELECT item_id, model,
       params->>'a' AS discrimination,
       params->>'b' AS difficulty,
       fitted_at
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 20;

-- [ ] mirt_ability 확인
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 20;

-- [ ] report_artifacts 확인
SELECT user_id, week_start, format, url, generated_at
FROM report_artifacts
ORDER BY generated_at DESC
LIMIT 10;
```

### 4. S3 검증

```bash
# [ ] S3 업로드 확인
aws s3 ls s3://seedtest-reports/reports/ --recursive --region ap-northeast-2 | head -20

# [ ] 리포트 다운로드 테스트
aws s3 cp s3://seedtest-reports/reports/<user_id>/<week_start>/report.pdf ./test-report.pdf --region ap-northeast-2

# [ ] 파일 확인
file test-report.pdf
# 예상: test-report.pdf: PDF document, version 1.4
```

---

## 📊 모니터링 설정

### CronJob 상태 모니터링

```bash
# [ ] 모든 CronJob 상태
kubectl -n seedtest get cronjob

# [ ] 최근 Job 실행 이력
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -20

# [ ] 실패한 Job 확인
kubectl -n seedtest get jobs --field-selector status.successful!=1

# [ ] 특정 CronJob 상세 정보
kubectl -n seedtest describe cronjob/<cronjob-name>
```

### 로그 모니터링

```bash
# [ ] seedtest-api 로그
kubectl -n seedtest logs -l app=seedtest-api --tail=100 | grep -i "theta\|error"

# [ ] 특정 CronJob 최근 로그
CRONJOB=compute-daily-kpis
LATEST_JOB=$(kubectl -n seedtest get jobs -l cronjob=$CRONJOB \
  --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl -n seedtest logs job/$LATEST_JOB --tail=100

# [ ] Cloud SQL Proxy 로그
kubectl -n seedtest logs job/$LATEST_JOB -c cloud-sql-proxy --tail=50
```

### 알림 설정 (선택사항)

```bash
# [ ] Slack/Email 알림 설정
# [ ] Prometheus AlertManager 규칙 설정
# [ ] GCP Cloud Monitoring 알림 정책 생성
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
```

### R IRT 서비스 연결 실패

```bash
# 서비스 엔드포인트 확인
kubectl -n seedtest get endpoints r-irt-plumber

# 네트워크 정책 확인
kubectl -n seedtest get networkpolicies

# Pod에서 직접 테스트
kubectl -n seedtest exec -it <pod-name> -- curl http://r-irt-plumber.seedtest.svc.cluster.local:80/health
```

### JWT 인증 실패

```bash
# seedtest-api 환경 변수 확인
kubectl -n seedtest get deployment seedtest-api -o yaml | grep -A 10 "env:"

# JWKS 엔드포인트 테스트
curl -v https://your-auth-server/.well-known/jwks.json

# 토큰 디코딩
echo $TOKEN | cut -d. -f2 | base64 -d | jq .
```

### S3 업로드 실패

```bash
# Secret 확인
kubectl -n seedtest get secret aws-s3-credentials -o yaml

# 로컬에서 권한 테스트
aws s3 ls s3://seedtest-reports/ --region ap-northeast-2

# Job 로그 확인
kubectl -n seedtest logs job/<report-job-name> | grep -i "s3\|boto\|upload"
```

---

## 📈 성능 최적화 (선택사항)

### 리소스 조정

```bash
# CPU/메모리 증가
kubectl -n seedtest set resources cronjob/compute-daily-kpis \
  --requests=cpu=1000m,memory=1Gi \
  --limits=cpu=2000m,memory=2Gi
```

### 동시성 제어

```yaml
# CronJob concurrencyPolicy 조정
spec:
  concurrencyPolicy: Forbid  # 또는 Replace, Allow
```

### 타임아웃 설정

```yaml
# Job activeDeadlineSeconds 조정
spec:
  jobTemplate:
    spec:
      activeDeadlineSeconds: 7200  # 2시간
```

---

## 🎯 다음 단계

### 1. 멀티-유저 리포트 생성

현재 `generate-weekly-report`는 단일 사용자 테스트용입니다. 실제 운영에서는:

**옵션 A: 사용자 루프 방식**
```python
# generate_weekly_report.py 수정
def main():
    users = load_active_users()  # DB에서 활성 사용자 목록
    for user_id in users:
        try:
            generate_report(user_id, week_start)
        except Exception as e:
            logger.error(f"Failed to generate report for {user_id}: {e}")
```

**옵션 B: 큐 기반 처리**
```bash
# 별도 컨트롤러가 사용자별 Job 생성
for user_id in $(get_active_users); do
  kubectl -n seedtest create job generate-report-${user_id} \
    --from=cronjob/generate-weekly-report \
    -- --user-id ${user_id}
done
```

### 2. R IRT 재시도 로직 추가

```python
# apps/seedtest_api/app/clients/r_irt.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def score_with_retry(self, item_params, responses):
    return await self.score(item_params, responses)
```

### 3. Prometheus 메트릭 추가

```python
from prometheus_client import Counter, Histogram

theta_update_counter = Counter(
    'theta_update_total', 
    'Total theta updates', 
    ['status']
)
theta_update_duration = Histogram(
    'theta_update_duration_seconds', 
    'Theta update duration'
)
```

### 4. ExternalSecrets Operator (ESO) 연동

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: seedtest-db-credentials
  namespace: seedtest
spec:
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: seedtest-db-credentials
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: seedtest-db-url
```

---

## 📚 참고 문서

- `/portal_front/ops/k8s/cron/PRODUCTION_DEPLOYMENT_GUIDE.md` - 상세 배포 가이드
- `/portal_front/ops/k8s/cron/FINAL_DEPLOYMENT_SUMMARY.md` - 전체 파이프라인 요약
- `/apps/seedtest_api/docs/IRT_ONLINE_UPDATE_GUIDE.md` - θ 업데이트 가이드
- `/apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md` - 리포팅 가이드

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**상태**: Production Ready - 체크리스트 완료 후 즉시 배포 가능
