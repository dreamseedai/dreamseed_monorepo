# ExternalSecret 마이그레이션 가이드 - calibrate-irt CronJob

**최종 업데이트**: 2025-11-02 01:29 KST  
**소요 시간**: 15분  
**난이도**: ⭐⭐ 중간

---

## 🎯 목표

calibrate-irt CronJob의 Secret을 수동 관리에서 **External Secrets Operator (ESO)**를 통한 자동 관리로 전환합니다.

---

## 📋 현재 상태 vs 목표 상태

### 현재 (수동 Secret 관리)

```yaml
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: seedtest-db-credentials  # 수동 생성
      key: DATABASE_URL

- name: R_IRT_INTERNAL_TOKEN
  valueFrom:
    secretKeyRef:
      name: r-irt-credentials  # 수동 생성
      key: token
```

### 목표 (ESO 자동 관리)

```yaml
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: calibrate-irt-credentials  # ESO가 자동 생성
      key: DATABASE_URL

- name: R_IRT_INTERNAL_TOKEN
  valueFrom:
    secretKeyRef:
      name: calibrate-irt-credentials  # ESO가 자동 생성
      key: R_IRT_INTERNAL_TOKEN
```

---

## 🔐 Secret 정보 요약

### calibrate-irt CronJob이 사용하는 Secret

| 환경 변수 | 현재 Secret 이름 | 현재 Secret 키 | ESO Secret 이름 | ESO Secret 키 | GCP Secret Manager 경로 |
|----------|----------------|---------------|----------------|--------------|----------------------|
| `DATABASE_URL` | `seedtest-db-credentials` | `DATABASE_URL` | `calibrate-irt-credentials` | `DATABASE_URL` | `seedtest/database-url` |
| `R_IRT_INTERNAL_TOKEN` | `r-irt-credentials` | `token` | `calibrate-irt-credentials` | `R_IRT_INTERNAL_TOKEN` | `r-irt-plumber/token` |

---

## 🚀 마이그레이션 단계

### Step 1: GCP Secret Manager에 Secret 생성 (5분)

#### 1.1 DATABASE_URL 생성

```bash
# 현재 Secret 값 추출
CURRENT_DB_URL=$(kubectl -n seedtest get secret seedtest-db-credentials \
  -o jsonpath='{.data.DATABASE_URL}' | base64 -d)

echo "Current DATABASE_URL: ${CURRENT_DB_URL:0:30}..."

# GCP Secret Manager에 저장
echo -n "$CURRENT_DB_URL" | gcloud secrets create seedtest-database-url \
  --data-file=- \
  --project=univprepai \
  --replication-policy=automatic

# 또는 기존 Secret 업데이트
echo -n "$CURRENT_DB_URL" | gcloud secrets versions add seedtest-database-url \
  --data-file=- \
  --project=univprepai
```

#### 1.2 R_IRT_INTERNAL_TOKEN 생성

```bash
# 현재 Secret 값 추출 (optional이므로 없을 수 있음)
CURRENT_TOKEN=$(kubectl -n seedtest get secret r-irt-credentials \
  -o jsonpath='{.data.token}' 2>/dev/null | base64 -d)

if [ -n "$CURRENT_TOKEN" ]; then
  echo "Current R_IRT_INTERNAL_TOKEN: ${CURRENT_TOKEN:0:20}..."
  
  # GCP Secret Manager에 저장
  echo -n "$CURRENT_TOKEN" | gcloud secrets create r-irt-plumber-token \
    --data-file=- \
    --project=univprepai \
    --replication-policy=automatic
else
  echo "R_IRT_INTERNAL_TOKEN not found (optional)"
fi
```

#### 1.3 Secret 확인

```bash
# GCP Secret Manager에서 확인
gcloud secrets list --project=univprepai | grep -E "seedtest-database|r-irt-plumber"

# 예상 출력:
# seedtest-database-url    2025-11-02T05:29:00  automatic  -
# r-irt-plumber-token      2025-11-02T05:29:30  automatic  -
```

---

### Step 2: ExternalSecret 배포 (2분)

#### 2.1 ExternalSecret 매니페스트 확인

```bash
# 파일 확인
cat portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml
```

**주요 내용**:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: calibrate-irt-credentials
  namespace: seedtest
spec:
  refreshInterval: "1h"
  secretStoreRef:
    name: gcp-secret-store
    kind: ClusterSecretStore
  target:
    name: calibrate-irt-credentials
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: seedtest/database-url
    
    - secretKey: R_IRT_INTERNAL_TOKEN
      remoteRef:
        key: r-irt-plumber/token
```

#### 2.2 ExternalSecret 배포

```bash
# ExternalSecret 배포
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# 상태 확인 (1-2분 대기)
kubectl -n seedtest get externalsecret calibrate-irt-credentials

# 예상 출력:
# NAME                          STORE              REFRESH   STATUS
# calibrate-irt-credentials     gcp-secret-store   1h        SecretSynced
```

#### 2.3 생성된 Secret 확인

```bash
# Secret 생성 확인
kubectl -n seedtest get secret calibrate-irt-credentials

# Secret 상세 확인
kubectl -n seedtest describe secret calibrate-irt-credentials

# 예상 출력:
# Name:         calibrate-irt-credentials
# Namespace:    seedtest
# Type:         Opaque
# 
# Data
# ====
# DATABASE_URL:            82 bytes
# R_IRT_INTERNAL_TOKEN:    32 bytes
```

---

### Step 3: CronJob 패치 적용 (3분)

#### 3.1 패치 파일 확인

```bash
# 패치 파일 확인
cat portal_front/ops/k8s/patches/calibrate-irt-externalsecret-patch.yaml
```

**패치 내용**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: calibrate-irt-weekly
  namespace: seedtest
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: calibrate-irt
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: calibrate-irt-credentials  # ✅ 변경됨
                  key: DATABASE_URL
            
            - name: R_IRT_INTERNAL_TOKEN
              valueFrom:
                secretKeyRef:
                  name: calibrate-irt-credentials  # ✅ 변경됨
                  key: R_IRT_INTERNAL_TOKEN
```

#### 3.2 패치 적용

```bash
# Strategic merge patch 적용
kubectl -n seedtest patch cronjob calibrate-irt-weekly \
  --type strategic \
  --patch-file portal_front/ops/k8s/patches/calibrate-irt-externalsecret-patch.yaml

# 또는 직접 패치
kubectl -n seedtest patch cronjob calibrate-irt-weekly \
  --type strategic \
  --patch "$(cat portal_front/ops/k8s/patches/calibrate-irt-externalsecret-patch.yaml)"
```

#### 3.3 패치 확인

```bash
# CronJob 환경 변수 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o yaml | grep -A 10 "env:"

# 예상 출력:
# env:
# - name: DATABASE_URL
#   valueFrom:
#     secretKeyRef:
#       key: DATABASE_URL
#       name: calibrate-irt-credentials  # ✅ 변경됨
# - name: R_IRT_INTERNAL_TOKEN
#   valueFrom:
#     secretKeyRef:
#       key: R_IRT_INTERNAL_TOKEN
#       name: calibrate-irt-credentials  # ✅ 변경됨
```

---

### Step 4: 테스트 실행 (5분)

#### 4.1 테스트 Job 생성

```bash
# CronJob에서 즉시 Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-eso-test-$(date +%s)

# Job 목록 확인
kubectl -n seedtest get jobs | grep calibrate-irt-eso-test
```

#### 4.2 로그 확인

```bash
# Pod 이름 확인
POD_NAME=$(kubectl -n seedtest get pods -l job-name --sort-by=.metadata.creationTimestamp | grep calibrate-irt-eso-test | tail -1 | awk '{print $1}')

# 로그 확인
kubectl -n seedtest logs -f $POD_NAME -c calibrate-irt

# 예상 로그:
# Starting IRT calibration...
# PYTHONPATH: /app:/app/apps
# Found /app/apps/seedtest_api/jobs/mirt_calibrate.py, using apps path
# [INFO] Loading attempt data (lookback=60 days)...
# [INFO] Loaded 50000 attempts
# [INFO] Calling R IRT service...
# ✅ IRT calibration completed successfully
```

#### 4.3 데이터베이스 검증

```sql
-- mirt_fit_meta 확인
SELECT run_id, model, n_items, n_students, fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- mirt_item_params 확인
SELECT COUNT(*) AS calibrated_items
FROM mirt_item_params
WHERE updated_at >= NOW() - INTERVAL '1 hour';
```

---

## ✅ 검증 체크리스트

### GCP Secret Manager
- [ ] `seedtest-database-url` Secret 생성 확인
- [ ] `r-irt-plumber-token` Secret 생성 확인 (optional)
- [ ] Secret 값이 올바른지 확인

### ExternalSecret
- [ ] ExternalSecret 배포 확인
- [ ] ExternalSecret 상태가 `SecretSynced` 확인
- [ ] Kubernetes Secret `calibrate-irt-credentials` 생성 확인
- [ ] Secret에 `DATABASE_URL`, `R_IRT_INTERNAL_TOKEN` 키 존재 확인

### CronJob
- [ ] CronJob 패치 적용 확인
- [ ] 환경 변수가 `calibrate-irt-credentials` Secret 참조 확인
- [ ] 테스트 Job 실행 성공 확인
- [ ] 로그에 에러 없음 확인
- [ ] 데이터베이스에 결과 저장 확인

---

## 🔄 롤백 방법

문제가 발생하면 이전 상태로 롤백할 수 있습니다:

```bash
# 원본 CronJob 재배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 또는 수동 패치로 롤백
kubectl -n seedtest patch cronjob calibrate-irt-weekly \
  --type strategic \
  --patch '
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: calibrate-irt
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: seedtest-db-credentials
                  key: DATABASE_URL
            - name: R_IRT_INTERNAL_TOKEN
              valueFrom:
                secretKeyRef:
                  name: r-irt-credentials
                  key: token
'
```

---

## 🐛 문제 해결

### 문제 1: ExternalSecret 상태가 SecretSyncedError

**증상**:
```bash
kubectl -n seedtest get externalsecret calibrate-irt-credentials
# STATUS: SecretSyncedError
```

**원인**: GCP Secret Manager에 Secret이 없거나 권한 부족

**해결**:
```bash
# GCP Secret 확인
gcloud secrets list --project=univprepai | grep -E "seedtest-database|r-irt-plumber"

# Secret이 없으면 생성 (Step 1 참조)

# 권한 확인
gcloud secrets get-iam-policy seedtest-database-url --project=univprepai
```

---

### 문제 2: Pod에서 DATABASE_URL 환경 변수 없음

**증상**:
```bash
kubectl -n seedtest logs <pod> -c calibrate-irt
# Error: DATABASE_URL is not set
```

**원인**: Secret이 생성되지 않았거나 키 이름 불일치

**해결**:
```bash
# Secret 확인
kubectl -n seedtest get secret calibrate-irt-credentials -o yaml

# Secret 키 확인
kubectl -n seedtest get secret calibrate-irt-credentials \
  -o jsonpath='{.data}' | jq 'keys'

# 예상 출력: ["DATABASE_URL", "R_IRT_INTERNAL_TOKEN"]
```

---

### 문제 3: GCP Secret Manager 접근 권한 부족

**증상**:
```
Error: Permission denied on secret seedtest-database-url
```

**원인**: ESO Service Account에 Secret Manager 접근 권한 없음

**해결**:
```bash
# Service Account 확인
kubectl -n seedtest get secret eso-gcp-credentials -o yaml

# GCP IAM 권한 추가
gcloud projects add-iam-policy-binding univprepai \
  --member="serviceAccount:<sa-email>" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 📊 마이그레이션 전후 비교

| 항목 | 마이그레이션 전 | 마이그레이션 후 |
|------|---------------|---------------|
| **Secret 관리** | 수동 kubectl create | ESO 자동 동기화 |
| **Secret 업데이트** | 수동 kubectl edit | GCP Secret Manager 업데이트 |
| **Secret 이름** | `seedtest-db-credentials`, `r-irt-credentials` | `calibrate-irt-credentials` |
| **Secret 키** | `DATABASE_URL`, `token` | `DATABASE_URL`, `R_IRT_INTERNAL_TOKEN` |
| **동기화 주기** | 수동 | 1시간마다 자동 |
| **버전 관리** | 없음 | GCP Secret Manager 버전 관리 |
| **감사 로그** | 제한적 | GCP Cloud Audit Logs |

---

## 🎯 이점

### 1. 자동화
- GCP Secret Manager에서 Secret 업데이트 시 자동 동기화
- 수동 kubectl 명령 불필요

### 2. 보안
- Secret이 Git에 저장되지 않음
- GCP IAM으로 접근 제어
- 버전 관리 및 감사 로그

### 3. 일관성
- 모든 환경에서 동일한 Secret 소스 사용
- Secret 이름 표준화

### 4. 유지보수
- Secret 업데이트가 간단함
- 롤백이 쉬움 (GCP Secret Manager 버전 관리)

---

## 📚 관련 문서

- **[SECRET_SETUP_GUIDE.md](./SECRET_SETUP_GUIDE.md)** - 기본 Secret 설정
- **[COMPLETE_DEPLOYMENT_GUIDE.md](./COMPLETE_DEPLOYMENT_GUIDE.md)** - 전체 배포 가이드
- **[externalsecret-calibrate-irt.yaml](./secrets/externalsecret-calibrate-irt.yaml)** - ExternalSecret 매니페스트
- **[calibrate-irt-externalsecret-patch.yaml](./patches/calibrate-irt-externalsecret-patch.yaml)** - CronJob 패치

---

## 🎉 완료!

calibrate-irt CronJob이 이제 External Secrets Operator를 통해 GCP Secret Manager에서 자동으로 Secret을 가져옵니다.

**다음 단계**: 다른 CronJob들도 동일한 방식으로 마이그레이션

---

**최종 업데이트**: 2025-11-02 01:29 KST  
**작성자**: Cascade AI  
**상태**: ✅ 마이그레이션 가이드 완성
