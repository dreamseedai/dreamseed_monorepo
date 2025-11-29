# Secret 설정 가이드 - IRT Analytics Pipeline

**최종 업데이트**: 2025-11-02 00:38 KST  
**소요 시간**: 2분  
**난이도**: ⭐ 쉬움

---

## 🔐 필수 Secret 목록

IRT Analytics Pipeline 배포를 위해 다음 2개의 Secret이 필요합니다:

1. **seedtest-db-credentials** - 데이터베이스 연결 정보
2. **r-irt-credentials** - R IRT Plumber 인증 토큰 (선택)

---

## 🚀 빠른 설정 (2분)

### Step 1: 데이터베이스 Secret 생성

```bash
# DATABASE_URL 형식: postgresql://user:password@host:port/database
# Cloud SQL Proxy 사용 시 host는 localhost여야 함

kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:password@localhost:5432/seedtest'
```

**예시**:
```bash
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://seedtest_user:mySecurePassword123@localhost:5432/seedtest'
```

---

### Step 2: R IRT 토큰 Secret 생성 (선택)

```bash
# ⚠️ 중요: <YOUR_R_IRT_INTERNAL_TOKEN>을 실제 토큰 값으로 교체하세요

kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='실제-토큰-값-여기'
```

**예시**:
```bash
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='mySecretToken123456'
```

**참고**: R IRT Plumber에서 인증이 필요하지 않으면 이 Secret은 선택 사항입니다.

---

## ✅ Secret 확인

### 생성 확인

```bash
# Secret 목록 확인
kubectl -n seedtest get secrets | grep -E "seedtest-db|r-irt"

# 예상 출력:
# seedtest-db-credentials   Opaque   1      10s
# r-irt-credentials         Opaque   1      5s
```

### Secret 상세 확인

```bash
# seedtest-db-credentials 상세
kubectl -n seedtest describe secret seedtest-db-credentials

# r-irt-credentials 상세
kubectl -n seedtest describe secret r-irt-credentials
```

**예상 출력**:
```
Name:         seedtest-db-credentials
Namespace:    seedtest
Type:         Opaque

Data
====
DATABASE_URL:  82 bytes
```

### Secret 값 확인 (주의: 민감 정보)

```bash
# DATABASE_URL 확인 (첫 30자만)
kubectl -n seedtest get secret seedtest-db-credentials \
  -o jsonpath='{.data.DATABASE_URL}' | base64 -d | head -c 30
echo "..."

# 예상 출력: postgresql://seedtest_user:...

# R IRT 토큰 확인 (첫 10자만)
kubectl -n seedtest get secret r-irt-credentials \
  -o jsonpath='{.data.token}' | base64 -d | head -c 10
echo "..."

# 예상 출력: mySecretTo...
```

---

## 🔄 Secret 업데이트

### 방법 1: 삭제 후 재생성 (권장)

```bash
# 1. 기존 Secret 삭제
kubectl -n seedtest delete secret seedtest-db-credentials

# 2. 새로운 값으로 재생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://new-user:new-password@localhost:5432/seedtest'
```

### 방법 2: kubectl edit (고급)

```bash
# Secret 편집 (base64 인코딩 필요)
kubectl -n seedtest edit secret seedtest-db-credentials

# 또는 patch 사용
kubectl -n seedtest patch secret seedtest-db-credentials \
  -p '{"data":{"DATABASE_URL":"'$(echo -n 'postgresql://new-url' | base64)'"}}'
```

---

## 🛠️ 문제 해결

### 문제 1: Secret 이미 존재

**증상**:
```
Error from server (AlreadyExists): secrets "seedtest-db-credentials" already exists
```

**해결**:
```bash
# 기존 Secret 삭제 후 재생성
kubectl -n seedtest delete secret seedtest-db-credentials
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://...'
```

---

### 문제 2: DATABASE_URL 형식 오류

**올바른 형식**:
```
postgresql://user:password@host:port/database
```

**Cloud SQL Proxy 사용 시**:
```
postgresql://user:password@localhost:5432/database
```

**잘못된 예시**:
```
❌ postgres://...  (postgresql:// 사용)
❌ postgresql://host:5432/db  (user:password 누락)
❌ postgresql://user:pass@cloud-sql-instance:5432/db  (Cloud SQL Proxy 사용 시 localhost 사용)
```

**올바른 예시**:
```
✅ postgresql://seedtest_user:myPass123@localhost:5432/seedtest
✅ postgresql://admin:SecureP@ss!@localhost:5432/seedtest_prod
```

---

### 문제 3: Secret 값이 비어있음

**확인**:
```bash
kubectl -n seedtest get secret seedtest-db-credentials -o yaml
```

**해결**:
```bash
# Secret 재생성 (값 확인 후)
kubectl -n seedtest delete secret seedtest-db-credentials
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:password@localhost:5432/seedtest'
```

---

## 🔐 보안 모범 사례

### 1. Secret 값 노출 방지

```bash
# ❌ 나쁜 예: 히스토리에 남음
kubectl create secret generic my-secret --from-literal=password='myPassword123'

# ✅ 좋은 예: 파일에서 읽기
echo -n 'myPassword123' > /tmp/password.txt
kubectl create secret generic my-secret --from-file=password=/tmp/password.txt
rm /tmp/password.txt

# ✅ 좋은 예: 환경 변수 사용
read -s DB_PASSWORD
kubectl create secret generic my-secret --from-literal=password="$DB_PASSWORD"
```

### 2. Secret 접근 제한

```bash
# RBAC로 Secret 접근 제한
kubectl -n seedtest create role secret-reader \
  --verb=get,list \
  --resource=secrets \
  --resource-name=seedtest-db-credentials

kubectl -n seedtest create rolebinding secret-reader-binding \
  --role=secret-reader \
  --serviceaccount=seedtest:seedtest-api
```

### 3. Secret 암호화

```bash
# Kubernetes Secret은 etcd에 base64로 저장됨 (암호화 아님)
# 프로덕션에서는 다음 중 하나 사용 권장:
# 1. Kubernetes Encryption at Rest
# 2. External Secrets Operator (ESO) + GCP Secret Manager
# 3. HashiCorp Vault
```

---

## 🔄 ExternalSecret 사용 (프로덕션 권장)

Secret을 수동으로 관리하는 대신 ExternalSecret을 사용하면 GCP Secret Manager와 자동 동기화됩니다.

### ExternalSecret 설정

```bash
# 1. GCP Secret Manager에 시크릿 생성
gcloud secrets create seedtest-database-url \
  --data-file=- \
  --project=univprepai <<EOF
postgresql://user:password@localhost:5432/seedtest
EOF

# 2. ExternalSecret 배포
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# 3. Secret 자동 생성 확인 (1-2분 대기)
kubectl -n seedtest get secret calibrate-irt-credentials
```

**장점**:
- ✅ Secret 자동 동기화 (1시간마다)
- ✅ 중앙 집중식 관리 (GCP Secret Manager)
- ✅ 버전 관리 및 감사 로그
- ✅ 접근 제어 (IAM)

**자세한 내용**: [DEPLOYMENT_EXECUTION_GUIDE.md](./DEPLOYMENT_EXECUTION_GUIDE.md)

---

## 📋 체크리스트

### Secret 생성 완료
- [ ] `seedtest-db-credentials` Secret 생성
- [ ] `r-irt-credentials` Secret 생성 (선택)
- [ ] Secret 목록 확인 (`kubectl get secrets`)
- [ ] Secret 값 검증 (첫 몇 자만)

### DATABASE_URL 검증
- [ ] 형식 확인: `postgresql://user:password@host:port/database`
- [ ] Cloud SQL Proxy 사용 시 host가 `localhost`인지 확인
- [ ] 사용자 이름과 비밀번호 정확한지 확인
- [ ] 데이터베이스 이름 정확한지 확인

### 보안 확인
- [ ] Secret 값이 히스토리에 남지 않았는지 확인
- [ ] Secret 접근 권한 설정 (RBAC)
- [ ] 프로덕션에서는 ExternalSecret 사용 고려

---

## 🎯 다음 단계

Secret 생성 후 CronJob을 배포하세요:

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 확인
kubectl -n seedtest get cronjob

# 테스트
kubectl -n seedtest create job --from=cronjob/calibrate-irt-nightly \
  calibrate-irt-test-$(date +%s)
```

---

## 📚 관련 문서

- **[QUICK_DEPLOY.md](./QUICK_DEPLOY.md)** - 5분 빠른 배포
- **[DEPLOYMENT_EXECUTION_GUIDE.md](./DEPLOYMENT_EXECUTION_GUIDE.md)** - ExternalSecret 사용
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - 테스트 및 디버깅

---

## 💡 팁

### 여러 환경 관리

```bash
# 개발 환경
kubectl -n seedtest-dev create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://dev_user:dev_pass@localhost:5432/seedtest_dev'

# 스테이징 환경
kubectl -n seedtest-staging create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://staging_user:staging_pass@localhost:5432/seedtest_staging'

# 프로덕션 환경
kubectl -n seedtest-prod create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://prod_user:prod_pass@localhost:5432/seedtest_prod'
```

### Secret 백업

```bash
# Secret 백업 (주의: 민감 정보 포함)
kubectl -n seedtest get secret seedtest-db-credentials -o yaml > secret-backup.yaml

# 복원
kubectl apply -f secret-backup.yaml

# 백업 파일 삭제 (보안)
rm secret-backup.yaml
```

---

**최종 업데이트**: 2025-11-02 00:38 KST  
**작성자**: Cascade AI  
**소요 시간**: 2분  
**난이도**: ⭐ 쉬움

**다음 단계**: CronJob 배포 - [QUICK_DEPLOY.md](./QUICK_DEPLOY.md)
