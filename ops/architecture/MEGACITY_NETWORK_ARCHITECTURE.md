# 🏙️ DreamSeedAI MegaCity Network Architecture Guide

**버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: DreamSeedAI Infrastructure Team

---

## 🌐 개요 (Overview)

DreamSeedAI MegaCity는 **9개의 독립된 교육·문화·AI 서비스 구역**으로 구성된 대규모 멀티테넌트 플랫폼입니다. 이 문서는 MegaCity 전체를 하나의 네트워크로 통합적으로 유지하고, 각 구역(**UnivPrepAI, CollegePrepAI, SkillPrepAI, MediPrepAI, MajorPrepAI, My-Ktube.com/.ai, mpcstudy.com, DreamSeedAI.com**)이 안전하게 운영될 수 있도록 하는 **종합 네트워크 아키텍처**입니다.

> **용어 정리**: 9개의 Zone (각 Zone은 1개 도메인 또는 2개 도메인으로 구현될 수 있음)  
> 예: K-Zone은 My-Ktube.com + My-Ktube.ai 2개 도메인으로 구성

### 문서 목적

1. 전체 인프라 **Edge → Gateway → Services → Databases → GPU 팜**의 상호 연결 구조를 시각적으로 설명
2. 네트워크·보안·라우팅 정책의 표준화
3. 멀티 도메인(Multi-Zone) 환경에서의 안정적 운영
4. 향후 **K-Zone AI, Multi-modal AI, CBT Platform** 확장을 위한 기반 정리

### 관련 문서

- `MEGACITY_DOMAIN_ARCHITECTURE.md` - 도메인 전략 및 DNS/SSL 설정
- `ops/dns/` - DNS 자동화 및 CI/CD
- `ops/reverse_proxy/` - Nginx/Traefik 설정

---

## 🗺️ 1. MegaCity 전체 네트워크 지도 (High-level Network Map)

```
                   ┌───────────────────────────────┐
                   │        Cloudflare Edge         │
                   │  - DNS / CDN / WAF / SSL       │
                   │  - Rate Limit / Firewall       │
                   │  - DDoS Protection (L3/L4/L7)  │
                   └───────────┬─────────────┬───────┘
                               │             │
                      (www, app, api)   (static assets)
                               │             │
                     ┌─────────▼──────────┐  │
                     │    Reverse Proxy    │  │
                     │ (Nginx / Traefik)   │  │
                     │  - Routing rules    │  │
                     │  - TLS termination  │  │
                     │  - Load balancing   │  │
                     └──┬────────┬─────────┘  │
                        │        │            │
    ┌───────────────────▼──┐   ┌─▼──────────────────┐
    │  Frontend Cluster     │   │   Backend Cluster  │
    │  Next.js SSR / SPA    │   │  FastAPI Services  │
    │  (포트 3000+)          │   │  (포트 8000+)       │
    └──────────┬────────────┘   └─────────┬──────────┘
               │                          │
               │         ┌────────────────┤
               │         │                │
        ┌──────▼──────┐  │       ┌────────▼─────────┐
        │ Redis Cache │  │       │ PostgreSQL DB     │
        │  (세션/TTL) │  │       │ (모든 테넌트/앱)  │
        └──────┬──────┘  │       └────────┬─────────┘
               │         │                │
               │         │                │
     ┌─────────▼─────────▼───────┐   ┌────▼─────────────────┐
     │  GPU Inference Cluster    │   │  File / Media Storage │
     │ (vLLM / Audio / PoseNet)  │   │ (S3 / Backblaze B2)   │
     │  - RTX 5090 x2            │   │  - R2 / MinIO         │
     │  - A100 (optional)        │   │                       │
     └─────────┬─────────────────┘   └────┬─────────────────┘
               │                          │
               └──────────┬───────────────┘
                          │
               ┌──────────▼──────────┐
               │ Monitoring Stack     │
               │ Prometheus / Grafana │
               │ Loki / Tempo / Jaeger│
               └──────────────────────┘
```

---

## 🧩 2. 네트워크 구성 요소 상세 (Components Breakdown)

### 2.1 Cloudflare Edge Layer

**DreamSeedAI 모든 트래픽은 Cloudflare를 통해 통과합니다.**

#### 역할
- **DNS Hosting** (Authoritative)
- **SSL/TLS 처리** (Edge Termination)
- **CDN Cache** (정적 파일)
- **WAF** (Rule 기반 공격 방어)
- **Bot Management**
- **HTTP/2, HTTP/3** 지원
- **DDoS 대응** (L3/L4/L7)
- **Rate Limiting** (Edge level)

#### 공통 엔드포인트 패턴
```
https://www.<domain>          # Landing page
https://app.<domain>          # Application UI
https://api.<domain>          # Backend API
https://static.<domain>       # CDN Static Assets
```

#### 도메인 목록 (9개 구역)
1. `univprepai.com` - 대학 입시 준비
2. `collegeprepai.com` - 전문대/College/편입 준비
3. `skillprepai.com` - 기술 자격증 준비
4. `mediprepai.com` - 의료 전문 자격증
5. `majorprepai.com` - 전공 심화 학습
6. `my-ktube.com` - K-Zone 콘텐츠 허브
7. `my-ktube.ai` - K-Zone AI 서비스
8. `mpcstudy.com` - MPC 학습 플랫폼
9. `dreamseedai.com` - 통합 포털

**각 도메인은 Cloudflare Zone으로 등록되며, NS는 Cloudflare가 제공하는 2개를 사용합니다.**

#### Cloudflare 설정 표준
```yaml
SSL/TLS: Full (Strict)
Always Use HTTPS: On
HSTS: Enabled (max-age 31536000, includeSubDomains, preload)
Auto Minify: HTML, CSS, JS
Brotli: On
HTTP/2: On
HTTP/3 (QUIC): On
```

---

### 2.2 Reverse Proxy Gateway (Nginx / Traefik)

**Cloudflare → Gateway → Application** 구조로 트래픽을 라우팅합니다.

#### Gateway 기능
- **서버별 라우팅** (Host-based routing)
- **도메인/서브도메인 기반 Virtual Hosting**
- **WebSocket 업그레이드 지원**
- **Rate Limit 시행** (Application level)
- **Security Header 부착**
- **Gzip, Brotli 압축**
- **Real IP 복원** (Cloudflare X-Forwarded-For)
- **Health Check** (Upstream 상태 모니터링)

#### 대표 라우팅 규칙

**예시 1: UnivPrepAI.com**
```nginx
www.univprepai.com      → frontend_app (3000)
app.univprepai.com      → frontend_app (3000)
api.univprepai.com      → backend_api (8000)
static.univprepai.com   → static_cdn (9000)
```

**예시 2: My-Ktube.ai (K-Zone AI)**
```nginx
www.my-ktube.ai         → frontend_app (3002)
api.my-ktube.ai         → kzone_ai_api (8100)
static.my-ktube.ai      → static_cdn (9000)
```

#### Nginx 설정 예시 (핵심 부분)
```nginx
# Upstream 정의
upstream backend_api {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream frontend_app {
    least_conn;
    server 127.0.0.1:3000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream kzone_ai_api {
    least_conn;
    server 127.0.0.1:8100 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Rate Limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=app_limit:10m rate=30r/s;

# API 라우팅
server {
    listen 443 ssl http2;
    server_name api.univprepai.com;
    
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend_api;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /ws {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 운영 전략: Nginx vs Traefik 선택 가이드

> **선택 기준:**
> - 단일 서버/전통적 배포 → **Nginx** 중심
> - Docker/Kubernetes·동적 라우팅 중심 → **Traefik** 중심
> - 실제 운영에서는 Nginx(Edge) + Traefik(내부 Service Mesh)를 조합하는 방식도 가능

#### Traefik 설정 예시 (Docker-native)
```yaml
# traefik.yml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  docker:
    exposedByDefault: false
  file:
    directory: /etc/traefik/dynamic
    watch: true

certificatesResolvers:
  cloudflare:
    acme:
      email: ops@dreamseedai.com
      storage: /etc/traefik/acme.json
      httpChallenge:
        entryPoint: web
```

---

### 2.3 Frontend Cluster (Next.js)

각 도메인의 `app.` 은 **Next.js 프론트엔드 클러스터**에서 SSR/CSR 기반으로 동작합니다.

#### 기술 스택
- **Next.js 14+** (App Router)
- **React 18+**
- **TypeScript**
- **TailwindCSS** (스타일링)
- **React Query / TanStack** (데이터 페칭)
- **next-intl** (i18n - ko/en/ja/es)
- **Zustand / Jotai** (상태 관리)

#### 포트 구조
```
3000: Root SSR (DreamSeedAI.com 통합 포털)
3001: UnivPrepAI / CollegePrepAI / SkillPrepAI (공유)
3002: K-Zone Frontend (My-Ktube.com)
3003: Admin Console (내부 관리)
```

#### 주요 기능
- **SSR** (Server-Side Rendering) for SEO
- **ISR** (Incremental Static Regeneration)
- **Client-Side Routing** (빠른 페이지 전환)
- **API Routes** (BFF 패턴 - Backend for Frontend)
- **Middleware** (Auth 체크, 언어 감지)

#### 환경 변수 예시
```bash
NEXT_PUBLIC_API_BASE_URL=https://api.univprepai.com
NEXT_PUBLIC_DOMAIN=univprepai.com
NEXT_PUBLIC_ZONE_ID=univ
NEXT_PUBLIC_GTM_ID=GTM-XXXXX
NEXT_TELEMETRY_DISABLED=1
```

---

### 2.4 Backend Cluster (FastAPI)

백엔드는 **멀티서비스, 멀티도메인 구조**를 공유하는 통합 아키텍처입니다.

#### 제공 기능
- **사용자 인증(Auth)** - JWT, OAuth2, MFA
- **Exam Engine / CAT 엔진** - Adaptive Testing
- **Tutor AI API 호출** - vLLM, OpenAI, Anthropic
- **Dashboard API** (교사/학부모/학생)
- **K-Zone AI 관련 프록시**
- **통합 정책/승인/감사 로그 서비스**
- **Multi-tenant 라우팅** (org_id, zone_id)

#### 포트 구조 예시
```
8000: DreamSeed Unified API (모든 구역 공통)
8001: UnivPrepAI API 구역 (선택적 분리)
8002: SkillPrepAI API 구역
8003: MediPrepAI API 구역
8100: K-Zone AI Inference API (vLLM + Whisper + PoseNet)
```

#### 기술 스택
- **FastAPI 0.110+**
- **Pydantic v2** (데이터 검증)
- **SQLAlchemy 2.0** (ORM)
- **Alembic** (Migration)
- **Redis** (캐싱, 세션)
- **PostgreSQL** (주 데이터베이스)
- **Celery** (비동기 작업 - optional)

#### API 엔드포인트 예시
```
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/users/me
GET    /api/v1/exams/{exam_id}
POST   /api/v1/exams/{exam_id}/start
POST   /api/v1/attempts/{attempt_id}/submit
GET    /api/v1/analytics/dashboard
POST   /api/v1/kzone/voice/analyze
POST   /api/v1/kzone/dance/pose-detection
```

#### Multi-tenant 라우팅 구조
```python
# FastAPI 라우터 예시
@router.get("/exams/{exam_id}")
async def get_exam(
    exam_id: int,
    zone_id: str = Depends(get_zone_from_domain),
    org_id: int = Depends(get_org_from_token),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.zone_id == zone_id,
        Exam.org_id == org_id
    ).first()
    return exam
```

---

### 2.5 Redis Cache Layer

#### 용도
- **세션 저장** (Session Store)
- **Exam Progress 캐싱** (CAT 상태)
- **Adaptive Engine (CAT) 상태 저장**
- **Rate Limit 카운터 저장** (API 보호)
- **K-Zone AI inference queue 관리**
- **Pub/Sub** (실시간 알림)
- **Leaderboard** (SortedSet)

#### 구성
```
redis:6379  (단일 인스턴스)
redis-cluster:6379-6384 (Cluster 모드 - 프로덕션)
```

#### 데이터 구조 예시
```
# 세션
session:{user_id}:{session_id} → JSON (TTL 7일)

# CAT 상태
cat:{attempt_id}:state → JSON (ability, item_pool, history)

# Rate Limit
rate_limit:{ip}:{endpoint} → Counter (TTL 1분)

# K-Zone AI Queue
kzone:queue:voice → List (LPUSH/RPOP)
```

#### Redis 설정 권장사항
```redis
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

---

### 2.6 PostgreSQL Database Layer

**중앙 통합 데이터 저장소** - 모든 구역의 핵심 엔티티를 PostgreSQL에 저장합니다.

#### 구조
- 물리적으로 **단일 DB** → 논리적으로 **multi-tenant** (`org_id`, `zone_id`)
- 향후 구역별 DB 샤딩도 가능

#### 주요 테이블 (스키마)
```sql
-- Users
users (id, email, password_hash, zone_id, org_id, created_at)

-- Organizations (Multi-tenant)
organizations (id, name, zone_id, plan, status)

-- Exams
exams (id, title, zone_id, org_id, exam_type, created_by)

-- Items (문항)
items (id, exam_id, content, difficulty, discrimination, guessing)

-- Attempts (응시)
attempts (id, exam_id, user_id, started_at, finished_at, score)

-- Responses (응답)
responses (id, attempt_id, item_id, response, is_correct, timestamp)

-- K-Zone Content
kzone_contents (id, title, content_type, url, tags, created_at)

-- K-Zone AI Results
kzone_ai_results (id, user_id, task_type, input_url, output_url, metadata)
```

#### 연결 설정
```python
# SQLAlchemy 연결 URL
DATABASE_URL = "postgresql://user:pass@localhost:5432/dreamseed_megacity"

# Connection Pool 설정
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False
)
```

#### 백업 전략
```bash
# 일일 백업 (Cron)
0 3 * * * pg_dump -U postgres dreamseed_megacity | gzip > /backup/db_$(date +\%Y\%m\%d).sql.gz

# PITR (Point-in-Time Recovery)
wal_level = replica
archive_mode = on
archive_command = 'cp %p /archive/%f'
```

---

### 2.7 GPU Inference Cluster (AI Zone)

#### 용도
- **vLLM** (Llama 3.1, Qwen 2.5, DeepSeek 등)
- **음성 분석** (Whisper - STT)
- **영상 분석** (PoseNet, MediaPipe - Pose Estimation)
- **Creator Studio** (영상 생성 - Stable Diffusion Video)
- **음성 합성** (TTS - Coqui TTS, XTTS)

#### 구성 예시
```
GPU Server #1 (RTX 5090 48GB)
  - vLLM (Llama 3.1 70B)
  - Port: 8100

GPU Server #2 (RTX 5090 48GB)
  - Whisper Large-v3
  - PoseNet / MediaPipe
  - Port: 8101

GPU Server #3 (A100 80GB - optional)
  - Multi-modal LLM (Qwen2-VL 72B)
  - Port: 8102
```

#### 네트워크 경로
```
api.my-ktube.ai 
  → Gateway (Nginx/Traefik) 
  → GPU cluster (8100) 
  → vLLM / Whisper / PoseNet
```

#### vLLM 설정 예시
```bash
# vLLM 서버 실행
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --host 0.0.0.0 \
  --port 8100 \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9
```

#### Whisper API 예시
```python
import whisper

model = whisper.load_model("large-v3")

@app.post("/api/v1/kzone/voice/transcribe")
async def transcribe_audio(file: UploadFile):
    audio_path = f"/tmp/{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())
    
    result = model.transcribe(audio_path, language="ko")
    return {"text": result["text"], "segments": result["segments"]}
```

---

### 2.8 File / Media Storage

#### 저장소 구성
1. **Cloudflare R2** (추천) - S3 호환, Egress 무료
2. **Backblaze B2** - 저렴한 스토리지
3. **MinIO** (Self-hosted) - S3 호환 오픈소스

#### 저장 용도
- 사용자 업로드 파일 (프로필 사진, 에세이)
- K-POP/드라마 학습 콘텐츠
- AI 생성 영상/오디오
- Pose/Keypoint JSON
- Exam 첨부 파일

#### 경로 구조
```
/users/{user_id}/profile.jpg
/kzone/audio/{content_id}/original.mp3
/kzone/video/{content_id}/processed.mp4
/kzone/pose/{content_id}/keypoints.json
/exams/{exam_id}/attachments/{file_id}.pdf
```

#### S3 클라이언트 예시 (Python)
```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='https://s3.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY
)

# 파일 업로드
s3.upload_file(
    '/tmp/video.mp4',
    'dreamseed-kzone',
    'kzone/video/12345/processed.mp4'
)

# Presigned URL 생성 (7일)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'dreamseed-kzone', 'Key': 'kzone/video/12345/processed.mp4'},
    ExpiresIn=604800
)
```

---

### 2.9 Monitoring & Observability

#### 모듈 구성
- **Prometheus**: 메트릭 수집
- **Grafana**: 대시보드 시각화
- **Loki**: 로그 수집 (Promtail)
- **Tempo / Jaeger**: 분산 추적 (Tracing)
- **AlertManager**: 알림 (Slack, PagerDuty)

#### 모니터링 항목
1. **API Latency** (p50, p90, p95, p99)
2. **GPU Inference Latency** (vLLM, Whisper)
3. **DB Connection Count** (PostgreSQL)
4. **Redis Hit Rate**
5. **도메인별 트래픽** (requests/sec)
6. **Error Rate** (5xx, 4xx)
7. **Disk I/O** (SSD IOPS)
8. **Network Bandwidth** (Mbps)

#### Prometheus 메트릭 예시
```yaml
# FastAPI 메트릭
http_requests_total{method="GET", endpoint="/api/v1/exams", status="200"}
http_request_duration_seconds{method="POST", endpoint="/api/v1/attempts"}

# GPU 메트릭
gpu_utilization_percent{device="cuda:0"}
gpu_memory_used_bytes{device="cuda:0"}
vllm_inference_duration_seconds{model="llama-3.1-70b"}

# DB 메트릭
pg_connections_active
pg_query_duration_seconds{query="select_exam"}
```

#### Grafana 대시보드 예시
```
Dashboard 1: MegaCity Overview
  - Total Requests (All Domains)
  - Error Rate (5xx)
  - API Latency (p95)
  - Active Users

Dashboard 2: K-Zone AI Performance
  - vLLM Inference Time
  - Whisper Transcription Time
  - PoseNet Detection Time
  - GPU Utilization

Dashboard 3: Database Health
  - Connection Pool Usage
  - Query Duration (Top 10)
  - Table Size Growth
  - Cache Hit Ratio

Dashboard 4: Zone별 성능 & 트래픽
  - Zone별 요청 수 (UnivPrep / CollegePrep / SkillPrep / MediPrep / MajorPrep / K-Zone / MPC / DreamSeed)
  - Zone별 오류율 (5xx)
  - Zone별 평균 응답 시간 (p50, p95, p99)
  - Zone별 동시 접속자 수
```

---

## 🔒 3. 보안 아키텍처 (Security Architecture)

DreamSeedAI MegaCity는 **다층 보안 전략(Defense in Depth)**을 채택하여 각 계층에서 독립적인 보안 제어를 수행합니다.

### 3.1 Edge 보안 (Cloudflare WAF)

Cloudflare WAF는 **첫 번째 방어선**으로, 모든 악의적인 트래픽을 Edge에서 차단합니다.

#### 3.1.1 WAF Rule Set 적용

**OWASP Top-10 대응**
```
Ruleset: Cloudflare OWASP Core Ruleset
  - SQL Injection (SQLi) 차단
  - Cross-Site Scripting (XSS) 차단
  - Command Injection 차단
  - Path Traversal 차단
  - Remote Code Execution (RCE) 차단
  - XML External Entity (XXE) 차단
  - Server-Side Request Forgery (SSRF) 차단
```

**Custom WAF Rules**
```javascript
// Rule 1: Block SQL Injection attempts
(http.request.uri.query contains "union select" or 
 http.request.uri.query contains "' or 1=1" or
 http.request.body contains "DROP TABLE") → Block

// Rule 2: Block XSS attempts
(http.request.uri.query contains "<script>" or
 http.request.body contains "javascript:" or
 http.request.body contains "onerror=") → Block

// Rule 3: Block suspicious User-Agents
(http.user_agent contains "sqlmap" or
 http.user_agent contains "nikto" or
 http.user_agent contains "nmap") → Block
```

#### 3.1.2 Bot 탐지 및 차단

**Bot Management**
```
Good Bots (Allow):
  - Googlebot
  - Bingbot
  - FacebookBot
  - TwitterBot

Bad Bots (Block):
  - Scrapers (HTTrack, Wget)
  - Vulnerability scanners (Nessus, OpenVAS)
  - Anonymous proxies (Tor, VPN)
  - Known bot networks

Challenge (CAPTCHA):
  - Suspicious user agents
  - Rapid request patterns
  - Low reputation IPs
```

**Bot Score Implementation**
```javascript
// Cloudflare Bot Score (1-99)
// 1-29: Likely bot → Block
// 30-49: Suspicious → Challenge
// 50-99: Likely human → Allow

(cf.bot_management.score lt 30) → Block
(cf.bot_management.score ge 30 and cf.bot_management.score lt 50) → Challenge
(cf.bot_management.score ge 50) → Allow
```

#### 3.1.3 DDoS 공격 완전 차단

**L3/L4 DDoS Protection**
```
UDP Flood: Auto-mitigated
SYN Flood: Auto-mitigated
ACK Flood: Auto-mitigated
ICMP Flood: Auto-mitigated
```

**L7 DDoS Protection (HTTP Flood)**
```javascript
// Rate Limit per IP
(rate(5m) gt 1000) → Block for 1 hour

// Sudden Traffic Spike
(rate(1m) gt 200 and rate_change(5m) gt 500%) → Challenge

// Distributed Attack (many IPs)
(cf.threat_score gt 10) → Challenge
```

#### 3.1.4 IP Reputation 기반 차단

**Cloudflare Threat Intelligence**
```javascript
// High threat score → Block
(cf.threat_score gt 50) → Block

// Known malicious IPs
(ip.src in $malicious_ip_list) → Block

// Tor Exit Nodes
(cf.client.tor) → Challenge or Block

// Anonymous Proxies
(cf.client.proxy) → Challenge
```

**Custom IP Whitelist/Blacklist**
```nginx
# Whitelist (관리자 IP)
1.2.3.4/32 → Allow all
5.6.7.8/32 → Allow all

# Blacklist (악의적 IP)
10.20.30.40/32 → Block
```

#### 3.1.5 도메인별 Rate Limit

각 도메인별로 **독립적인 Rate Limit** 적용:

| 도메인 | 엔드포인트 | Rate Limit | Burst | 조치 |
|--------|-----------|-----------|-------|-----|
| `api.univprepai.com` | `/api/v1/*` | 100 req/min | 20 | Block |
| `api.univprepai.com` | `/api/v1/auth/login` | 5 req/min | 2 | Block 15min |
| `api.my-ktube.ai` | `/api/v1/kzone/*` | 50 req/min | 10 | Challenge |
| `app.<domain>` | `/*` | 200 req/min | 50 | Challenge |
| `static.<domain>` | `/*` | 500 req/min | 100 | Allow (CDN) |

**Cloudflare Rate Limiting Rule 예시**
```javascript
// API Login Rate Limit (Brute-force 방지)
(http.host eq "api.univprepai.com" and
 http.request.uri.path eq "/api/v1/auth/login")
→ Rate Limit: 5 requests per 60 seconds
→ Action: Block for 900 seconds (15분)

// API General Rate Limit
(http.host contains "api." and
 http.request.uri.path matches "^/api/v1/.*")
→ Rate Limit: 100 requests per 60 seconds
→ Action: Block for 60 seconds

// K-Zone AI Rate Limit (GPU 보호)
(http.host eq "api.my-ktube.ai" and
 http.request.uri.path matches "^/api/v1/kzone/.*")
→ Rate Limit: 50 requests per 60 seconds (per IP)
→ Action: Challenge (CAPTCHA)
```

---

### 3.2 API 백엔드 보안 (Application Layer)

#### 3.2.1 JWT 기반 인증 (Authentication)

**토큰 구조**
```json
{
  "sub": "user_12345",
  "email": "student@univprepai.com",
  "zone_id": "univ",
  "org_id": 42,
  "role": "student",
  "permissions": ["exam:read", "attempt:create"],
  "iat": 1700000000,
  "exp": 1700086400,
  "jti": "unique-token-id"
}
```

**토큰 발급 및 검증**
```python
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 24  # hours

def create_access_token(user: User) -> str:
    """Access Token 생성"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE)
    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "zone_id": user.zone_id,
        "org_id": user.org_id,
        "role": user.role,
        "exp": expire,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Token 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Redis에서 블랙리스트 확인 (로그아웃된 토큰)
        if redis_client.exists(f"blacklist:{payload['jti']}"):
            raise JWTError("Token revoked")
        
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Refresh Token 전략**
```python
# Access Token: 24시간 (짧은 수명)
# Refresh Token: 30일 (긴 수명, httpOnly cookie)

@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_token: str = Cookie(None)):
    """Refresh Token으로 새 Access Token 발급"""
    payload = verify_refresh_token(refresh_token)
    user = get_user_by_id(payload["sub"])
    new_access_token = create_access_token(user)
    return {"access_token": new_access_token}
```

#### 3.2.2 Role-Based Access Control (RBAC)

**역할 정의**
```python
class Role(str, Enum):
    SUPER_ADMIN = "super_admin"      # 전체 시스템 관리
    ZONE_ADMIN = "zone_admin"        # 구역별 관리 (UnivPrepAI 전체)
    ORG_ADMIN = "org_admin"          # 조직별 관리 (특정 학교/기관)
    TEACHER = "teacher"              # 교사 (시험 생성, 학생 관리)
    STUDENT = "student"              # 학생 (시험 응시, 결과 조회)
    PARENT = "parent"                # 학부모 (자녀 성적 조회)
    GUEST = "guest"                  # 게스트 (제한적 접근)

# 권한 매핑
PERMISSIONS = {
    Role.SUPER_ADMIN: ["*"],  # All permissions
    Role.ZONE_ADMIN: [
        "zone:*", "org:read", "org:create",
        "user:*", "exam:*", "report:*"
    ],
    Role.ORG_ADMIN: [
        "org:read", "org:update",
        "user:read", "user:create", "user:update",
        "exam:*", "class:*", "report:read"
    ],
    Role.TEACHER: [
        "exam:create", "exam:read", "exam:update",
        "item:create", "item:read", "item:update",
        "student:read", "attempt:read", "report:read"
    ],
    Role.STUDENT: [
        "exam:read", "attempt:create", "attempt:read",
        "profile:read", "profile:update"
    ],
    Role.PARENT: [
        "student:read", "attempt:read", "report:read"
    ],
    Role.GUEST: [
        "exam:read"  # 공개 시험만
    ]
}
```

**권한 체크 데코레이터**
```python
from functools import wraps
from fastapi import Depends, HTTPException

def require_permission(permission: str):
    """특정 권한을 가진 사용자만 접근 허용"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
            user_permissions = PERMISSIONS.get(current_user["role"], [])
            
            # Wildcard 권한 체크
            if "*" in user_permissions:
                return await func(*args, current_user=current_user, **kwargs)
            
            # 특정 권한 체크
            resource, action = permission.split(":")
            if f"{resource}:*" in user_permissions or permission in user_permissions:
                return await func(*args, current_user=current_user, **kwargs)
            
            raise HTTPException(status_code=403, detail="Permission denied")
        return wrapper
    return decorator

# 사용 예시
@app.post("/api/v1/exams")
@require_permission("exam:create")
async def create_exam(exam: ExamCreate, current_user: dict = Depends(get_current_user)):
    """시험 생성 (교사 이상만 가능)"""
    return create_exam_service(exam, current_user)
```

#### 3.2.3 org_id + zone_id 기반 권한 검사 (Multi-tenant Isolation)

**데이터 격리 전략**
```python
@app.get("/api/v1/exams/{exam_id}")
@require_permission("exam:read")
async def get_exam(
    exam_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """시험 조회 - Multi-tenant 격리"""
    
    # 1. zone_id 체크 (도메인 기반)
    if current_user["zone_id"] != get_zone_from_request():
        raise HTTPException(status_code=403, detail="Zone mismatch")
    
    # 2. org_id 체크 (조직 격리)
    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.zone_id == current_user["zone_id"],
        Exam.org_id == current_user["org_id"]  # 같은 조직만 접근
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # 3. 추가 권한 체크 (공개 여부)
    if not exam.is_public and current_user["role"] == Role.GUEST:
        raise HTTPException(status_code=403, detail="Private exam")
    
    return exam
```

**Cross-zone 접근 방지**
```python
# SQLAlchemy ORM 레벨에서 자동 필터링
class BaseModel(Base):
    __abstract__ = True
    
    zone_id = Column(String, nullable=False, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    
    @declared_attr
    def __table_args__(cls):
        return (
            Index(f'idx_{cls.__tablename__}_zone_org', 'zone_id', 'org_id'),
        )

# Query 시 자동 필터 적용
def get_db_query(model: Type[Base], current_user: dict):
    """Multi-tenant 자동 필터링"""
    query = db.query(model).filter(
        model.zone_id == current_user["zone_id"],
        model.org_id == current_user["org_id"]
    )
    return query
```

#### 3.2.4 Request Signature (향후 구현)

**HMAC 서명 검증**
```python
import hmac
import hashlib
from datetime import datetime

def generate_signature(payload: dict, secret_key: str) -> str:
    """Request 서명 생성"""
    timestamp = int(datetime.utcnow().timestamp())
    payload["timestamp"] = timestamp
    
    # Payload를 정렬된 문자열로 변환
    message = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
    
    # HMAC-SHA256 서명
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def verify_signature(payload: dict, signature: str, secret_key: str) -> bool:
    """Request 서명 검증"""
    # Timestamp 검증 (5분 이내)
    timestamp = payload.get("timestamp", 0)
    if abs(int(datetime.utcnow().timestamp()) - timestamp) > 300:
        return False  # Replay attack 방지
    
    # 서명 재생성 및 비교
    expected_signature = generate_signature(payload, secret_key)
    return hmac.compare_digest(signature, expected_signature)
```

#### 3.2.5 Parent-Student Approval 검증

**학부모-자녀 연결 검증**
```python
@app.get("/api/v1/students/{student_id}/reports")
@require_permission("report:read")
async def get_student_reports(
    student_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """학생 성적 조회 (학부모 권한)"""
    
    # 1. Role 체크
    if current_user["role"] not in [Role.PARENT, Role.TEACHER, Role.ORG_ADMIN]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 2. Parent-Student 관계 검증
    if current_user["role"] == Role.PARENT:
        relationship = db.query(ParentStudentRelationship).filter(
            ParentStudentRelationship.parent_id == current_user["id"],
            ParentStudentRelationship.student_id == student_id,
            ParentStudentRelationship.status == "approved"  # 승인된 관계만
        ).first()
        
        if not relationship:
            raise HTTPException(status_code=403, detail="Not your child")
    
    # 3. 성적 조회
    reports = db.query(Report).filter(
        Report.student_id == student_id,
        Report.zone_id == current_user["zone_id"],
        Report.org_id == current_user["org_id"]
    ).all()
    
    return reports

# Parent-Student 관계 승인 플로우
@app.post("/api/v1/parents/link-student")
async def request_student_link(
    student_email: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """학부모 → 자녀 연결 요청"""
    student = db.query(User).filter(
        User.email == student_email,
        User.role == Role.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # 연결 요청 생성
    relationship = ParentStudentRelationship(
        parent_id=current_user["id"],
        student_id=student.id,
        status="pending",  # 학생 승인 대기
        requested_at=datetime.utcnow()
    )
    db.add(relationship)
    db.commit()
    
    # 학생에게 이메일/앱 알림 발송
    send_notification(student.email, "Parent link request", ...)
    
    return {"message": "Link request sent"}

@app.post("/api/v1/students/approve-parent/{parent_id}")
async def approve_parent_link(
    parent_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """학생 → 학부모 연결 승인"""
    relationship = db.query(ParentStudentRelationship).filter(
        ParentStudentRelationship.parent_id == parent_id,
        ParentStudentRelationship.student_id == current_user["id"],
        ParentStudentRelationship.status == "pending"
    ).first()
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # 승인 처리
    relationship.status = "approved"
    relationship.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Parent link approved"}
```

#### 3.2.6 AuditLog 자동 기록

**모든 중요 작업 로깅**
```python
from enum import Enum

class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    zone_id = Column(String, nullable=False)
    org_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # AuditAction
    resource_type = Column(String, nullable=False)  # "exam", "user", "attempt"
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def log_audit(
    user: dict,
    action: AuditAction,
    resource_type: str,
    resource_id: int = None,
    details: dict = None,
    request: Request = None
):
    """Audit Log 생성"""
    log = AuditLog(
        user_id=user["id"],
        zone_id=user["zone_id"],
        org_id=user["org_id"],
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details=details
    )
    db.add(log)
    db.commit()

# 사용 예시
@app.post("/api/v1/exams/{exam_id}/delete")
@require_permission("exam:delete")
async def delete_exam(
    exam_id: int,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """시험 삭제 (Audit 로깅)"""
    exam = get_exam_or_404(exam_id, current_user, db)
    
    # Audit Log 기록
    log_audit(
        user=current_user,
        action=AuditAction.DELETE,
        resource_type="exam",
        resource_id=exam_id,
        details={"exam_title": exam.title, "org_id": exam.org_id},
        request=request
    )
    
    db.delete(exam)
    db.commit()
    
    return {"message": "Exam deleted"}
```

**Audit Log 조회 (관리자)**
```python
@app.get("/api/v1/admin/audit-logs")
@require_permission("admin:read")
async def get_audit_logs(
    start_date: datetime = None,
    end_date: datetime = None,
    user_id: int = None,
    action: AuditAction = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Audit Log 조회 (Zone Admin 이상)"""
    query = db.query(AuditLog).filter(
        AuditLog.zone_id == current_user["zone_id"]
    )
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(1000).all()
    return logs
```

---

### 3.3 데이터 보안 (Data Security)

#### 3.3.1 모든 API HTTPS 강제

**Cloudflare Always Use HTTPS**
```
설정: SSL/TLS → Edge Certificates → Always Use HTTPS: On

효과:
- 모든 HTTP 요청 → HTTPS 301 Redirect
- HSTS 헤더 자동 추가
- 브라우저 캐싱 (max-age=31536000)
```

**Nginx HTTPS 리다이렉트**
```nginx
server {
    listen 80;
    server_name api.univprepai.com;
    
    # HTTP → HTTPS 강제 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.univprepai.com;
    
    # TLS 1.2+ 강제
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # HSTS 헤더
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    location / {
        proxy_pass http://backend_api;
    }
}
```

#### 3.3.2 DB at-rest Encryption (PostgreSQL 암호화)

**TDE (Transparent Data Encryption)**
```bash
# PostgreSQL 14+ 암호화 설정
# 1. 데이터 디렉토리 암호화 (LUKS)
cryptsetup luksFormat /dev/sdb
cryptsetup luksOpen /dev/sdb pgdata_encrypted

# 2. 파일시스템 생성
mkfs.ext4 /dev/mapper/pgdata_encrypted
mount /dev/mapper/pgdata_encrypted /var/lib/postgresql/14/main

# 3. PostgreSQL 설정
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'

# 4. 연결 강제 SSL (pg_hba.conf)
hostssl all all 0.0.0.0/0 md5
```

**Column-level Encryption (선택적)**
```sql
-- pgcrypto 확장 설치
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 민감한 컬럼 암호화
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    ssn_encrypted BYTEA,  -- 주민등록번호 암호화
    phone_encrypted BYTEA  -- 전화번호 암호화
);

-- 암호화 저장
INSERT INTO users (email, ssn_encrypted)
VALUES ('user@example.com', pgp_sym_encrypt('123456-1234567', 'encryption_key'));

-- 복호화 조회
SELECT email, pgp_sym_decrypt(ssn_encrypted, 'encryption_key') AS ssn
FROM users WHERE id = 1;
```

#### 3.3.3 비밀번호 해싱 (bcrypt)

**bcrypt 사용 (Work Factor: 12)**
```python
from passlib.context import CryptContext

# bcrypt 설정 (rounds=12, 약 300ms 소요)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

# 회원가입 시 해싱
@app.post("/api/v1/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 비밀번호 강도 검증
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    
    # 해싱 후 저장
    hashed = hash_password(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed,
        zone_id=user.zone_id,
        org_id=user.org_id
    )
    db.add(new_user)
    db.commit()
    return {"message": "User created"}

# 로그인 시 검증
@app.post("/api/v1/auth/login")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # JWT 발급
    access_token = create_access_token(user)
    return {"access_token": access_token}
```

**비밀번호 정책 강제**
```python
import re

def validate_password_strength(password: str) -> bool:
    """비밀번호 강도 검증"""
    # 최소 8자
    if len(password) < 8:
        return False
    
    # 대문자 포함
    if not re.search(r"[A-Z]", password):
        return False
    
    # 소문자 포함
    if not re.search(r"[a-z]", password):
        return False
    
    # 숫자 포함
    if not re.search(r"[0-9]", password):
        return False
    
    # 특수문자 포함
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    
    return True
```

#### 3.3.4 PII 암호화 (선택: Fernet/GCP KMS)

**Fernet 대칭키 암호화**
```python
from cryptography.fernet import Fernet

# 키 생성 (환경 변수에 저장)
ENCRYPTION_KEY = os.getenv("FERNET_KEY")  # Fernet.generate_key()
cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_pii(data: str) -> str:
    """PII 암호화"""
    return cipher.encrypt(data.encode()).decode()

def decrypt_pii(encrypted_data: str) -> str:
    """PII 복호화"""
    return cipher.decrypt(encrypted_data.encode()).decode()

# 사용 예시
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    phone_encrypted = Column(String, nullable=True)  # 암호화된 전화번호
    ssn_encrypted = Column(String, nullable=True)    # 암호화된 주민번호
    
    @property
    def phone(self) -> str:
        """전화번호 복호화"""
        if self.phone_encrypted:
            return decrypt_pii(self.phone_encrypted)
        return None
    
    @phone.setter
    def phone(self, value: str):
        """전화번호 암호화"""
        self.phone_encrypted = encrypt_pii(value)
```

**GCP KMS (Cloud Key Management Service)**
```python
from google.cloud import kms

def encrypt_with_kms(plaintext: str, project_id: str, location: str, key_ring: str, key: str) -> bytes:
    """GCP KMS로 암호화"""
    client = kms.KeyManagementServiceClient()
    key_name = client.crypto_key_path(project_id, location, key_ring, key)
    
    response = client.encrypt(
        request={'name': key_name, 'plaintext': plaintext.encode()}
    )
    return response.ciphertext

def decrypt_with_kms(ciphertext: bytes, project_id: str, location: str, key_ring: str, key: str) -> str:
    """GCP KMS로 복호화"""
    client = kms.KeyManagementServiceClient()
    key_name = client.crypto_key_path(project_id, location, key_ring, key)
    
    response = client.decrypt(
        request={'name': key_name, 'ciphertext': ciphertext}
    )
    return response.plaintext.decode()
```

---

### 3.4 보안 헤더 (Security Headers)

**Nginx/Traefik에서 자동 추가**
```nginx
# Security Headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.univprepai.com" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Server 정보 숨기기
server_tokens off;
```

---

### 3.5 보안 체크리스트

#### 개발 단계
```
□ 1. 모든 API 엔드포인트에 인증 적용
□ 2. RBAC 권한 체크 구현
□ 3. Multi-tenant 격리 (zone_id, org_id)
□ 4. Input Validation (Pydantic)
□ 5. SQL Injection 방지 (ORM 사용)
□ 6. XSS 방지 (출력 escape)
□ 7. CSRF 토큰 적용
□ 8. Rate Limiting 적용
□ 9. Audit Logging 구현
□ 10. 비밀번호 해싱 (bcrypt)
```

#### 배포 단계
```
□ 1. Cloudflare WAF 활성화
□ 2. Bot Management 설정
□ 3. Rate Limit 규칙 적용
□ 4. HTTPS 강제 (Always Use HTTPS)
□ 5. HSTS 헤더 활성화
□ 6. Security Headers 적용
□ 7. DB 암호화 (TDE)
□ 8. SSL 인증서 검증 (SSL Labs A+)
□ 9. IP Whitelist (Admin 경로)
□ 10. 모니터링 알림 설정
```

#### 운영 단계
```
□ 1. 주간 보안 로그 검토
□ 2. 월간 취약점 스캔 (OWASP ZAP)
□ 3. 분기별 침투 테스트
□ 4. 비밀번호 정책 강제 (90일 갱신)
□ 5. 의심스러운 로그인 알림
□ 6. Audit Log 분석
□ 7. 백업 복구 테스트
□ 8. 보안 패치 적용 (OS, 라이브러리)
□ 9. 보안 교육 (개발팀)
□ 10. GDPR/CCPA 컴플라이언스 검토
```

---

---

## 🚦 4. 라우팅 규칙 요약 (Routing Logic)

### 4.1 Domain-level Routing

**전체 도메인별 라우팅 매트릭스**

| Hostname | Routing Target | Port | Service | 설명 |
|----------|----------------|------|---------|------|
| `www.<domain>` | `frontend_app` | 3000-3003 | Next.js SSR | Landing page (SEO 최적화) |
| `app.<domain>` | `frontend_app` | 3000-3003 | Next.js SPA | Application UI (로그인 후) |
| `api.<domain>` | `backend_api` | 8000-8003 | FastAPI | REST API (인증 필요) |
| `static.<domain>` | `static_cdn` | 9000 | MinIO/R2 | 정적 파일 (CDN 캐시 7일) |
| `admin.<domain>` | `admin_app` | 3100 | Admin Console | 내부 관리 (IP Whitelist) |

---

### 4.2 Path-based Routing (API 엔드포인트)

#### 4.2.1 UnivPrepAI.com 라우팅

```nginx
# Landing Page
https://www.univprepai.com/
  → frontend_app:3001
  → Next.js SSR (홈, 소개, 가격)

# Application UI
https://app.univprepai.com/dashboard
https://app.univprepai.com/exams
https://app.univprepai.com/analytics
  → frontend_app:3001
  → Next.js SPA (로그인 후 UI)

# API Routes
https://api.univprepai.com/api/v1/auth/login
https://api.univprepai.com/api/v1/exams
https://api.univprepai.com/api/v1/attempts
  → backend_api:8000
  → FastAPI (JWT 인증)

# Static Assets
https://static.univprepai.com/images/logo.png
https://static.univprepai.com/css/styles.css
  → static_cdn:9000
  → MinIO/R2 (Cloudflare CDN Cache)

# Admin Console
https://admin.univprepai.com/
  → admin_app:3100
  → Admin Dashboard (IP Whitelist: 1.2.3.4/32)
```

---

#### 4.2.2 My-Ktube.ai 라우팅 (K-Zone AI)

```nginx
# AI Hub Landing
https://www.my-ktube.ai/
  → frontend_app:3002
  → Next.js SSR (K-Zone 소개)

# K-Zone App
https://app.my-ktube.ai/voice-tutor
https://app.my-ktube.ai/dance-lab
https://app.my-ktube.ai/drama-coach
  → frontend_app:3002
  → Next.js SPA (K-Zone AI 기능)

# AI Inference API
https://api.my-ktube.ai/api/v1/kzone/voice/analyze
https://api.my-ktube.ai/api/v1/kzone/dance/pose-detection
https://api.my-ktube.ai/api/v1/kzone/drama/scene-analysis
  → kzone_ai_api:8100
  → FastAPI → vLLM/Whisper/PoseNet (GPU)

# Static Assets (Large Media)
https://static.my-ktube.ai/videos/kpop-sample.mp4
  → static_cdn:9000
  → R2 (500MB max body size)
```

---

### 4.3 Nginx 라우팅 설정 (상세)

#### 4.3.1 UnivPrepAI.com 전체 설정

```nginx
# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    server_name www.univprepai.com app.univprepai.com api.univprepai.com static.univprepai.com;
    return 301 https://$server_name$request_uri;
}

# Landing Page (www)
server {
    listen 443 ssl http2;
    server_name www.univprepai.com;
    
    include conf.d/ssl.conf;
    include conf.d/security.conf;
    
    location / {
        proxy_pass http://frontend_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Next.js Static Assets (Cache)
    location /_next/static/ {
        proxy_pass http://frontend_app;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
}

# Application UI (app)
server {
    listen 443 ssl http2;
    server_name app.univprepai.com;
    
    include conf.d/ssl.conf;
    include conf.d/security.conf;
    
    # Rate Limit (30 req/sec per IP)
    limit_req zone=app_limit burst=50 nodelay;
    
    location / {
        proxy_pass http://frontend_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 지원 (optional)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API Proxy (BFF 패턴)
    location /api/ {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Backend API (api)
server {
    listen 443 ssl http2;
    server_name api.univprepai.com;
    
    include conf.d/ssl.conf;
    include conf.d/security.conf;
    include conf.d/cloudflare-ips.conf;
    
    # Rate Limit (10 req/sec per IP)
    limit_req zone=api_limit burst=20 nodelay;
    
    # CORS Headers
    add_header Access-Control-Allow-Origin "https://app.univprepai.com" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
    add_header Access-Control-Allow-Credentials "true" always;
    
    # OPTIONS Preflight
    if ($request_method = 'OPTIONS') {
        return 204;
    }
    
    location / {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # WebSocket (실시간 시험 동기화)
    location /ws {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # WebSocket 타임아웃
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # Health Check (모니터링)
    location /health {
        proxy_pass http://backend_api/health;
        access_log off;
    }
}

# Static CDN (static)
server {
    listen 443 ssl http2;
    server_name static.univprepai.com;
    
    include conf.d/ssl.conf;
    
    # No Rate Limit (CDN cached)
    
    location / {
        proxy_pass http://static_cdn;
        proxy_set_header Host $host;
        
        # Cache Headers (7일)
        proxy_cache_valid 200 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
        add_header X-Cache-Status $upstream_cache_status;
        
        # CORS (모든 도메인 허용)
        add_header Access-Control-Allow-Origin "*" always;
    }
    
    # Image Optimization (optional)
    location ~* \.(jpg|jpeg|png|gif|webp)$ {
        proxy_pass http://static_cdn;
        proxy_cache_valid 200 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }
}

# Admin Console (admin)
server {
    listen 443 ssl http2;
    server_name admin.univprepai.com;
    
    include conf.d/ssl.conf;
    include conf.d/security.conf;
    
    # IP Whitelist (관리자 IP만 허용)
    allow 1.2.3.4;      # Office IP
    allow 5.6.7.8;      # VPN IP
    deny all;
    
    location / {
        proxy_pass http://admin_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Basic Auth (추가 보안)
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

---

#### 4.3.2 K-Zone AI 특화 설정 (My-Ktube.ai)

```nginx
# K-Zone AI API (대용량 업로드 지원)
server {
    listen 443 ssl http2;
    server_name api.my-ktube.ai;
    
    include conf.d/ssl.conf;
    include conf.d/security.conf;
    include conf.d/cloudflare-ips.conf;
    
    # Large File Upload (500MB)
    client_max_body_size 500M;
    client_body_timeout 300s;
    
    # Rate Limit (AI 보호)
    limit_req zone=api_limit burst=10 nodelay;
    
    location / {
        proxy_pass http://kzone_ai_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Long Timeout (AI Inference)
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 900s;  # 15분 (긴 영상 처리)
        
        # Buffering OFF (실시간 스트리밍)
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # Voice Analysis (음성 분석)
    location /api/v1/kzone/voice/ {
        proxy_pass http://kzone_ai_api;
        
        # 음성 파일 (최대 50MB)
        client_max_body_size 50M;
        
        # Whisper Inference (약 30초)
        proxy_read_timeout 60s;
    }
    
    # Dance Lab (영상 분석)
    location /api/v1/kzone/dance/ {
        proxy_pass http://kzone_ai_api;
        
        # 영상 파일 (최대 500MB)
        client_max_body_size 500M;
        
        # PoseNet Inference (약 3분)
        proxy_read_timeout 300s;
    }
    
    # Creator Studio (영상 생성)
    location /api/v1/kzone/creator/ {
        proxy_pass http://kzone_ai_api;
        
        # 영상 생성 (최대 15분)
        proxy_read_timeout 900s;
    }
}
```

---

### 4.4 Traefik 라우팅 설정 (Docker-native)

#### 4.4.1 Dynamic Routers (routers.yml)

```yaml
http:
  routers:
    # UnivPrepAI - Landing Page
    univprepai-www:
      rule: "Host(`www.univprepai.com`)"
      entryPoints:
        - websecure
      service: frontend-app
      middlewares:
        - security-headers
        - gzip-compress
      tls:
        certResolver: cloudflare
    
    # UnivPrepAI - Application UI
    univprepai-app:
      rule: "Host(`app.univprepai.com`)"
      entryPoints:
        - websecure
      service: frontend-app
      middlewares:
        - security-headers
        - app-rate-limit
        - gzip-compress
      tls:
        certResolver: cloudflare
    
    # UnivPrepAI - Backend API
    univprepai-api:
      rule: "Host(`api.univprepai.com`)"
      entryPoints:
        - websecure
      service: backend-api
      middlewares:
        - security-headers
        - api-rate-limit
        - cors-headers
      tls:
        certResolver: cloudflare
    
    # UnivPrepAI - Static CDN
    univprepai-static:
      rule: "Host(`static.univprepai.com`)"
      entryPoints:
        - websecure
      service: static-cdn
      middlewares:
        - cors-headers
      tls:
        certResolver: cloudflare
    
    # My-Ktube.ai - K-Zone AI API
    my-ktube-ai-api:
      rule: "Host(`api.my-ktube.ai`)"
      entryPoints:
        - websecure
      service: kzone-ai-api
      middlewares:
        - security-headers
        - api-rate-limit
      tls:
        certResolver: cloudflare
    
    # Admin Console (IP Whitelist)
    admin-console:
      rule: "Host(`admin.univprepai.com`)"
      entryPoints:
        - websecure
      service: admin-app
      middlewares:
        - security-headers
        - admin-ip-whitelist
      tls:
        certResolver: cloudflare
```

---

### 4.5 서브도메인별 포트 매핑

| 구역 | 도메인 | 서브도메인 | 포트 | 서비스 |
|------|--------|-----------|------|--------|
| **UnivPrepAI** | univprepai.com | www | 3001 | Next.js Landing |
| | | app | 3001 | Next.js App |
| | | api | 8000 | FastAPI Backend |
| | | static | 9000 | MinIO/R2 |
| **CollegePrepAI** | collegeprepai.com | www | 3001 | Next.js Landing |
| | | app | 3001 | Next.js App |
| | | api | 8000 | FastAPI Backend |
| | | static | 9000 | MinIO/R2 |
| **K-Zone** | my-ktube.ai | www | 3002 | Next.js K-Zone |
| | | app | 3002 | Next.js K-Zone |
| | | api | 8100 | K-Zone AI API |
| | | static | 9000 | MinIO/R2 |
| **Admin** | (모든 도메인) | admin | 3100 | Admin Console |

---

### 4.6 WebSocket 라우팅 (실시간 통신)

**사용 사례:**
- 실시간 시험 동기화 (Teacher → Students)
- 실시간 채팅 (Tutor AI)
- Live 성적 업데이트
- K-Zone AI 스트리밍 결과

**Nginx WebSocket 설정**
```nginx
location /ws {
    proxy_pass http://backend_api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # Keep-alive (1시간)
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    
    # Buffering OFF
    proxy_buffering off;
}
```

**FastAPI WebSocket 엔드포인트**
```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

---

### 4.7 라우팅 결정 플로우차트

```
1. 사용자 요청: https://app.univprepai.com/exams
   ↓
2. DNS 조회 (Cloudflare Authoritative DNS)
   ↓ IP 반환 (Cloudflare Proxy IP)
3. Cloudflare Edge
   ↓ WAF 통과, SSL 처리, Cache MISS
4. Origin Server (Nginx/Traefik)
   ↓ Host 헤더: app.univprepai.com
5. Routing Rule 매칭
   ↓ Rule: app.univprepai.com → frontend_app (3001)
6. Upstream 선택
   ↓ Load Balancing (least_conn)
7. Next.js Server (Port 3001)
   ↓ SSR 렌더링, API 호출 (api.univprepai.com)
8. Backend API 호출
   ↓ GET /api/v1/exams
9. FastAPI (Port 8000)
   ↓ JWT 검증, DB 조회
10. PostgreSQL Query
   ↓ SELECT * FROM exams WHERE zone_id='univ'
11. Response 반환
   ↓ JSON → Next.js → HTML
12. Cloudflare Edge Cache (선택)
   ↓ 정적 파일 캐싱
13. 사용자 브라우저 렌더링
```

---

### 4.8 라우팅 체크리스트

#### 설정 검증
```bash
# Nginx 설정 테스트
nginx -t

# Traefik 설정 검증
docker exec traefik traefik healthcheck

# DNS 확인
dig @1.1.1.1 app.univprepai.com +short

# SSL 인증서 확인
openssl s_client -connect api.univprepai.com:443 -servername api.univprepai.com

# Upstream Health Check
curl https://api.univprepai.com/health

# WebSocket 테스트
wscat -c wss://api.univprepai.com/ws
```

#### 라우팅 테스트
```bash
# Landing Page (SSR)
curl -I https://www.univprepai.com/
# Expected: 200 OK, Content-Type: text/html

# API (인증 필요)
curl -H "Authorization: Bearer <token>" https://api.univprepai.com/api/v1/exams
# Expected: 200 OK, JSON response

# Static CDN (Cache Hit)
curl -I https://static.univprepai.com/images/logo.png
# Expected: X-Cache-Status: HIT

# Rate Limit 테스트
for i in {1..150}; do curl https://api.univprepai.com/api/v1/exams; done
# Expected: 429 Too Many Requests (after 100 req)

# Admin IP Whitelist
curl https://admin.univprepai.com/
# Expected: 403 Forbidden (if not whitelisted IP)
```

---

## 🚀 5. 트래픽 흐름 예시 (Traffic Flow Examples)

### 4.1 학생이 시험 시작 (Exam Start)

```
1. 브라우저: https://app.univprepai.com/exams/123/start
2. Cloudflare Edge: DNS resolve → SSL termination → Cache MISS
3. Nginx Proxy: app.univprepai.com → frontend_app (3001)
4. Next.js SSR: /exams/123/start 페이지 렌더링 → API 호출
5. Next.js → https://api.univprepai.com/v1/exams/123/start
6. Cloudflare Edge → Nginx Proxy → backend_api (8000)
7. FastAPI: JWT 검증 → DB 조회 (exam, items) → CAT 초기화
8. PostgreSQL: SELECT exam, items WHERE exam_id=123
9. Redis: SET cat:attempt_123:state (능력치 추정 초기값)
10. FastAPI → Response (첫 문항)
11. Next.js → SSR 완료 → HTML 반환
12. 브라우저: 시험 페이지 렌더링
```

---

### 4.2 K-Zone AI 음성 분석 (Voice Analysis)

```
1. 브라우저: https://app.my-ktube.ai/voice-tutor
2. 사용자: 마이크 녹음 (K-POP 따라 부르기)
3. JavaScript: 녹음 완료 → FormData 업로드
4. POST https://api.my-ktube.ai/v1/kzone/voice/analyze
5. Cloudflare Edge → Nginx Proxy (500MB body size)
6. Nginx → kzone_ai_api (8100)
7. FastAPI: 파일 수신 → S3 업로드 (R2)
8. FastAPI → GPU Server (8101): Whisper transcription
9. Whisper: 음성 → 텍스트 변환 (한국어)
10. FastAPI → GPU Server (8100): vLLM 피드백 생성
11. vLLM: "발음이 90% 정확합니다. '사랑해' 발음을 조금 더..."
12. FastAPI → Response (텍스트, 점수, 피드백)
13. 브라우저: 결과 페이지 렌더링 (점수 + 피드백 + 재생)
```

---

### 4.3 정적 파일 제공 (Static Assets)

```
1. 브라우저: https://static.univprepai.com/images/logo.png
2. Cloudflare Edge: Cache HIT → 즉시 반환 (Origin 접근 없음)
3. (Cache MISS 시)
4. Cloudflare → Nginx Proxy → static_cdn (9000)
5. MinIO / R2: /images/logo.png 반환
6. Cloudflare: Cache 저장 (TTL 7일)
7. 브라우저: 이미지 렌더링
```

---

## 🧪 5. 성능 최적화 및 확장성 (Performance & Scalability)

### 5.1 캐싱 전략

#### L1: Cloudflare CDN Cache
- **정적 파일**: 7일 (이미지, CSS, JS)
- **HTML**: 5분 (Bypass for logged-in users)

#### L2: Nginx Proxy Cache
- **API 응답**: 1분 (GET 요청만)
- **동적 콘텐츠**: Cache 비활성화

#### L3: Redis Application Cache
- **Exam 메타데이터**: 1시간
- **User Profile**: 10분
- **Leaderboard**: 5분

#### L4: Next.js ISR
- **Static Pages**: 재생성 간격 60초
- **Dynamic Pages**: On-demand revalidation

---

### 5.2 Load Balancing

#### Nginx (least_conn)
```nginx
upstream backend_api {
    least_conn;
    server backend1:8000 weight=1;
    server backend2:8000 weight=1;
    server backend3:8000 weight=2;  # 더 강력한 서버
}
```

#### Traefik (Weighted Round-Robin)
```yaml
services:
  backend-api:
    loadBalancer:
      servers:
        - url: "http://backend1:8000"
          weight: 1
        - url: "http://backend2:8000"
          weight: 2
```

---

### 5.3 Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
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
```

---

### 5.4 Database Optimization

#### Read Replica
```
Master (Write): postgres-master:5432
Replica 1 (Read): postgres-replica-1:5432
Replica 2 (Read): postgres-replica-2:5432
```

#### Connection Pooling (PgBouncer)
```ini
[databases]
dreamseed_megacity = host=postgres-master port=5432 dbname=dreamseed_megacity

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

#### Query Optimization
```sql
-- Index 추가
CREATE INDEX idx_attempts_user_exam ON attempts(user_id, exam_id);
CREATE INDEX idx_responses_attempt ON responses(attempt_id);
CREATE INDEX idx_items_exam_difficulty ON items(exam_id, difficulty);

-- Partitioning (시간 기반)
CREATE TABLE attempts_2025_11 PARTITION OF attempts
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

---

## 📊 6. 용량 계획 및 자원 할당 (Capacity Planning)

### 6.1 예상 트래픽 (2025년 말 기준)

| 구역 | DAU | Peak RPS | 스토리지 |
|------|-----|----------|---------|
| UnivPrepAI | 50K | 500 | 500GB |
| CollegePrepAI | 20K | 200 | 200GB |
| SkillPrepAI | 30K | 300 | 300GB |
| MediPrepAI | 10K | 100 | 100GB |
| MajorPrepAI | 15K | 150 | 150GB |
| My-Ktube.com | 100K | 1000 | 5TB |
| My-Ktube.ai | 50K | 500 | 2TB |
| mpcstudy.com | 5K | 50 | 50GB |
| **Total** | **280K** | **2800** | **8.3TB** |

---

### 6.2 서버 리소스 할당

#### Frontend (Next.js)
```
CPU: 4 vCPU per instance
RAM: 8GB per instance
Instances: 3-10 (auto-scaling)
```

#### Backend (FastAPI)
```
CPU: 8 vCPU per instance
RAM: 16GB per instance
Instances: 5-20 (auto-scaling)
```

#### Database (PostgreSQL)
```
CPU: 16 vCPU
RAM: 64GB
Storage: 2TB SSD (IOPS 20,000+)
Backup: Daily + PITR
```

#### Redis
```
CPU: 4 vCPU
RAM: 32GB
Persistence: RDB + AOF
```

#### GPU Cluster
```
GPU: 2x RTX 5090 (48GB each)
CPU: 32 vCPU
RAM: 128GB
Storage: 4TB NVMe SSD
```

---

### 6.3 비용 예측 (월별)

| 항목 | 수량 | 단가 | 월 비용 |
|------|------|------|---------|
| Cloudflare Pro | 9 zones | $25/zone | $225 |
| AWS EC2 (Frontend) | 10x c6i.2xlarge | $0.34/hr | $2,448 |
| AWS EC2 (Backend) | 20x c6i.4xlarge | $0.68/hr | $9,792 |
| AWS RDS (PostgreSQL) | 1x db.r6g.4xlarge | $1.33/hr | $959 |
| AWS ElastiCache (Redis) | 1x cache.r6g.2xlarge | $0.50/hr | $360 |
| GPU Server (Self-hosted) | 2x RTX 5090 | Capex | $800 |
| S3 / R2 Storage | 10TB | $0.015/GB | $150 |
| Monitoring (Grafana Cloud) | 1 account | $50 | $50 |
| **Total** | | | **$14,784** |

---

## 🔧 7. 운영 및 유지보수 (Operations & Maintenance)

### 7.1 배포 프로세스 (Deployment)

#### CI/CD Pipeline (GitHub Actions)
```yaml
name: Deploy Backend API

on:
  push:
    branches: [main]
    paths: ['backend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t backend-api:${{ github.sha }} backend/
      - name: Push to ECR
        run: docker push backend-api:${{ github.sha }}
      - name: Deploy to ECS
        run: aws ecs update-service --cluster megacity --service backend-api --force-new-deployment
```

#### Blue-Green Deployment
```
1. Green 환경에 새 버전 배포
2. Health Check 통과 확인
3. Nginx upstream에 Green 추가
4. Blue 트래픽 점진적 이동 (10% → 50% → 100%)
5. Blue 환경 종료
```

---

### 7.2 모니터링 및 알림

#### AlertManager 규칙
```yaml
groups:
- name: api_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} (threshold: 0.05)"
    
  - alert: HighAPILatency
    expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
    for: 10m
    annotations:
      summary: "API latency is too high"
      description: "P95 latency is {{ $value }}s (threshold: 2s)"
```

#### Slack 알림
```bash
curl -X POST https://hooks.slack.com/services/xxx \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🚨 [ALERT] High error rate on api.univprepai.com",
    "attachments": [{
      "color": "danger",
      "fields": [
        {"title": "Error Rate", "value": "8.5%", "short": true},
        {"title": "Endpoint", "value": "/api/v1/exams", "short": true}
      ]
    }]
  }'
```

---

### 7.3 백업 및 복구

#### 데이터베이스 백업
```bash
# 일일 전체 백업 (3 AM)
0 3 * * * pg_dump -U postgres dreamseed_megacity | gzip > /backup/db_$(date +\%Y\%m\%d).sql.gz

# WAL 아카이빙 (연속)
archive_mode = on
archive_command = 'aws s3 cp %p s3://megacity-wal-archive/%f'
```

#### Redis 백업
```bash
# RDB 스냅샷 (매 시간)
save 3600 1

# AOF (실시간)
appendonly yes
appendfsync everysec
```

#### 복구 절차
```bash
# PostgreSQL PITR
pg_restore -U postgres -d dreamseed_megacity /backup/db_20251120.sql.gz

# Redis
redis-cli --rdb /backup/dump.rdb
```

---

### 7.4 장애 대응 (Incident Response)

#### Runbook: API 서버 다운
```
1. Alert 확인 (Slack, PagerDuty)
2. Grafana 대시보드 확인 (CPU, Memory, Disk)
3. 로그 확인 (Loki)
   - kubectl logs -f deployment/backend-api
4. Health Check 확인
   - curl https://api.univprepai.com/health
5. 재시작 (필요 시)
   - kubectl rollout restart deployment/backend-api
6. 트래픽 재분배
   - Nginx upstream에서 문제 서버 제거
7. Post-mortem 작성
```

---

## 🌍 8. 다중 리전 확장 (Multi-region Expansion)

### 8.1 리전 구조 (2026년 목표)

```
Region 1: Asia-Pacific (Seoul)
  - Primary Database
  - Main API Cluster
  - GPU Cluster (K-Zone AI)

Region 2: US-East (Virginia)
  - Read Replica Database
  - API Cluster (Read-heavy)
  - CDN Edge (Cloudflare)

Region 3: Europe (Frankfurt)
  - Read Replica Database
  - API Cluster (Read-heavy)
  - CDN Edge (Cloudflare)
```

---

### 8.2 Global Load Balancing (Cloudflare)

```
Cloudflare Load Balancer
  → Health Check (every 30s)
  → Geo-steering
    - Asia → Seoul
    - Americas → Virginia
    - Europe → Frankfurt
```

---

### 8.3 데이터 복제 (Replication)

#### PostgreSQL Streaming Replication
```
Master (Seoul) → Replica (Virginia, Frankfurt)
  - Async replication (lag < 1s)
  - Automatic failover (Patroni)
```

#### Redis Cluster (Global)
```
Redis Cluster (Seoul) → Redis Cluster (Virginia)
  - Active-Active (CRDT)
  - Conflict resolution
```

---

## 📚 9. 관련 문서 및 참고 자료

### 내부 문서
- `MEGACITY_DOMAIN_ARCHITECTURE.md` - 도메인 전략 및 DNS 설정
- `ops/dns/README.md` - DNS 자동화 가이드
- `ops/reverse_proxy/README.md` - Nginx/Traefik 설정
- `backend/API_GUIDE.md` - FastAPI 개발 가이드
- `docs/GOVERNANCE_MONITORING_QUICKSTART.md` - 모니터링 빠른 시작

### 외부 참고
- [Cloudflare Docs](https://developers.cloudflare.com/)
- [Nginx Best Practices](https://nginx.org/en/docs/)
- [FastAPI Performance](https://fastapi.tiangolo.com/async/)
- [PostgreSQL Tuning](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)
- [vLLM Docs](https://docs.vllm.ai/)

---

## 📋 10. 체크리스트

### 초기 설정
```
□ 1. Cloudflare 계정 생성 및 9개 도메인 등록
□ 2. Nginx/Traefik 설치 및 설정
□ 3. Next.js Frontend 배포 (3000+)
□ 4. FastAPI Backend 배포 (8000+)
□ 5. PostgreSQL 설치 및 마이그레이션
□ 6. Redis 설치 및 설정
□ 7. GPU 서버 설정 (vLLM, Whisper)
□ 8. S3/R2 버킷 생성
□ 9. Prometheus + Grafana 설치
□ 10. 첫 배포 테스트
```

### 일상 운영
```
□ 1. 매일 오전 모니터링 대시보드 확인
□ 2. 주간 백업 검증
□ 3. 월간 용량 검토
□ 4. 분기별 보안 감사
□ 5. 반기별 DR 훈련
```

---

**MegaCity Network Architecture v1.0 완성** 🎉

DreamSeedAI MegaCity의 네트워크 인프라가 완전히 문서화되었습니다. 이 문서를 기반으로 안정적이고 확장 가능한 플랫폼을 구축하세요!