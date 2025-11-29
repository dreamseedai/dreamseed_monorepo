# 레거시 PHP 환경 모니터링 가이드

mpcstudy.com과 같은 레거시 PHP/Nginx 환경에서 Prometheus 메트릭을 노출하는 방법

## 📋 목차

1. [옵션 1: Nginx/PHP-FPM 익스포터](#옵션-1-nginxphp-fpm-익스포터)
2. [옵션 2: FastAPI 어댑터 (권장)](#옵션-2-fastapi-어댑터-권장)
3. [ServiceMonitor 설정](#servicemonitor-설정)
4. [PromQL 쿼리](#promql-쿼리)

---

## 옵션 1: Nginx/PHP-FPM 익스포터

### 1.1 Nginx Exporter 배포

```yaml
# nginx-exporter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-exporter
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-exporter
  template:
    metadata:
      labels:
        app: nginx-exporter
        service: mpcstudy-api
        version: stable
    spec:
      containers:
      - name: nginx-exporter
        image: nginx/nginx-prometheus-exporter:0.11.0
        args:
          - -nginx.scrape-uri=http://mpcstudy-nginx/nginx_status
        ports:
        - name: metrics
          containerPort: 9113
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-exporter
  labels:
    app: nginx-exporter
    service: mpcstudy-api
spec:
  selector:
    app: nginx-exporter
  ports:
  - name: metrics
    port: 9113
    targetPort: 9113
```

### 1.2 Nginx 설정 (stub_status 활성화)

```nginx
# nginx.conf 또는 site.conf
server {
    listen 80;
    server_name mpcstudy.com;
    
    # stub_status 엔드포인트 (내부 전용)
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;  # K8s Pod CIDR
        deny all;
    }
    
    # 기존 PHP 애플리케이션
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
    
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
    }
}
```

### 1.3 PHP-FPM Exporter 배포

```yaml
# php-fpm-exporter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: php-fpm-exporter
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: php-fpm-exporter
  template:
    metadata:
      labels:
        app: php-fpm-exporter
        service: mpcstudy-api
        version: stable
    spec:
      containers:
      - name: php-fpm-exporter
        image: hipages/php-fpm_exporter:2.2.0
        env:
        - name: PHP_FPM_SCRAPE_URI
          value: "tcp://mpcstudy-php-fpm:9000/status"
        ports:
        - name: metrics
          containerPort: 9253
---
apiVersion: v1
kind: Service
metadata:
  name: php-fpm-exporter
  labels:
    app: php-fpm-exporter
    service: mpcstudy-api
spec:
  selector:
    app: php-fpm-exporter
  ports:
  - name: metrics
    port: 9253
    targetPort: 9253
```

### 1.4 PHP-FPM 설정 (status 페이지 활성화)

```ini
; /etc/php-fpm.d/www.conf
[www]
pm.status_path = /status
ping.path = /ping
```

---

## 옵션 2: FastAPI 어댑터 (권장)

레거시 PHP 앞에 얇은 FastAPI 프록시를 두고 `/metrics`와 `x-trace-id` 헤더를 주입합니다.

### 2.1 FastAPI 어댑터 코드

```python
# adapter/main.py
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid

app = FastAPI()

# Prometheus 메트릭
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'version', 'method', 'path', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['service', 'version', 'method', 'path', 'status']
)

BACKEND_URL = "http://mpcstudy-php-backend"
SERVICE_NAME = "mpcstudy-api"
SERVICE_VERSION = "stable"

logger = structlog.get_logger()

@app.middleware("http")
async def proxy_middleware(request: Request, call_next):
    # Trace ID 생성
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    
    # 로깅 컨텍스트
    logger.bind(trace_id=trace_id, path=request.url.path, method=request.method)
    
    start_time = time.time()
    
    # PHP 백엔드로 프록시
    if request.url.path == "/metrics":
        response = await call_next(request)
    else:
        async with httpx.AsyncClient() as client:
            # 헤더 전달
            headers = dict(request.headers)
            headers["x-trace-id"] = trace_id
            
            # 요청 프록시
            backend_response = await client.request(
                method=request.method,
                url=f"{BACKEND_URL}{request.url.path}",
                headers=headers,
                content=await request.body(),
                params=request.query_params
            )
            
            # 응답 생성
            response = Response(
                content=backend_response.content,
                status_code=backend_response.status_code,
                headers=dict(backend_response.headers),
            )
            response.headers["x-trace-id"] = trace_id
    
    # 메트릭 기록
    duration = time.time() - start_time
    status = response.status_code
    
    http_requests_total.labels(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        method=request.method,
        path=request.url.path,
        status=status
    ).inc()
    
    http_request_duration_seconds.labels(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        method=request.method,
        path=request.url.path,
        status=status
    ).observe(duration)
    
    logger.info("request_completed", status=status, duration=duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
```

### 2.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY adapter/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
```

### 2.3 requirements.txt

```txt
fastapi==0.104.0
uvicorn[standard]==0.24.0
httpx==0.25.0
prometheus-client==0.17.0
structlog==23.1.0
```

### 2.4 Kubernetes Deployment

```yaml
# mpcstudy-adapter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mpcstudy-adapter
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mpcstudy-adapter
  template:
    metadata:
      labels:
        app: mpcstudy-adapter
        service: mpcstudy-api
        version: stable
    spec:
      containers:
      - name: adapter
        image: registry.example.com/mpcstudy-adapter:latest
        ports:
        - name: http
          containerPort: 8010
        env:
        - name: BACKEND_URL
          value: "http://mpcstudy-php-backend"
        - name: SERVICE_NAME
          value: "mpcstudy-api"
        - name: SERVICE_VERSION
          value: "stable"
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8010
          initialDelaySeconds: 2
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8010
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mpcstudy-api
  labels:
    app: mpcstudy-adapter
    service: mpcstudy-api
spec:
  selector:
    app: mpcstudy-adapter
  ports:
  - name: http
    port: 8010
    targetPort: 8010
```

---

## ServiceMonitor 설정

### 옵션 1용 (Nginx/PHP-FPM Exporter)

```yaml
# servicemonitor-nginx-exporter.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: nginx-exporter
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: nginx-exporter
  endpoints:
  - port: metrics
    interval: 15s
    relabelings:
    - sourceLabels: [__address__]
      targetLabel: service
      replacement: mpcstudy-api
    - sourceLabels: [__address__]
      targetLabel: version
      replacement: stable
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: php-fpm-exporter
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: php-fpm-exporter
  endpoints:
  - port: metrics
    interval: 15s
    relabelings:
    - sourceLabels: [__address__]
      targetLabel: service
      replacement: mpcstudy-api
    - sourceLabels: [__address__]
      targetLabel: version
      replacement: stable
```

### 옵션 2용 (FastAPI 어댑터)

기존 Helm 차트의 ServiceMonitor를 그대로 사용:

```bash
helm upgrade --install mpcstudy-api ./helm-chart -f values-mpcstudy.yaml
```

---

## PromQL 쿼리

### Nginx Exporter 메트릭

```promql
# 요청 수 (RPS)
rate(nginx_http_requests_total{service="mpcstudy-api"}[5m])

# 활성 연결 수
nginx_connections_active{service="mpcstudy-api"}

# 요청 대기 중
nginx_connections_waiting{service="mpcstudy-api"}
```

### PHP-FPM Exporter 메트릭

```promql
# 활성 프로세스
phpfpm_active_processes{service="mpcstudy-api"}

# 대기 중인 프로세스
phpfpm_idle_processes{service="mpcstudy-api"}

# 느린 요청
rate(phpfpm_slow_requests{service="mpcstudy-api"}[5m])

# 프로세스 큐
phpfpm_listen_queue{service="mpcstudy-api"}
```

### FastAPI 어댑터 메트릭 (옵션 2)

기존 공통 쿼리와 100% 호환:

```promql
# 요청 수
sum by (service, version) (rate(http_requests_total{service="mpcstudy-api"}[5m]))

# 에러율
sum(rate(http_requests_total{service="mpcstudy-api", status=~"5.."}[5m]))
/ sum(rate(http_requests_total{service="mpcstudy-api"}[5m]))

# p95 지연시간
histogram_quantile(0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket{service="mpcstudy-api"}[5m]))
)
```

---

## Grafana 대시보드 변수

### 옵션 1용 (Nginx/PHP-FPM)

```json
{
  "templating": {
    "list": [
      {
        "name": "service",
        "query": "label_values(nginx_http_requests_total, service)"
      }
    ]
  },
  "panels": [
    {
      "title": "Nginx Requests/sec",
      "targets": [
        {
          "expr": "rate(nginx_http_requests_total{service=\"$service\"}[5m])"
        }
      ]
    },
    {
      "title": "PHP-FPM Active Processes",
      "targets": [
        {
          "expr": "phpfpm_active_processes{service=\"$service\"}"
        }
      ]
    }
  ]
}
```

### 옵션 2용 (FastAPI 어댑터)

기존 `api-monitoring-template.json` 그대로 사용 가능!

---

## 권장 사항

### ✅ 옵션 2 (FastAPI 어댑터) 선택 시 장점

1. **통일된 메트릭**: 다른 API 서비스와 동일한 라벨/쿼리 사용
2. **Trace ID 전파**: 로그-메트릭 상관관계 추적 가능
3. **Grafana 재사용**: 기존 대시보드 그대로 사용
4. **Argo Rollouts 호환**: 카나리 배포 자동화 가능
5. **점진적 마이그레이션**: PHP → FastAPI로 점진적 전환 가능

### ⚠️ 옵션 1 (Exporter) 선택 시 고려사항

1. **별도 대시보드 필요**: Nginx/PHP-FPM 전용 패널 작성
2. **라벨 불일치**: relabeling으로 수동 매핑 필요
3. **제한된 메트릭**: HTTP 메서드, 경로별 분석 어려움
4. **Rollouts 불가**: 카나리 배포 자동화 불가능

---

## 배포 순서 (옵션 2 권장)

```bash
# 1. FastAPI 어댑터 이미지 빌드
cd adapter/
docker build -t registry.example.com/mpcstudy-adapter:latest .
docker push registry.example.com/mpcstudy-adapter:latest

# 2. Helm 차트로 배포
cd ../ops/k8s/monitoring/helm-chart
helm upgrade --install mpcstudy-api . -f values-mpcstudy.yaml

# 3. Ingress 라우팅 변경
# 기존: mpcstudy.com → mpcstudy-php-backend
# 신규: mpcstudy.com → mpcstudy-api (어댑터) → mpcstudy-php-backend

# 4. 메트릭 확인
kubectl port-forward svc/mpcstudy-api 8010:8010
curl http://localhost:8010/metrics

# 5. Grafana에서 service=mpcstudy-api 선택하여 모니터링
```

---

**작성일**: 2025-11-09  
**권장 옵션**: FastAPI 어댑터 (옵션 2)
