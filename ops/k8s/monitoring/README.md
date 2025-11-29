# API Observability & Canary Rollout

공통 Helm 차트를 사용한 API 서비스 모니터링 및 카나리 배포 시스템

## 📁 디렉토리 구조

```
ops/k8s/monitoring/
├── helm-chart/
│   ├── Chart.yaml                      # Helm 차트 메타데이터
│   ├── values.yaml                     # 기본 values
│   ├── values-univprepai.yaml          # univprepai-api 오버라이드
│   ├── values-seedtest.yaml            # seedtest-api 오버라이드
│   └── templates/
│       ├── _helpers.tpl                # 템플릿 헬퍼 함수
│       ├── service.yaml                # Kubernetes Service
│       ├── servicemonitor.yaml         # Prometheus ServiceMonitor
│       ├── rollout.yaml                # Argo Rollouts 카나리 배포
│       └── analysistemplate.yaml       # 자동 분석 템플릿
└── grafana-dashboards/
    └── api-monitoring-template.json    # Grafana 대시보드
```

## 🚀 빠른 시작

### 사전 요구사항

1. **Argo Rollouts 설치**
```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

2. **kube-prometheus-stack 설치**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

3. **Grafana 대시보드 임포트**
```bash
# Grafana UI에서 Import → Upload JSON file
# ops/k8s/monitoring/grafana-dashboards/api-monitoring-template.json 선택
```

### 배포 명령어

#### 전체 프로젝트 일괄 배포
```bash
cd ops/k8s/monitoring/helm-chart

# 7개 프로젝트 배포
helm upgrade --install collegeprepai-api . -f values-collegeprepai.yaml
helm upgrade --install skillprepai-api . -f values-skillprepai.yaml
helm upgrade --install univprepai-api . -f values-univprepai.yaml
helm upgrade --install majorprepai-api . -f values-majorprepai.yaml
helm upgrade --install dreamseedai-api . -f values-dreamseedai.yaml
helm upgrade --install mediprepai-api . -f values-mediprepai.yaml
helm upgrade --install my-ktube-api . -f values-my-ktube.yaml
helm upgrade --install mpcstudy-api . -f values-mpcstudy.yaml  # 레거시 PHP (어댑터 필요)
helm upgrade --install seedtest-api . -f values-seedtest.yaml
```

#### 개별 프로젝트 배포 예시

**CollegePrepAI (포트 8008)**
```bash
helm upgrade --install collegeprepai-api . -f values-collegeprepai.yaml

# 배포 상태 확인
kubectl argo rollouts get rollout collegeprepai-api --watch

# 수동 승격 (필요 시)
kubectl argo rollouts promote collegeprepai-api
```

**UnivPrepAI (포트 8006)**
```bash
helm upgrade --install univprepai-api . -f values-univprepai.yaml
```

**MpcsStudy (포트 8010 - 레거시 PHP)**
```bash
# 레거시 PHP 환경은 FastAPI 어댑터 필요
# 상세 가이드: LEGACY_PHP_MONITORING.md 참고
helm upgrade --install mpcstudy-api . -f values-mpcstudy.yaml
```

#### 포트 매핑 참고

| 프로젝트 | 서비스명 | 포트 | 상태 |
|---------|---------|------|------|
| My-Ktube | my-ktube-api | 8001 | ✅ |
| SkillPrepAI | skillprepai-api | 8005 | ✅ |
| UnivPrepAI | univprepai-api | 8006 | ✅ |
| MajorPrepAI | majorprepai-api | 8007 | ✅ |
| CollegePrepAI | collegeprepai-api | 8008 | ✅ |
| DreamSeedAI | dreamseedai-api | 8009 | ✅ |
| SeedTest | seedtest-api | 8009 | ✅ |
| MpcsStudy | mpcstudy-api | 8010 | ⚠️ 레거시 |
| MediPrepAI | mediprepai-api | 8011 | ✅ |

## 📊 모니터링 확인

### 1. Service 및 메트릭 확인
```bash
# Service 존재 확인
kubectl get svc univprepai-api

# 메트릭 엔드포인트 테스트
kubectl port-forward svc/univprepai-api 8006:8006
curl http://localhost:8006/metrics
```

### 2. Prometheus 쿼리 확인
```promql
# 요청 수
sum by (service, version) (rate(http_requests_total{service="univprepai-api"}[5m]))

# 에러율
sum(rate(http_requests_total{service="univprepai-api", status=~"5.."}[5m]))
/ sum(rate(http_requests_total{service="univprepai-api"}[5m]))

# p95 지연시간
histogram_quantile(0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket{service="univprepai-api"}[5m]))
)
```

### 3. Grafana 대시보드
1. Grafana UI 접속
2. 변수 선택:
   - `service`: univprepai-api
   - `version`: canary 또는 stable
3. 패널 확인:
   - Request Rate (rps)
   - Error Rate (5xx)
   - p95/p99 Latency
   - Top Endpoints

## 🎯 카나리 배포 전략

### 기본 단계 (values.yaml)
```yaml
rollouts:
  steps:
    - setWeight: 10          # 10% 트래픽
    - pause: { duration: 60 } # 60초 대기
    - analysis: true          # 자동 분석
    - setWeight: 50          # 50% 트래픽
    - pause: { duration: 60 }
    - analysis: true          # 최종 분석
```

### 자동 분석 기준
```yaml
analysis:
  successP95Seconds: 0.30     # p95 < 300ms
  successErrorRate: 0.02      # 에러율 < 2%
  intervalSeconds: 60         # 60초마다 체크
  count: 5                    # 5회 체크
  failureLimit: 1             # 1회 실패 시 롤백
```

## 🔧 커스터마이징

### 새로운 서비스 추가

1. **values 파일 생성** (`values-myservice.yaml`)
```yaml
fullnameOverride: "myservice-api"
service:
  name: "myservice-api"
  version: "canary"
  port: 8010
image:
  repository: "registry.example.com/myservice-api"
  tag: "latest"
prometheus:
  address: "http://prometheus-server.monitoring.svc.cluster.local"
servicemonitor:
  labels:
    release: kube-prometheus-stack
```

2. **배포**
```bash
helm upgrade --install myservice-api . -f values-myservice.yaml
```

### 라벨 정책 (Cardinality 방지)

✅ **사용 가능한 라벨**:
- `service`: 서비스 이름
- `version`: canary/stable
- `method`: GET/POST/PUT/DELETE
- `path`: 템플릿 경로 (`/users/{id}`)
- `status`: HTTP 상태 코드

❌ **사용 금지 라벨**:
- `user_id`: 사용자별 라벨 (카디널리티 폭주)
- `trace_id`: 요청별 ID (로그에만 사용)
- `timestamp`: 시간 정보

## 🔍 트러블슈팅

### ServiceMonitor가 메트릭을 수집하지 않음
```bash
# ServiceMonitor 확인
kubectl get servicemonitor univprepai-api -o yaml

# Prometheus targets 확인
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# http://localhost:9090/targets 접속
```

### AnalysisTemplate 실패
```bash
# AnalysisRun 로그 확인
kubectl get analysisrun
kubectl describe analysisrun <name>

# Prometheus 쿼리 직접 테스트
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
```

### Rollout이 진행되지 않음
```bash
# Rollout 상태 확인
kubectl argo rollouts get rollout univprepai-api

# 이벤트 확인
kubectl describe rollout univprepai-api

# 수동 승격
kubectl argo rollouts promote univprepai-api

# 롤백
kubectl argo rollouts undo univprepai-api
```

## 📚 참고 문서

- [K8S_MONITORING_GUIDE.md](../../../docs/K8S_MONITORING_GUIDE.md) - 상세 가이드
- [K8S_MONITORING_SUMMARY.md](../../../docs/K8S_MONITORING_SUMMARY.md) - 요약
- [Argo Rollouts 문서](https://argoproj.github.io/argo-rollouts/)
- [Prometheus Operator 문서](https://prometheus-operator.dev/)

## 🎓 운영 팁

### 카나리 → 스테이블 승격
```bash
# 1. values 파일에서 version 변경
# values-univprepai.yaml:
#   service:
#     version: "stable"  # canary → stable

# 2. 재배포
helm upgrade univprepai-api . -f values-univprepai.yaml

# 3. Grafana/Prometheus 쿼리가 동일 라벨로 유지됨
```

### 멀티 환경 관리
```bash
# DEV 환경
helm upgrade --install univprepai-api . \
  -f values-univprepai.yaml \
  -f values-dev.yaml \
  --namespace dev

# PROD 환경
helm upgrade --install univprepai-api . \
  -f values-univprepai.yaml \
  -f values-prod.yaml \
  --namespace prod
```

### 성능 최적화
- Prometheus scrape interval: 15s (기본값)
- Analysis interval: 60s (기본값)
- Histogram buckets: 자동 (Prometheus 기본값)

---

**작성일**: 2025-11-09  
**버전**: 0.1.0
