# ExternalSecret 설정 가이드

**작성일**: 2025-11-02  
**목적**: calibrate-irt CronJob에 ExternalSecret 연동

---

## 개요

External Secrets Operator (ESO)를 사용하여 Google Secret Manager (GSM) 또는 다른 secret store에서 Kubernetes Secret을 자동으로 생성/갱신합니다.

---

## 전제 조건

### 1. External Secrets Operator 설치

```bash
# ESO 설치 확인
kubectl get crd | grep externalsecrets

# 없으면 설치
kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/charts/external-secrets/templates/crds/ExternalSecret.yaml
# 또는 Helm 사용
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

### 2. GCP Secret Manager에 Secret 저장

```bash
# DATABASE_URL 저장
echo -n 'postgresql://user:pass@host:5432/dbname' | \
  gcloud secrets create seedtest-database-url \
    --data-file=- \
    --project=univprepai \
    --replication-policy="automatic"

# R IRT Token 저장 (선택)
echo -n 'your-token-here' | \
  gcloud secrets create r-irt-plumber-token \
    --data-file=- \
    --project=univprepai \
    --replication-policy="automatic"
```

### 3. GCP Service Account 생성 및 권한 부여

```bash
# Service Account 생성
gcloud iam service-accounts create eso-gcp-sa \
  --project=univprepai \
  --display-name="External Secrets Operator GCP SA"

# Secret Manager 권한 부여
gcloud projects add-iam-policy-binding univprepai \
  --member="serviceAccount:eso-gcp-sa@univprepai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Service Account Key 다운로드
gcloud iam service-accounts keys create eso-gcp-key.json \
  --iam-account=eso-gcp-sa@univprepai.iam.gserviceaccount.com \
  --project=univprepai
```

---

## 설정 단계

### Step 1: GCP Service Account Key Secret 생성

```bash
# private_key 추출
PRIVATE_KEY=$(cat eso-gcp-key.json | jq -r .private_key)

# Kubernetes Secret 생성
kubectl -n seedtest create secret generic eso-gcp-credentials \
  --from-literal=secret-access-key="$PRIVATE_KEY"
```

### Step 2: ClusterSecretStore 생성

```bash
# ClusterSecretStore 적용
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml
# (ClusterSecretStore 섹션만 적용)

# 또는 별도 파일로 생성
cat > cluster-secret-store.yaml <<EOF
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
kubectl apply -f cluster-secret-store.yaml
```

### Step 3: ExternalSecret 생성

```bash
# ExternalSecret 적용
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# Secret 생성 확인
kubectl -n seedtest get secret calibrate-irt-credentials

# ExternalSecret 상태 확인
kubectl -n seedtest get externalsecret calibrate-irt-credentials
kubectl -n seedtest describe externalsecret calibrate-irt-credentials
```

### Step 4: CronJob 업데이트

```bash
# ExternalSecret을 사용하는 CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml

# 또는 기존 CronJob 수정
kubectl -n seedtest patch cronjob calibrate-irt-weekly -p '
{
  "spec": {
    "jobTemplate": {
      "spec": {
        "template": {
          "spec": {
            "containers": [{
              "name": "calibrate-irt",
              "env": [
                {
                  "name": "DATABASE_URL",
                  "valueFrom": {
                    "secretKeyRef": {
                      "name": "calibrate-irt-credentials",
                      "key": "DATABASE_URL"
                    }
                  }
                },
                {
                  "name": "R_IRT_INTERNAL_TOKEN",
                  "valueFrom": {
                    "secretKeyRef": {
                      "name": "calibrate-irt-credentials",
                      "key": "R_IRT_INTERNAL_TOKEN",
                      "optional": true
                    }
                  }
                }
              ]
            }]
          }
        }
      }
    }
  }
}'
```

---

## 검증

### 1. Secret 생성 확인

```bash
# Secret 존재 확인
kubectl -n seedtest get secret calibrate-irt-credentials

# Secret 내용 확인 (base64 디코딩)
kubectl -n seedtest get secret calibrate-irt-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

### 2. ExternalSecret 상태 확인

```bash
# ExternalSecret 상태
kubectl -n seedtest get externalsecret calibrate-irt-credentials

# 상세 정보
kubectl -n seedtest describe externalsecret calibrate-irt-credentials
```

**정상 상태 예시**:
```
Status:
  Conditions:
    - Status: True
      Type: Ready
  Refresh Time: 2025-11-02T12:00:00Z
  Synced Resource Version: abc123
```

### 3. CronJob에서 Secret 사용 확인

```bash
# CronJob 환경 변수 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].env[*]}' | jq

# 수동 Job 생성 및 테스트
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)

# 로그 확인 (Secret 값은 로그에 표시되지 않아야 함)
kubectl -n seedtest logs job/calibrate-irt-test-* -c calibrate-irt
```

---

## 문제 해결

### ExternalSecret이 Ready 상태가 아님

```bash
# 이벤트 확인
kubectl -n seedtest describe externalsecret calibrate-irt-credentials

# 일반적인 원인:
# 1. ClusterSecretStore가 없음
# 2. GCP Service Account 권한 부족
# 3. GSM에 Secret이 없음
# 4. Secret 경로 오류
```

### Secret이 생성되지 않음

```bash
# ExternalSecret 로그 확인
kubectl -n external-secrets-system logs -l app.kubernetes.io/name=external-secrets

# GCP 인증 확인
kubectl -n seedtest get secret eso-gcp-credentials
```

### CronJob이 Secret을 찾지 못함

```bash
# CronJob의 Secret 참조 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o yaml | grep -A 10 secretKeyRef

# Secret 이름/키 확인
kubectl -n seedtest get secret calibrate-irt-credentials -o yaml | grep -A 2 "data:"
```

---

## 대안: 직접 Secret 생성 (ESO 사용 안 함)

ESO를 사용하지 않는 경우, 직접 Secret을 생성할 수 있습니다:

```bash
# Secret 직접 생성
kubectl -n seedtest create secret generic calibrate-irt-credentials \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/dbname' \
  --from-literal=R_IRT_INTERNAL_TOKEN='<token>'

# 또는 파일에서
kubectl -n seedtest create secret generic calibrate-irt-credentials \
  --from-file=DATABASE_URL=./database-url.txt \
  --from-file=R_IRT_INTERNAL_TOKEN=./token.txt
```

그 후 기존 CronJob (`calibrate-irt.yaml`)을 사용하면 됩니다.

---

## 자동 갱신

ExternalSecret은 `refreshInterval` (기본: 1시간)마다 자동으로 갱신됩니다.

GSM의 Secret이 업데이트되면, Kubernetes Secret도 자동으로 업데이트됩니다.

**수동 갱신**:
```bash
# ExternalSecret 재동기화
kubectl -n seedtest annotate externalsecret calibrate-irt-credentials \
  force-sync=$(date +%s) \
  --overwrite
```

---

## 보안 모범 사례

1. **최소 권한**: GCP Service Account에는 Secret Manager 접근 권한만 부여
2. **Secret 버전 관리**: GSM에서 Secret 버전 관리 활용
3. **네임스페이스 격리**: Secret은 필요한 네임스페이스에만 생성
4. **정기 갱신**: `refreshInterval` 설정으로 정기 갱신
5. **감사 로깅**: GCP Audit Logs로 Secret 접근 모니터링

---

## 참고 자료

- External Secrets Operator: https://external-secrets.io/
- GCP Secret Manager: https://cloud.google.com/secret-manager/docs
- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/

