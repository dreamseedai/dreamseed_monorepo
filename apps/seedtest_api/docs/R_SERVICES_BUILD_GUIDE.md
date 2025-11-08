# R 서비스 빌드 및 배포 가이드

## R 서비스 디렉토리 위치

### r-brms-plumber
- **경로**: `./r-brms-plumber/` (프로젝트 루트)
- **파일**: `api.R`, `Dockerfile`, `plumber.R`
- **이미지**: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest`

### r-forecast-plumber
- **경로**: `./portal_front/r-forecast-plumber/` (권장)
- **또는**: `./r-forecast-plumber/` (프로젝트 루트)
- **파일**: `api.R`, `Dockerfile`
- **이미지**: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest`

## 빌드 및 푸시

### r-brms-plumber

```bash
cd r-brms-plumber
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest
```

### r-forecast-plumber

```bash
cd portal_front/r-forecast-plumber
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest
```

## 배포

### K8s 매니페스트 적용

```bash
# r-brms-plumber
kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/

# r-forecast-plumber
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/
```

### Pod 재시작 (이미지 업데이트 후)

```bash
kubectl -n seedtest rollout restart deployment/r-brms-plumber
kubectl -n seedtest rollout restart deployment/r-forecast-plumber
```

## 상태 확인

### Pod 상태
```bash
kubectl -n seedtest get pods | grep -E "r-brms|r-forecast"
```

### 서비스 엔드포인트
```bash
kubectl -n seedtest get svc r-brms-plumber r-forecast-plumber
```

### 로그 확인
```bash
# r-brms-plumber
kubectl -n seedtest logs -l app=r-brms-plumber --tail=50

# r-forecast-plumber
kubectl -n seedtest logs -l app=r-forecast-plumber --tail=50
```

## 트러블슈팅

### ImagePullBackOff 오류
- 이미지가 푸시되지 않았거나 경로가 잘못되었을 수 있습니다.
- 이미지 경로 확인: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/<service-name>:latest`
- 빌드 및 푸시 재실행

### 서비스 연결 실패
- Pod가 정상 실행 중인지 확인
- Service 엔드포인트 확인
- 네트워크 정책 확인

### 환경 변수 오류
- ExternalSecret이 정상 동기화되었는지 확인
- Secret 존재 여부 확인

