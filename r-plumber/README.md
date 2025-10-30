# R Plumber GLMM Analytics Service

고급 통계 분석을 위한 R 기반 마이크로서비스입니다. GLMM(Generalized Linear Mixed Model) 적합, 예측, 예보를 제공합니다.

## 📋 Features

- **GLMM Fitting**: Binomial GLMM 모델 적합 (`lme4::glmer`)
- **Batch Prediction**: 경량화된 모델로 배치 예측
- **Forecast Summary**: Normal 근사 기반 확률 계산
- **Model Diagnostics**: 모델 진단 및 수렴 확인
- **Health Check**: Kubernetes 준비 상태 체크

## 🚀 Quick Start

### Local Development

```bash
# R에서 직접 실행
R -e "pr <- plumber::plumb('r-plumber/api.R'); pr$run(host='0.0.0.0', port=8000)"

# 또는 Docker로
docker build -t r-glmm-plumber:dev ./r-plumber
docker run --rm -p 8000:8000 r-glmm-plumber:dev
```

### Testing

```bash
# Health check
curl http://localhost:8000/healthz

# GLMM fit
curl -X POST http://localhost:8000/glmm/fit \
  -H "Content-Type: application/json" \
  -d '{
    "observations": [
      {"student_id": "s1", "item_id": "i1", "correct": 1},
      {"student_id": "s1", "item_id": "i2", "correct": 0},
      {"student_id": "s2", "item_id": "i1", "correct": 1}
    ]
  }'
```

전체 테스트 시나리오는 `tests/r-plumber.http` 참조.

## 🔐 Security

### Internal Token Authentication

```bash
# 환경 변수로 토큰 설정
export INTERNAL_TOKEN="your-secret-token"

# 요청 시 헤더에 포함
curl -X POST http://localhost:8000/glmm/fit \
  -H "X-Internal-Token: your-secret-token" \
  -H "Content-Type: application/json" \
  -d '...'
```

### Network Policy (Kubernetes)

내부 전용 서비스로 운영 시 Ingress를 제거하고 ClusterIP만 노출:

```yaml
# ops/k8s/r-plumber/deployment.yaml에서 Ingress 블록 제거
# 또는 NetworkPolicy로 seedtest 네임스페이스에서만 접근 허용
```

## 📦 Deployment (Kubernetes)

```bash
# 이미지 빌드 및 푸시
docker build -t ghcr.io/your-org/r-glmm-plumber:1.0.0 ./r-plumber
docker push ghcr.io/your-org/r-glmm-plumber:1.0.0

# Kubernetes 배포
kubectl apply -k ops/k8s/r-plumber

# 상태 확인
kubectl get pods -l app=r-glmm-plumber
kubectl logs -l app=r-glmm-plumber
```

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `PLUMBER_PORT` | API 포트 | `8000` |
| `PLUMBER_HOST` | 바인딩 호스트 | `0.0.0.0` |
| `INTERNAL_TOKEN` | 내부 인증 토큰 (선택) | `""` |

## 📊 API Endpoints

### `GET /healthz`
서비스 상태 확인

### `POST /glmm/fit`
GLMM 모델 적합

**Request:**
```json
{
  "observations": [
    {"student_id": "s1", "item_id": "i1", "correct": 1}
  ],
  "formula": "correct ~ 1 + (1|student_id) + (1|item_id)"
}
```

**Response:**
```json
{
  "success": true,
  "model": {
    "formula": "...",
    "fixed_effects": {...},
    "random_effects": {...}
  }
}
```

### `POST /glmm/predict`
모델 예측

**Request:**
```json
{
  "model": {...},
  "newdata": [
    {"student_id": "s1", "item_id": "i3"}
  ]
}
```

### `POST /forecast/summary`
Normal 근사 기반 예측

**Request:**
```json
{
  "mean": 0.7,
  "sd": 0.1,
  "target": 0.8
}
```

## 🛠️ Operations

### Resource Requirements

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Scaling

- **HPA**: CPU 70% 목표, 2-10 replicas
- **긴 작업**: CronJob으로 분리, 본 서비스는 on-demand 진단용

### Monitoring

- ServiceMonitor로 `/healthz` 스크레이프
- 커스텀 메트릭 추가 시 `/metrics` 엔드포인트 구현

## 🔗 Integration

FastAPI 클라이언트 예시는 `apps/seedtest-api/clients/r_plumber.py` 참조.

```python
client = RPlumberClient(
    base_url="http://r-glmm-plumber.seedtest.svc.cluster.local:8000",
    internal_token=os.getenv("R_PLUMBER_INTERNAL_TOKEN")
)

result = await client.glmm_fit(observations=[...])
```

## 📚 References

- [Plumber Documentation](https://www.rplumber.io/)
- [lme4 Package](https://cran.r-project.org/package=lme4)
- [GLMM FAQ](https://bbolker.github.io/mixedmodels-misc/glmmFAQ.html)

## 🐛 Troubleshooting

### Convergence Warnings

GLMM 적합 시 수렴 경고가 발생하면:
- 데이터 크기 확인 (최소 100+ observations 권장)
- Random effects 그룹 크기 확인
- `control = glmerControl(optimizer = "bobyqa")` 이미 적용됨

### Memory Issues

대용량 데이터 적합 시:
- 배치 크기 조정
- CronJob으로 오프라인 처리
- 리소스 limits 증가

## 📄 License

Internal use only - Dreamseed Education Platform

