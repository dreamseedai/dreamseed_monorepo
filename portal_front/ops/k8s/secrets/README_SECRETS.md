# Kubernetes Secrets 관리 가이드

**작성일**: 2025-11-02  
**목적**: IRT 캘리브레이션 및 관련 서비스에 필요한 Secret 생성/관리

---

## 📋 필요한 Secrets

### 1. r-irt-credentials

**용도**: R IRT Plumber 서비스 내부 인증 토큰

**키**: `token`

**생성 방법**:

```bash
# 방법 1: 스크립트 사용 (대화형)
./portal_front/ops/k8s/secrets/create-r-irt-credentials.sh

# 방법 2: 직접 kubectl 명령어
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='your-actual-token-here'
```

**토큰이 필요 없는 경우**:
- r-irt-plumber가 인증을 요구하지 않는 경우
- Secret을 생성하지 않아도 됨 (CronJob에서 `optional: true`로 설정됨)

---

### 2. seedtest-db-credentials

**용도**: 데이터베이스 연결 URL

**키**: `DATABASE_URL`

**생성 방법**:

```bash
# 직접 생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/dbname'

# 또는 ExternalSecret 사용 (권장)
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml
```

---

### 3. aws-s3-credentials (리포트 생성용)

**용도**: AWS S3 업로드를 위한 자격 증명

**키**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

**생성 방법**:

```bash
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='your-access-key' \
  --from-literal=AWS_SECRET_ACCESS_KEY='your-secret-key'
```

---

## 🔍 Secret 확인

### 모든 Secrets 나열

```bash
kubectl -n seedtest get secrets
```

### 특정 Secret 확인

```bash
# r-irt-credentials
kubectl -n seedtest get secret r-irt-credentials

# seedtest-db-credentials
kubectl -n seedtest get secret seedtest-db-credentials
```

### Secret 내용 확인 (디코딩)

```bash
# r-irt-credentials token
kubectl -n seedtest get secret r-irt-credentials -o jsonpath='{.data.token}' | base64 -d
echo

# DATABASE_URL
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d
echo
```

---

## 🔄 Secret 업데이트

### 기존 Secret 삭제 후 재생성

```bash
# r-irt-credentials
kubectl -n seedtest delete secret r-irt-credentials
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='new-token'

# seedtest-db-credentials
kubectl -n seedtest delete secret seedtest-db-credentials
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='new-url'
```

### Secret 패치 (일부만 변경)

```bash
# 토큰만 업데이트 (주의: 전체 Secret이 교체됨)
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='new-token' \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

## 🔐 ExternalSecret 사용 (권장)

### 장점

- Secret을 Kubernetes에 직접 저장하지 않음
- Google Secret Manager 등 중앙 관리 시스템 사용
- 자동 갱신 (refreshInterval)
- 버전 관리 지원

### 설정 방법

1. **ClusterSecretStore 생성**
   ```bash
   kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml
   # (ClusterSecretStore 섹션만)
   ```

2. **ExternalSecret 생성**
   ```bash
   kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml
   ```

3. **Secret 자동 생성 확인**
   ```bash
   kubectl -n seedtest get secret calibrate-irt-credentials
   kubectl -n seedtest get externalsecret calibrate-irt-credentials
   ```

**자세한 가이드**: `portal_front/ops/k8s/secrets/EXTERNALSECRET_SETUP_GUIDE.md`

---

## ✅ 검증

### Secret이 CronJob에서 참조되는지 확인

```bash
# calibrate-irt-weekly CronJob의 환경 변수 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].env[*]}' | \
  jq -r '.[] | select(.valueFrom.secretKeyRef.name == "r-irt-credentials")'
```

### Pod에서 Secret 사용 확인

```bash
# 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  test-secret-check-$(date +%s)

# 로그 확인 (에러 없이 실행되는지)
kubectl -n seedtest logs job/test-secret-check-* -c calibrate-irt --tail=50

# 정리
kubectl -n seedtest delete job test-secret-check-*
```

---

## 🔒 보안 모범 사례

1. **최소 권한**: Secret에는 필요한 정보만 포함
2. **토큰 로테이션**: 주기적으로 토큰 변경
3. **네임스페이스 격리**: Secret을 필요한 네임스페이스에만 생성
4. **감사 로깅**: Secret 접근 모니터링
5. **ExternalSecret 사용**: 중앙 관리 시스템 활용

---

## 📝 체크리스트

- [ ] r-irt-credentials Secret 생성 (토큰이 필요한 경우)
- [ ] seedtest-db-credentials Secret 생성 (또는 ExternalSecret 설정)
- [ ] aws-s3-credentials Secret 생성 (리포트 생성 시)
- [ ] Secret이 CronJob에서 올바르게 참조되는지 확인
- [ ] Pod에서 Secret 접근 테스트

---

## 문제 해결

### Secret을 찾을 수 없음

```
Error: secrets "r-irt-credentials" not found
```

**해결**:
```bash
# Secret 생성
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='your-token'

# 또는 optional로 설정된 경우 Secret 생성 생략 가능
```

### Secret 값이 잘못됨

**해결**:
```bash
# Secret 재생성
kubectl -n seedtest delete secret r-irt-credentials
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='correct-token'
```

### ExternalSecret이 Ready가 아님

**해결**:
```bash
# ExternalSecret 상태 확인
kubectl -n seedtest describe externalsecret calibrate-irt-credentials

# 일반적인 원인:
# - ClusterSecretStore 미설정
# - GCP 인증 문제
# - GSM에 Secret 없음
```

---

**Secret 관리 준비 완료!** 🔐

