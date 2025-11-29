# 🏗️ 하이브리드 아키텍처 설계

> **로컬 RTX 5090 GPU + 최소 클라우드 전략**  
> **작성일**: 2025년 11월 10일  
> **목표**: 100만 유저 / 1만 동시접속을 월 $200~$500으로 운영

---

## 📌 Executive Summary

### 현재 상황
- **보유 자산**: RTX 5090 32GB × 1대
- **계획**: RTX 5090 추가 구입 (총 3~4대)
- **경험**: GCP $1,600/월 청구 → 비용 최적화 필요

### 하이브리드 전략
```
┌─────────────────────────────────────────────────────────┐
│ 클라우드 (최소)                                          │
│ - API 서버: Cloud Run (Scale-to-zero)                   │
│ - CDN: Cloudflare (무제한 트래픽)                        │
│ - 스토리지: R2/Backblaze B2 (저렴한 오브젝트)            │
│ - 백업: 일일 스냅샷 → Glacier                           │
└─────────────────────────────────────────────────────────┘
                          ↕ gRPC/HTTP
┌─────────────────────────────────────────────────────────┐
│ 로컬 (핵심)                                             │
│ - LLM Inference: RTX 5090 × 3대 (vLLM)                 │
│ - PostgreSQL: NVMe SSD (고성능)                         │
│ - Redis: 로컬 클러스터 (낮은 지연)                       │
│ - Kafka: 로컬 브로커 (이벤트 스트림)                     │
└─────────────────────────────────────────────────────────┘
```

### 비용 비교

| 아키텍처 | 월 비용 | 확장성 | 지연시간 | 장애 복구 |
|---------|---------|--------|----------|-----------|
| **풀 클라우드** (GCP/AWS) | $1,500~$3,000 | ⭐⭐⭐⭐⭐ | 50~100ms | 자동 |
| **하이브리드** (권장) | **$200~$500** | ⭐⭐⭐⭐ | 10~30ms | 수동+자동 |
| **풀 온프렘** | $100~$150 | ⭐⭐ | <10ms | 수동 |

---

## 🎯 A) 아키텍처 개요

### 1️⃣ 전체 구조도

```
                    인터넷
                      ↓
         ┌────────────────────────┐
         │   Cloudflare CDN       │ ← WAF, DDoS 방어, 캐시
         │   (Pro: $20/월)        │
         └────────────────────────┘
                      ↓
         ┌────────────────────────┐
         │   Cloud Run API        │ ← 무상태 API 서버
         │   (min=0, max=10)      │    Scale-to-zero
         │   ($50~$150/월)        │
         └────────────────────────┘
                      ↓ gRPC (내부망)
    ┌─────────────────────────────────────┐
    │      로컬 데이터센터 (집/오피스)      │
    │                                     │
    │  ┌──────────────────────────────┐  │
    │  │  RTX 5090 GPU Farm           │  │
    │  │  ┌─────┐ ┌─────┐ ┌─────┐    │  │
    │  │  │ #1  │ │ #2  │ │ #3  │    │  │ ← vLLM/TGI
    │  │  │32GB │ │32GB │ │32GB │    │  │    LLM 서빙
    │  │  └─────┘ └─────┘ └─────┘    │  │
    │  └──────────────────────────────┘  │
    │                                     │
    │  ┌──────────────────────────────┐  │
    │  │  PostgreSQL Primary          │  │ ← NVMe SSD
    │  │  (32GB RAM, 2TB NVMe)        │  │    고성능 DB
    │  └──────────────────────────────┘  │
    │           ↓ 비동기 복제              │
    │  ┌──────────────────────────────┐  │
    │  │  Redis Cluster (3 nodes)     │  │ ← 캐시 레이어
    │  └──────────────────────────────┘  │
    │                                     │
    │  ┌──────────────────────────────┐  │
    │  │  Kafka (3 brokers)           │  │ ← 이벤트 큐
    │  └──────────────────────────────┘  │
    └─────────────────────────────────────┘
                      ↓ 백업 (야간)
         ┌────────────────────────┐
         │   Backblaze B2         │ ← 오브젝트 스토리지
         │   ($5/TB/월)           │    저렴한 백업
         └────────────────────────┘
```

### 2️⃣ 트래픽 흐름

```
사용자 요청 → Cloudflare → Cloud Run API → gRPC → 로컬 GPU
    ↓                                              ↓
정적 자산 캐시 (95% 히트)                    LLM 생성
    ↓                                              ↓
CDN에서 즉시 응답                          Redis 캐시 확인
                                                   ↓
                                            PostgreSQL 조회
                                                   ↓
                                            Kafka 이벤트 발행
                                                   ↓
                                            응답 → Cloud Run → 사용자
```

---

## 💻 B) 로컬 GPU 팜 설계

### 1️⃣ RTX 5090 사양 및 성능

**단일 GPU 성능**:
- VRAM: 32GB GDDR7
- FP16 성능: ~180 TFLOPS
- 모델 서빙 능력:
  - 7B 모델: 600~800 tok/s
  - 13B 모델: 300~400 tok/s
  - 70B 모델: 80~100 tok/s (양자화 필요)

**3대 클러스터 성능**:
```python
# 성능 계산 (보수적 추정)
GPUs = 3
tokens_per_sec_per_gpu = 500  # 평균 (7B~13B 혼합)
total_throughput = GPUs * tokens_per_sec_per_gpu  # 1,500 tok/s

# 동시 처리 가능 요청 수
avg_response_length = 200  # 토큰
concurrent_requests = total_throughput / avg_response_length  # 7.5 req/s
peak_capacity = concurrent_requests * 60  # 450 req/min

# 동접 1만 명 중 동시 AI 생성 비율
concurrent_ai_users = 450
total_concurrent_users = 10000
ai_concurrency_ratio = concurrent_ai_users / total_concurrent_users  # 4.5%
```

**결론**: 
- ✅ 동접 1만 명 중 **4.5%가 동시에 AI 생성**하면 대기 없이 처리
- ✅ 일반적인 EdTech 패턴 (2~3% AI 동시성)에 충분
- ⚠️ 피크타임 대응: 큐잉 + 우선순위 시스템 필요

### 2️⃣ GPU 서버 스펙

```yaml
# 로컬 GPU 서버 × 1대 (3×RTX 5090 탑재)
CPU: AMD Threadripper PRO 5975WX (32코어)
RAM: 128GB DDR4 ECC
GPU: RTX 5090 32GB × 3 (PCIe 4.0 x16)
Storage: 
  - 2TB NVMe Gen4 (모델 저장)
  - 4TB SATA SSD (로그, 캐시)
Network: 10Gbps 이더넷
전력: 2000W PSU (80+ Platinum)
비용: ~$15,000 (일회성)
```

**전기 비용**:
```
소비 전력: 1,500W (풀 로드)
월 가동: 24시간 × 30일 = 720시간
월 전력: 1.5kW × 720h = 1,080 kWh
전기 요금: 1,080 kWh × $0.12/kWh = $130/월
```

### 3️⃣ vLLM 설정

```python
# vllm_server.py
from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine

# GPU 샤딩 설정 (3대 분산)
engine_args = AsyncEngineArgs(
    model="meta-llama/Llama-2-13b-chat-hf",
    tensor_parallel_size=3,  # 3개 GPU로 분산
    dtype="float16",
    max_model_len=4096,
    gpu_memory_utilization=0.9,
    enable_prefix_caching=True,  # 프롬프트 캐시
)

engine = AsyncLLMEngine.from_engine_args(engine_args)

# 요청 큐 처리
async def process_request(prompt: str, user_id: str):
    # 우선순위 큐잉
    priority = get_user_priority(user_id)  # 유료 > 무료
    
    # 캐시 확인
    cache_key = hash(prompt)
    if cached := await redis.get(cache_key):
        return cached
    
    # LLM 생성
    result = await engine.generate(prompt, SamplingParams(
        temperature=0.7,
        top_p=0.9,
        max_tokens=200,
    ))
    
    # 캐시 저장 (1시간 TTL)
    await redis.setex(cache_key, 3600, result)
    
    return result
```

### 4️⃣ 부하 분산 전략

```python
# load_balancer.py
from collections import deque
from dataclasses import dataclass
from enum import Enum

class Priority(Enum):
    PREMIUM = 1  # 유료 유저
    STANDARD = 2  # 무료 유저
    BATCH = 3  # 백그라운드 작업

@dataclass
class Request:
    id: str
    prompt: str
    priority: Priority
    timestamp: float

class GPULoadBalancer:
    def __init__(self, num_gpus=3):
        self.queues = {
            Priority.PREMIUM: deque(),
            Priority.STANDARD: deque(),
            Priority.BATCH: deque(),
        }
        self.gpu_workers = [GPUWorker(i) for i in range(num_gpus)]
    
    async def enqueue(self, request: Request):
        """우선순위 큐에 추가"""
        self.queues[request.priority].append(request)
        await self.dispatch()
    
    async def dispatch(self):
        """유휴 GPU에 작업 할당"""
        for worker in self.gpu_workers:
            if not worker.is_busy():
                # PREMIUM → STANDARD → BATCH 순서로 처리
                for priority in Priority:
                    if self.queues[priority]:
                        req = self.queues[priority].popleft()
                        await worker.process(req)
                        break
```

---

## ☁️ C) 최소 클라우드 설계

### 1️⃣ Cloud Run API 서버

**장점**:
- Scale-to-zero (유휴 시 $0)
- 자동 HTTPS 인증서
- 자동 로드 밸런싱
- 리전별 배포 가능

**설정**:
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: dreamseed-api
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/target: "80"
    spec:
      containerConcurrency: 100
      timeoutSeconds: 300
      containers:
      - image: gcr.io/PROJECT_ID/api-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: GPU_ENDPOINT
          value: "https://your-home-ip:8000"  # 로컬 GPU gRPC
        - name: REDIS_URL
          value: "redis://localhost:6379"
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
```

**비용**:
```
요청 수: 1M req/월
CPU 시간: 100ms/req × 2 vCPU = 200 vCPU-ms
메모리: 4GB × 100ms = 400 GB-ms

비용 계산:
- vCPU: $0.00002400/vCPU-second × (200ms × 1M req) = $48
- 메모리: $0.00000250/GB-second × (400ms × 1M req) = $10
- 요청: $0.40/M requests × 1M = $0.40

합계: ~$58/월 (1M 요청 기준)
```

### 2️⃣ Cloudflare CDN

**기능**:
- 무제한 대역폭 (Pro 플랜)
- DDoS 방어
- WAF (Web Application Firewall)
- 자동 캐싱
- SSL/TLS 인증서

**설정**:
```nginx
# Cloudflare Page Rules
# 1. 정적 자산 캐시 (1년)
*.dreamseed.ai/static/*
  Cache Level: Cache Everything
  Edge Cache TTL: 1 year

# 2. API 캐시 (5분)
api.dreamseed.ai/v1/questions/*
  Cache Level: Cache Everything
  Edge Cache TTL: 5 minutes

# 3. 이미지 최적화
*.dreamseed.ai/images/*
  Polish: Lossless
  Mirage: On
```

**비용**:
- Free: $0 (제한적)
- Pro: **$20/월** (무제한 트래픽)
- Business: $200/월 (고급 WAF)

### 3️⃣ Backblaze B2 스토리지

**용도**:
- 정적 자산 (이미지, PDF)
- 일일 백업 (DB, 모델)
- 사용자 업로드 파일

**비용**:
```
저장: 1TB × $5/TB = $5/월
다운로드: 100GB × $0.01/GB = $1/월 (Cloudflare 파트너십으로 무료)
트랜잭션: 무시 가능

합계: ~$5~10/월
```

**설정**:
```python
# b2_backup.py
import b2sdk.v2 as b2

# B2 클라이언트
info = b2.InMemoryAccountInfo()
b2_api = b2.B2Api(info)
b2_api.authorize_account("production", APPLICATION_KEY_ID, APPLICATION_KEY)

# 일일 백업 (PostgreSQL)
bucket = b2_api.get_bucket_by_name("dreamseed-backups")

def daily_backup():
    # DB 덤프
    os.system("pg_dump dreamseed > /tmp/backup.sql")
    
    # B2 업로드
    local_file = "/tmp/backup.sql"
    b2_file_name = f"postgres/backup_{datetime.now():%Y%m%d}.sql"
    
    bucket.upload_local_file(
        local_file=local_file,
        file_name=b2_file_name,
        file_infos={"timestamp": str(datetime.now())}
    )
    
    print(f"Backup uploaded: {b2_file_name}")
```

---

## 🔗 D) 로컬 ↔ 클라우드 연결

### 1️⃣ gRPC 통신

**왜 gRPC인가?**
- HTTP/2 기반 (멀티플렉싱)
- 프로토콜 버퍼 (바이너리, 빠름)
- 양방향 스트리밍
- 타입 안정성

**프로토콜 정의**:
```protobuf
// llm_service.proto
syntax = "proto3";

service LLMService {
  rpc Generate(GenerateRequest) returns (GenerateResponse);
  rpc GenerateStream(GenerateRequest) returns (stream GenerateResponse);
}

message GenerateRequest {
  string prompt = 1;
  string user_id = 2;
  int32 max_tokens = 3;
  float temperature = 4;
  Priority priority = 5;
}

message GenerateResponse {
  string text = 1;
  int32 tokens_generated = 2;
  float latency_ms = 3;
}

enum Priority {
  BATCH = 0;
  STANDARD = 1;
  PREMIUM = 2;
}
```

**서버 (로컬 GPU)**:
```python
# grpc_server.py
import grpc
from concurrent import futures
import llm_service_pb2_grpc

class LLMServicer(llm_service_pb2_grpc.LLMServiceServicer):
    def Generate(self, request, context):
        # vLLM 호출
        result = await vllm_engine.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        return llm_service_pb2.GenerateResponse(
            text=result.text,
            tokens_generated=result.num_tokens,
            latency_ms=result.latency,
        )

# gRPC 서버 시작
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
llm_service_pb2_grpc.add_LLMServiceServicer_to_server(LLMServicer(), server)
server.add_insecure_port('[::]:50051')
server.start()
```

**클라이언트 (Cloud Run)**:
```python
# grpc_client.py
import grpc
import llm_service_pb2_grpc

# gRPC 채널 (로컬 GPU 서버)
channel = grpc.insecure_channel('YOUR_HOME_IP:50051')
stub = llm_service_pb2_grpc.LLMServiceStub(channel)

async def call_llm(prompt: str, user_id: str):
    request = llm_service_pb2.GenerateRequest(
        prompt=prompt,
        user_id=user_id,
        max_tokens=200,
        temperature=0.7,
        priority=get_user_priority(user_id),
    )
    
    response = stub.Generate(request, timeout=30)
    return response.text
```

### 2️⃣ 네트워크 보안

**문제**: 집/오피스 IP가 동적이면?

**해결책 1: Tailscale (권장)**
```bash
# 로컬 GPU 서버
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Cloud Run에서 Tailscale IP로 접근
# 예: 100.64.1.2:50051
```

**해결책 2: Cloudflare Tunnel**
```bash
# 로컬 서버에 Tunnel 설치
cloudflared tunnel create dreamseed-gpu
cloudflared tunnel route dns dreamseed-gpu gpu.dreamseed.ai

# Cloud Run에서 접근
# gpu.dreamseed.ai:50051
```

**해결책 3: 고정 IP + VPN**
```bash
# 비즈니스 인터넷 (고정 IP) + WireGuard VPN
# Cloud Run → VPN → 로컬 GPU
```

---

## 💾 E) 로컬 데이터베이스 설계

### 1️⃣ PostgreSQL 고성능 설정

**하드웨어**:
- CPU: 16코어
- RAM: 32GB
- Storage: 2TB NVMe Gen4 (7,000 MB/s 읽기)

**튜닝**:
```sql
-- postgresql.conf
shared_buffers = 8GB              # 25% of RAM
effective_cache_size = 24GB       # 75% of RAM
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1            # NVMe SSD
effective_io_concurrency = 200
work_mem = 64MB
min_wal_size = 2GB
max_wal_size = 8GB
max_worker_processes = 16
max_parallel_workers_per_gather = 4
max_parallel_workers = 16
```

**성능 목표**:
```
TPS: 5,000~10,000 (읽기 위주)
쓰기: 500~1,000 TPS
지연: p95 < 5ms (로컬)
동시 접속: 500 connections
```

### 2️⃣ 클라우드 백업 전략

```bash
#!/bin/bash
# daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/postgres_$DATE.sql.gz"

# 1. PostgreSQL 덤프
pg_dump -U postgres dreamseed | gzip > $BACKUP_FILE

# 2. Backblaze B2 업로드
b2 upload-file dreamseed-backups $BACKUP_FILE postgres/$DATE.sql.gz

# 3. 30일 이상 된 백업 삭제
b2 ls dreamseed-backups postgres/ | \
  awk -v cutoff=$(date -d '30 days ago' +%Y%m%d) '$1 < cutoff {print $2}' | \
  xargs -I {} b2 delete-file-version dreamseed-backups {}

# 4. 로컬 임시 파일 삭제
rm $BACKUP_FILE

echo "Backup completed: $DATE"
```

**Cron 설정**:
```cron
# 매일 새벽 3시 백업
0 3 * * * /home/scripts/daily_backup.sh >> /var/log/backup.log 2>&1
```

### 3️⃣ 재해 복구 (DR)

**RPO/RTO 목표**:
- RPO (Recovery Point Objective): 15분
- RTO (Recovery Time Objective): 1시간

**전략**:
```yaml
# DR 절차
1. 로컬 PostgreSQL 장애 감지 (Health Check 실패)
   ↓
2. 자동으로 Cloud SQL 리드온리 레플리카로 전환
   ↓
3. 수동으로 Cloud SQL을 Primary로 승격
   ↓
4. 로컬 서버 복구 후 다시 Primary로 전환
```

**Cloud SQL 대기 서버** (최소 사양):
```bash
# Cloud SQL 생성 (평소엔 정지, 장애 시만 기동)
gcloud sql instances create dreamseed-dr \
  --tier=db-f1-micro \  # 최소 사양 ($7.67/월)
  --region=asia-northeast3 \
  --database-version=POSTGRES_15 \
  --backup-start-time=04:00 \
  --enable-bin-log \
  --availability-type=zonal  # HA 불필요 (DR용)
```

---

## 📊 F) 비용 분석

### 1️⃣ 월별 운영비 (3×RTX 5090 기준)

| 항목 | 비용 | 비고 |
|------|------|------|
| **로컬 전기** | $130 | 1,500W × 720h × $0.12/kWh |
| **Cloud Run** | $50~$150 | 요청 수에 따라 변동 |
| **Cloudflare Pro** | $20 | 고정 (무제한 트래픽) |
| **Backblaze B2** | $10 | 1TB 스토리지 + 백업 |
| **고정 IP** | $10 | 비즈니스 인터넷 추가 요금 |
| **Cloud SQL (DR)** | $8 | 평소 정지, 필요 시만 기동 |
| **도메인/SSL** | $2 | 연 $24 ÷ 12 |
| **합계** | **$230~$330** | 평균 **$280/월** |

### 2️⃣ 초기 투자 비용

| 항목 | 비용 | 비고 |
|------|------|------|
| RTX 5090 × 3 | $6,000 | $2,000/개 |
| GPU 서버 (베어본) | $5,000 | CPU, RAM, 케이스, PSU |
| NVMe SSD 2TB × 2 | $400 | 모델 + DB 저장 |
| 네트워크 장비 | $300 | 10Gbps 스위치 |
| UPS (무정전) | $500 | 1,500W 백업 |
| **합계** | **$12,200** | 일회성 |

**ROI 계산**:
```
풀 클라우드 비용: $1,500/월
하이브리드 비용: $280/월
월간 절감액: $1,220

투자 회수 기간: $12,200 / $1,220 = 10개월
2년 총 절감액: $1,220 × 24 = $29,280
```

### 3️⃣ 유저 수별 비용 시뮬레이션

| 유저 수 | 동접 | API RPS | Cloud Run | 로컬 GPU | 전기 | 총 비용 |
|---------|------|---------|-----------|----------|------|---------|
| 1,000 | 100 | 10 | $20 | 1대 | $50 | **$100** |
| 10,000 | 500 | 50 | $50 | 2대 | $90 | **$180** |
| 100,000 | 3,000 | 300 | $120 | 3대 | $130 | **$290** |
| 500,000 | 7,000 | 700 | $250 | 4대 | $180 | **$480** |
| 1,000,000 | 10,000 | 1,000 | $400 | 5대 | $230 | **$710** |

---

## 🔧 G) 구현 로드맵

### Phase 1: 프로토타입 (Week 1~2)

**목표**: RTX 5090 1대로 MVP 검증

```bash
# Day 1-2: 로컬 vLLM 서버 구축
docker run -d \
  --gpus all \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-2-7b-chat-hf \
  --tensor-parallel-size 1

# Day 3-4: Cloud Run API 배포
gcloud run deploy dreamseed-api \
  --image gcr.io/PROJECT_ID/api-server \
  --min-instances=0 \
  --max-instances=3

# Day 5-6: Cloudflare 설정
# - DNS 이전
# - SSL 인증서
# - 캐시 정책

# Day 7: 부하 테스트
k6 run --vus 100 --duration 5m load_test.js
```

### Phase 2: 확장 (Week 3~4)

**목표**: RTX 5090 3대 클러스터 구축

```bash
# GPU 2대 추가 구입 및 설치
# vLLM 텐서 병렬화 (3-way)

docker run -d \
  --gpus all \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-2-13b-chat-hf \
  --tensor-parallel-size 3  # 3개 GPU 분산

# Redis 클러스터 구축
docker-compose up -d redis-cluster

# Kafka 브로커 설정
docker-compose up -d kafka
```

### Phase 3: 최적화 (Week 5~8)

**목표**: 프로덕션 레벨 안정성

- [ ] 모니터링 (Prometheus + Grafana)
- [ ] 자동 백업 (매일 3AM)
- [ ] DR 리허설 (월 1회)
- [ ] 부하 테스트 (1만 동접)
- [ ] 캐시 최적화 (히트율 95%+)

---

## 🛡️ H) 장애 대응

### 1️⃣ GPU 장애

**증상**: vLLM 서버 응답 없음

**대응**:
```bash
# 1. GPU 상태 확인
nvidia-smi

# 2. GPU 리셋
sudo nvidia-smi --gpu-reset

# 3. vLLM 재시작
docker restart vllm-server

# 4. 여전히 실패 시 Cloud GPU로 Failover
# (GCP A100 Spot Instance 자동 기동)
gcloud compute instances start gpu-failover-1 --zone=us-central1-a
```

### 2️⃣ 네트워크 단절

**증상**: Cloud Run → 로컬 GPU 연결 끊김

**대응**:
```python
# grpc_client.py에 Retry 로직
import grpc
from grpc import RpcError

async def call_llm_with_retry(prompt: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await call_llm(prompt)
        except RpcError as e:
            if attempt == max_retries - 1:
                # Fallback: OpenAI API
                return await openai_fallback(prompt)
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 3️⃣ 정전

**대응**:
```yaml
# UPS (무정전 전원)
- 용량: 1,500W × 10분 = 충분한 종료 시간
- 자동 종료 스크립트 (UPS 배터리 20% 이하 시)

#!/bin/bash
# ups_shutdown.sh
BATTERY=$(apcaccess | grep BCHARGE | awk '{print $3}' | tr -d '%')

if [ $BATTERY -lt 20 ]; then
  # Graceful shutdown
  docker stop vllm-server
  systemctl stop postgresql
  shutdown -h now
fi
```

---

## 📈 I) 성능 최적화

### 1️⃣ 캐시 전략

```python
# cache_strategy.py
from functools import lru_cache
import hashlib

class LLMCache:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def get_cache_key(self, prompt: str, params: dict) -> str:
        """프롬프트 + 파라미터 해시"""
        data = f"{prompt}:{params['temperature']}:{params['max_tokens']}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def get_or_generate(self, prompt: str, params: dict):
        cache_key = self.get_cache_key(prompt, params)
        
        # 캐시 확인
        if cached := await self.redis.get(cache_key):
            return {"text": cached, "cache_hit": True}
        
        # LLM 생성
        result = await vllm_generate(prompt, params)
        
        # 캐시 저장 (1시간 TTL)
        await self.redis.setex(cache_key, 3600, result)
        
        return {"text": result, "cache_hit": False}
```

**예상 히트율**:
- 시험 문제: 90% (동일 문제 반복 출제)
- AI 피드백: 70% (유사 오답 패턴)
- 추천: 50% (협업 필터링)

### 2️⃣ 배치 처리

```python
# batch_processor.py
import asyncio

class BatchProcessor:
    def __init__(self, batch_size=8, max_wait_ms=100):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.queue = []
    
    async def add_request(self, request):
        self.queue.append(request)
        
        if len(self.queue) >= self.batch_size:
            await self.process_batch()
    
    async def process_batch(self):
        """배치 처리로 GPU 효율 극대화"""
        batch = self.queue[:self.batch_size]
        self.queue = self.queue[self.batch_size:]
        
        # vLLM 배치 생성
        prompts = [req.prompt for req in batch]
        results = await vllm_engine.generate_batch(prompts)
        
        # 결과 반환
        for req, result in zip(batch, results):
            req.set_result(result)
```

**배치 효과**:
- 단일 요청: 200 tok/s
- 배치 8개: 1,200 tok/s (6배 향상)

---

## 🎯 J) 결론

### 하이브리드가 최선인 이유

| 기준 | 풀 클라우드 | **하이브리드** | 풀 온프렘 |
|------|-------------|----------------|-----------|
| 비용 | ❌ $1,500/월 | ✅ $280/월 | ✅ $150/월 |
| 확장성 | ✅ 무제한 | ✅ 충분 | ❌ 제한적 |
| 지연 | 🟡 50ms | ✅ 15ms | ✅ 5ms |
| 안정성 | ✅ 99.95% | 🟡 99.5% | ❌ 95% |
| 관리 | ✅ 쉬움 | 🟡 보통 | ❌ 어려움 |
| **총평** | 비쌈 | **균형** | 위험 |

### 스타트업 런웨이

```
초기 자금: $20,000
월 운영비: $280
런웨이: 71개월 (거의 6년)

vs 풀 클라우드:
월 운영비: $1,500
런웨이: 13개월 (1년)

차이: 58개월 (거의 5년 추가 생존)
```

### 다음 단계

이제 **ELASTIC_SCALING_PLAN.md**로 유저 수 증가에 따른 확장 전략을 정리하겠습니다.

---

**작성**: GitHub Copilot  
**날짜**: 2025년 11월 10일  
**버전**: 1.0  
**이전 문서**: [COST_CRISIS_SOLUTION.md](./COST_CRISIS_SOLUTION.md)  
**다음 문서**: [ELASTIC_SCALING_PLAN.md](./ELASTIC_SCALING_PLAN.md)
