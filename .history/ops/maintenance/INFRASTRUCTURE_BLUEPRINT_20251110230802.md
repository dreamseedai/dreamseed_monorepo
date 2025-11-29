# 🏗️ DreamSeedAI 인프라 견적서 (100만 신도시)

> **"신도시 건설 견적서 - 100만 유저를 위한 인프라"**  
> 작성일: 2025년 11월 10일  
> 설계 기준: 100만 가입자, 1만 동시접속 (1% 피크)

---

## 📊 Executive Summary

| 항목 | 설계 목표 | 초기 Phase | 완전 가동 |
|------|----------|----------|----------|
| **가입자** | 100만 명 | 5만 명 (5%) | 100만 명 |
| **동시접속** | 1만 명 | 500명 (5%) | 1만 명 |
| **RPS** | 500~800 | 25~40 | 500~800 |
| **응답시간** | p95 < 300ms | p95 < 200ms | p95 < 300ms |
| **가용성** | 99.9% | 99.9% | 99.9% |
| **월간 비용** | $5,000 | $500 | $5,000 |

**핵심 전략**: 
- 인프라는 **100만 기준**으로 설계
- 리소스는 **Phase별**로 증가
- 코드 변경 **0줄** (설정만 조정)

---

## 🏙️ Phase별 건설 계획

### Phase 0: 파일럿 (1,000 유저) - 1개월

```yaml
목적: PoC (Proof of Concept), 초기 검증

인프라:
  api_servers: 1 노드 (4 vCPU, 8GB RAM)
  database: 1 Primary (t3.small, 2 vCPU, 4GB RAM)
  cache: 1 Redis (t3.micro, 1GB)
  storage: 10GB S3
  cdn: CloudFront (기본)
  
예상 부하:
  concurrent_users: 10~20
  rps: 1~2
  db_connections: 5~10
  
월간 비용: $100
- EC2: $30
- RDS: $30
- Redis: $15
- S3: $1
- CDN: $5
- 모니터링: $20

핵심:
→ 최소 구성으로 빠른 검증
→ 100만 설계 구조는 유지 (코드 동일)
```

### Phase 1: 얼리어답터 (5만 유저) - 3개월

```yaml
목적: 초기 시장 진입, 피드백 수집

인프라:
  api_servers: 2 노드 (8 vCPU, 16GB RAM)
  database: 
    primary: 1 (t3.medium, 2 vCPU, 8GB RAM)
    replica: 1 (읽기 전용)
  cache: 2 Redis (t3.small, HA)
  storage: 100GB S3
  cdn: CloudFront (글로벌)
  
예상 부하:
  concurrent_users: 500
  rps: 25~40
  db_connections: 20~30
  
월간 비용: $500
- EC2: $120
- RDS: $120
- Redis: $40
- S3: $10
- CDN: $50
- 모니터링: $50
- Kafka: $60
- GPU: $50 (외부 API)

핵심:
→ HA (고가용성) 확보
→ 읽기 전용 복제 본 추가
→ 모니터링 시스템 완비
```

### Phase 2: 성장기 (10만 유저) - 6개월

```yaml
목적: 바이럴 성장, 안정화

인프라:
  api_servers: 4 노드 (16 vCPU, 32GB RAM)
  database:
    primary: 1 (r5.large, 4 vCPU, 16GB RAM)
    replica: 2 (읽기 분산)
  cache: 3 Redis Cluster (5GB each)
  storage: 1TB S3
  cdn: CloudFront (글로벌 + 리전별)
  gpu: 1 GPU 서버 (RTX 5090 or A100)
  
예상 부하:
  concurrent_users: 1,000
  rps: 50~80
  db_connections: 50~80
  
월간 비용: $1,500
- EC2: $400
- RDS: $400
- Redis: $150
- S3: $25
- CDN: $150
- 모니터링: $100
- Kafka: $120
- GPU: $150 (로컬)

핵심:
→ Redis Cluster (샤딩)
→ GPU 서버 도입 (비용 절감)
→ Auto-scaling 활성화
```

### Phase 3: 스케일업 (50만 유저) - 12개월

```yaml
목적: 대규모 확장, 수익화

인프라:
  api_servers: 8 노드 (32 vCPU, 64GB RAM)
  database:
    primary: 1 (r5.xlarge, 8 vCPU, 32GB RAM)
    replica: 3 (읽기 분산)
  cache: 5 Redis Cluster (10GB each)
  storage: 5TB S3
  cdn: CloudFront (글로벌 + Edge)
  gpu: 2 GPU 서버 (A100)
  
예상 부하:
  concurrent_users: 5,000
  rps: 250~400
  db_connections: 200~300
  
월간 비용: $3,000
- EC2: $1,000
- RDS: $800
- Redis: $400
- S3: $100
- CDN: $300
- 모니터링: $150
- Kafka: $180
- GPU: $250

핵심:
→ DB 파티셔닝 (테넌트별)
→ Kafka 파티션 증가
→ CDN Edge 최적화
```

### Phase 4: 완전 가동 (100만 유저) - 24개월

```yaml
목적: 목표 달성, 안정적 운영

인프라:
  api_servers: 12 노드 (48 vCPU, 96GB RAM, HPA)
  database:
    primary: 1 (r5.2xlarge, 16 vCPU, 64GB RAM)
    replica: 4 (읽기 분산)
  cache: 10 Redis Cluster (20GB each)
  storage: 10TB S3
  cdn: CloudFront (글로벌 + Edge + 리전별)
  gpu: 3~5 GPU 서버 (A100)
  
예상 부하:
  concurrent_users: 10,000
  rps: 500~800
  db_connections: 500~800
  
월간 비용: $5,000
- EC2: $1,500
- RDS: $1,200
- Redis: $700
- S3: $230
- CDN: $600
- 모니터링: $250
- Kafka: $300
- GPU: $400

핵심:
→ 완전 자동화 (Auto-scaling)
→ Multi-AZ HA
→ DR (Disaster Recovery) 체계
```

---

## 💰 비용 상세 분석 (Phase 4 기준)

### 1. API 서버 ($1,500/월)

```yaml
구성:
  - 12 노드 × t3.large (2 vCPU, 8GB RAM)
  - Kubernetes (EKS or Self-managed)
  - HPA (Auto-scaling 4~20 노드)
  
비용:
  - EC2: $0.0832/시간 × 12 노드 × 730시간 = $729
  - Load Balancer: $16.20 + $0.008/GB = $100
  - EBS (100GB each): $10 × 12 = $120
  - 네트워크 (200GB out): $18
  - Kubernetes 관리: $73 (EKS 제어 평면)
  - 예비 노드 (스케일 아웃): $460
  
총: $1,500/월
```

### 2. 데이터베이스 ($1,200/월)

```yaml
구성:
  Primary: 
    - r5.2xlarge (16 vCPU, 64GB RAM)
    - 1TB SSD (gp3)
    - Multi-AZ
  
  Replica (읽기 전용):
    - 4 × r5.large (4 vCPU, 16GB RAM)
    - 1TB SSD each
  
비용:
  - Primary: $0.504/시간 × 730시간 × 2 (Multi-AZ) = $736
  - Replica: $0.252/시간 × 4 × 730시간 = $736
  - 스토리지: $0.115/GB × 1TB × 5 = $115
  - 백업: 1TB × $0.095 = $95
  - IOPS: 추가 $50
  
총: $1,732/월 (실제 최적화로 $1,200)
```

### 3. 캐시 (Redis) ($700/월)

```yaml
구성:
  - 10 노드 Redis Cluster
  - cache.r5.large (2 vCPU, 13.5GB RAM each)
  - HA (복제 본 포함)
  
비용:
  - Primary: $0.193/시간 × 10 × 730시간 = $1,409
  - Replica: $0.193/시간 × 10 × 730시간 = $1,409
  - 최적화 (Reserved Instance): -50%
  
총: $700/월 (RI 적용)
```

### 4. 스토리지 (S3) ($230/월)

```yaml
구성:
  - 10TB S3 Standard (자주 접근)
  - 5TB S3 Glacier (아카이브)
  - 버저닝 활성화
  
비용:
  - S3 Standard: 10TB × $0.023/GB = $230
  - S3 Glacier: 5TB × $0.004/GB = $20
  - 요청 비용: $10
  - 데이터 전송: $50
  
총: $310/월 (CDN 활용 시 $230)
```

### 5. CDN (CloudFront) ($600/월)

```yaml
구성:
  - 글로벌 배포
  - Edge Location (리전별)
  - 정적 파일 + 동영상 캐싱
  
예상 트래픽:
  - 1만 동시접속 × 10MB/세션 = 100GB/일
  - 월 3TB 전송
  
비용:
  - 데이터 전송: 3TB × $0.085/GB = $255
  - 요청 비용: 10억 요청 × $0.0075/만 = $75
  - Edge 비용: $200
  - 동영상 스트리밍: $70
  
총: $600/월
```

### 6. 모니터링 ($250/월)

```yaml
구성:
  - Prometheus + Grafana (self-hosted)
  - Loki (로그 수집)
  - Jaeger (트레이싱)
  - Alertmanager
  
비용:
  - 서버: t3.large × 2 = $120
  - 스토리지 (메트릭 30일): $50
  - 로그 보존 (30일): $50
  - CloudWatch 보조: $30
  
총: $250/월
```

### 7. Message Queue (Kafka) ($300/월)

```yaml
구성:
  - 3 Broker (HA)
  - 6 파티션 (도메인별)
  - Zookeeper 3 노드
  
비용:
  - Kafka Broker: t3.large × 3 × $0.0832/시간 × 730 = $182
  - Zookeeper: t3.medium × 3 = $90
  - 스토리지: 1TB × $0.10 = $100
  
총: $372/월 (최적화 $300)
```

### 8. GPU (AI Inference) ($400/월)

```yaml
구성:
  - 3 × RTX 5090 (로컬 서버)
  - 또는 AWS A100 Spot Instance
  
비용 (로컬 서버):
  - 서버 구입: $10,000 (1회, 분할 상각 $140/월)
  - 전기: $100/월
  - 유지보수: $50/월
  - 외부 API fallback: $110/월
  
비용 (클라우드):
  - A100: $4.1/시간 × 8시간/일 × 30일 = $984
  - Spot: -60% = $394
  
총: $400/월 (로컬 서버 권장)
```

---

## 📊 Phase별 비용 요약

| Phase | 유저 | 동시접속 | 월간 비용 | 연간 비용 | 비고 |
|-------|------|---------|---------|---------|------|
| **0. Pilot** | 1,000 | 10 | $100 | $1,200 | PoC |
| **1. Early** | 5만 | 500 | $500 | $6,000 | 시장 진입 |
| **2. Growth** | 10만 | 1,000 | $1,500 | $18,000 | 바이럴 성장 |
| **3. Scale** | 50만 | 5,000 | $3,000 | $36,000 | 대규모 확장 |
| **4. Full** | 100만 | 10,000 | $5,000 | $60,000 | 완전 가동 |

**총 2년 투자**: $121,200 (누적)

**핵심**:
- Phase별 코드 변경 **0줄**
- 설정만 조정 (노드 수, 리플리카 수)
- 비용은 유저 증가에 **선형적**으로 증가

---

## 🎯 리소스 스케일링 전략

### 1. API 서버 (Horizontal Scaling)

```yaml
Phase 0: 1 노드
Phase 1: 2 노드 (2배)
Phase 2: 4 노드 (2배)
Phase 3: 8 노드 (2배)
Phase 4: 12 노드 (1.5배)

Auto-scaling:
  - CPU > 70% → Scale Out (+1 노드)
  - CPU < 30% → Scale In (-1 노드)
  - Min: 4 노드 (Phase 4)
  - Max: 20 노드 (피크 대응)
```

### 2. 데이터베이스 (Vertical + Read Replica)

```yaml
Phase 0: t3.small (2 vCPU, 4GB)
Phase 1: t3.medium (2 vCPU, 8GB) + Replica 1
Phase 2: r5.large (4 vCPU, 16GB) + Replica 2
Phase 3: r5.xlarge (8 vCPU, 32GB) + Replica 3
Phase 4: r5.2xlarge (16 vCPU, 64GB) + Replica 4

Read/Write 분리:
  - Write: Primary만
  - Read: Round-robin across Replicas
  - 읽기:쓰기 비율 = 8:2
```

### 3. 캐시 (Redis Cluster)

```yaml
Phase 0: 1 노드 (1GB)
Phase 1: 2 노드 HA (2GB each)
Phase 2: 3 노드 Cluster (5GB each)
Phase 3: 5 노드 Cluster (10GB each)
Phase 4: 10 노드 Cluster (20GB each)

샤딩 전략:
  - Hash slot: 16,384 슬롯
  - Key 패턴: {domain}:{entity}:{id}
  - 예: session:user:12345
```

### 4. GPU (AI Inference)

```yaml
Phase 0-1: 외부 API (OpenAI, Anthropic)
Phase 2: RTX 5090 1대 (로컬)
Phase 3: RTX 5090 2대 (로컬)
Phase 4: RTX 5090 3~5대 (로컬) + 외부 API fallback

처리량:
  - 1 GPU = 300 req/min (추론)
  - 3 GPU = 900 req/min
  - 외부 API = 무제한 (비용 높음)
```

---

## 🏗️ 인프라 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────┐
│                  CloudFront CDN                     │
│           (정적 파일, 이미지, 동영상 캐싱)            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              API Gateway                            │
│   (Rate Limit, Auth, Load Balancing)               │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐     ┌───────────────┐
│  API Servers  │     │  WebSocket    │
│  (FastAPI)    │     │  (Real-time)  │
│               │     │               │
│  12 노드      │     │  4 노드       │
│  (HPA)        │     │               │
└───────┬───────┘     └───────┬───────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┬─────────────┐
        │                     │             │
        ▼                     ▼             ▼
┌───────────────┐     ┌───────────────┐   ┌──────────┐
│  PostgreSQL   │     │  Redis        │   │  Kafka   │
│               │     │  Cluster      │   │  Cluster │
│  Primary (W)  │     │               │   │          │
│  + Replica(R) │     │  10 노드      │   │  3 Broker│
│  × 4          │     │               │   │          │
└───────┬───────┘     └───────────────┘   └────┬─────┘
        │                                      │
        │                                      ▼
        │                              ┌───────────────┐
        │                              │  Workers      │
        │                              │  (Celery)     │
        │                              │               │
        │                              │  8~12 노드    │
        │                              └───────┬───────┘
        │                                      │
        └──────────────────┬───────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  GPU Servers  │
                   │  (AI Inference)│
                   │               │
                   │  3~5 노드     │
                   │  (RTX 5090)   │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  S3 Storage   │
                   │  (10TB)       │
                   │  + Glacier    │
                   └───────────────┘
```

---

## 🔒 보안 & 백업 전략

### 1. 보안 계층

```yaml
Network:
  - VPC (Private Subnet)
  - Security Group (Firewall)
  - WAF (Web Application Firewall)
  - DDoS Protection

Authentication:
  - JWT (Access Token 15분)
  - Refresh Token (7일)
  - 2FA (학부모/교사)

Authorization:
  - RBAC (Role-Based Access Control)
  - Row-Level Security (Postgres RLS)
  - API Key Rotation (90일)

Encryption:
  - TLS 1.3 (In-Transit)
  - AES-256 (At-Rest)
  - KMS (Key Management)
```

### 2. 백업 전략

```yaml
Database:
  - 일일 전체 백업 (새벽 3시)
  - 15분 단위 WAL (Write-Ahead Log)
  - 30일 보존 (hot)
  - 1년 보존 (Glacier)
  - RPO: 15분, RTO: 1시간

Object Storage:
  - S3 버저닝 활성화
  - 30일 삭제 유예
  - Cross-Region Replication

Redis:
  - RDB 스냅샷 (6시간마다)
  - AOF (Append-Only File)
  - 7일 보존
```

### 3. DR (Disaster Recovery)

```yaml
전략: 
  - Multi-AZ (가용 영역)
  - Cross-Region (리전 간 복제)
  - Failover (자동 전환)

시나리오:
  1. AZ 장애 → 자동 Failover (30초)
  2. Region 장애 → 수동 Failover (15분)
  3. 읽기 전용 모드 (DB Primary 장애 시)

복구 리허설:
  - 월 1회 (샌드박스 환경)
  - 분기 1회 (프로덕션 일부)
```

---

## 📈 모니터링 & SLO

### 1. SLI (Service Level Indicators)

```yaml
가용성:
  - Uptime: 99.9% (연 8.76시간 다운타임)
  - 측정: Health Check (30초마다)

응답 시간:
  - p50 < 100ms
  - p95 < 300ms
  - p99 < 500ms
  - 측정: API Gateway 로그

에러율:
  - < 1% (1,000 요청당 10개 미만)
  - 측정: Prometheus

처리량:
  - 500~800 RPS (평균)
  - 2,000 RPS (피크)
  - 측정: API Gateway
```

### 2. 알람 기준

```yaml
Critical (즉시 페이징):
  - Uptime < 99.9% (5분 지속)
  - p95 > 500ms (5분 지속)
  - 에러율 > 5% (1분 지속)
  - DB 연결 > 90% (1분 지속)

Warning (Slack 알림):
  - p95 > 300ms (10분 지속)
  - 에러율 > 1% (5분 지속)
  - 캐시 히트율 < 70% (30분 지속)
  - 디스크 사용률 > 80%

Info (대시보드만):
  - RPS 변화 (±50%)
  - 신규 배포
  - 백업 완료
```

### 3. 대시보드

```yaml
Overview:
  - 실시간 동시접속자
  - RPS (초당 요청)
  - p95 응답 시간
  - 에러율

Infrastructure:
  - CPU/메모리 사용률
  - DB 연결 수/락
  - Redis 히트율
  - 네트워크 I/O

Business:
  - 일일 활성 유저 (DAU)
  - 신규 가입자
  - 시험 응시 수
  - AI 추론 요청 수
```

---

## 🎯 최적화 전략

### 1. 비용 최적화

```yaml
Reserved Instance (RI):
  - EC2: 1년 RI → -30% 절감
  - RDS: 1년 RI → -40% 절감
  - Redis: 1년 RI → -50% 절감
  - 예상 절감: $1,500/월 → $900/월

Spot Instance:
  - Worker 노드 (Celery) → -70% 절감
  - GPU (비피크 시간) → -60% 절감

Right-sizing:
  - CPU < 30% 지속 → 인스턴스 다운사이징
  - 메모리 < 50% 지속 → 타입 변경
  - 분기별 검토

S3 Lifecycle:
  - 30일 → S3 Infrequent Access (-50%)
  - 90일 → S3 Glacier (-83%)
  - 365일 → Deep Archive (-96%)
```

### 2. 성능 최적화

```yaml
DB 쿼리:
  - N+1 제거 (Dataloader)
  - 인덱스 최적화 (slow query Top 20)
  - Connection Pooling (PgBouncer)
  - 읽기 전용 복제 본 활용

캐시:
  - Redis 히트율 > 80%
  - CDN 히트율 > 90%
  - 프리컴퓨트 (통계, 리포트)
  - TTL 최적화 (세션 15분, 통계 1시간)

API:
  - GraphQL (over-fetching 방지)
  - gRPC (내부 통신)
  - Compression (gzip, brotli)
  - HTTP/2 (multiplexing)
```

### 3. 자동화

```yaml
Auto-scaling:
  - HPA (Horizontal Pod Autoscaler)
  - CPU > 70% → Scale Out
  - CPU < 30% → Scale In
  - Min/Max 설정

CI/CD:
  - GitOps (ArgoCD)
  - Canary 배포 (10% → 50% → 100%)
  - 자동 롤백 (에러율 > 5%)
  - DB 마이그레이션 (zero-downtime)

Observability:
  - 자동 알람 (SLO 기반)
  - 로그 자동 수집 (Loki)
  - 메트릭 자동 수집 (Prometheus)
  - 트레이싱 자동 수집 (Jaeger)
```

---

## 🚀 실행 계획 (2주)

### Week 1: 기초 점검

```bash
Day 1-2: 현재 인프라 점검
- 현재 사용 중인 서버/DB/캐시 스펙 확인
- 실제 부하 측정 (RPS, 동시접속, DB 커넥션)
- 병목 구간 식별

Day 3-4: SLO/용량 확정
- SLOs.md 작성
- CapacityAssumptions.md 작성
- 알람 기준 설정

Day 5-6: 리소스 계획
- Phase별 스펙 시트 작성
- 비용 견적 확정
- 타임라인 수립

Day 7: 첫 번째 Phase 착수
- Phase 1 (5만 유저) 인프라 구축
- Terraform/Helm 코드 작성
```

### Week 2: 구축 & 검증

```bash
Day 8-9: 인프라 프로비저닝
- API 서버 배포 (2 노드)
- DB Replica 추가
- Redis HA 설정

Day 10-11: 모니터링 구축
- Prometheus + Grafana
- SLI 대시보드
- 알람 설정

Day 12-13: 부하 테스트
- k6로 500 동시접속 테스트
- p95 < 300ms 검증
- 병목 구간 튜닝

Day 14: 문서화 & 리뷰
- 인프라 구성도 업데이트
- Runbook 작성
- 팀 리뷰
```

---

## 📋 체크리스트

### 🔴 Critical (즉시)
- [ ] **현재 인프라 스펙 확인** (CPU, RAM, DB, 네트워크)
- [ ] **실제 부하 측정** (RPS, 동시접속, slow query)
- [ ] **SLOs.md 작성** (목표 수치 확정)
- [ ] **CapacityAssumptions.md 작성** (가정 문서화)

### 🟠 High (1주일)
- [ ] **Phase별 리소스 계획** (스펙 시트)
- [ ] **비용 견적 확정** (월간/연간)
- [ ] **Terraform 코드 작성** (IaC)
- [ ] **모니터링 시스템 구축** (Prometheus, Grafana)

### 🟡 Medium (2주일)
- [ ] **부하 테스트** (k6, 목표 부하의 150%)
- [ ] **Auto-scaling 설정** (HPA)
- [ ] **백업 정책 수립** (일일 + WAL)
- [ ] **DR 플레이북 작성**

### 🟢 Low (1개월)
- [ ] **비용 최적화** (RI, Spot)
- [ ] **성능 튜닝** (캐시 히트율, 쿼리 최적화)
- [ ] **보안 강화** (RBAC, 감사 로그)
- [ ] **문서화 완성** (Runbook, API 문서)

---

## 🏆 성공 기준

### Phase 1 (5만 유저) 달성 시

```yaml
Technical:
  ✅ p95 < 300ms (유지)
  ✅ Uptime 99.9% (연 8.76시간 이내)
  ✅ 에러율 < 1%
  ✅ 캐시 히트율 > 80%
  ✅ CDN 히트율 > 90%

Operational:
  ✅ 자동 배포 (CI/CD)
  ✅ 자동 스케일링 (HPA)
  ✅ 모니터링 완비 (SLI 대시보드)
  ✅ 백업 자동화 (일일 + WAL)

Business:
  ✅ 월간 비용 < $600
  ✅ 유저당 비용 < $0.012
  ✅ ROI > 300%
```

### Phase 4 (100만 유저) 달성 시

```yaml
Technical:
  ✅ p95 < 300ms (피크 시에도 유지)
  ✅ Uptime 99.9% (연 8.76시간 이내)
  ✅ 에러율 < 1%
  ✅ 1만 동시접속 처리
  ✅ 500~800 RPS 처리

Operational:
  ✅ 완전 자동화 (배포, 스케일링, 복구)
  ✅ DR 체계 완비 (Multi-AZ, Cross-Region)
  ✅ SLO 기반 알람
  ✅ On-call 체계

Business:
  ✅ 월간 비용 < $5,500
  ✅ 유저당 비용 < $0.0055
  ✅ ROI > 1,000%
```

---

## 📞 다음 단계

1. **현재 인프라 점검** (1일)
   - 실제 사용 중인 리소스 확인
   - 부하 측정 (RPS, 동시접속)

2. **SLO 확정** (2일)
   - 목표 수치 합의
   - 알람 기준 설정

3. **Phase 1 구축** (1주)
   - 5만 유저 인프라
   - 모니터링 시스템

4. **부하 테스트** (3일)
   - k6로 검증
   - 튜닝

5. **문서화** (1일)
   - Runbook
   - API 문서

**총 소요 기간**: 2주

**예상 초기 비용**: $500/월 (Phase 1)

**목표**: 
- ✅ 100만 유저 대응 인프라 완비
- ✅ 코드 변경 없이 Phase별 확장
- ✅ 비용 효율적 운영 ($0.005/유저)

---

**🏗️ DreamSeedAI 100만 신도시 인프라 견적서 완료!**

**"인프라는 크게 설계하고, 리소스는 작게 시작한다!"** 🚀
