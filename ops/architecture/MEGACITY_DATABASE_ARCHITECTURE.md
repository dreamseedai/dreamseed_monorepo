# 🗄️ DreamSeedAI MegaCity – Database Architecture

## Multi‑Tenant · Multi‑Zone · High‑Availability PostgreSQL Design

**버전:** 1.0  
**작성일:** 2025-11-21  
**작성자:** DreamSeedAI Architecture Team

---

# 📌 0. 개요

DreamSeedAI MegaCity Database Architecture는 **9개 Zone(도메인) + 수많은 Tenant(학교/학원/기관)** 를 하나의 통합 데이터베이스 내에서 안정적으로 운영하기 위한 기술 설계 문서입니다.

MegaCity 데이터 구조의 목표:

* **모든 Zone이 하나의 DB를 공유하되, 완전한 데이터 분리 보장**
* **테넌트 단위(org_id)로 강력한 격리 (RLS)**
* **Zone 단위(zone_id)로 글로벌 정책 적용**
* **고성능·확장성·백업·보안 모두 충족**
* **향후 Multi‑Region 확장을 위한 기반 구축**

이 문서는 MegaCity의 **PostgreSQL, Redis, Storage** 전체 구성과
스키마 전략(Entity Model), 성능 설계, 파티셔닝, 백업·복구를 모두 포함합니다.

---

# 🧱 1. Database Topology Overview

```
            ┌─────────────────────────┐
            │    PostgreSQL Cluster   │
            │  (Primary + Replicas)   │
            └──────────┬──────────────┘
                       │
               ┌───────▼─────────┐
               │   PgBouncer      │
               │ Connection Pool  │
               └───────┬─────────┘
                       │
         ┌─────────────▼────────────────┐
         │        FastAPI Backend        │
         │ (Multi‑Tenant Query Layer)    │
         └─────────────┬────────────────┘
                       │
       ┌───────────────▼───────────────┐
       │  Redis Cache / Redis Streams  │
       │ (Session, CAT State, Queues)  │
       └────────────────────────────────┘
```

---

# 🧩 2. Core Multi‑Tenant Design (zone_id + org_id)

MegaCity는 **Zone → Tenant → User** 구조입니다.

## 2.1 zone_id

* 도메인 단위(9개 Zone)
* `req.hostname` → zone 자동 추출

예:

```
univprepai.com → zone_id = 100
my-ktube.ai     → zone_id = 610
mpcstudy.com    → zone_id = 900
```

## 2.2 org_id

* 테넌트(학교/학원/기관) 단위 고유 ID
* 같은 Zone이라도 여러 org 존재 가능
* RLS(Row-Level Security)의 핵심 키

## 2.3 모든 주요 테이블에 두 필드 포함

```sql
zone_id  VARCHAR   NOT NULL
org_id   INTEGER   NOT NULL
```

---

# 🧵 3. Core Schema Entity Model

Megacity 공통 엔티티 구조:

```
organizations
users
students
teachers
classes
exams
exam_sessions
attempts
responses
items
kzone_contents
kzone_ai_results
```

## 3.1 Example: exams 테이블

```sql
CREATE TABLE exams (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  exam_type VARCHAR(50),
  zone_id VARCHAR NOT NULL,
  org_id INTEGER NOT NULL,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 3.2 Example: attempts 테이블

```sql
CREATE TABLE attempts (
  id SERIAL PRIMARY KEY,
  exam_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  zone_id VARCHAR NOT NULL,
  org_id INTEGER NOT NULL,
  started_at TIMESTAMP DEFAULT NOW(),
  ended_at TIMESTAMP,
  theta FLOAT,
  standard_error FLOAT,
  score FLOAT
);
```

---

# 🔒 4. Row-Level Security (RLS) – 데이터 격리의 핵심

RLS는 MegaCity DB 보안의 중심입니다.

## 4.1 RLS 활성화

```sql
ALTER TABLE attempts ENABLE ROW LEVEL SECURITY;
```

## 4.2 정책 정의

```sql
CREATE POLICY tenant_isolation_policy ON attempts
  USING (org_id = current_setting('app.current_org_id')::int
     AND zone_id = current_setting('app.current_zone_id'));
```

## 4.3 FastAPI에서 org_id / zone_id 설정

```python
async def set_tenant_context(request, call_next):
    user = get_current_user()
    session.execute(f"SET app.current_org_id = {user.org_id}")
    session.execute(f"SET app.current_zone_id = '{user.zone_id}'")
    return await call_next(request)
```

이 방식으로 DB가 **자동으로 잘못된 접근을 차단**합니다.

---

# 🗃️ 5. Indexing Strategy (성능 최적화)

MegaCity는 대량 데이터(시험, 응시기록, AI 로그)를 다루므로 인덱스 설계가 매우 중요합니다.

## 5.1 zone_id + org_id 복합 인덱스

```sql
CREATE INDEX idx_attempts_zone_org
ON attempts(zone_id, org_id);
```

## 5.2 자주 조회되는 필드 인덱스

```sql
CREATE INDEX idx_attempts_user ON attempts(user_id);
CREATE INDEX idx_responses_attempt ON responses(attempt_id);
CREATE INDEX idx_items_exam_difficulty ON items(exam_id, difficulty);
```

---

# 🧱 6. Partitioning Strategy (파티셔닝)

특히 `attempts`, `responses`, `kzone_ai_results` 같은 대량 테이블에 중요합니다.

## 6.1 시간 기반 파티셔닝

```sql
CREATE TABLE attempts_2025_11 PARTITION OF attempts
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

## 6.2 Zone 기반 파티셔닝 (선택)

대통령급 트래픽이 예상될 경우 Zone별 물리 분리도 가능:

```
attempts_univpartition
attempts_skillpartition
attempts_kzonepartition
```

---

# 💾 7. Connection Pooling (PgBouncer)

100k+ 유저가 동시에 사용해도 안정성 유지.

```ini
[databases]
dreamseed = host=postgres-primary port=5432 dbname=dreamseed

[pgbouncer]
pool_mode = transaction
max_client_conn = 2000
default_pool_size = 30
```

---

# 🚀 8. Redis Architecture

Redis는 MegaCity에서 다음 용도로 사용됩니다:

* Session storage
* CAT Engine 상태
* Redis Streams (Queue)
* K-Zone AI job queue
* Rate Limit counter

## 8.1 Redis Key Namespace

```
zone:{zone_id}:org:{org_id}:user:{user_id}:session
zone:{zone_id}:org:{org_id}:exam:{id}
zone:{zone_id}:kzone:audio:{id}
```

## 8.2 Streams

```
ai_jobs
exam_scoring
video_render
```

---

# 🧪 9. Transaction Strategy

## 9.1 ExamSession 흐름에서의 예시

```sql
BEGIN;
INSERT INTO attempts (exam_id, user_id, zone_id, org_id) VALUES (...);
UPDATE exam_sessions SET status = 'in_progress' WHERE id = ...;
COMMIT;
```

## 9.2 AI Job

* enqueue → GPU worker → store result → notify

---

# 🔁 10. Replication & HA

## 10.1 Streaming Replication

```
Primary → Replica1 → Replica2
```

읽기 전용 쿼리는 Replica로 분산.

## 10.2 Failover (Patroni)

* 자동 failover
* 리더 선출
* WAL 재동기화

---

# 🔐 11. Backup & PITR (Point‑in‑Time Recovery)

## 11.1 Daily Backup

```bash
pg_dump dreamseed | gzip > backup/db_$(date +%F).sql.gz
```

## 11.2 WAL Archive

```bash
archive_mode = on
archive_command = 'aws s3 cp %p s3://wal-archive/%f'
```

## 11.3 복구

```bash
pg_restore -d dreamseed backup.sql
```

---

# 📊 12. Performance Tuning

## 12.1 PostgreSQL 설정 권장값

```ini
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
max_connections = 300
work_mem = 64MB
```

## 12.2 Slow Query 모니터링

```sql
CREATE EXTENSION pg_stat_statements;

SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

# 🔍 13. Query Optimization Best Practices

## 13.1 N+1 문제 방지

```python
# Bad
for exam in exams:
    items = db.query(Item).filter(Item.exam_id == exam.id).all()

# Good
exams_with_items = db.query(Exam).options(joinedload(Exam.items)).all()
```

## 13.2 Pagination

```python
# Cursor-based pagination (권장)
SELECT * FROM attempts
WHERE id > last_id
ORDER BY id
LIMIT 100;
```

---

# 🧱 14. Data Migration Strategy

## 14.1 Zero-Downtime Migration (Alembic)

```bash
alembic revision --autogenerate -m "add zone_id to exams"
alembic upgrade head
```

## 14.2 Large Table Migration

```sql
-- Add column with default
ALTER TABLE attempts ADD COLUMN zone_id VARCHAR DEFAULT '100';

-- Update in batches
UPDATE attempts SET zone_id = '200' WHERE org_id BETWEEN 2000 AND 2999;

-- Remove default, add NOT NULL
ALTER TABLE attempts ALTER COLUMN zone_id DROP DEFAULT;
ALTER TABLE attempts ALTER COLUMN zone_id SET NOT NULL;
```

---

# 🌍 15. Multi-Region 확장 전략 (Phase 4)

## 15.1 지역별 Read Replica

```
KR Region: Primary
US Region: Read Replica (async)
EU Region: Read Replica (async)
```

## 15.2 Cross-Region Replication

```bash
# Logical Replication
CREATE PUBLICATION megacity_pub FOR ALL TABLES;
CREATE SUBSCRIPTION megacity_sub
CONNECTION 'host=kr-primary ...'
PUBLICATION megacity_pub;
```

---

# 🔒 16. Security Best Practices

## 16.1 암호화

* **At Rest**: PostgreSQL TDE (Transparent Data Encryption)
* **In Transit**: SSL/TLS 필수

```sql
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
```

## 16.2 Audit Logging

```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  action VARCHAR(50) NOT NULL,
  table_name VARCHAR(100),
  record_id INTEGER,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

---

# 📈 17. Scaling Roadmap

| 사용자 규모 | DB 구성 | 전략 |
|---------|---------|------|
| < 10K | Single Primary + 1 Replica | 기본 구성 |
| 10K-100K | Primary + 2 Replicas + PgBouncer | Read 분산 |
| 100K-1M | Primary + 3 Replicas + 파티셔닝 | Zone별 분리 고려 |
| 1M+ | Multi-Region + Sharding | 글로벌 확장 |

---

**문서 완료 - DreamSeedAI MegaCity Database Architecture v1.0**
