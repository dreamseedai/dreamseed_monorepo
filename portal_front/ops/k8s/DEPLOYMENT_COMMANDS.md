# IRT Analytics Pipeline - 배포 명령어

**최종 업데이트**: 2025-11-01  
**네임스페이스**: seedtest

---

## 🚀 빠른 배포 (자동 스크립트)

```bash
# Dry-run으로 미리보기
./portal_front/ops/k8s/deploy-irt-pipeline.sh --dry-run

# 실제 배포
./portal_front/ops/k8s/deploy-irt-pipeline.sh
```

---

## 📋 수동 배포 (단계별)

### 1. ExternalSecret 적용 (R IRT 토큰)

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/r-irt-plumber/externalsecret.yaml
```

**검증**:
```bash
# Secret 생성 확인 (1-2분 소요)
kubectl -n seedtest get secret r-irt-credentials
kubectl -n seedtest describe secret r-irt-credentials
```

---

### 2. IRT Calibration CronJob 배포

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
```

**검증**:
```bash
# CronJob 확인
kubectl -n seedtest get cronjob mirt-calibrate
kubectl -n seedtest describe cronjob mirt-calibrate

# 스케줄 확인
# Expected: "0 3 * * *" (daily at 03:00 UTC)
```

---

### 3. GLMM 매니페스트 배포

```bash
# Scripts ConfigMap
kubectl -n seedtest apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-scripts.yaml

# One-off Job template
kubectl -n seedtest apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-now.yaml

# CronJob
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/glmm-fit-progress.yaml
```

**검증**:
```bash
# CronJob 확인
kubectl -n seedtest get cronjob glmm-fit-progress
# Expected schedule: "30 3 * * 1" (Monday 03:30 UTC)

# ConfigMap 확인
kubectl -n seedtest get configmap glmm-fit-progress-scripts
```

---

### 4. R IRT 서비스 Health Check

```bash
# In-cluster curl test
kubectl -n seedtest run curl-irt --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz
```

**예상 응답**:
```json
{"status": "ok", "service": "r-irt-plumber", "version": "1.0.0"}
```

**실패 시**:
```bash
# R IRT Plumber 상태 확인
kubectl -n seedtest get pods -l app=r-irt-plumber
kubectl -n seedtest logs -l app=r-irt-plumber --tail=50

# 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get endpoints r-irt-plumber
```

---

### 5. One-off IRT Calibration 실행 (테스트)

```bash
# 기존 Job 삭제 (있는 경우)
kubectl -n seedtest delete job calibrate-irt-now --ignore-not-found

# Job 생성
kubectl -n seedtest create -f portal_front/ops/k8s/jobs/calibrate-irt-now.yaml

# 로그 실시간 확인
kubectl -n seedtest logs -f job/calibrate-irt-now
```

**예상 출력**:
```
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 50 anchors/seeds from question.meta
[INFO] Total observations: 12345
[INFO] Model: 2PL, Anchors: 50
[INFO] Calling R IRT service...
[INFO] Linking constants received: ['slope', 'intercept']
Calibration upsert completed: 150 items, 500 abilities
✅ IRT calibration completed successfully
```

**재시도 로직 작동 예시**:
```
[WARN] R IRT service call failed (attempt 1/3): Connection timeout
[INFO] Retrying in 5.0 seconds...
[INFO] Calling R IRT service...
✅ IRT calibration completed successfully
```

---

### 6. One-off GLMM Fit 실행 (테스트)

```bash
# 기존 Job 삭제 (있는 경우)
kubectl -n seedtest delete job glmm-fit-progress-now --ignore-not-found

# Job 생성
kubectl -n seedtest create -f portal_front/ops/k8s/jobs/glmm-fit-progress-now.yaml

# 로그 실시간 확인
kubectl -n seedtest logs -f job/glmm-fit-progress-now
```

**예상 출력**:
```
[INFO] Loading weekly scores for GLMM fitting...
[INFO] Found 500 users with sufficient data
[INFO] Calling R GLMM service...
[INFO] Fixed effects: intercept=0.28, week=0.35
[INFO] Random effects: student_id (2 levels), topic_id (10 levels)
✅ GLMM fit completed successfully
```

---

## 🔍 배포 검증

### CronJobs 확인
```bash
kubectl -n seedtest get cronjobs
```

**예상 출력**:
```
NAME                  SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
mirt-calibrate        0 3 * * *     False     0        12h             1d
glmm-fit-progress     30 3 * * 1    False     0        3d              1d
```

### Secrets 확인
```bash
kubectl -n seedtest get secrets | grep irt
```

**예상 출력**:
```
r-irt-credentials                Opaque               1      1d
```

### Jobs 실행 이력
```bash
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp
```

### 최근 로그 확인
```bash
# IRT Calibration 최근 실행
kubectl -n seedtest logs -l job-name=mirt-calibrate --tail=100 --timestamps

# GLMM Fit 최근 실행
kubectl -n seedtest logs -l job-name=glmm-fit-progress --tail=100 --timestamps
```

---

## 📊 데이터베이스 검증

### IRT Calibration 결과
```sql
-- 최근 calibration 확인
SELECT 
    COUNT(*) AS item_count,
    AVG((params->>'a')::float) AS avg_discrimination,
    AVG((params->>'b')::float) AS avg_difficulty,
    MAX(fitted_at) AS last_fitted
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day';

-- 사용자 능력 확인
SELECT 
    COUNT(*) AS user_count,
    AVG(theta) AS avg_theta,
    STDDEV(theta) AS sd_theta,
    MAX(fitted_at) AS last_fitted
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 day';

-- Linking constants 확인
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 앵커 문항 확인
SELECT COUNT(*) AS anchor_count
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;
```

### GLMM 결과
```sql
-- 최근 GLMM fit 확인
SELECT 
    run_id,
    fixed_effects,
    fit_metrics,
    fitted_at
FROM growth_glmm_meta
ORDER BY fitted_at DESC
LIMIT 5;
```

---

## 🔄 일일 운영

### 매일 아침 체크 (09:00 KST)
```bash
# 1. 어젯밤 Jobs 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -10

# 2. 실패한 Jobs 확인
kubectl -n seedtest get jobs --field-selector status.successful!=1

# 3. 최근 로그 확인
kubectl -n seedtest logs -l job-name=mirt-calibrate --tail=50 --since=12h
```

### 매주 월요일 체크 (10:00 KST)
```bash
# 1. GLMM Job 확인
kubectl -n seedtest get jobs -l app=glmm-fit-progress --sort-by=.metadata.creationTimestamp

# 2. 로그 확인
kubectl -n seedtest logs -l job-name=glmm-fit-progress --tail=100
```

---

## 🐛 문제 해결

### Job 실패 시
```bash
# 1. Job 상태 확인
kubectl -n seedtest describe job <job-name>

# 2. Pod 로그 확인
kubectl -n seedtest logs job/<job-name>

# 3. Pod 상태 확인
kubectl -n seedtest get pods -l job-name=<job-name>
kubectl -n seedtest describe pod <pod-name>

# 4. Job 재실행
kubectl -n seedtest delete job <job-name>
kubectl -n seedtest create -f portal_front/ops/k8s/jobs/<job-name>.yaml
```

### R IRT 서비스 연결 실패
```bash
# 1. 서비스 상태
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get endpoints r-irt-plumber

# 2. Pod 상태
kubectl -n seedtest get pods -l app=r-irt-plumber
kubectl -n seedtest logs -l app=r-irt-plumber --tail=100

# 3. 연결 테스트
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz
```

### Secret 없음
```bash
# 1. ExternalSecret 상태
kubectl -n seedtest get externalsecret r-irt-credentials
kubectl -n seedtest describe externalsecret r-irt-credentials

# 2. SecretStore 확인
kubectl -n seedtest get secretstore gcpsm-secret-store
kubectl -n seedtest describe secretstore gcpsm-secret-store

# 3. GCP Secret Manager 확인
gcloud secrets describe r-irt-internal-token --project=univprepai
```

---

## 🔄 롤백

### CronJob 일시 중지
```bash
# IRT Calibration 중지
kubectl -n seedtest patch cronjob mirt-calibrate -p '{"spec":{"suspend":true}}'

# GLMM Fit 중지
kubectl -n seedtest patch cronjob glmm-fit-progress -p '{"spec":{"suspend":true}}'

# 재개
kubectl -n seedtest patch cronjob mirt-calibrate -p '{"spec":{"suspend":false}}'
kubectl -n seedtest patch cronjob glmm-fit-progress -p '{"spec":{"suspend":false}}'
```

### 전체 삭제
```bash
# CronJobs 삭제
kubectl -n seedtest delete cronjob mirt-calibrate
kubectl -n seedtest delete cronjob glmm-fit-progress

# Jobs 삭제
kubectl -n seedtest delete job -l app=mirt-calibrate
kubectl -n seedtest delete job -l app=glmm-fit-progress

# Secrets 삭제 (주의!)
kubectl -n seedtest delete secret r-irt-credentials
kubectl -n seedtest delete externalsecret r-irt-credentials
```

---

## 📚 관련 문서

- **배포 가이드**: `apps/seedtest_api/docs/DEPLOYMENT_GUIDE_IRT_PIPELINE.md`
- **IRT 가이드**: `apps/seedtest_api/docs/IRT_CALIBRATION_GUIDE.md`
- **GLMM 가이드**: `apps/seedtest_api/docs/R_GLMM_SERVICE_GUIDE.md`
- **전체 로드맵**: `apps/seedtest_api/docs/ADVANCED_ANALYTICS_ROADMAP.md`

---

**배포 스크립트**: `./portal_front/ops/k8s/deploy-irt-pipeline.sh`
