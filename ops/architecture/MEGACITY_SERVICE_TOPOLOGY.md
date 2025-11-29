# 🏙️ DreamSeedAI MegaCity – Service Topology Architecture

**버전:** 1.0 — 2025-11-20  
**작성자:** DreamSeedAI Infrastructure Team

---

📌 **0. Executive Summary**

DreamSeedAI MegaCity는 9개의 전문 교육·AI 도메인으로 이루어진 대규모 멀티테넌트 플랫폼이다. 이 문서는 MegaCity 전체 서비스가 어떤 방식으로 구성되고 상호 연결되는지를 설명하는 "서비스 토폴로지(Service Topology)" 설계 문서이다.

본 문서는 다음 내용을 포함한다:

- 전체 Microservice 구조
- API Gateway / Edge / Reverse Proxy
- 각 서비스의 책임과 종속성
- AI Engine Cluster(vLLM, Whisper, PoseNet)
- Background Worker & Event Stream 구조
- Monitoring / Logging / Observability
- Scaling 정책
- 향후 Multi-region 확장 계획

---

🗺️ **1. MegaCity 전체 서비스 지도 (Service Map)**

```text
                   ┌──────────────────────────────┐
                   │      Cloudflare Edge          │
                   │  DNS / CDN / WAF / SSL / RRL │
                   └───────────┬──────────────────┘
                               │
                     ┌─────────▼─────────┐
                     │ Reverse Proxy /    │
                     │ API Gateway        │
                     │ Nginx / Traefik    │
                     └──┬─────────────┬──┘
                        │             │
      ┌─────────────────▼──┐   ┌──────▼────────────────┐
      │  Frontend Cluster   │   │   Backend Cluster      │
      │  Next.js SSR / SPA  │   │  FastAPI Multi-Service │
      └──────────┬──────────┘   └──────────┬────────────┘
                 │                         │
          ┌──────▼──────┐           ┌──────▼────────────┐
          │ Redis Cache │           │ PostgreSQL (Core)  │
          └──────┬──────┘           └────────┬───────────┘
                 │                            │
       ┌─────────▼────────────┐     ┌────────▼──────────────┐
       │   AI Engine Cluster   │     │  Object Storage (B2/S3)│
       │  vLLM / Whisper /     │     │  Media / Upload / CDN  │
       │  PoseNet / Diffusion  │     └────────┬──────────────┘
       └─────────┬────────────┘              │
                 │                            │
                 └────────────┬───────────────┘
                              │
                     ┌────────▼────────┐
                     │ Monitoring Stack │
                     │ Prometheus       │
                     │ Grafana / Loki   │
                     │ Tempo / Jaeger   │
                     └──────────────────┘
```

---

🧩 **2. Backend Service Topology (FastAPI Multi-Service)**

DreamSeedAI의 모든 백엔드는 단일 FastAPI 앱이 아니라 도메인 구역·기능별 서비스 묶음으로 구성된다.

### 2.1 서비스 목록

**Core Services (공통 기반)**

- core-api: 공유 REST 엔드포인트 (tenant-aware), cross-domain primitives
- auth-service: SSO · JWT · MFA
- user-service: User/Profile/Parent-Child linking
- tenant-service: Zone/Org 관리
- policy-service: StudentPolicy, ExamPolicy
- audit-service: AuditLog 기록

**Education Services**

- exam-service: CAT/IRT 엔진
- item-service: ItemBank
- class-service: Class 관리
- dashboard-service: Teacher/Parent 대시보드
- tutor-service: 1:1 튜터링 세션, 과제 관리, 튜터 대시보드

**K-Zone Services (AI Heavy)**

- voice-ai-service: 발음/노래 분석 (Whisper + librosa)
- dance-ai-service: K-POP 모션 분석 (PoseNet)
- drama-ai-service: 감정/억양/표정 분석
- creator-ai-service: AI 영상·오디오 생성

**Public Services**

- mpc-study-service: 무료 학습 문제 API
- storage-service: 파일 업로드/다운로드

**Background Worker Services**

- worker-service: Celery / RabbitMQ / Redis Stream
- ai-job-queue: 대규모 inference job 관리

---

🧠 **3. AI Engine Topology (GPU Inference Architecture)**

DreamSeedAI는 로컬 GPU 팜 + 외부 API를 혼합한 하이브리드 AI 구조를 가진다.

### 3.1 AI Engine 구성

1) **vLLM Cluster**

- Llama 3.1, Qwen2.5, DeepSeek, Seoul-Medium-KR
- Token throughput: 500–1000 tok/s per GPU
- 용도: Essay feedback, Dialogue Tutor, Role-play

2) **Whisper Cluster (음성 인식)**

- Whisper Large-V3 optimized CUDA
- 한국어/영어/일본어 멀티어셋 지원
- 실시간 발음 분석

3) **PoseNet / MoveNet Cluster (댄스 분석)**

- Skeleton Keypoint Extraction
- DTW 기반 동작 비교

4) **Diffusion / Video Generation**

- Shorts 챌린지 AI 비디오 자동 생성
- Thumbnail Generator

### 3.2 AI Routing Logic

AI 요청은 다음 기준으로 AI 엔진을 선택한다:

```text
Zone       Primary AI Model     Secondary
-------------------------------------------
UnivPrep   Local GPT (KR)       GPT-4 / Claude
SkillPrep  Llama 3.1            DeepSeek
My-Ktube.com  Whisper / PoseNet Diffusion
My-Ktube.ai   All AI Engines    Cloud fallback
MPCStudy      Lightweight Models None
```

### 3.3 AI Pipeline 예시

**음성 분석 요청 (voice/analyze):**

```text
User → Cloudflare → api.my-ktube.ai → Gateway → Whisper GPU → Feedback → Frontend
```

**AI Tutor 세션 (tutor/feedback):**

```text
Student → app.univprepai.com → Gateway → tutor-service
   ↓
tutor-service → AI Engine (vLLM)
   ↓ (Essay analysis request)
vLLM (Llama 3.1 70B) → Generate feedback
   ↓
tutor-service → Store session + feedback (PostgreSQL)
   ↓
WebSocket → Frontend (Real-time feedback display)
```

**K-Zone 댄스 분석 (dance/analyze):**

```text
User uploads video → api.my-ktube.ai → storage-service (S3)
   ↓
Redis Stream (video_jobs) → video_worker
   ↓
PoseNet Pod → Skeleton extraction (33 keypoints)
   ↓
DTW Engine → Compare with reference choreography
   ↓
Feedback DB → Frontend (Score + improvement tips)
```

### 3.4 Audio/Video Analysis Pods (K-Zone 전용)

**Pod 구성:**

```yaml
# Kubernetes Pod Spec
apiVersion: v1
kind: Pod
metadata:
  name: audio-analysis-pod
  labels:
    app: kzone-ai
    type: audio-analysis
spec:
  containers:
  - name: whisper-analyzer
    image: dreamseed/whisper-large-v3:cuda12.1
    resources:
      limits:
        nvidia.com/gpu: 1
        memory: 8Gi
      requests:
        nvidia.com/gpu: 1
        memory: 4Gi
    env:
    - name: MODEL_NAME
      value: "whisper-large-v3"
    - name: BATCH_SIZE
      value: "8"
    ports:
    - containerPort: 8001
    volumeMounts:
    - name: model-cache
      mountPath: /models
  
  - name: librosa-processor
    image: dreamseed/librosa:latest
    resources:
      limits:
        memory: 4Gi
      requests:
        memory: 2Gi
    ports:
    - containerPort: 8002
  
  volumes:
  - name: model-cache
    persistentVolumeClaim:
      claimName: ai-model-cache
```

**Video Analysis Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: video-analysis-pod
  labels:
    app: kzone-ai
    type: video-analysis
spec:
  containers:
  - name: posenet-analyzer
    image: dreamseed/mediapipe-posenet:latest
    resources:
      limits:
        nvidia.com/gpu: 1
        memory: 6Gi
      requests:
        nvidia.com/gpu: 1
        memory: 3Gi
    env:
    - name: MODEL_COMPLEXITY
      value: "2"
    - name: MIN_DETECTION_CONFIDENCE
      value: "0.5"
    ports:
    - containerPort: 8003
  
  - name: emotion-detector
    image: dreamseed/emotion-recognition:latest
    resources:
      limits:
        memory: 4Gi
      requests:
        memory: 2Gi
    ports:
    - containerPort: 8004
```

**Analysis Pipeline Flow:**

```
1. Audio Analysis Pipeline:
   User uploads audio (MP3/WAV)
   → API Gateway → storage-service (S3)
   → Redis Stream (ai_jobs)
   → Whisper Pod (음성 → 텍스트)
   → librosa Pod (발음/피치/리듬 분석)
   → Feedback DB 저장
   → WebSocket → Frontend (실시간 결과)

2. Video Analysis Pipeline:
   User uploads video (MP4/WebM)
   → API Gateway → storage-service
   → Redis Stream (video_jobs)
   → PoseNet Pod (스켈레톤 추출)
   → DTW Pod (동작 비교)
   → Emotion Pod (표정 분석)
   → 결과 합성 → Frontend
```

**Pod Scaling 정책:**

| 조건 | Action |
|------|--------|
| Queue depth > 50 | Scale up to 5 pods |
| Queue depth < 10 | Scale down to 1 pod |
| GPU utilization > 80% | Add 1 GPU pod |
| Processing time > 30s | Alert + investigate |

---

🔄 **4. Eventing & Worker Topology**

비동기 작업은 Redis Streams 또는 Kafka로 처리한다.

### 4.1 Queue 구조

```text
redis-streams:
  ai_jobs
  exam_scoring
  video_render
  audio_normalize
```

### 4.2 Worker 모듈 (Queue 매핑)

**Worker → Queue 매핑:**

- `ai_worker` → `ai_jobs` 큐 소비
  - Whisper/PoseNet 작업 스케줄링
  - 음성/댄스 분석 처리
  
- `audio_worker` → `audio_normalize` 큐 소비
  - 오디오 정규화, 노이즈 제거
  - MP3/WAV 포맷 변환
  
- `video_worker` → `video_render` 큐 소비
  - Creator Studio 영상 생성
  - 썸네일 생성, 자막 합성
  
- `exam_worker` → `exam_scoring` 큐 소비
  - CAT 점수 후처리
  - IRT 파라미터 업데이트

### 4.3 Scaling 정책

- AI Job 증가 → GPU worker autoscale
- Exam traffic 증가 → exam_worker autoscale

### 4.4 Message Queue Architecture (Redis Stream / Kafka 비교)

**현재 구성: Redis Streams (Phase 1)**

```python
# Redis Streams 구현
import redis
from redis.commands.stream import StreamCommands

redis_client = redis.Redis(host='redis-cluster', port=6379)

# Producer: AI Job 생성
def enqueue_ai_job(user_id: int, job_type: str, payload: dict):
    job_id = redis_client.xadd(
        'ai_jobs',
        {
            'user_id': user_id,
            'job_type': job_type,
            'payload': json.dumps(payload),
            'created_at': datetime.utcnow().isoformat()
        }
    )
    return job_id

# Consumer: Worker가 Job 처리
def process_ai_jobs():
    while True:
        messages = redis_client.xread(
            {'ai_jobs': '0'},
            count=10,
            block=5000
        )
        
        for stream, msgs in messages:
            for msg_id, data in msgs:
                job_type = data['job_type']
                payload = json.loads(data['payload'])
                
                # Job 처리
                if job_type == 'voice_analysis':
                    result = analyze_voice(payload)
                elif job_type == 'dance_analysis':
                    result = analyze_dance(payload)
                
                # 처리 완료 표시
                redis_client.xack('ai_jobs', 'worker-group', msg_id)
```

**향후 확장: Kafka (Phase 2)**

```yaml
# Kafka Topics 구조
topics:
  - ai.jobs.voice
  - ai.jobs.dance
  - ai.jobs.video
  - exam.scoring
  - audit.logs
  - notifications

# Kafka Consumer Groups
consumer_groups:
  - voice-workers (3 consumers)
  - dance-workers (2 consumers)
  - exam-workers (5 consumers)
```

**Queue 비교 매트릭스:**

| 특징 | Redis Streams | Kafka |
|------|---------------|-------|
| Throughput | ~10K msg/s | ~1M msg/s |
| Latency | <10ms | 10-100ms |
| Persistence | Limited (AOF) | Full (Disk) |
| Replay | ✅ | ✅ |
| Partitioning | ❌ | ✅ |
| 사용 시점 | Phase 1-2 | Phase 3+ |

---

🗄️ **5. Database & Storage Topology**

### 5.1 PostgreSQL (Central Core DB)

- 단일 DB → org_id + zone_id 기반 논리 분리
- 필수 테이블: org, users, classes, exams, items, attempts
- Materialized View로 Dashboard 최적화

### 5.2 Redis

- Session
- CAT Engine state
- Rate Limit counter
- AI job queue (Streams)

### 5.3 Object Storage (S3/B2/R2)

- AI 생성 이미지/비디오
- 문제 이미지/LaTeX render
- K-pop Motion JSON 데이터

**Media CDN 전달 경로:**
```
User → Cloudflare CDN → Origin (S3/B2/R2)
- Static assets: Cloudflare CDN (300+ PoPs)
- Media files: B2 Origin → Cloudflare CDN
- AI-generated content: S3 → CloudFront/Cloudflare
```

---

🎨 **6. Frontend Topology (Next.js)**

### 6.1 Zone별 앱 구조

- UnivPrepAI → SSR-rich + Student Dashboard
- K-Zone → Media-heavy + Creator Studio

### 6.2 App Router 구조

```text
/app
 ├─ /(public)
 ├─ /courses
 ├─ /exam
 ├─ /class
 ├─ /kzone
 ├─ /creator
 └─ /settings
```

### 6.3 Static Asset Flow

```text
/_next/static → Cloudflare CDN → static.<domain>
```

---

📡 **7. Edge, WAF, CDN Topology (Cloudflare)**

### 7.1 Cloudflare 기능 사용

- DNS
- SSL/TLS
- CDN (static assets)
- WAF (SQLi/XSS 보호)
- R2 (오브젝트 저장)
- KV/Workers (Edge Compute)

### 7.2 Edge Workers 적용 계획

- AI pre-validation
- A/B 테스트
- zone detection
- custom rate limit

---

🕸️ **7.5 Internal Service Mesh (선택: Traefik vs Linkerd vs Istio)**

### 7.5.1 Service Mesh 비교 분석

| 기능 | Traefik | Linkerd | Istio |
|------|---------|---------|-------|
| **복잡도** | 낮음 | 중간 | 높음 |
| **성능 오버헤드** | ~5ms | ~1ms | ~10ms |
| **메모리 사용량** | 50MB/pod | 20MB/pod | 100MB/pod |
| **학습 곡선** | 쉬움 | 보통 | 어려움 |
| **mTLS** | ✅ | ✅ | ✅ |
| **Circuit Breaker** | ✅ | ✅ | ✅ |
| **Observability** | 기본 | 강력 | 매우 강력 |
| **Community** | 중간 | 강력 | 매우 강력 |

### 7.5.2 DreamSeed 선택: **Linkerd** (추천)

**선택 이유:**
1. **경량화**: 메모리 20MB/pod (Istio 대비 1/5)
2. **낮은 레이턴시**: ~1ms 오버헤드 (중요: AI 추론 시간에 영향 최소화)
3. **간단한 설정**: Rust 기반, 설정 복잡도 낮음
4. **강력한 mTLS**: 자동 암호화, 인증서 관리
5. **Observability**: Prometheus/Grafana 기본 통합

**Linkerd 아키텍처:**

```
┌─────────────────────────────────────────┐
│         Linkerd Control Plane           │
│  (linkerd-identity, linkerd-proxy-api)  │
└─────────────────┬───────────────────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
┌────▼────┐  ┌────▼────┐  ┌────▼────┐
│ Service │  │ Service │  │ Service │
│   A     │  │   B     │  │   C     │
│ +Proxy  │  │ +Proxy  │  │ +Proxy  │
└─────────┘  └─────────┘  └─────────┘
  (auth)      (exam)        (ai)
```

### 7.5.3 Linkerd 설치 및 설정

```bash
# 1. Linkerd CLI 설치
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh
export PATH=$PATH:$HOME/.linkerd2/bin

# 2. Linkerd Control Plane 설치
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -

# 3. Linkerd Viz (모니터링) 설치
linkerd viz install | kubectl apply -f -

# 4. 네임스페이스에 자동 Injection 활성화
kubectl annotate namespace dreamseed-backend linkerd.io/inject=enabled
kubectl annotate namespace dreamseed-ai linkerd.io/inject=enabled
kubectl annotate namespace dreamseed-workers linkerd.io/inject=enabled

# 5. 기존 Pod 재시작 (Proxy 주입)
kubectl rollout restart deployment -n dreamseed-backend
```

### 7.5.4 Service Mesh 기능 적용

**1) mTLS 자동 암호화**

```yaml
# 모든 서비스 간 통신이 자동으로 암호화됨
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  annotations:
    linkerd.io/inject: enabled
spec:
  ports:
  - port: 8000
```

**2) Traffic Split (Canary Deployment)**

```yaml
apiVersion: split.smi-spec.io/v1alpha2
kind: TrafficSplit
metadata:
  name: exam-service-split
spec:
  service: exam-service
  backends:
  - service: exam-service-v1
    weight: 90
  - service: exam-service-v2
    weight: 10  # 10% 트래픽만 새 버전으로
```

**3) Circuit Breaker**

```yaml
apiVersion: policy.linkerd.io/v1beta1
kind: Server
metadata:
  name: ai-service
spec:
  podSelector:
    matchLabels:
      app: ai-engine
  port: 8100
  proxyProtocol: HTTP/1
  timeout: 30s
  retries:
    max: 3
    backoff: exponential
```

**4) Rate Limiting**

```yaml
apiVersion: policy.linkerd.io/v1alpha1
kind: HTTPRoute
metadata:
  name: ai-tutor-route
spec:
  parentRefs:
  - name: ai-service
    kind: Service
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api/v1/ai/tutor
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
        - name: X-Rate-Limit
          value: "100-per-minute"
```

### 7.5.5 Service Mesh Observability

**Linkerd Dashboard 접근:**

```bash
linkerd viz dashboard
```

**주요 메트릭:**
- Success Rate (요청 성공률)
- RPS (초당 요청 수)
- Latency (p50, p95, p99)
- TCP Connections

**Prometheus 메트릭 예시:**

```promql
# 서비스 간 성공률
sum(rate(request_total{classification="success"}[1m])) by (dst_service)

# AI 서비스 레이턴시
histogram_quantile(0.99, 
  sum(rate(response_latency_ms_bucket{dst_service="ai-engine"}[1m])) by (le)
)

# Circuit Breaker 트립 횟수
sum(rate(outbound_http_route_backend_requests_total{status="circuit_breaker"}[5m]))
```

---

📊 **8. Monitoring & Observability Topology**

### 8.1 Prometheus Metrics

- API latency
- AI inference duration
- DB queries/sec
- Redis hit rate

### 8.2 Grafana Dashboards

- Zone-level traffic
- AI job usage
- GPU utilization
- CAT Engine performance

### 8.3 Central Logging

- Loki: structured logs
- Tempo/Jaeger: tracing
- AlertManager: Slack alerts

---

🌍 **9. Multi-Region Topology (향후 확장)**

### 9.1 Deployment Topology Evolution

**Phase 1: Single Region (KR/JP) - Current**

```
Region: ap-northeast-2 (Seoul)
├── Frontend Cluster (3 nodes)
├── Backend Cluster (5 nodes)
├── AI GPU Cluster (2 x RTX 5090)
├── PostgreSQL Primary (RDS)
├── Redis Cluster (3 nodes)
└── Object Storage (B2/S3)

Availability Zones:
- ap-northeast-2a (Primary)
- ap-northeast-2c (Standby)
```

**Phase 2: Korea + US East**

```
Region: ap-northeast-2 (Seoul)          Region: us-east-1 (Virginia)
├── Full Stack                          ├── Frontend Cluster
├── AI GPU Cluster (Primary)            ├── Backend Cluster (Read-only)
├── PostgreSQL Primary                  ├── AI GPU Cluster (Replicated)
└── Redis Primary                       ├── PostgreSQL Read Replica
                                        └── Redis Replica
                ↕
        Cross-region replication
        Latency: ~150ms
```

**Phase 3: Global Edge + Multi-modal**

```
Regions:
1. ap-northeast-2 (Seoul) - Primary
2. us-east-1 (Virginia) - Secondary
3. eu-west-1 (Ireland) - Tertiary

Edge Locations (Cloudflare):
- 300+ PoPs globally
- K-Zone 콘텐츠 CDN 강화
- Edge AI pre-processing (Cloudflare Workers)
```

### 9.2 Multi-Region AI Routing

**GeoDNS + AI Model Selection:**

```python
def select_ai_region(user_location: str, model: str) -> str:
    """사용자 위치와 모델 기반 최적 Region 선택"""
    
    # 1. Geo-routing
    if user_location in ['KR', 'JP', 'CN']:
        primary_region = 'ap-northeast-2'
    elif user_location in ['US', 'CA', 'MX']:
        primary_region = 'us-east-1'
    elif user_location in ['EU', 'UK']:
        primary_region = 'eu-west-1'
    else:
        primary_region = 'ap-northeast-2'  # Default
    
    # 2. Model availability check
    available_models = check_model_availability(primary_region)
    
    if model in available_models:
        return primary_region
    else:
        # Fallback to Seoul (모든 모델 보유)
        return 'ap-northeast-2'

# 예시
user_in_usa = select_ai_region('US', 'llama-3.1-70b')
# → 'us-east-1' (로컬 GPU 사용, 레이턴시 최소화)
```

---

⚖️ **9.5 Scaling 정책 (Horizontal / Vertical / GPU Auto Scaling)**

### 9.5.1 Horizontal Pod Autoscaling (HPA)

**Frontend Scaling:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend-nextjs
  minReplicas: 3
  maxReplicas: 20
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
```

**Backend Scaling:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-fastapi
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"  # 1000 RPS/pod
```

### 9.5.2 Vertical Pod Autoscaling (VPA)

**AI Worker VPA:**

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ai-worker-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-worker
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: whisper-worker
      minAllowed:
        memory: "4Gi"
        cpu: "2"
      maxAllowed:
        memory: "16Gi"
        cpu: "8"
      controlledResources:
      - memory
      - cpu
```

### 9.5.3 GPU Auto Scaling

**GPU Node Auto Scaling:**

```yaml
# GKE/EKS Node Pool 설정
apiVersion: v1
kind: NodePool
metadata:
  name: gpu-pool
spec:
  autoscaling:
    enabled: true
    minNodeCount: 2
    maxNodeCount: 10
  nodeConfig:
    machineType: g5.xlarge  # 1x NVIDIA A10G
    accelerators:
    - type: nvidia-tesla-a10g
      count: 1
    taints:
    - key: nvidia.com/gpu
      value: "true"
      effect: NoSchedule
```

**GPU Job Queue-based Scaling:**

```python
# GPU 사용률 기반 Auto Scaling
def check_gpu_scaling():
    # 1. Queue depth 확인
    queue_depth = redis_client.xlen('ai_jobs')
    
    # 2. 현재 GPU Pod 수
    current_pods = len(get_gpu_pods())
    
    # 3. Scaling 결정
    if queue_depth > 100 and current_pods < 10:
        # Scale up
        scale_gpu_pods(current_pods + 2)
    elif queue_depth < 20 and current_pods > 2:
        # Scale down
        scale_gpu_pods(current_pods - 1)

# 메트릭 기반 스케일링
SCALING_RULES = {
    'queue_depth > 50': 'scale_up',
    'gpu_utilization > 80%': 'scale_up',
    'avg_wait_time > 30s': 'scale_up',
    'queue_depth < 10': 'scale_down',
    'gpu_utilization < 30%': 'scale_down'
}
```

### 9.5.4 Scaling Metrics Dashboard

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Frontend RPS** | > 10K | HPA: +5 pods |
| **Backend CPU** | > 70% | HPA: +10 pods |
| **AI Queue Depth** | > 50 jobs | GPU: +1 node |
| **DB Connections** | > 80% | VPA: +2GB RAM |
| **Redis Memory** | > 80% | Add cluster node |
| **GPU Utilization** | > 85% | Add GPU pod |
| **Response Time** | > 3s | Investigate + Scale |

---

🧭 **10. Service Dependency Map**

```text
frontend → gateway → backend → redis + db → ai-engine → storage
backend (exam-service) → ai-engine (vLLM) → storage
backend (creator) → render_worker → storage
parent-service → dashboard-service → db
```

---

🛡️ **10.5 Disaster Recovery (DR) 구조**

### 10.5.1 DR 전략 개요

**목표:**
- **RPO (Recovery Point Objective)**: 15분 (데이터 손실 최대 15분)
- **RTO (Recovery Time Objective)**: 1시간 (서비스 복구 최대 1시간)

**DR 티어 분류:**

| 서비스 | 티어 | RPO | RTO | 복구 방식 |
|--------|------|-----|-----|----------|
| 인증 서비스 | Tier 1 | 0분 | 5분 | Hot Standby |
| 시험 서비스 | Tier 1 | 5분 | 15분 | Warm Standby |
| AI 서비스 | Tier 2 | 15분 | 30분 | Warm Standby |
| 대시보드 | Tier 2 | 30분 | 1시간 | Cold Standby |
| K-Zone 분석 | Tier 3 | 1시간 | 2시간 | Backup Restore |

### 10.5.2 Database DR 구조

**PostgreSQL HA + DR:**

```
Primary DB (ap-northeast-2a)
    ↓ Streaming Replication (sync)
Standby DB (ap-northeast-2c) - Same Region HA
    ↓ Streaming Replication (async)
DR Replica (us-east-1) - Cross-region DR
```

**PostgreSQL 설정:**

```sql
-- Primary DB 설정
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET synchronous_standby_names = 'standby1';

-- Standby DB 설정 (recovery.conf)
standby_mode = 'on'
primary_conninfo = 'host=primary-db port=5432 user=replicator'
restore_command = 'cp /archive/%f %p'
```

**자동 Failover (Patroni):**

```yaml
# Patroni 설정
scope: dreamseed-postgres
name: postgres-primary
restapi:
  listen: 0.0.0.0:8008
  connect_address: postgres-primary:8008

etcd:
  host: etcd-cluster:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 500
        shared_buffers: 8GB
```

### 10.5.3 Redis DR 구조

**Redis Sentinel (HA):**

```
Redis Primary (ap-northeast-2a)
    ↓ Replication
Redis Replica 1 (ap-northeast-2c)
Redis Replica 2 (ap-northeast-2a)

Sentinel Cluster (3 nodes)
    ↓ Auto Failover (30s)
```

**Redis Sentinel 설정:**

```conf
# sentinel.conf
sentinel monitor mymaster redis-primary 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 180000
```

### 10.5.4 AI Model DR (GPU Cluster Backup)

**모델 파일 백업:**

```bash
# 모델 파일 S3 백업 (일 1회)
aws s3 sync /models/llama-3.1-70b/ \
  s3://dreamseed-models-backup/llama-3.1-70b/ \
  --storage-class GLACIER_IR

# DR Region으로 복제
aws s3 sync s3://dreamseed-models-backup/ \
  s3://dreamseed-models-dr-us-east/ \
  --source-region ap-northeast-2 \
  --region us-east-1
```

**GPU 장애 시 대응:**

```
1. GPU 노드 장애 감지 (Prometheus Alert)
   ↓
2. AI Job Queue → 다른 GPU 노드로 라우팅
   ↓
3. 30분 이상 복구 불가 → 외부 API (OpenAI/Anthropic) Fallback
   ↓
4. 비용 알림 (Slack)
```

### 10.5.5 Backup 스케줄

**자동 백업 정책:**

```yaml
# Velero Backup 설정
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
spec:
  schedule: "0 2 * * *"  # 매일 오전 2시
  template:
    includedNamespaces:
    - dreamseed-backend
    - dreamseed-ai
    - dreamseed-workers
    storageLocation: s3-backup
    volumeSnapshotLocations:
    - ebs-snapshots
    ttl: 720h  # 30일 보관
```

**백업 항목:**

| 대상 | 빈도 | 보관 기간 | 저장 위치 |
|------|------|----------|----------|
| PostgreSQL | 1시간 | 7일 | S3 Standard |
| PostgreSQL (Full) | 1일 | 30일 | S3 Glacier |
| Redis Snapshot | 6시간 | 3일 | S3 Standard |
| AI Models | 1일 | 90일 | S3 Glacier Deep |
| User Files | 실시간 | 무제한 | B2/S3 |
| Config/Secrets | 1일 | 90일 | S3 Encrypted |

### 10.5.6 DR 테스트 계획

**월간 DR Drill:**

```
1. DB Failover 테스트 (매월 첫째 주 일요일 03:00)
   - Primary → Standby 전환
   - 검증: 데이터 일관성, RTO 측정
   
2. AI Cluster Failover (매월 둘째 주)
   - Primary GPU → Secondary GPU
   - 검증: Job Queue 처리 연속성
   
3. 전체 Region Failover (분기 1회)
   - ap-northeast-2 → us-east-1
   - 검증: 전체 서비스 복구 시간
```

### 10.5.7 재해 복구 Runbook

**시나리오 1: DB 장애**

```bash
# 1. Standby를 Primary로 승격
pg_ctl promote -D /var/lib/postgresql/data

# 2. Application 연결 문자열 변경
kubectl set env deployment/backend-api \
  DATABASE_URL=postgresql://standby-db:5432/dreamseed

# 3. DNS 업데이트 (Route53)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://failover-db.json
```

**시나리오 2: 전체 Region 장애**

```bash
# 1. DNS Failover to DR Region
aws route53 update-health-check --health-check-id xxx --disabled

# 2. DR Region Standby → Active
kubectl scale deployment --replicas=10 -n dreamseed-backend-dr

# 3. PostgreSQL Replica → Primary 승격
# 4. Redis Replica → Primary 승격
# 5. AI Model 로드 (S3 DR → GPU)
# 6. 서비스 Health Check 확인
```

---

✔️ **11. 결론**

이 문서는 DreamSeedAI MegaCity 전체의 Service Topology를 표준화한 문서로서:

✅ **완전한 Microservices 지도**
- Core API / Auth API / Tutor API
- AI Engine Cluster (vLLM, Whisper, PoseNet)
- Background Worker & Event Stream

✅ **GPU Inference Architecture**
- Audio/Video Analysis Pods 상세 구조
- Pod Scaling 정책 (Queue depth 기반)

✅ **Internal Service Mesh**
- Linkerd 선택 (경량, 저지연)
- mTLS, Circuit Breaker, Traffic Split

✅ **Message Queue**
- Redis Streams (Phase 1)
- Kafka 확장 계획 (Phase 2)

✅ **Scaling 정책**
- Horizontal Pod Autoscaling (HPA)
- Vertical Pod Autoscaling (VPA)
- GPU Auto Scaling (Queue-based)

✅ **Multi-Region Deployment**
- Phase 1: Seoul (Current)
- Phase 2: Seoul + US East
- Phase 3: Global Edge + Multi-modal

✅ **Disaster Recovery**
- RPO: 15분 / RTO: 1시간
- PostgreSQL HA (Patroni)
- Redis Sentinel
- AI Model Backup
- 월간 DR Drill

✅ **Monitoring & Observability**
- Prometheus + Grafana
- Linkerd Dashboard
- Loki + Tempo + Jaeger

---

## 📚 12. 관련 문서

### 내부 문서
- `MEGACITY_DOMAIN_ARCHITECTURE.md` - 도메인 전략 및 DNS 설정
- `MEGACITY_NETWORK_ARCHITECTURE.md` - 네트워크 아키텍처 및 보안
- `MEGACITY_TENANT_ARCHITECTURE.md` - Multi-zone/Multi-tenant 구조
- `MEGACITY_AUTH_SSO_ARCHITECTURE.md` - SSO & 인증 체계
- `backend/API_GUIDE.md` - FastAPI Multi-tenant 구현 가이드

### 외부 참고
- [Linkerd Architecture](https://linkerd.io/2.14/reference/architecture/)
- [Kubernetes HPA Best Practices](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [PostgreSQL HA with Patroni](https://github.com/zalando/patroni)
- [Redis Sentinel Documentation](https://redis.io/docs/management/sentinel/)
- [Velero Backup & DR](https://velero.io/docs/)

---

**MEGACITY_SERVICE_TOPOLOGY v1.0 완성** 🏙️

DreamSeedAI MegaCity의 완전한 서비스 토폴로지가 문서화되었습니다. 이 문서를 기반으로 확장 가능하고 안전한 인프라를 구축하세요!
