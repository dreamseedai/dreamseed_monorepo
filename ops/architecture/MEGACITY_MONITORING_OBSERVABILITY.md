# 🛰️ DreamSeedAI MegaCity – Monitoring & Observability Architecture

## Prometheus · Grafana · Loki · Tempo · Alerting

**버전:** 1.0  
**작성일:** 2025-11-21  
**작성자:** DreamSeedAI Architecture Team

---

# 📌 0. 개요

DreamSeedAI MegaCity는 9개 Zone(도메인)과 Core City(DreamSeedAI.com), AI Cluster, Backend/Frontend 서비스 등 **대규모 멀티도메인·멀티서비스 환경**을 운영합니다.

이 문서는 MegaCity 전체를 건강하게 유지하기 위한 **Observability(가시성)·Monitoring(모니터링)·Alerting(알림)** 의 전체 설계를 정의합니다.

MegaCity의 목표는:

* 장애를 **사전에 감지**하고
* 문제의 **원인을 신속히 추적**하며
* 도시 전체를 중앙에서 **관측 및 통제**하는 것입니다.

이를 위해 DreamSeedAI는 다음 4대 Pillar를 사용합니다:

```
1. Metrics → Prometheus
2. Logs → Loki
3. Traces → Tempo / Jaeger
4. Dashboards → Grafana
```

---

# 🧩 1. Observability Stack 개요

```
                    ┌────────────────────────┐
                    │   Grafana Dashboard    │
                    │  (Visualization Layer) │
                    └──────────┬────────────┘
                               │
       ┌───────────────┬───────┴────────┬──────────────────┐
       │               │                │                  │
┌──────▼─────┐   ┌─────▼──────┐   ┌─────▼──────┐   ┌──────▼─────────┐
│ Prometheus │   │    Loki     │   │   Tempo    │   │ AlertManager    │
│  (Metrics) │   │   (Logs)    │   │ (Traces)   │   │ (Alert Routing) │
└──────┬─────┘   └─────────────┘   └────────────┘   └───────────────┘
       │              │                 │                  │
       │              │                 │                  │
 ┌─────▼───────┐ ┌────▼────────┐ ┌──────▼────────┐ ┌──────▼──────────┐
 │ FastAPI API │ │ Nginx Proxy │ │ GPU Inference │ │ PostgreSQL/Redis │
 │ Frontend    │ │ Traefik     │ │   Cluster     │ │    Storage       │
 └─────────────┘ └─────────────┘ └───────────────┘ └──────────────────┘
```

---

# 📊 2. Metrics Architecture (Prometheus)

Prometheus는 MegaCity 전체의 메트릭 수집의 **중추 시스템**입니다.

## 2.1 수집되는 주요 메트릭

### API 레이어

* `http_requests_total{status=200}`
* `http_request_duration_seconds_bucket{le="0.5"}`
* `/api/v1/exams` p95 latency
* 로그인/회원가입 속도

### GPU / AI Cluster

* `gpu_utilization_percent{device="cuda:0"}`
* Whisper 처리 지연 시간
* vLLM token throughput

### DB / Redis

* PostgreSQL connection count
* Slow query log count
* Redis hit/miss ratio

### Reverse Proxy

* Nginx/Traefik 요청 수
* 4xx / 5xx 비율
* Rate limit 동작량

## 2.2 Prometheus Targets

```yaml
- job_name: 'backend'
  static_configs:
    - targets: ['localhost:8000']

- job_name: 'frontend'
  static_configs:
    - targets: ['localhost:3000']

- job_name: 'nginx'
  static_configs:
    - targets: ['localhost:9113']  # nginx-exporter

- job_name: 'postgres'
  static_configs:
    - targets: ['localhost:9187']

- job_name: 'redis'
  static_configs:
    - targets: ['localhost:9121']

- job_name: 'gpu'
  static_configs:
    - targets: ['localhost:9400']  # DCGM exporter
```

---

# 📑 3. Logging Architecture (Loki)

Loki는 DreamSeedAI MegaCity 전체의 로그를 저장하는 **분산 로그 플랫폼**입니다.

## 3.1 수집되는 로그 종류

* FastAPI 로그 (Access / Error)
* Nginx/Traefik Proxy 로그
* Worker/Queue 로그
* GPU inference 로그 (vLLM, Whisper, PoseNet)
* Database Error 로그
* Policy Engine 로그 (정책 위반 기록)

## 3.2 Promtail 설정 (Agent)

```yaml
scrape_configs:
  - job_name: fastapi
    static_configs:
      - targets: ['localhost']
        labels:
          job: fastapi
          __path__: /var/log/fastapi/*.log

  - job_name: nginx
    static_configs:
      - targets: ['localhost']
        labels:
          job: nginx
          __path__: /var/log/nginx/*.log
```

---

# 🔎 4. Tracing Architecture (Tempo / Jaeger)

Tracing은 **요청이 어디서 느려졌는지**, **AI inference가 어느 단계에서 정체되는지**
정확히 시각화합니다.

## 4.1 트레이싱이 필요한 주요 경로

* Next.js → FastAPI → DB → Redis
* FastAPI → GPU(vLLM/Whisper) → 응답
* Worker → Storage 업로드 → 응답
* ExamSession → CAT Engine → AI Tutor 흐름

## 4.2 FastAPI Tracing 설정

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://tempo:4318/v1/traces"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

FastAPIInstrumentor.instrument_app(app)
AsyncPGInstrumentor().instrument()
```

---

# 📈 5. Grafana Dashboards (Visualization)

MegaCity는 **Zone별 / 서비스별 / AI별로 분리된 7종 대시보드 세트**를 운영합니다.

## 5.1 Dashboard #1 — MegaCity Overview

* 전체 트래픽 흐름
* 도메인별 요청 수
* 구역별 에러율
* 전체 p95 latency
* 활성 사용자(Active Users)

## 5.2 Dashboard #2 — API Performance

* endpoint별 latency(p50/p90/p95/p99)
* FastAPI concurrency
* CPU/RAM usage
* 실패 요청(5xx/4xx)

## 5.3 Dashboard #3 — GPU AI Cluster

* Whisper latency
* PoseNet 분석 시간
* vLLM token throughput
* GPU utilization / memory
* AI queue backlog

## 5.4 Dashboard #4 — Database (PostgreSQL)

* connection pool usage
* slow query 리스트
* table size growth
* index hit ratio

## 5.5 Dashboard #5 — Redis / Queue

* hit/miss rate
* worker job count
* retry count
* stream backlog

## 5.6 Dashboard #6 — Reverse Proxy

* Nginx/Traefik 요청량
* TLS negotiation time
* Cache HIT/MISS

## 5.7 Dashboard #7 — K-Zone AI

* Dance pose estimation delay
* Voice Tutor 분석 속도
* Drama Coach 감정 분석 latency
* Creator Studio 영상 렌더링 시간

---

# 🚨 6. Alerting Architecture (AlertManager)

Alert은 **24/7 MegaCity 건강**을 책임지는 마지막 보호벽입니다.

## 6.1 Critical Alerts (즉각적 페이징)

* API Error Rate > **5%** (1분)
* p95 latency > **2.0s** (5분)
* GPU latency > **10s** 지속
* Database connection 90% 초과
* Redis down

## 6.2 Warning Alerts (Slack)

* API Error Rate > **1%** (5분)
* Cache hit < **70%**
* Disk Usage > **80%**
* WAL archive 지연 > **10분**

## 6.3 Info Alerts (대시보드)

* 버전 배포
* 모델 교체
* 정책 위반 증가

## 6.4 Example Rule

```yaml
- alert: HighAPILatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "API Latency p95 is over 2 seconds"
    description: "Observed value = {{ $value }}s"
```

---

# 🧪 7. Synthetic Monitoring

Cloudflare + k6를 함께 사용한 Synthetic Test:

* 로그인 프로세스 점검
* ExamStart API 99th percentile
* AI inference pipeline 측정

```bash
k6 run loadtests/exam_start.js
```

---

# 🧱 8. Log Aggregation & Long-term Retention

* Loki: 7일~30일 operational logs
* S3/R2: 1년 이상 archive logs

Retention 전략:

```
operational logs → 30일
AI inference logs → 90일
security logs → 1년 (GDPR/PIPA)
```

---

**문서 완료 - DreamSeedAI MegaCity Monitoring & Observability Architecture v1.0**
