# 배포 상태 및 다음 단계

## 배포 완료 내역

### ✅ 1. K8s 매니페스트 적용

#### r-brms-plumber
- ✅ Deployment: `configured`
- ✅ ExternalSecret: `configured`
- ✅ Service: `unchanged`

#### r-forecast-plumber
- ✅ Deployment: `created`
- ✅ Service: `created`
- ⚠️ ExternalSecret: `v1beta1` 버전 오류 (수정 필요)

### ✅ 2. CronJob 배포

- ✅ `fit-bayesian-growth`: `configured` (매주 월요일 04:30 UTC)
- ✅ `forecast-prophet`: `created` (매주 월요일 05:00 UTC)
- ✅ `fit-survival-churn`: `created` (매일 05:00 UTC)

### ✅ 3. 테스트 Job 생성

- ✅ `brms-test-<timestamp>`: 생성 완료
- ✅ `prophet-test-<timestamp>`: 생성 완료
- ✅ `survival-test-<timestamp>`: 생성 완료

## 현재 상태

### ⚠️ 이슈

#### 1. R 서비스 Pod ImagePullBackOff
```
r-brms-plumber-*: ImagePullBackOff
r-forecast-plumber-*: ImagePullBackOff
```

**원인**: Docker 이미지가 아직 빌드/푸시되지 않음

**해결**:
```bash
# R 서비스 소스 디렉토리 확인 후 빌드
cd <r-brms-plumber-source-dir>
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest

cd <r-forecast-plumber-source-dir>
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest
```

#### 2. ExternalSecret 버전 오류
```
error: resource mapping not found for name: "r-forecast-credentials" 
namespace: "seedtest" from ".../externalsecret.yaml": 
no matches for kind "ExternalSecret" in version "external-secrets.io/v1beta1"
```

**해결**: `externalsecret.yaml`의 `apiVersion`을 `v1`로 변경:
```yaml
apiVersion: external-secrets.io/v1  # v1beta1 → v1
```

## 다음 단계

### 1. R 서비스 이미지 빌드 및 푸시

R 서비스 소스 코드가 있는 디렉토리에서:

```bash
# r-brms-plumber
cd <r-brms-plumber-source>
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest

# r-forecast-plumber
cd <r-forecast-plumber-source>
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest
```

### 2. ExternalSecret 수정

```bash
# externalsecret.yaml 수정
sed -i 's/apiVersion: external-secrets.io\/v1beta1/apiVersion: external-secrets.io\/v1/g' \
  portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml

# 재적용
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml
```

### 3. 베이지안 KPI 활성화

`seedtest-api` Deployment에 환경 변수 추가:

```bash
kubectl -n seedtest edit deployment seedtest-api

# env 섹션에 추가:
#   - name: METRICS_USE_BAYESIAN
#     value: "true"
```

또는 패치로 적용:

```bash
kubectl -n seedtest patch deployment seedtest-api --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/env/-", "value": {"name": "METRICS_USE_BAYESIAN", "value": "true"}}]'
```

### 4. 배포 검증

#### Pod 상태 확인
```bash
kubectl -n seedtest get pods | grep -E "r-brms|r-forecast"
```

#### 서비스 엔드포인트 확인
```bash
kubectl -n seedtest get svc r-brms-plumber r-forecast-plumber
```

#### 테스트 Job 로그 확인
```bash
# brms-test
kubectl -n seedtest logs -f job/brms-test-<timestamp>

# prophet-test
kubectl -n seedtest logs -f job/prophet-test-<timestamp>

# survival-test
kubectl -n seedtest logs -f job/survival-test-<timestamp>
```

#### weekly_kpi.P 확인
```bash
psql $DATABASE_URL -c "
  SELECT user_id, week_start, kpis->>'P' AS goal_probability, kpis->>'sigma' AS uncertainty
  FROM weekly_kpi
  WHERE kpis ? 'P'
  ORDER BY week_start DESC
  LIMIT 10;
"
```

## 참고

- R 서비스 소스 코드 위치 확인 필요
- 이미지 경로: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/<service-name>:latest`
- ExternalSecret은 GCP Secret Manager 또는 다른 외부 시크릿 관리 시스템 연동 필요

