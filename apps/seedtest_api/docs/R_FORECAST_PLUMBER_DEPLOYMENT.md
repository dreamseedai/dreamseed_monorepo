# r-forecast-plumber 배포 가이드

## 개요

r-forecast-plumber는 Prophet 시계열 예측 및 Survival 생존분석을 제공하는 R Plumber 서비스입니다.

## 전제 조건

1. Docker 설치 및 로그인
2. GCP Container Registry 접근 권한
3. Kubernetes 클러스터 접근 권한
4. External Secrets Operator 설정 완료

## 빌드 및 푸시

### 1. 이미지 빌드

```bash
# 프로젝트 루트에서 실행
cd portal_front/r-forecast-plumber

# Docker 이미지 빌드
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:staging .
```

**또는 프로젝트 루트에서**:
```bash
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:staging ./portal_front/r-forecast-plumber
```

### 2. 이미지 푸시

```bash
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:staging
```

### 3. 프로덕션 태그 (선택)

```bash
# staging 이미지를 latest로 태그
docker tag asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:staging \
           asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest

# latest 푸시
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest
```

## Kubernetes 배포

### 1. ExternalSecret 적용

External Secrets Operator를 통해 GCP Secret Manager에서 비밀을 동기화:

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml
```

**검증**:
```bash
# Secret 생성 확인
kubectl -n seedtest get secret r-forecast-credentials

# ExternalSecret 상태 확인
kubectl -n seedtest get externalsecret r-forecast-credentials
kubectl -n seedtest describe externalsecret r-forecast-credentials
```

### 2. Deployment 적용

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/deployment.yaml
```

**검증**:
```bash
# Pod 상태 확인
kubectl -n seedtest get pods -l app=r-forecast-plumber

# Pod 로그 확인
kubectl -n seedtest logs -f deployment/r-forecast-plumber

# Pod 상세 정보
kubectl -n seedtest describe deployment r-forecast-plumber
```

### 3. Service 적용

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/service.yaml
```

**검증**:
```bash
# Service 확인
kubectl -n seedtest get svc r-forecast-plumber

# Endpoint 확인
kubectl -n seedtest get endpoints r-forecast-plumber
```

### 4. 헬스체크

```bash
# Pod 내부에서 테스트
kubectl -n seedtest run -it --rm test-curl --image=curlimages/curl --restart=Never -- \
  curl http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz

# 또는 Port Forward로 테스트
kubectl -n seedtest port-forward svc/r-forecast-plumber 8080:80
curl http://localhost:8080/healthz
```

## 전체 배포 스크립트

```bash
#!/bin/bash
set -e

PROJECT="univprepai"
IMAGE="asia-northeast3-docker.pkg.dev/${PROJECT}/seedtest/r-forecast-plumber"
TAG="staging"
NAMESPACE="seedtest"

echo "=== r-forecast-plumber 배포 시작 ==="

# 1. 이미지 빌드
echo "1. 이미지 빌드 중..."
docker build -t ${IMAGE}:${TAG} ./portal_front/r-forecast-plumber

# 2. 이미지 푸시
echo "2. 이미지 푸시 중..."
docker push ${IMAGE}:${TAG}

# 3. K8s 매니페스트 적용
echo "3. ExternalSecret 적용 중..."
kubectl -n ${NAMESPACE} apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml

echo "4. Deployment 적용 중..."
kubectl -n ${NAMESPACE} apply -f portal_front/ops/k8s/r-forecast-plumber/deployment.yaml

echo "5. Service 적용 중..."
kubectl -n ${NAMESPACE} apply -f portal_front/ops/k8s/r-forecast-plumber/service.yaml

# 4. 배포 상태 확인
echo "6. 배포 상태 확인..."
kubectl -n ${NAMESPACE} rollout status deployment/r-forecast-plumber --timeout=300s

# 5. 헬스체크
echo "7. 헬스체크..."
sleep 5
kubectl -n ${NAMESPACE} run -it --rm test-curl --image=curlimages/curl --restart=Never -- \
  curl -f http://r-forecast-plumber.${NAMESPACE}.svc.cluster.local:80/healthz || echo "헬스체크 실패"

echo "=== r-forecast-plumber 배포 완료 ==="
```

## 문제 해결

### 이미지 Pull 실패

**증상**: `ImagePullBackOff` 또는 `ErrImagePull`

**해결**:
```bash
# 이미지 존재 확인
gcloud container images list-tags asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber

# 이미지 Pull Secret 확인
kubectl -n seedtest get secret | grep gcr

# Service Account 권한 확인
kubectl -n seedtest describe sa seedtest-api
```

### Secret 동기화 실패

**증상**: `r-forecast-credentials` Secret이 생성되지 않음

**해결**:
```bash
# ExternalSecret 상태 확인
kubectl -n seedtest describe externalsecret r-forecast-credentials

# SecretStore 확인
kubectl -n seedtest get secretstore gcpsm-secret-store

# ESO 로그 확인
kubectl -n external-secrets-system logs -l app.kubernetes.io/name=external-secrets | grep r-forecast
```

### Pod 시작 실패

**증상**: Pod가 `CrashLoopBackOff` 상태

**해결**:
```bash
# Pod 로그 확인
kubectl -n seedtest logs -l app=r-forecast-plumber --tail=100

# Pod 이벤트 확인
kubectl -n seedtest describe pod -l app=r-forecast-plumber

# ConfigMap 확인 (있는 경우)
kubectl -n seedtest get configmap -l app=r-forecast-plumber
```

### 서비스 접근 불가

**증상**: 다른 Pod에서 r-forecast-plumber 접근 불가

**해결**:
```bash
# Service 확인
kubectl -n seedtest get svc r-forecast-plumber -o yaml

# Endpoint 확인
kubectl -n seedtest get endpoints r-forecast-plumber

# 네트워크 정책 확인
kubectl -n seedtest get networkpolicies | grep r-forecast
```

## 환경 변수

### Deployment 환경 변수

- `R_FORECAST_PORT`: 서비스 포트 (기본값: 80)
- `R_FORECAST_LOG_LEVEL`: 로그 레벨 (기본값: INFO)

### ExternalSecret을 통한 환경 변수

- `R_FORECAST_INTERNAL_TOKEN`: 내부 인증 토큰 (GCP Secret: `r-forecast-internal-token`)

## 업데이트

### 이미지 업데이트

```bash
# 새 이미지 빌드 및 푸시
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:staging ./portal_front/r-forecast-plumber
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:staging

# Deployment 재시작 (이미지 Pull 정책이 Always인 경우 자동 Pull)
kubectl -n seedtest rollout restart deployment/r-forecast-plumber

# 또는 이미지 태그 업데이트 후 Deployment 업데이트
kubectl -n seedtest set image deployment/r-forecast-plumber \
  r-forecast-plumber=asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:staging
```

### 설정 업데이트

```bash
# Deployment 업데이트
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/deployment.yaml

# 롤아웃 상태 확인
kubectl -n seedtest rollout status deployment/r-forecast-plumber
```

## 모니터링

### 로그 확인

```bash
# 실시간 로그
kubectl -n seedtest logs -f deployment/r-forecast-plumber

# 최근 100줄
kubectl -n seedtest logs --tail=100 deployment/r-forecast-plumber

# 특정 Pod 로그
kubectl -n seedtest logs <pod-name>
```

### 메트릭 확인

ServiceMonitor가 설정된 경우:
```bash
# Prometheus에서 메트릭 확인
kubectl -n seedtest get servicemonitor r-forecast-plumber
```

## 참고

- [R Plumber 공식 문서](https://www.rplumber.io/)
- [Prophet API 포맷 명세서](./API_FORMAT_SPEC.md)
- [Survival API 포맷 명세서](./API_FORMAT_SPEC.md)

