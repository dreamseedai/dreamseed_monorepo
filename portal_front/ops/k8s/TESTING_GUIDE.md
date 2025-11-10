# IRT Calibration - 테스트 및 디버깅 가이드

**최종 업데이트**: 2025-11-02 00:17 KST  
**상태**: 실행 중

---

## 🧪 테스트 실행

### 수동 Job 생성

```bash
# Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)

# Job 목록 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -5
```

### 로그 실시간 확인

```bash
# 방법 1: 특정 컨테이너 로그
kubectl -n seedtest logs job/calibrate-irt-test-* -c calibrate-irt -f

# 방법 2: 모든 컨테이너 로그
kubectl -n seedtest logs job/calibrate-irt-test-* --all-containers=true -f

# 방법 3: Pod 이름으로 직접 확인
POD_NAME=$(kubectl -n seedtest get pods -l job-name=calibrate-irt-test-* -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest logs -f $POD_NAME -c calibrate-irt
```

---

## ✅ 예상 로그 출력

### 정상 실행 시

```
Waiting for Cloud SQL Proxy to be ready...
Starting IRT calibration...
PYTHONPATH: /app:/app/apps
Looking for seedtest_api:
/app/apps/seedtest_api
Found /app/apps/seedtest_api/jobs/mirt_calibrate.py, using apps path

[INFO] Starting IRT calibration job
[INFO] Environment: MIRT_LOOKBACK_DAYS=60, MIRT_MODEL=2PL, MIRT_MAX_OBS=500000
[INFO] R IRT service URL: http://r-irt-plumber.seedtest.svc.cluster.local:80

[INFO] Loading observations from attempt VIEW...
[INFO] Loaded 12345 observations (500 users, 150 items)
[INFO] Date range: 2024-10-03 to 2024-12-02

[INFO] Loading anchor items from question.meta...
[INFO] Loaded 50 anchors/seeds from question.meta
[INFO] Anchor items: [101, 102, 103, ..., 150]

[INFO] Preparing calibration payload...
[INFO] Total observations: 12345
[INFO] Model: 2PL
[INFO] Anchors: 50

[INFO] Calling R IRT service...
[INFO] Request: POST http://r-irt-plumber.seedtest.svc.cluster.local:80/irt/calibrate
[INFO] Payload size: 2.5 MB

[INFO] R IRT service response received (elapsed: 45.2s)
[INFO] Linking constants received: {'slope': 1.02, 'intercept': 0.05}
[INFO] Item parameters: 150 items
[INFO] User abilities: 500 users

[INFO] Upserting item parameters to mirt_item_params...
[INFO] Upserted 150 item parameters

[INFO] Upserting user abilities to mirt_ability...
[INFO] Upserted 500 user abilities

[INFO] Storing fit metadata to mirt_fit_meta...
[INFO] Run ID: fit-2025-11-02T04:15:23Z
[INFO] Linking constants stored in model_spec.linking_constants

✅ IRT calibration completed successfully
[INFO] Total duration: 52.3 seconds
```

---

## ⚠️ 일반적인 오류 및 해결

### 오류 1: mirt_calibrate.py not found

**로그**:
```
Looking for seedtest_api:
Error: mirt_calibrate.py not found in expected locations
```

**원인**: 이미지에 코드가 없거나 경로가 잘못됨

**해결**:
```bash
# 1. Pod 내부 확인
POD_NAME=$(kubectl -n seedtest get pods -l job-name=calibrate-irt-test-* -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest exec -it $POD_NAME -c calibrate-irt -- /bin/sh

# Pod 내부에서
find /app -name "mirt_calibrate.py"
ls -la /app/apps/seedtest_api/jobs/

# 2. 이미지 확인
kubectl -n seedtest get job calibrate-irt-test-* -o jsonpath='{.spec.template.spec.containers[0].image}'

# 3. 최신 이미지로 업데이트
kubectl -n seedtest set image cronjob/calibrate-irt-weekly \
  calibrate-irt=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest
```

---

### 오류 2: Database connection failed

**로그**:
```
[ERROR] could not connect to server: Connection refused
[ERROR] Is the server running on host "..." and accepting TCP/IP connections on port 5432?
```

**원인**: DATABASE_URL 오류 또는 Cloud SQL Proxy 문제

**해결**:
```bash
# 1. Secret 확인
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d
echo ""

# 2. Cloud SQL Proxy 로그 확인
kubectl -n seedtest logs job/calibrate-irt-test-* -c cloud-sql-proxy

# 3. Cloud SQL Proxy 상태 확인
kubectl -n seedtest describe job calibrate-irt-test-*

# 4. DATABASE_URL 형식 확인
# 올바른 형식: postgresql://user:password@localhost:5432/seedtest
# Cloud SQL Proxy 사용 시 host는 localhost여야 함

# 5. Secret 재생성
kubectl -n seedtest delete secret seedtest-db-credentials
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:password@localhost:5432/seedtest'
```

---

### 오류 3: R IRT service connection failed

**로그**:
```
[INFO] Calling R IRT service...
[WARN] R IRT service call failed (attempt 1/3): Connection refused
[INFO] Retrying in 5.0 seconds...
[WARN] R IRT service call failed (attempt 2/3): Connection refused
[INFO] Retrying in 10.0 seconds...
[WARN] R IRT service call failed (attempt 3/3): Connection refused
[ERROR] R IRT service call failed after 3 attempts
```

**원인**: R IRT Plumber 서비스 미배포 또는 네트워크 문제

**해결**:
```bash
# 1. R IRT 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 2. R IRT Pod 상태 확인
kubectl -n seedtest describe pods -l app=r-irt-plumber

# 3. R IRT 로그 확인
kubectl -n seedtest logs -l app=r-irt-plumber --tail=50

# 4. Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz

# 5. R IRT 서비스 재시작
kubectl -n seedtest rollout restart deployment r-irt-plumber

# 6. Endpoint 확인
kubectl -n seedtest get endpoints r-irt-plumber
```

---

### 오류 4: No observations found

**로그**:
```
[INFO] Loading observations from attempt VIEW...
[INFO] Loaded 0 observations
[WARN] No observations found; exiting.
```

**원인**: attempt VIEW에 데이터 없음 또는 LOOKBACK_DAYS 너무 짧음

**해결**:
```sql
-- 1. attempt VIEW 데이터 확인
SELECT 
    COUNT(*) AS total_attempts,
    MIN(completed_at) AS earliest,
    MAX(completed_at) AS latest,
    COUNT(DISTINCT student_id) AS unique_users,
    COUNT(DISTINCT question_id) AS unique_items
FROM attempt
WHERE completed_at >= NOW() - INTERVAL '60 days';

-- 2. 날짜 범위 확인
SELECT 
    DATE(completed_at) AS date,
    COUNT(*) AS attempts
FROM attempt
WHERE completed_at >= NOW() - INTERVAL '60 days'
GROUP BY DATE(completed_at)
ORDER BY date DESC
LIMIT 10;
```

**환경 변수 조정**:
```bash
# LOOKBACK_DAYS 증가
kubectl -n seedtest set env cronjob/calibrate-irt-weekly \
  MIRT_LOOKBACK_DAYS=90

# 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o yaml | grep MIRT_LOOKBACK_DAYS
```

---

### 오류 5: No anchor items found

**로그**:
```
[INFO] Loading anchor items from question.meta...
[INFO] Loaded 0 anchors/seeds from question.meta
[WARN] No anchor items found; proceeding without anchors
```

**원인**: 앵커 문항 태그 없음

**해결**:
```bash
# 1. 앵커 문항 태깅
python -m apps.seedtest_api.jobs.tag_anchor_items --max-candidates 50

# 2. 검증
python -c "
from apps.seedtest_api.services.db import get_session
from sqlalchemy import text

with get_session() as session:
    result = session.execute(text('''
        SELECT COUNT(*) FROM question 
        WHERE meta->'tags' @> '[\"anchor\"]'::jsonb
    '''))
    print(f'Anchor items: {result.fetchone()[0]}')
"

# 3. SQL로 직접 확인
psql $DATABASE_URL -c "
SELECT 
    id,
    meta->'tags' AS tags,
    meta->'irt' AS irt_params
FROM question
WHERE meta->'tags' @> '[\"anchor\"]'::jsonb
LIMIT 10;
"
```

---

### 오류 6: R IRT service timeout

**로그**:
```
[INFO] Calling R IRT service...
[ERROR] R IRT service call failed: Timeout after 60 seconds
```

**원인**: 관측 데이터가 너무 많거나 R 서비스 성능 문제

**해결**:
```bash
# 1. Timeout 증가
kubectl -n seedtest set env cronjob/calibrate-irt-weekly \
  R_IRT_TIMEOUT_SECS=300

# 2. 관측 수 제한
kubectl -n seedtest set env cronjob/calibrate-irt-weekly \
  MIRT_MAX_OBS=100000

# 3. R IRT 서비스 리소스 확인
kubectl -n seedtest top pods -l app=r-irt-plumber

# 4. R IRT 서비스 리소스 증가
kubectl -n seedtest set resources deployment r-irt-plumber \
  --requests=cpu=1000m,memory=2Gi \
  --limits=cpu=4000m,memory=8Gi
```

---

### 오류 7: ImagePullBackOff

**로그**:
```bash
kubectl -n seedtest get pods -l job-name=calibrate-irt-test-*
# STATUS: ImagePullBackOff
```

**원인**: 이미지가 존재하지 않거나 접근 권한 없음

**해결**:
```bash
# 1. Pod 상세 확인
kubectl -n seedtest describe pod -l job-name=calibrate-irt-test-*

# 2. 이미지 확인
gcloud container images list --repository=asia-northeast3-docker.pkg.dev/univprepai/seedtest

# 3. 최신 이미지 태그 확인
gcloud container images list-tags \
  asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api \
  --limit=5

# 4. CronJob 이미지 업데이트
kubectl -n seedtest set image cronjob/calibrate-irt-weekly \
  calibrate-irt=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:<correct-tag>

# 5. 새 Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)
```

---

## 🔍 디버깅 명령어

### Job 상태 확인

```bash
# Job 목록
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -10

# 특정 Job 상세
kubectl -n seedtest describe job calibrate-irt-test-<timestamp>

# Job 상태 요약
kubectl -n seedtest get job calibrate-irt-test-<timestamp> -o jsonpath='{.status}'
```

### Pod 상태 확인

```bash
# Pod 목록
kubectl -n seedtest get pods -l job-name=calibrate-irt-test-<timestamp>

# Pod 상세
kubectl -n seedtest describe pod -l job-name=calibrate-irt-test-<timestamp>

# Pod 이벤트
kubectl -n seedtest get events --sort-by=.metadata.creationTimestamp | grep calibrate-irt
```

### 로그 확인

```bash
# 메인 컨테이너 로그
kubectl -n seedtest logs job/calibrate-irt-test-<timestamp> -c calibrate-irt

# Cloud SQL Proxy 로그
kubectl -n seedtest logs job/calibrate-irt-test-<timestamp> -c cloud-sql-proxy

# 모든 컨테이너 로그
kubectl -n seedtest logs job/calibrate-irt-test-<timestamp> --all-containers=true

# 이전 로그 (재시작된 경우)
kubectl -n seedtest logs job/calibrate-irt-test-<timestamp> -c calibrate-irt --previous
```

### 환경 변수 확인

```bash
# CronJob 환경 변수
kubectl -n seedtest get cronjob calibrate-irt-weekly -o yaml | grep -A 50 "env:"

# Job 환경 변수
kubectl -n seedtest get job calibrate-irt-test-<timestamp> -o yaml | grep -A 50 "env:"

# Pod에서 직접 확인
POD_NAME=$(kubectl -n seedtest get pods -l job-name=calibrate-irt-test-<timestamp> -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest exec $POD_NAME -c calibrate-irt -- env | grep MIRT
```

### Secret 확인

```bash
# Secret 존재 확인
kubectl -n seedtest get secrets | grep -E "seedtest-db|r-irt"

# Secret 상세
kubectl -n seedtest describe secret seedtest-db-credentials

# Secret 값 확인 (주의: 민감 정보)
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d | head -c 30
echo "..."
```

---

## 📊 성공 확인

### Job 완료 확인

```bash
# Job 상태
kubectl -n seedtest get job calibrate-irt-test-<timestamp>
# COMPLETIONS: 1/1

# Pod 상태
kubectl -n seedtest get pods -l job-name=calibrate-irt-test-<timestamp>
# STATUS: Completed

# 최종 로그
kubectl -n seedtest logs job/calibrate-irt-test-<timestamp> -c calibrate-irt --tail=20
# 예상: ✅ IRT calibration completed successfully
```

### 데이터베이스 검증

```sql
-- 1. 최근 calibration 확인
SELECT 
    run_id,
    model_spec->>'model' AS model,
    model_spec->>'n_items' AS n_items,
    model_spec->>'n_users' AS n_users,
    model_spec->>'n_anchors' AS n_anchors,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 2. Item parameters 확인
SELECT 
    COUNT(*) AS item_count,
    AVG((params->>'a')::float) AS avg_discrimination,
    AVG((params->>'b')::float) AS avg_difficulty,
    MAX(fitted_at) AS last_fitted
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 hour';

-- 3. User abilities 확인
SELECT 
    COUNT(*) AS user_count,
    AVG(theta) AS avg_theta,
    STDDEV(theta) AS sd_theta,
    MAX(fitted_at) AS last_fitted
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour';

-- 4. 전체 파이프라인 검증
SELECT 
    'mirt_item_params' AS table_name,
    COUNT(*)::text AS count,
    MAX(fitted_at)::text AS last_update
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 
    'mirt_ability',
    COUNT(*)::text,
    MAX(fitted_at)::text
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 
    'anchor_items',
    COUNT(*)::text,
    'N/A'
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;
```

---

## 🧹 정리

### Job 삭제

```bash
# 특정 Job 삭제
kubectl -n seedtest delete job calibrate-irt-test-<timestamp>

# 완료된 모든 Job 삭제
kubectl -n seedtest delete jobs -l app=calibrate-irt --field-selector status.successful=1

# 실패한 모든 Job 삭제
kubectl -n seedtest delete jobs -l app=calibrate-irt --field-selector status.successful=0
```

### Pod 정리

```bash
# 완료된 Pod 자동 정리 (CronJob 설정)
kubectl -n seedtest patch cronjob calibrate-irt-weekly -p '
{
  "spec": {
    "successfulJobsHistoryLimit": 1,
    "failedJobsHistoryLimit": 2
  }
}'
```

---

## 📚 관련 문서

- **[QUICK_DEPLOY.md](./QUICK_DEPLOY.md)** - 빠른 배포
- **[DEPLOYMENT_COMMANDS.md](./DEPLOYMENT_COMMANDS.md)** - 전체 명령어
- **[INTEGRATION_TEST_GUIDE.md](../../apps/seedtest_api/docs/INTEGRATION_TEST_GUIDE.md)** - 통합 테스트

---

## ✅ 테스트 체크리스트

### Job 실행
- [ ] Job 생성 성공
- [ ] Pod Running 상태
- [ ] 로그 출력 정상

### 로그 확인
- [ ] "Starting IRT calibration" 메시지
- [ ] "Loaded X observations" 메시지
- [ ] "Loaded X anchors" 메시지
- [ ] "Calling R IRT service" 메시지
- [ ] "✅ IRT calibration completed successfully" 메시지

### 데이터베이스 검증
- [ ] mirt_item_params 업데이트
- [ ] mirt_ability 업데이트
- [ ] mirt_fit_meta linking_constants 저장
- [ ] 앵커 문항 태그 확인

---

**최종 업데이트**: 2025-11-02 00:17 KST  
**작성자**: Cascade AI

**다음 단계**: 로그 확인 후 데이터베이스 검증
