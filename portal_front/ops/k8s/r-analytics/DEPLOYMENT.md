# r-analytics K8s 배포 가이드

## 개요

r-analytics는 통합 R Plumber API 서비스(포트 8010)로, 다음 기능을 제공합니다:

- **Topic Theta Scoring**: IRT 기반 능력 추정
- **Improvement Index**: 성장 추적 (I_t 메트릭)
- **Goal Attainment**: 목표 달성 확률 추정
- **Topic Recommendations**: 다음 학습 토픽 추천
- **Churn Risk**: 14일 이탈 위험 평가
- **Report Generation**: 종합 분석 리포트 생성

## 사전 요구사항

1. **Docker 이미지**: r-analytics 이미지 빌드 및 푸시 완료
2. **Google Secret Manager**: `r-analytics-internal-token` 시크릿 생성
3. **Kubernetes**: `gcpsm-secret-store` SecretStore가 seedtest 네임스페이스에 존재
4. **데이터베이스**: PostgreSQL 및 필수 스키마 준비 완료

## 배포 단계

### 1. Docker 이미지 빌드 및 푸시

```bash
cd /home/won/projects/dreamseed_monorepo

# r-analytics 디렉토리 확인 (r-analytics/Dockerfile 존재해야 함)
ls -la r-analytics/

# 이미지 빌드
docker build -t gcr.io/univprepai/r-analytics:latest \
  -f r-analytics/Dockerfile \
  r-analytics/

# 또는 Artifact Registry 사용 (최신 프로젝트 표준)
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-analytics:latest \
  -f r-analytics/Dockerfile \
  r-analytics/

# 이미지 푸시
docker push gcr.io/univprepai/r-analytics:latest
# 또는
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-analytics:latest
```

**참고**: `deployment.yaml`의 이미지 경로와 일치해야 합니다:
- 현재 설정: `gcr.io/univprepai/r-analytics:latest`
- Artifact Registry로 전환하려면 `deployment.yaml` 수정 필요

### 2. Google Secret Manager에 토큰 생성

```bash
# 랜덤 토큰 생성
TOKEN=$(openssl rand -base64 32)

# Secret Manager에 시크릿 생성
echo -n "$TOKEN" | gcloud secrets create r-analytics-internal-token \
  --data-file=- \
  --project=univprepai \
  --replication-policy="automatic"

# 또는 기존 시크릿 업데이트
echo -n "$TOKEN" | gcloud secrets versions add r-analytics-internal-token \
  --data-file=- \
  --project=univprepai

# 토큰 확인 (로컬 개발용, .env 파일에 저장)
echo "R_ANALYTICS_TOKEN=$TOKEN" >> .env.local
```

### 3. Kubernetes 매니페스트 적용

```bash
# ExternalSecret 적용 (Secret 자동 생성)
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml

# ExternalSecret 상태 확인
kubectl -n seedtest get externalsecret r-analytics-credentials
kubectl -n seedtest describe externalsecret r-analytics-credentials

# Secret 생성 확인
kubectl -n seedtest get secret r-analytics-credentials

# Deployment 및 Service 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/service.yaml

# ServiceMonitor 적용 (Prometheus 모니터링)
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/servicemonitor.yaml

# 롤아웃 상태 확인
kubectl -n seedtest rollout status deployment/r-analytics --timeout=5m
```

### 4. 배포 검증

```bash
# Pod 상태 확인
kubectl -n seedtest get pods -l app=r-analytics

# Pod 로그 확인
kubectl -n seedtest logs -l app=r-analytics --tail=50

# Service 확인
kubectl -n seedtest get svc r-analytics

# 헬스 체크 (Port-forward)
kubectl -n seedtest port-forward svc/r-analytics 8010:80 &
curl http://localhost:8010/health

# 내부 토큰으로 테스트
TOKEN=$(kubectl -n seedtest get secret r-analytics-credentials -o jsonpath='{.data.token}' | base64 -d)
curl -H "X-Internal-Token: $TOKEN" http://localhost:8010/health
```

## 구성 파일

### ExternalSecret (`externalsecret.yaml`)

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: r-analytics-credentials
  namespace: seedtest
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: r-analytics-credentials
    creationPolicy: Owner
  data:
    - secretKey: token
      remoteRef:
        key: r-analytics-internal-token  # GCP Secret Manager 키
```

### Deployment (`deployment.yaml`)

주요 설정:
- **Replicas**: 2 (고가용성)
- **Container Port**: 8010
- **Health Checks**: `/health` 엔드포인트 사용
- **Resources**: 
  - Requests: CPU 1000m, Memory 2Gi
  - Limits: CPU 4000m, Memory 8Gi
- **Pod Anti-Affinity**: 노드 분산 배치

### Service (`service.yaml`)

```yaml
spec:
  type: ClusterIP
  ports:
  - port: 80              # 외부 클러스터 접근 포트
    targetPort: 8010      # 컨테이너 포트
    name: http
```

**클러스터 내부 접근 URL**: `http://r-analytics.seedtest.svc.cluster.local:80`

### ServiceMonitor (`servicemonitor.yaml`)

Prometheus가 메트릭을 스크래핑하도록 설정:
- **Port**: `http` (Service의 포트 이름)
- **Path**: `/health` (메트릭 엔드포인트)
- **Interval**: 30초

## 환경 변수 설정

### R 서비스 (Deployment)

`deployment.yaml`에 이미 설정됨:
- `R_ANALYTICS_INTERNAL_TOKEN`: ExternalSecret에서 자동 주입

### Python 클라이언트 (FastAPI)

`seedtest-api` Deployment에 추가:

```yaml
env:
  - name: R_ANALYTICS_BASE_URL
    value: "http://r-analytics.seedtest.svc.cluster.local:80"
  - name: R_ANALYTICS_TOKEN
    valueFrom:
      secretKeyRef:
        name: r-analytics-credentials
        key: token
  - name: R_ANALYTICS_TIMEOUT_SECS
    value: "20"
```

## 모니터링

### Pod 상태 모니터링

```bash
# Pod 상태 확인
kubectl -n seedtest get pods -l app=r-analytics -o wide

# Pod 이벤트 확인
kubectl -n seedtest describe pod -l app=r-analytics

# 리소스 사용량 확인
kubectl -n seedtest top pods -l app=r-analytics
```

### 로그 모니터링

```bash
# 실시간 로그 스트리밍
kubectl -n seedtest logs -f deployment/r-analytics

# 최근 에러 로그 필터링
kubectl -n seedtest logs -l app=r-analytics --tail=100 | grep -i error

# 특정 Pod 로그
kubectl -n seedtest logs <pod-name> --tail=50
```

### Prometheus 메트릭

```bash
# ServiceMonitor 확인
kubectl -n seedtest get servicemonitor r-analytics

# Prometheus 타겟 확인 (Prometheus UI)
# http://prometheus.<namespace>.svc.cluster.local:9090/targets
```

## 트러블슈팅

### Pod가 시작되지 않음

```bash
# Pod 상태 및 이벤트 확인
kubectl -n seedtest describe pod -l app=r-analytics

# 이미지 Pull 실패 확인
kubectl -n seedtest get events --sort-by='.lastTimestamp' | grep r-analytics

# 이미지 경로 확인
kubectl -n seedtest get deployment r-analytics -o jsonpath='{.spec.template.spec.containers[0].image}'
```

**일반적인 문제:**
- 이미지가 존재하지 않음 → 이미지 빌드 및 푸시 확인
- 이미지 Pull 권한 부족 → GCP 인증 확인 (`gcloud auth configure-docker`)
- 리소스 부족 → 노드 리소스 확인

### Secret 문제

```bash
# ExternalSecret 상태 확인
kubectl -n seedtest get externalsecret r-analytics-credentials -o yaml

# Secret 생성 확인
kubectl -n seedtest get secret r-analytics-credentials

# GCP Secret Manager 확인
gcloud secrets list --project=univprepai | grep r-analytics

# Secret 수동 동기화 (필요시)
kubectl -n seedtest delete secret r-analytics-credentials
kubectl -n seedtest apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml
```

### 헬스 체크 실패

```bash
# Pod 로그 확인
kubectl -n seedtest logs -l app=r-analytics --tail=100

# 수동 헬스 체크
kubectl -n seedtest port-forward svc/r-analytics 8010:80 &
curl -v http://localhost:8010/health

# 컨테이너 내부에서 확인
kubectl -n seedtest exec -it <pod-name> -- curl http://localhost:8010/health
```

**원인:**
- R 플러거 서비스가 시작되지 않음
- 포트 불일치 (8010 vs 8080)
- 의존성 패키지 설치 실패

### FastAPI에서 연결 실패

```bash
# DNS 해상도 확인
kubectl -n seedtest run -it --rm debug --image=busybox --restart=Never -- \
  nslookup r-analytics.seedtest.svc.cluster.local

# 연결성 테스트
kubectl -n seedtest run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -v http://r-analytics.seedtest.svc.cluster.local:80/health

# FastAPI Pod에서 직접 테스트
kubectl -n seedtest exec -it deployment/seedtest-api -- \
  python -c "from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient; print(RAnalyticsClient().health())"
```

## 스케일링

### 수동 스케일링

```bash
# 스케일 업
kubectl -n seedtest scale deployment r-analytics --replicas=3

# 스케일 다운
kubectl -n seedtest scale deployment r-analytics --replicas=1
```

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: r-analytics-hpa
  namespace: seedtest
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: r-analytics
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 롤백

```bash
# 배포 히스토리 확인
kubectl -n seedtest rollout history deployment/r-analytics

# 이전 버전으로 롤백
kubectl -n seedtest rollout undo deployment/r-analytics

# 특정 리비전으로 롤백
kubectl -n seedtest rollout undo deployment/r-analytics --to-revision=2

# 롤백 상태 확인
kubectl -n seedtest rollout status deployment/r-analytics
```

## 업데이트 절차

1. **이미지 빌드 및 푸시**
   ```bash
   docker build -t gcr.io/univprepai/r-analytics:latest -f r-analytics/Dockerfile r-analytics/
   docker push gcr.io/univprepai/r-analytics:latest
   ```

2. **Deployment 업데이트** (이미지 태그 변경 또는 `imagePullPolicy: Always`로 자동 업데이트)

3. **롤아웃 재시작**
   ```bash
   kubectl -n seedtest rollout restart deployment/r-analytics
   kubectl -n seedtest rollout status deployment/r-analytics
   ```

## 관련 문서

- [DEPLOYMENT_CHECKLIST.md](../../DEPLOYMENT_CHECKLIST.md) - 전체 배포 체크리스트
- [README.md](./README.md) - r-analytics 서비스 상세 문서
- [analytics_proxy.py](../../../../apps/seedtest_api/routers/analytics_proxy.py) - FastAPI 프록시 라우터
- [r_analytics.py](../../../../apps/seedtest_api/app/clients/r_analytics.py) - Python 클라이언트

