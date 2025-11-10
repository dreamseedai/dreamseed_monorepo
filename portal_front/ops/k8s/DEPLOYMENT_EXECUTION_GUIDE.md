# IRT Analytics Pipeline - 배포 실행 가이드

**최종 업데이트**: 2025-11-02 00:12 KST  
**상태**: ✅ 즉시 실행 가능

---

## 🚀 빠른 배포 (3단계)

사용자께서 제공하신 명령어로 즉시 배포 가능합니다:

```bash
# 1. ExternalSecret 설정
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# 2. Secret 확인 (1-2분 대기)
kubectl -n seedtest get secret calibrate-irt-credentials

# 3. CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml
```

---

## 📋 상세 배포 단계

### Phase 1: 사전 준비 (5분)

#### 1.1 GCP Secret Manager에 시크릿 생성

```bash
# DATABASE_URL 생성
gcloud secrets create seedtest-database-url \
  --data-file=- \
  --project=univprepai <<EOF
postgresql://user:password@host:5432/seedtest
EOF

# R IRT 토큰 생성 (선택)
gcloud secrets create r-irt-plumber-token \
  --data-file=- \
  --project=univprepai <<EOF
your-secret-token-here
EOF

# 확인
gcloud secrets list --project=univprepai | grep -E "seedtest-database-url|r-irt-plumber-token"
```

#### 1.2 GCP Service Account 설정

```bash
# Service Account 생성
gcloud iam service-accounts create eso-secret-accessor \
  --display-name="External Secrets Operator Secret Accessor" \
  --project=univprepai

# Secret Manager 접근 권한 부여
gcloud projects add-iam-policy-binding univprepai \
  --member="serviceAccount:eso-secret-accessor@univprepai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Service Account Key 생성
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=eso-secret-accessor@univprepai.iam.gserviceaccount.com \
  --project=univprepai

# Kubernetes Secret 생성
kubectl -n seedtest create secret generic eso-gcp-credentials \
  --from-file=secret-access-key=sa-key.json

# 정리
rm sa-key.json
```

#### 1.3 ClusterSecretStore 생성 (한 번만)

```bash
# ClusterSecretStore 확인
kubectl get clustersecretstore gcp-secret-store

# 없으면 생성
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: gcp-secret-store
spec:
  provider:
    gcpsm:
      projectId: univprepai
      auth:
        secretRef:
          secretAccessKeySecretRef:
            name: eso-gcp-credentials
            key: secret-access-key
            namespace: seedtest
EOF
```

---

### Phase 2: ExternalSecret 배포 (2분)

#### 2.1 ExternalSecret 적용

```bash
# ExternalSecret 배포
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# 상태 확인
kubectl -n seedtest get externalsecret calibrate-irt-credentials
```

**예상 출력**:
```
NAME                         STORE              REFRESH INTERVAL   STATUS   READY
calibrate-irt-credentials    gcp-secret-store   1h                 SecretSynced   True
```

#### 2.2 Secret 생성 확인

```bash
# Secret 생성 확인 (1-2분 대기)
kubectl -n seedtest get secret calibrate-irt-credentials

# Secret 내용 확인
kubectl -n seedtest describe secret calibrate-irt-credentials
```

**예상 출력**:
```
Name:         calibrate-irt-credentials
Namespace:    seedtest
Type:         Opaque

Data
====
DATABASE_URL:           82 bytes
R_IRT_INTERNAL_TOKEN:   32 bytes
```

#### 2.3 Secret 값 검증 (선택)

```bash
# DATABASE_URL 확인 (첫 20자만)
kubectl -n seedtest get secret calibrate-irt-credentials \
  -o jsonpath='{.data.DATABASE_URL}' | base64 -d | head -c 20
# 예상: postgresql://user:

# R_IRT_INTERNAL_TOKEN 확인 (첫 10자만)
kubectl -n seedtest get secret calibrate-irt-credentials \
  -o jsonpath='{.data.R_IRT_INTERNAL_TOKEN}' | base64 -d | head -c 10
```

---

### Phase 3: CronJob 배포 (1분)

#### 3.1 CronJob 배포

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml

# 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly
```

**예상 출력**:
```
NAME                   SCHEDULE    SUSPEND   ACTIVE   LAST SCHEDULE   AGE
calibrate-irt-weekly   0 3 * * *   False     0        <none>          10s
```

#### 3.2 CronJob 상세 확인

```bash
# 상세 정보
kubectl -n seedtest describe cronjob calibrate-irt-weekly

# 환경 변수 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o yaml | grep -A 30 "env:"
```

---

### Phase 4: 테스트 실행 (5-10분)

#### 4.1 One-off Job 생성

```bash
# 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)

# Job 목록 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -5
```

#### 4.2 로그 실시간 확인

```bash
# 최신 Job의 로그 확인
JOB_NAME=$(kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl -n seedtest logs -f job/$JOB_NAME
```

**예상 로그**:
```
Waiting for Cloud SQL Proxy to be ready...
Starting IRT calibration...
PYTHONPATH: /app:/app/apps
Looking for seedtest_api:
Found /app/apps/seedtest_api/jobs/mirt_calibrate.py, using apps path
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 50 anchors/seeds from question.meta
[INFO] Total observations: 12345
[INFO] Model: 2PL, Anchors: 50
[INFO] Calling R IRT service...
[INFO] Linking constants received: {'slope': 1.02, 'intercept': 0.05}
Calibration upsert completed: 150 items, 500 abilities
✅ IRT calibration completed successfully
```

#### 4.3 Job 상태 확인

```bash
# Job 완료 확인
kubectl -n seedtest get job $JOB_NAME

# Pod 상태 확인
kubectl -n seedtest get pods -l job-name=$JOB_NAME

# 실패 시 디버깅
kubectl -n seedtest describe job $JOB_NAME
kubectl -n seedtest logs job/$JOB_NAME --all-containers=true
```

---

### Phase 5: 데이터베이스 검증 (2분)

#### 5.1 Calibration 결과 확인

```sql
-- mirt_item_params 확인
SELECT 
    COUNT(*) AS item_count,
    AVG((params->>'a')::float) AS avg_discrimination,
    AVG((params->>'b')::float) AS avg_difficulty,
    MAX(fitted_at) AS last_fitted
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 hour';

-- 예상 결과
-- item_count | avg_discrimination | avg_difficulty | last_fitted
-- -----------|-------------------|----------------|-------------
-- 150        | 1.15              | 0.05           | 2025-11-02 04:15:23
```

#### 5.2 사용자 능력 확인

```sql
-- mirt_ability 확인
SELECT 
    COUNT(*) AS user_count,
    AVG(theta) AS avg_theta,
    STDDEV(theta) AS sd_theta,
    MAX(fitted_at) AS last_fitted
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour';

-- 예상 결과
-- user_count | avg_theta | sd_theta | last_fitted
-- -----------|-----------|----------|-------------
-- 500        | 0.02      | 0.98     | 2025-11-02 04:15:23
```

#### 5.3 Linking constants 확인

```sql
-- mirt_fit_meta 확인
SELECT 
    run_id,
    model_spec->>'model' AS model,
    model_spec->>'n_items' AS n_items,
    model_spec->>'n_users' AS n_users,
    model_spec->>'n_anchors' AS n_anchors,
    model_spec->'linking_constants' AS linking_constants,
    metrics->>'aic' AS aic,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 예상 결과
-- run_id                   | model | n_items | n_users | n_anchors | linking_constants              | aic      | fitted_at
-- -------------------------|-------|---------|---------|-----------|--------------------------------|----------|----------
-- fit-2025-11-02T04:15:23Z | 2PL   | 150     | 500     | 50        | {"slope":1.02,"intercept":0.05}| 12345.67 | 2025-11-02 04:15:23
```

#### 5.4 앵커 문항 확인

```sql
-- 앵커 문항 확인
SELECT 
    COUNT(*) AS anchor_count,
    AVG((meta->'irt'->>'a')::float) AS avg_anchor_discrimination,
    AVG((meta->'irt'->>'b')::float) AS avg_anchor_difficulty
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;

-- 예상 결과
-- anchor_count | avg_anchor_discrimination | avg_anchor_difficulty
-- -------------|---------------------------|----------------------
-- 50           | 1.18                      | 0.03
```

---

## 🔍 배포 검증 체크리스트

### Phase 1: 사전 준비 ✅
- [ ] GCP Secret Manager에 시크릿 생성
  - [ ] `seedtest-database-url`
  - [ ] `r-irt-plumber-token` (선택)
- [ ] GCP Service Account 생성 및 권한 부여
- [ ] Kubernetes Secret `eso-gcp-credentials` 생성
- [ ] ClusterSecretStore `gcp-secret-store` 생성

### Phase 2: ExternalSecret ✅
- [ ] ExternalSecret 배포 성공
- [ ] ExternalSecret 상태 `SecretSynced`
- [ ] Kubernetes Secret `calibrate-irt-credentials` 생성
- [ ] Secret에 `DATABASE_URL`, `R_IRT_INTERNAL_TOKEN` 포함

### Phase 3: CronJob ✅
- [ ] CronJob `calibrate-irt-weekly` 배포
- [ ] 스케줄 확인: `0 3 * * *` (매일 03:00 UTC)
- [ ] 환경 변수 확인
  - [ ] `MIRT_LOOKBACK_DAYS=60`
  - [ ] `MIRT_MAX_RETRIES=3`
  - [ ] `R_IRT_TIMEOUT_SECS=60`

### Phase 4: 테스트 실행 ✅
- [ ] One-off Job 생성 성공
- [ ] Job 완료 (Completed)
- [ ] 로그에 에러 없음
- [ ] "IRT calibration completed successfully" 메시지 확인

### Phase 5: 데이터베이스 검증 ✅
- [ ] `mirt_item_params` 업데이트 (150+ items)
- [ ] `mirt_ability` 업데이트 (500+ users)
- [ ] `mirt_fit_meta` linking_constants 저장
- [ ] 앵커 문항 태그 확인 (50+ items)

---

## 🐛 문제 해결

### 문제 1: ExternalSecret 상태가 `SecretSyncedError`

**증상**:
```bash
kubectl -n seedtest get externalsecret calibrate-irt-credentials
# STATUS: SecretSyncedError
```

**원인**:
- GCP Secret Manager에 시크릿 없음
- Service Account 권한 부족
- ClusterSecretStore 설정 오류

**해결**:
```bash
# 1. ExternalSecret 상세 확인
kubectl -n seedtest describe externalsecret calibrate-irt-credentials

# 2. ClusterSecretStore 확인
kubectl get clustersecretstore gcp-secret-store -o yaml

# 3. GCP Secret 확인
gcloud secrets list --project=univprepai | grep seedtest-database-url

# 4. Service Account 권한 확인
gcloud projects get-iam-policy univprepai \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:eso-secret-accessor@univprepai.iam.gserviceaccount.com"
```

---

### 문제 2: Secret 생성되지 않음

**증상**:
```bash
kubectl -n seedtest get secret calibrate-irt-credentials
# Error from server (NotFound): secrets "calibrate-irt-credentials" not found
```

**원인**:
- ExternalSecret이 아직 처리 중
- ESO가 설치되지 않음

**해결**:
```bash
# 1. ExternalSecret 상태 확인
kubectl -n seedtest get externalsecret

# 2. ESO Pod 확인
kubectl -n external-secrets get pods

# 3. ESO 로그 확인
kubectl -n external-secrets logs -l app.kubernetes.io/name=external-secrets --tail=50

# 4. 수동 Secret 생성 (임시)
kubectl -n seedtest create secret generic calibrate-irt-credentials \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/seedtest' \
  --from-literal=R_IRT_INTERNAL_TOKEN='token'
```

---

### 문제 3: Job 실행 실패 (ImagePullBackOff)

**증상**:
```bash
kubectl -n seedtest get pods -l job-name=$JOB_NAME
# STATUS: ImagePullBackOff
```

**원인**:
- 이미지가 존재하지 않음
- 이미지 레지스트리 접근 권한 없음

**해결**:
```bash
# 1. 이미지 확인
gcloud container images list --repository=asia-northeast3-docker.pkg.dev/univprepai/seedtest

# 2. 최신 이미지 태그 확인
gcloud container images list-tags \
  asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api \
  --limit=5

# 3. CronJob 이미지 업데이트
kubectl -n seedtest set image cronjob/calibrate-irt-weekly \
  calibrate-irt=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:<new-tag>
```

---

### 문제 4: Job 실행 실패 (CrashLoopBackOff)

**증상**:
```bash
kubectl -n seedtest logs job/$JOB_NAME
# Error: mirt_calibrate.py not found in expected locations
```

**원인**:
- 이미지에 코드가 없음
- 경로 설정 오류

**해결**:
```bash
# 1. Pod 내부 확인
POD_NAME=$(kubectl -n seedtest get pods -l job-name=$JOB_NAME -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest exec -it $POD_NAME -- /bin/sh

# Pod 내부에서
find /app -name "mirt_calibrate.py"
ls -la /app/apps/seedtest_api/jobs/

# 2. PYTHONPATH 확인
kubectl -n seedtest logs job/$JOB_NAME | grep PYTHONPATH

# 3. 이미지 재빌드 필요 시
# (CI/CD 파이프라인에서 재빌드)
```

---

### 문제 5: R IRT 서비스 연결 실패

**증상**:
```bash
kubectl -n seedtest logs job/$JOB_NAME
# [ERROR] R IRT service call failed after 3 attempts: Connection refused
```

**원인**:
- R IRT Plumber 서비스 미배포
- 네트워크 문제

**해결**:
```bash
# 1. R IRT 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 2. Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz

# 3. R IRT 로그 확인
kubectl -n seedtest logs -l app=r-irt-plumber --tail=50

# 4. 서비스 재시작
kubectl -n seedtest rollout restart deployment r-irt-plumber
```

---

## 📊 모니터링

### CloudWatch/Stackdriver 메트릭

```yaml
# 모니터링할 메트릭
- cronjob_success_count{job="calibrate-irt-weekly"}
- cronjob_duration_seconds{job="calibrate-irt-weekly"}
- cronjob_failure_count{job="calibrate-irt-weekly"}
```

### 알림 설정

```yaml
# AlertManager 규칙
- alert: IRTCalibrationFailed
  expr: cronjob_failure_count{job="calibrate-irt-weekly"} > 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "IRT Calibration job failed"
    description: "calibrate-irt-weekly job has failed {{ $value }} times"
```

---

## 🔄 일일 운영

### 매일 아침 체크 (09:00 KST)

```bash
# 1. 어젯밤 Job 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -10

# 2. 최근 로그 확인
kubectl -n seedtest logs -l job-name=calibrate-irt-weekly --tail=100 --since=12h

# 3. DB 확인
psql $DATABASE_URL -c "
SELECT 
    'mirt_item_params' AS table_name,
    COUNT(*) AS count,
    MAX(fitted_at) AS last_update
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day'
UNION ALL
SELECT 
    'mirt_ability',
    COUNT(*),
    MAX(fitted_at)
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 day';
"
```

---

## ✅ 배포 완료 확인

### 성공 기준
- [ ] ExternalSecret 상태 `SecretSynced`
- [ ] Kubernetes Secret 생성 및 값 확인
- [ ] CronJob 배포 성공
- [ ] One-off Job 완료 (Completed)
- [ ] 로그에 "IRT calibration completed successfully"
- [ ] mirt_item_params 업데이트 (150+ items)
- [ ] mirt_ability 업데이트 (500+ users)
- [ ] linking_constants 저장

### 최종 검증 명령어

```bash
# 전체 파이프라인 검증
kubectl -n seedtest get externalsecret,secret,cronjob,job -l app=calibrate-irt

# 데이터베이스 검증
psql $DATABASE_URL <<EOF
SELECT 'ExternalSecret' AS component, 'OK' AS status
UNION ALL
SELECT 'mirt_item_params', CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'FAIL' END FROM mirt_item_params WHERE fitted_at >= NOW() - INTERVAL '1 day'
UNION ALL
SELECT 'mirt_ability', CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'FAIL' END FROM mirt_ability WHERE fitted_at >= NOW() - INTERVAL '1 day'
UNION ALL
SELECT 'linking_constants', CASE WHEN model_spec->'linking_constants' IS NOT NULL THEN 'OK' ELSE 'FAIL' END FROM mirt_fit_meta ORDER BY fitted_at DESC LIMIT 1;
EOF
```

---

**최종 업데이트**: 2025-11-02 00:12 KST  
**작성자**: Cascade AI  
**상태**: ✅ 즉시 실행 가능

**다음 단계**: 위 3단계 명령어 실행
