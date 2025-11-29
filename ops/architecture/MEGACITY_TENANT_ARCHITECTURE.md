# 🏛️ DreamSeedAI Multi-Zone / Multi-Tenant City Architecture

**버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: DreamSeedAI Architecture Team

---

## 🏙️ 0. 개요 (Executive Summary)

**DreamSeedAI는 9개 도메인 = 9개의 교육 특화 도시 구역(District)**으로 구성된 대규모 **MegaCity Architecture**를 운영합니다.

각 도메인은 서로 다른 목적(입시·전문대·취업·의료·전공·K-Culture·공공 교육)을 가진 **독립 도시(Zone)**이지만, 실제로는 하나의 중앙 **"DreamSeed Core City"** 아래에서 **데이터/인증/AI 모델을 공유**합니다.

이 문서는 **도메인별 분리(Zone)**와 **학생/교사/학부모 테넌트(Tenant)**를 함께 설명하는 **DreamSeedAI의 통합 멀티테넌트 구조 공식 설계 문서**입니다.

### 핵심 개념

```
MegaCity (DreamSeedAI)
 ├── Zone (9개 도메인/구역)
 │   ├── Tenant (조직: 학교/학원/기관)
 │   │   ├── User (학생/교사/학부모)
 │   │   ├── Class (반/수업)
 │   │   └── Exam (시험/평가)
 │   └── Zone-specific AI Models
 └── Core Infrastructure (SSO, API Gateway, DB, Redis, GPU)
```

---

## 🗺️ 1. MegaCity의 9개 Zone 구조

각 도메인은 DreamSeedAI 메가시티의 **독립 행정구역(Zone)**입니다.

| Zone | Domain | 역할 | 테넌트 타입 | AI 모델 특화 |
|------|--------|------|------------|-------------|
| **Z1** | `UnivPrepAI.com` | 대학 입시 전문 구역 | `academic` | SAT/ACT, 수능 예측 |
| **Z2** | `CollegePrepAI.com` | 전문대/폴리텍 준비 | `vocational` | 전문대 입시, 실무 역량 |
| **Z3** | `SkillPrepAI.com` | 직업/취업 역량 | `vocational` | 자격증, 취업 면접 |
| **Z4** | `MediPrepAI.com` | 간호/의료 보건 | `medical` | NCLEX, 간호사 국시 |
| **Z5** | `MajorPrepAI.com` | 대학원·전공·전문직 | `academic` | GRE, GMAT, 전공 심화 |
| **Z6** | `My-Ktube.com` | 문화·교육 허브 | `k-culture` | K-POP, 드라마, 한글 |
| **Z7** | `My-Ktube.ai` | K-Culture AI 기능 | `k-culture` | 음성/영상/댄스 분석 |
| **Z8** | `mpcstudy.com` | 무료 공공 교육 | `public` | 기초 학습, 무료 콘텐츠 |
| **Z9** | `DreamSeedAI.com` | 중앙 관제·Auth·Infra | `core` | 통합 플랫폼 |

### Zone 구조 비유 (도시 메타포)

DreamSeedAI는 **도시 메가시티의 9개 특별도시**로 구성되어 있고, 모든 도시는 다음 **공통 도로/철도망**을 공유합니다:

- 🔐 **SSO (Single Identity)** - 하나의 여권으로 모든 도시 이동
- 🚪 **Global API Gateway** - 중앙 관문
- 🤖 **Shared AI Engine** (vLLM GPU Cluster) - 공유 AI 인프라
- 🗄️ **Central DB / Redis Router** - 중앙 데이터센터
- 🔒 **City-Wide Security / Logging Framework** - 통합 보안

---

## 🧩 2. Tenant = 조직 단위 (학교/학원/기관)

### 개념 정의

- **Zone** = 도메인 / 국가 / 교육 목적
- **Tenant** = 각 도메인 안의 조직(학교/학원/기관)

즉:

```
MegaCity
 └── Zone (도메인)
      └── Tenant (학교/학원/교육기관)
           └── Users (학생/교사/학부모)
```

### 예시

**UnivPrepAI.com**
- 서울대입시학원 (org_id: 1001)
- 대치동 종합반 (org_id: 1002)
- 강남 SKY학원 (org_id: 1003)

**MediPrepAI.com**
- 간호학원 (org_id: 4001)
- 보건치료센터 교육기관 (org_id: 4002)

**My-Ktube.com**
- 해외 한국문화센터 (org_id: 6001)
- 대학교 한국학과 (org_id: 6002)

**DreamSeedAI.com**
- B2C 글로벌 단일 테넌트 (org_id: 9999)

---

## 🏛️ 3. Multi-Tenant DB 모델 (org_id 기반)

### 3.1 공통 스키마

모든 Zone과 Tenant는 **단일 PostgreSQL**에서 `org_id` 기준으로 분리됩니다.

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|----------|
| `organizations` | 테넌트(기관) | `id`, `name`, `zone_id`, `tenant_type`, `plan` |
| `users` | 사용자 (학생/교사/학부모/관리자) | `id`, `email`, `org_id`, `zone_id`, `role` |
| `classes` | 반·수업 | `id`, `name`, `org_id`, `teacher_id` |
| `students` | 학생 Profile | `id`, `user_id`, `org_id`, `grade`, `status` |
| `teachers` | 교사 Profile | `id`, `user_id`, `org_id`, `subject` |
| `exams` | 시험 정의 | `id`, `title`, `org_id`, `zone_id`, `exam_type` |
| `exam_sessions` | 시험 세션 | `id`, `exam_id`, `class_id`, `start_time` |
| `attempts` | 문항 응시 기록 | `id`, `exam_id`, `user_id`, `org_id`, `score` |
| `parent_student_relationships` | 학부모-학생 연결 | `parent_id`, `student_id`, `status` |

### 3.2 org_id 규칙

1. **같은 Zone이라도 여러 학교(Academy)가 존재** → `org_id`로 분리
2. **Zone의 도메인은 별개**, `org_id`는 DB 내부 식별자
3. **학생이 Zone을 이동해도 `user_id` 유지** (global identity)
4. **Cross-zone SSO**: 한 번 로그인하면 모든 Zone 접근 가능 (권한에 따라)

### 3.3 스키마 예시

```sql
-- Organizations (Tenant)
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    zone_id VARCHAR(20) NOT NULL,           -- "univ", "medi", "ktube"
    tenant_type VARCHAR(50) NOT NULL,       -- "academic", "vocational", "medical", "k-culture", "public"
    plan VARCHAR(50) DEFAULT 'free',        -- "free", "basic", "premium", "enterprise"
    status VARCHAR(20) DEFAULT 'active',    -- "active", "suspended", "deleted"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_org_zone (zone_id),
    INDEX idx_org_type (tenant_type)
);

-- Users (Global Identity)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    zone_id VARCHAR(20) NOT NULL,           -- Primary zone
    role VARCHAR(50) NOT NULL,              -- "student", "teacher", "parent", "org_admin"
    status VARCHAR(20) DEFAULT 'active',
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_org (org_id),
    INDEX idx_user_zone (zone_id),
    INDEX idx_user_role (role)
);

-- Exams (Multi-tenant)
CREATE TABLE exams (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    zone_id VARCHAR(20) NOT NULL,
    exam_type VARCHAR(50),                  -- "adaptive", "linear", "practice"
    created_by INTEGER REFERENCES users(id),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_exam_org_zone (org_id, zone_id)
);

-- Attempts (Multi-tenant)
CREATE TABLE attempts (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER NOT NULL REFERENCES exams(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    zone_id VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    score DECIMAL(5,2),
    ability_estimate DECIMAL(5,2),
    INDEX idx_attempt_user (user_id),
    INDEX idx_attempt_org (org_id)
);
```

---

## 🔒 4. Multi-Tenant 보안 (PostgreSQL RLS)

### 4.1 Row-Level Security (RLS) 개념

모든 테넌트는 **DB 차원에서 행 수준 보안(Row Level Security)**이 적용됩니다.

```sql
-- RLS 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE attempts ENABLE ROW LEVEL SECURITY;

-- Tenant Isolation Policy
CREATE POLICY tenant_isolation_policy ON users
    USING (org_id = current_setting('app.current_org_id')::int);

CREATE POLICY tenant_isolation_policy ON exams
    USING (org_id = current_setting('app.current_org_id')::int);

CREATE POLICY tenant_isolation_policy ON attempts
    USING (org_id = current_setting('app.current_org_id')::int);
```

### 4.2 FastAPI 미들웨어 자동 설정

```python
from fastapi import Request, Depends
from sqlalchemy.orm import Session

async def set_tenant_context(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """로그인 후 자동으로 Tenant Context 설정"""
    org_id = current_user["org_id"]
    
    # PostgreSQL 세션 변수 설정
    db.execute(f"SET app.current_org_id = {org_id}")
    db.execute(f"SET app.current_zone_id = '{current_user['zone_id']}'")
    
    request.state.org_id = org_id
    request.state.zone_id = current_user["zone_id"]

# FastAPI App에 미들웨어 적용
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # JWT에서 org_id 추출 → RLS 설정
    # ...
    response = await call_next(request)
    return response
```

### 4.3 RLS 효과

✅ **교사는 자기 학원(org_id)의 학생만 조회 가능**
```sql
-- Teacher (org_id=1001)가 조회 시
SELECT * FROM students;
-- 자동으로 WHERE org_id=1001 필터링됨
```

✅ **학부모는 자기 자녀만 조회 가능**
```sql
CREATE POLICY parent_student_policy ON students
    USING (
        id IN (
            SELECT student_id FROM parent_student_relationships
            WHERE parent_id = current_setting('app.current_user_id')::int
            AND status = 'approved'
        )
    );
```

✅ **하나의 DB에서 수천 테넌트 분리 가능**
- Application 코드에서 `org_id` 체크 불필요
- DB 레벨에서 자동 격리
- Cross-tenant 데이터 누출 방지

### 4.4 RLS 트러블슈팅 가이드

**일반적인 RLS 문제와 해결법:**

#### 문제 1: RLS가 적용되지 않음 (No rows returned)

**증상:**
```python
# FastAPI에서 쿼리 실행 시 빈 결과
users = db.query(User).all()  # []
```

**원인:** `app.current_org_id`가 설정되지 않음

**해결:**
```python
# 미들웨어에서 app.current_org_id 설정 확인
@app.middleware("http")
async def set_tenant_context(request: Request, call_next):
    user = get_current_user(request)
    
    # ✅ 반드시 설정 필요
    db.execute(f"SET app.current_org_id = {user.org_id}")
    
    response = await call_next(request)
    return response
```

#### 문제 2: Performance 저하 (Slow queries)

**원인:** `org_id`에 Index가 없음

**해결:**
```sql
-- org_id Index 생성
CREATE INDEX CONCURRENTLY idx_attempts_org_id ON attempts(org_id);

-- Composite Index (복합 조건)
CREATE INDEX CONCURRENTLY idx_attempts_org_user 
  ON attempts(org_id, user_id);
```

#### 문제 3: Cross-Tenant Data Leak

**원인:** `FORCE ROW LEVEL SECURITY`가 설정되지 않음

**해결:**
```sql
-- FORCE ROW LEVEL SECURITY 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;
```

---

## 🏙️ 5. Multi-Zone의 핵심: Domain ↔ Zone ↔ org_id 매핑

### 5.1 Zone ID 표

| Zone ID | Domain | Zone Code | Tenant Type |
|---------|--------|-----------|-------------|
| **100** | `univprepai.com` | `univ` | `academic` |
| **200** | `collegeprepai.com` | `college` | `vocational` |
| **300** | `skillprepai.com` | `skill` | `vocational` |
| **400** | `mediprepai.com` | `medi` | `medical` |
| **500** | `majorprepai.com` | `major` | `academic` |
| **600** | `my-ktube.com` | `ktube` | `k-culture` |
| **610** | `my-ktube.ai` | `ktube-ai` | `k-culture` |
| **900** | `mpcstudy.com` | `mpc` | `public` |
| **999** | `dreamseedai.com` | `core` | `core` |

### 5.2 org_id 범위 전략

각 Zone은 독립적인 `org_id` 범위를 갖습니다.

| Zone | org_id 범위 | 예시 조직 |
|------|------------|----------|
| **UnivPrep** | 1000–1999 | 서울대입시학원 (1001), 대치동학원 (1002) |
| **CollegePrep** | 2000–2999 | 폴리텍 입시학원 (2001) |
| **SkillPrep** | 3000–3999 | IT자격증학원 (3001), 공무원학원 (3002) |
| **MediPrep** | 4000–4999 | 간호학원 (4001), 간호사국시반 (4002) |
| **MajorPrep** | 5000–5999 | 대학원 준비 (5001), MBA학원 (5002) |
| **My-Ktube.com** | 6000–6099 | 해외 한국문화센터 (6001) |
| **My-Ktube.ai** | 6100–6199 | K-Zone AI 개인 사용자 (6101) |
| **MPCStudy** | 9000–9099 | 공공 교육 플랫폼 (9001) |
| **DreamSeedAI Core** | 9999 | 글로벌 B2C 단일 테넌트 (9999) |

### 5.3 도메인 → Zone → org_id 자동 매핑

```python
# Domain → Zone ID 매핑
DOMAIN_ZONE_MAP = {
    "univprepai.com": {"zone_id": 100, "zone_code": "univ", "tenant_type": "academic"},
    "collegeprepai.com": {"zone_id": 200, "zone_code": "college", "tenant_type": "vocational"},
    "skillprepai.com": {"zone_id": 300, "zone_code": "skill", "tenant_type": "vocational"},
    "mediprepai.com": {"zone_id": 400, "zone_code": "medi", "tenant_type": "medical"},
    "majorprepai.com": {"zone_id": 500, "zone_code": "major", "tenant_type": "academic"},
    "my-ktube.com": {"zone_id": 600, "zone_code": "ktube", "tenant_type": "k-culture"},
    "my-ktube.ai": {"zone_id": 610, "zone_code": "ktube-ai", "tenant_type": "k-culture"},
    "mpcstudy.com": {"zone_id": 900, "zone_code": "mpc", "tenant_type": "public"},
    "dreamseedai.com": {"zone_id": 999, "zone_code": "core", "tenant_type": "core"}
}

def get_zone_from_domain(domain: str) -> dict:
    """도메인에서 Zone 정보 추출"""
    return DOMAIN_ZONE_MAP.get(domain, DOMAIN_ZONE_MAP["dreamseedai.com"])

# FastAPI 미들웨어에서 자동 추출
@app.middleware("http")
async def zone_detection_middleware(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0]
    zone_info = get_zone_from_domain(host)
    request.state.zone_id = zone_info["zone_code"]
    request.state.tenant_type = zone_info["tenant_type"]
    response = await call_next(request)
    return response
```

---

## 🔑 6. Cross-Domain SSO (Single Sign-On)

### 6.1 SSO 개념

**한 번의 로그인으로 모든 Zone 접근 가능**

- 학생이 `UnivPrepAI.com`에서 로그인 → `MediPrepAI.com`으로 이동 시 재로그인 불필요
- JWT는 Zone에 독립적 (Global Identity)
- 권한은 Zone별로 다를 수 있음

### 6.2 SSO 아키텍처

```
사용자 → app.univprepai.com/login
  ↓ 로그인 성공
JWT 발급 (Global Token)
  ↓ 토큰 저장 (Cookie, domain=.dreamseedai.com)
사용자 → api.mediprepai.com/exams
  ↓ JWT 검증 (Zone 무관)
✅ 접근 허용 (org_id, zone_id 기반 권한 체크)
```

### 6.3 JWT 구조 (Cross-zone)

```json
{
  "sub": "user_12345",
  "email": "student@univprepai.com",
  "zone_id": "univ",                    // Primary zone
  "org_id": 1001,
  "role": "student",
  "permissions": ["exam:read", "attempt:create"],
  "zones_access": ["univ", "medi", "skill"],  // 접근 가능한 Zone 목록
  "iat": 1700000000,
  "exp": 1700086400
}
```

### 6.4 Cross-zone 권한 체크

```python
@app.get("/api/v1/exams/{exam_id}")
async def get_exam(
    exam_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cross-zone 시험 조회"""
    
    # 1. 현재 요청 Zone 추출
    current_zone = request.state.zone_id
    
    # 2. 사용자의 Zone 접근 권한 확인
    if current_zone not in current_user.get("zones_access", []):
        raise HTTPException(status_code=403, detail="Zone access denied")
    
    # 3. Exam 조회 (Zone 격리)
    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.zone_id == current_zone,
        Exam.org_id == current_user["org_id"]
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    return exam
```

### 6.5 Cross-zone 사용자 이동 시나리오

**시나리오**: 학생이 UnivPrep (입시) → MediPrep (간호사 준비)로 이동

```python
# 1. 사용자가 MediPrep 가입 신청
@app.post("/api/v1/users/join-zone")
async def join_zone(
    target_zone: str,  # "medi"
    target_org_id: int,  # 4001 (간호학원)
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """다른 Zone 가입 신청"""
    
    # 2. User의 zones_access 업데이트
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # 3. Zone 권한 추가
    if target_zone not in user.zones_access:
        user.zones_access.append(target_zone)
    
    # 4. 새 조직 연결 (secondary org)
    user_org_link = UserOrganizationLink(
        user_id=user.id,
        org_id=target_org_id,
        zone_id=target_zone,
        status="active"
    )
    db.add(user_org_link)
    db.commit()
    
    # 5. JWT 재발급 (새 zones_access 반영)
    new_token = create_access_token(user)
    return {"access_token": new_token, "message": "Joined MediPrep zone"}
```

---

## 🗄️ 7. 데이터 파티셔닝 전략 (Multi-Tenant Data Isolation)

### 7.1 Logical Partitioning (org_id 기반)

**단일 테이블에서 `org_id`로 논리적 분리**

```sql
-- 장점: 간단한 구조, Cross-tenant 집계 가능
-- 단점: 대규모 테넌트 시 성능 저하 가능

SELECT * FROM exams WHERE org_id = 1001;
```

### 7.2 Physical Partitioning (Zone별 테이블)

**Zone별로 물리적 테이블 분리 (향후 확장)**

```sql
-- Zone별 파티션 테이블
CREATE TABLE exams_univ PARTITION OF exams FOR VALUES IN ('univ');
CREATE TABLE exams_medi PARTITION OF exams FOR VALUES IN ('medi');
CREATE TABLE exams_ktube PARTITION OF exams FOR VALUES IN ('ktube');

-- 자동 라우팅
INSERT INTO exams (zone_id, title, org_id) VALUES ('univ', 'SAT Math', 1001);
-- 자동으로 exams_univ에 저장됨
```

### 7.3 Hybrid Partitioning (Zone + org_id)

```sql
-- Zone별 파티션 + org_id 인덱스
CREATE TABLE exams (
    id SERIAL,
    zone_id VARCHAR(20),
    org_id INTEGER,
    title VARCHAR(255),
    PRIMARY KEY (id, zone_id)
) PARTITION BY LIST (zone_id);

CREATE INDEX idx_exams_org ON exams_univ (org_id);
CREATE INDEX idx_exams_org ON exams_medi (org_id);
```

### 7.4 데이터 격리 수준 비교

| 전략 | 격리 수준 | 성능 | 복잡도 | 추천 시나리오 |
|------|----------|------|--------|-------------|
| **Logical (org_id)** | ⭐⭐⭐ | ⭐⭐ | ⭐ | 초기 단계, 테넌트 < 1000 |
| **Physical (Zone)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Zone별 독립 DB, 테넌트 > 10000 |
| **Hybrid (Zone+org)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 대규모 운영, 최고 성능 |

---

## 🔴 8. Multi-Tenant Redis Caching 전략

### 8.1 Redis Key Namespace

**Tenant별 키 네임스페이스 분리**

```
Pattern: {zone_id}:{org_id}:{resource_type}:{resource_id}

Examples:
- univ:1001:exam:123           # UnivPrep 학원 1001의 시험 123
- medi:4001:user:456           # MediPrep 학원 4001의 사용자 456
- ktube:6001:session:789       # K-Zone 조직 6001의 세션 789
- core:9999:global:config      # 글로벌 설정 (모든 Zone 공유)
```

### 8.2 Redis 캐싱 예시

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_exam_cache(zone_id: str, org_id: int, exam_id: int) -> dict:
    """Multi-tenant 캐시 조회"""
    cache_key = f"{zone_id}:{org_id}:exam:{exam_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # DB에서 조회 후 캐싱
    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.zone_id == zone_id,
        Exam.org_id == org_id
    ).first()
    
    # TTL 1시간
    redis_client.setex(cache_key, 3600, json.dumps(exam.dict()))
    return exam

def invalidate_exam_cache(zone_id: str, org_id: int, exam_id: int):
    """캐시 무효화"""
    cache_key = f"{zone_id}:{org_id}:exam:{exam_id}"
    redis_client.delete(cache_key)
```

### 8.3 Multi-Tenant Cache Patterns

#### Pattern 1: Tenant-specific Cache
```python
# 특정 테넌트의 모든 시험 목록 캐싱
def get_tenant_exams(zone_id: str, org_id: int) -> list:
    cache_key = f"{zone_id}:{org_id}:exams:list"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    exams = db.query(Exam).filter(
        Exam.zone_id == zone_id,
        Exam.org_id == org_id
    ).all()
    
    redis_client.setex(cache_key, 600, json.dumps([e.dict() for e in exams]))
    return exams
```

#### Pattern 2: User Session Cache
```python
# 사용자 세션 (Cross-zone)
def set_user_session(user_id: int, zone_id: str, session_data: dict):
    """사용자 세션 저장 (Zone 무관)"""
    cache_key = f"session:{user_id}:{zone_id}"
    redis_client.setex(cache_key, 86400, json.dumps(session_data))  # 24시간

def get_user_session(user_id: int, zone_id: str) -> dict:
    cache_key = f"session:{user_id}:{zone_id}"
    cached = redis_client.get(cache_key)
    return json.loads(cached) if cached else None
```

#### Pattern 3: CAT State Cache (Exam Progress)
```python
# Adaptive Testing 상태 (Tenant 독립)
def get_cat_state(attempt_id: int, zone_id: str, org_id: int) -> dict:
    """CAT 상태 조회"""
    cache_key = f"{zone_id}:{org_id}:cat:{attempt_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # 새 CAT 상태 초기화
    cat_state = {
        "ability": 0.0,
        "sem": 1.0,
        "items_administered": [],
        "responses": []
    }
    redis_client.setex(cache_key, 7200, json.dumps(cat_state))  # 2시간
    return cat_state
```

### 8.4 Redis 캐시 무효화 전략

```python
# 1. Exam 수정 시 캐시 무효화
@app.put("/api/v1/exams/{exam_id}")
async def update_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    # DB 업데이트
    exam.title = exam_update.title
    db.commit()
    
    # 캐시 무효화
    invalidate_exam_cache(exam.zone_id, exam.org_id, exam_id)
    
    # 테넌트 전체 시험 목록 캐시도 무효화
    redis_client.delete(f"{exam.zone_id}:{exam.org_id}:exams:list")
    
    return exam
```

---

## 🚪 9. Multi-Tenant API Gateway 라우팅 규칙

### 9.1 API Gateway 라우팅 흐름

```
1. 사용자 요청: https://api.univprepai.com/api/v1/exams
   ↓
2. Cloudflare Edge (DNS resolve)
   ↓
3. Nginx/Traefik (Reverse Proxy)
   ↓ Host 헤더: api.univprepai.com
4. Zone 감지: zone_id = "univ"
   ↓
5. JWT 검증 → org_id = 1001, role = "teacher"
   ↓
6. FastAPI Backend (Port 8000)
   ↓ SET app.current_org_id = 1001
7. PostgreSQL RLS 적용
   ↓ WHERE org_id = 1001
8. Response 반환
```

### 9.2 API Endpoint 규칙

**전체 API는 Zone에 무관하게 동일한 구조 사용**

```
https://api.<domain>/api/v1/exams
https://api.<domain>/api/v1/attempts
https://api.<domain>/api/v1/users/me
https://api.<domain>/api/v1/analytics
```

**Zone별 특화 API (선택적)**

```
# K-Zone AI 전용 API
https://api.my-ktube.ai/api/v1/kzone/voice/analyze
https://api.my-ktube.ai/api/v1/kzone/dance/pose-detection

# MediPrep 전용 API
https://api.mediprepai.com/api/v1/nclex/practice
```

### 9.3 Multi-Tenant API 라우팅 구현

```python
# FastAPI 라우터
@app.get("/api/v1/exams")
async def get_exams(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Multi-tenant 시험 목록 조회"""
    
    # 1. Zone 감지 (미들웨어에서 자동 설정)
    zone_id = request.state.zone_id
    org_id = current_user["org_id"]
    
    # 2. RLS 적용 (자동)
    db.execute(f"SET app.current_org_id = {org_id}")
    
    # 3. 쿼리 (org_id 필터링은 RLS가 자동 처리)
    exams = db.query(Exam).filter(
        Exam.zone_id == zone_id
    ).all()
    
    return exams
```

---

## 🤖 10. AI 모델 선택 규칙 (Zone별 AI 특화)

### 10.1 Zone별 AI 모델 매핑

| Zone | Primary AI Model | Language | Specialization |
|------|-----------------|----------|----------------|
| **UnivPrep** | Qwen2.5-72B-Instruct | 한국어/영어 | SAT/ACT, 수능 예측 |
| **CollegePrep** | Llama 3.1-70B | 한국어/영어 | 전문대 입시, 실무 |
| **SkillPrep** | GPT-4o | 다국어 | 자격증, 면접 분석 |
| **MediPrep** | Claude 3.5 Sonnet | 영어/한국어 | NCLEX, 의료 전문 |
| **MajorPrep** | DeepSeek-V2.5 | 영어/한국어 | GRE, GMAT, 논문 |
| **K-Zone** | Whisper-Large-v3 | 한국어 | 음성/영상 분석 |
| **K-Zone AI** | MediaPipe + vLLM | 한국어 | Pose, 댄스, 드라마 |
| **MPCStudy** | Llama 3.2-3B | 다국어 | 기초 학습 |

### 10.2 AI 모델 라우팅 로직

```python
# Zone별 AI 모델 선택
AI_MODEL_MAP = {
    "univ": "qwen2.5-72b-instruct",
    "college": "llama-3.1-70b",
    "skill": "gpt-4o",
    "medi": "claude-3.5-sonnet",
    "major": "deepseek-v2.5",
    "ktube": "whisper-large-v3",
    "ktube-ai": "vllm-llama-3.1-70b",
    "mpc": "llama-3.2-3b"
}

async def get_ai_response(zone_id: str, prompt: str) -> str:
    """Zone별 AI 모델 호출"""
    model = AI_MODEL_MAP.get(zone_id, "llama-3.1-70b")
    
    # vLLM API 호출
    response = await vllm_client.complete(
        model=model,
        prompt=prompt,
        max_tokens=1024,
        temperature=0.7
    )
    
    return response["choices"][0]["text"]
```

### 10.3 Multi-modal AI 선택 (K-Zone)

```python
# K-Zone AI 특화 라우팅
@app.post("/api/v1/kzone/voice/analyze")
async def analyze_voice(file: UploadFile):
    """음성 분석 (Whisper)"""
    audio_path = await save_uploaded_file(file)
    
    # Whisper 호출
    result = whisper_model.transcribe(audio_path, language="ko")
    
    # vLLM으로 피드백 생성
    feedback = await vllm_client.complete(
        model="llama-3.1-70b",
        prompt=f"다음 발음을 평가해주세요:\n{result['text']}"
    )
    
    return {
        "transcription": result["text"],
        "feedback": feedback,
        "pronunciation_score": calculate_score(result)
    }
```

---

## 🔐 11. SSO + 권한 + 정책 통합 (Unified Auth)

### 11.1 통합 인증 아키텍처

```
┌─────────────────────────────────────────────┐
│       DreamSeedAI Core Auth Service         │
│  (Single Identity, Global JWT)              │
└────────┬────────────────────────────────────┘
         │
         ├─── UnivPrepAI.com (Zone: univ, org_id: 1001-1999)
         ├─── CollegePrepAI.com (Zone: college, org_id: 2000-2999)
         ├─── MediPrepAI.com (Zone: medi, org_id: 4000-4999)
         ├─── My-Ktube.ai (Zone: ktube-ai, org_id: 6100-6199)
         └─── DreamSeedAI.com (Zone: core, org_id: 9999)
```

### 11.2 RBAC 역할 정의 (Zone 독립적)

```python
class Role(str, Enum):
    SUPER_ADMIN = "super_admin"      # 전체 시스템 관리 (모든 Zone)
    ZONE_ADMIN = "zone_admin"        # Zone별 관리 (UnivPrep 전체)
    ORG_ADMIN = "org_admin"          # 조직별 관리 (특정 학원)
    TEACHER = "teacher"              # 교사 (시험 생성, 학생 관리)
    STUDENT = "student"              # 학생 (시험 응시)
    PARENT = "parent"                # 학부모 (자녀 성적 조회)
    GUEST = "guest"                  # 게스트 (공개 시험만)

# Zone별 역할 매핑
ZONE_ROLE_MAP = {
    "univ": ["org_admin", "teacher", "student", "parent"],
    "medi": ["org_admin", "teacher", "student"],
    "ktube": ["student", "guest"],  # 개인 사용자 중심
    "core": ["super_admin", "zone_admin"]
}
```

### 11.3 Cross-zone 권한 체크

```python
def check_zone_access(user: dict, target_zone: str) -> bool:
    """Zone 접근 권한 확인"""
    
    # 1. Super Admin은 모든 Zone 접근 가능
    if user["role"] == "super_admin":
        return True
    
    # 2. 사용자의 zones_access 확인
    if target_zone in user.get("zones_access", []):
        return True
    
    # 3. Primary Zone 체크
    if user["zone_id"] == target_zone:
        return True
    
    return False

@app.get("/api/v1/cross-zone/analytics")
async def get_cross_zone_analytics(
    zones: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cross-zone 분석 (Super Admin만)"""
    
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    
    analytics = {}
    for zone in zones:
        analytics[zone] = get_zone_analytics(zone, db)
    
    return analytics
```

---

## 📊 12. "Mega City 행정구역" 메타포 요약

DreamSeedAI MegaCity를 **실제 도시**로 비유하면:

| 개념 | 도시 메타포 | DreamSeedAI |
|------|-----------|-------------|
| **MegaCity** | 서울특별시 (전체 도시) | DreamSeedAI 플랫폼 |
| **Zone** | 강남구, 종로구 (행정구역) | UnivPrep, MediPrep, K-Zone (도메인) |
| **Tenant** | 아파트 단지, 학교 (건물) | 학원, 학교, 기관 (org_id) |
| **User** | 주민 (학생, 교사, 학부모) | 플랫폼 사용자 |
| **SSO** | 주민등록증 (하나의 신분증) | Global JWT (하나의 로그인) |
| **API Gateway** | 지하철/버스 (교통망) | Nginx/Traefik (라우팅) |
| **Database** | 시청 데이터센터 (중앙 DB) | PostgreSQL (통합 DB) |
| **Redis** | 구청 캐시 (지역 캐시) | Redis (Zone별 캐시) |
| **AI Models** | 구청별 공공 서비스 | Zone별 특화 AI 모델 |

### 12.1 "도시 이동" 시나리오 (Cross-zone)

**시나리오**: 학생이 강남구(UnivPrep) → 종로구(MediPrep) 이동

1. **주민등록증 (SSO)**: 한 번 발급받으면 모든 구역 이동 가능
2. **전입신고 (Zone 가입)**: MediPrep 학원에 등록 → `zones_access` 업데이트
3. **구청 서비스 (Zone-specific API)**: MediPrep 전용 NCLEX 시험 접근
4. **데이터 격리**: 강남구 학원 성적과 종로구 학원 성적은 별도 관리
5. **통합 대시보드**: 시청(Core)에서 모든 구역 성적 통합 조회 가능

---

## 📋 13. Multi-Tenant 체크리스트

### 개발 단계
```
□ 1. Zone ID 매핑 테이블 생성
□ 2. org_id 범위 정의 (Zone별)
□ 3. PostgreSQL RLS 정책 적용
□ 4. Multi-tenant 미들웨어 구현
□ 5. Redis Key Namespace 표준화
□ 6. Cross-zone SSO 구현
□ 7. Zone별 AI 모델 라우팅
□ 8. RBAC 권한 체계 구현
□ 9. Audit Log (Tenant 격리)
□ 10. Unit Test (Multi-tenant 시나리오)
```

### 배포 단계
```
□ 1. Zone별 도메인 DNS 설정
□ 2. Nginx/Traefik Zone 라우팅 설정
□ 3. PostgreSQL RLS 활성화
□ 4. Redis Cluster (Namespace 분리)
□ 5. JWT Secret 보안 설정
□ 6. Cross-zone 권한 테스트
□ 7. 성능 테스트 (Tenant 격리)
□ 8. Backup/복구 (Tenant별)
□ 9. 모니터링 (Tenant별 메트릭)
□ 10. 문서화 (Tenant 가이드)
```

### 운영 단계
```
□ 1. Tenant 추가 프로세스 자동화
□ 2. Zone간 데이터 이관 도구
□ 3. Tenant별 리소스 모니터링
□ 4. Cross-zone 사용자 분석
□ 5. RLS 정책 검증 (월간)
□ 6. Redis 캐시 효율 분석
□ 7. AI 모델 사용량 추적 (Zone별)
□ 8. Tenant Isolation 감사
□ 9. 성능 최적화 (Partitioning)
□ 10. 보안 감사 (Cross-tenant 누출 방지)
```

---

---

---

## 🌐 6. Multi-Zone Request Routing (Global Gateway)

### 6.0 Domain → Zone Header 매핑 테이블 (운영 참고)

**전체 9개 도메인 API 라우팅 매트릭스:**

| Domain | API Host | X-Zone-Id | X-Zone-Code | X-Tenant-Type | org_id Range |
|--------|----------|-----------|-------------|---------------|-------------|
| UnivPrepAI.com | api.univprepai.com | 100 | univ | academic | 1000-1999 |
| CollegePrepAI.com | api.collegeprepai.com | 200 | college | vocational | 2000-2999 |
| SkillPrepAI.com | api.skillprepai.com | 300 | skill | vocational | 3000-3999 |
| MediPrepAI.com | api.mediprepai.com | 400 | medi | medical | 4000-4999 |
| MajorPrepAI.com | api.majorprepai.com | 500 | major | academic | 5000-5999 |
| My-Ktube.com | api.my-ktube.com | 600 | ktube | k-culture | 6000-6099 |
| My-Ktube.ai | api.my-ktube.ai | 610 | ktube-ai | k-culture | 6100-6199 |
| mpcstudy.com | api.mpcstudy.com | 900 | mpc | public | 9000-9099 |
| DreamSeedAI.com | api.dreamseedai.com | 999 | core | core | 9900-9999 |

**사용 예시:**

```bash
# UnivPrep API 호출
curl -H "X-Zone-Id: 100" \
     -H "X-Zone-Code: univ" \
     -H "Authorization: Bearer <token>" \
     https://api.univprepai.com/api/v1/exams

# K-Zone AI API 호출
curl -H "X-Zone-Id: 610" \
     -H "X-Zone-Code: ktube-ai" \
     -H "Authorization: Bearer <token>" \
     https://api.my-ktube.ai/api/v1/voice/analyze
```

**API Gateway 검증 스크립트:**

```bash
#!/bin/bash
# scripts/validate_zone_routing.sh

DOMAINS=(
  "api.univprepai.com:100:univ"
  "api.skillprepai.com:300:skill"
  "api.my-ktube.ai:610:ktube-ai"
)

for entry in "${DOMAINS[@]}"; do
  IFS=":" read -r domain zone_id zone_code <<< "$entry"
  
  echo "Testing $domain..."
  
  response=$(curl -s -H "X-Zone-Id: $zone_id" \
                   -H "X-Zone-Code: $zone_code" \
                   "https://$domain/health")
  
  if echo "$response" | grep -q "ok"; then
    echo "✅ $domain: Zone routing OK"
  else
    echo "❌ $domain: Zone routing FAILED"
  fi
done
```

---

### 6.1 Browser → Next.js (Frontend Zone Detection)

**Frontend는 Domain 기반으로 Zone을 자동 감지합니다.**

```typescript
// lib/zone-detection.ts
export const ZONE_CONFIG = {
  'app.univprepai.com': { 
    zoneId: 100, 
    zoneCode: 'univ', 
    tenantType: 'academic',
    primaryColor: '#1E40AF',
    logo: '/logos/univ.svg'
  },
  'app.collegeprepai.com': { 
    zoneId: 200, 
    zoneCode: 'college', 
    tenantType: 'vocational',
    primaryColor: '#059669',
    logo: '/logos/college.svg'
  },
  'app.skillprepai.com': { 
    zoneId: 300, 
    zoneCode: 'skill', 
    tenantType: 'vocational',
    primaryColor: '#DC2626',
    logo: '/logos/skill.svg'
  },
  'app.mediprepai.com': { 
    zoneId: 400, 
    zoneCode: 'medi', 
    tenantType: 'medical',
    primaryColor: '#7C3AED',
    logo: '/logos/medi.svg'
  },
  'app.majorprepai.com': { 
    zoneId: 500, 
    zoneCode: 'major', 
    tenantType: 'academic',
    primaryColor: '#EA580C',
    logo: '/logos/major.svg'
  },
  'app.my-ktube.com': { 
    zoneId: 600, 
    zoneCode: 'ktube', 
    tenantType: 'k-culture',
    primaryColor: '#EC4899',
    logo: '/logos/ktube.svg'
  },
  'app.my-ktube.ai': { 
    zoneId: 610, 
    zoneCode: 'ktube-ai', 
    tenantType: 'k-culture',
    primaryColor: '#8B5CF6',
    logo: '/logos/ktube-ai.svg'
  },
  'app.mpcstudy.com': { 
    zoneId: 900, 
    zoneCode: 'mpc', 
    tenantType: 'public',
    primaryColor: '#10B981',
    logo: '/logos/mpc.svg'
  },
  'app.dreamseedai.com': { 
    zoneId: 999, 
    zoneCode: 'core', 
    tenantType: 'core',
    primaryColor: '#3B82F6',
    logo: '/logos/dreamseed.svg'
  }
};

export function getZoneFromHostname(hostname: string) {
  return ZONE_CONFIG[hostname] || ZONE_CONFIG['app.dreamseedai.com'];
}

export function getCurrentZone() {
  if (typeof window === 'undefined') return null;
  return getZoneFromHostname(window.location.hostname);
}
```

**Next.js Middleware에서 Zone 감지**
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getZoneFromHostname } from '@/lib/zone-detection';

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const zone = getZoneFromHostname(hostname);
  
  // Zone 정보를 헤더에 추가
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-zone-id', zone.zoneId.toString());
  requestHeaders.set('x-zone-code', zone.zoneCode);
  requestHeaders.set('x-tenant-type', zone.tenantType);
  
  // API 호출 시 자동으로 Zone 정보 포함
  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });
  
  // Cookie에 Zone 저장 (선택적)
  response.cookies.set('zone_id', zone.zoneCode, {
    httpOnly: false,
    sameSite: 'lax',
    maxAge: 86400 // 24시간
  });
  
  return response;
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
```

**React Component에서 Zone 사용**
```tsx
// components/ZoneAwareHeader.tsx
'use client';

import { getCurrentZone } from '@/lib/zone-detection';

export function ZoneAwareHeader() {
  const zone = getCurrentZone();
  
  return (
    <header style={{ backgroundColor: zone?.primaryColor }}>
      <img src={zone?.logo} alt={zone?.zoneCode} />
      <h1>{zone?.zoneCode.toUpperCase()} Prep AI</h1>
    </header>
  );
}
```

---

### 6.2 Edge Proxy (Cloudflare Worker / Traefik)

**Cloudflare Worker로 Zone 감지 및 라우팅**

```javascript
// Cloudflare Worker: zone-router.js
const ZONE_MAP = {
  'app.univprepai.com': { zoneId: 100, backend: 'backend-univ.internal' },
  'app.skillprepai.com': { zoneId: 300, backend: 'backend-skill.internal' },
  'app.mediprepai.com': { zoneId: 400, backend: 'backend-medi.internal' },
  'app.my-ktube.ai': { zoneId: 610, backend: 'backend-kzone.internal' }
};

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const hostname = url.hostname;
  
  // Zone 감지
  const zone = ZONE_MAP[hostname] || { zoneId: 999, backend: 'backend-core.internal' };
  
  // 요청 헤더에 Zone 정보 추가
  const modifiedHeaders = new Headers(request.headers);
  modifiedHeaders.set('X-Zone-Id', zone.zoneId.toString());
  modifiedHeaders.set('X-Zone-Hostname', hostname);
  
  // Cookie에서 user_id/token 추출
  const cookies = request.headers.get('Cookie') || '';
  const tokenMatch = cookies.match(/access_token=([^;]+)/);
  const token = tokenMatch ? tokenMatch[1] : null;
  
  if (token) {
    modifiedHeaders.set('Authorization', `Bearer ${token}`);
  }
  
  // Backend로 라우팅
  const backendUrl = `https://${zone.backend}${url.pathname}${url.search}`;
  
  const modifiedRequest = new Request(backendUrl, {
    method: request.method,
    headers: modifiedHeaders,
    body: request.body,
    redirect: 'follow'
  });
  
  // Backend 호출
  const response = await fetch(modifiedRequest);
  
  // Response 헤더에 Zone 정보 추가
  const modifiedResponse = new Response(response.body, response);
  modifiedResponse.headers.set('X-Zone-Id', zone.zoneId.toString());
  
  return modifiedResponse;
}
```

### 6.2.1 Domain → Zone Header 매핑 테이블 (운영 참고)

**전체 9개 도메인 API 라우팅 매트릭스:**

| Domain | API Host | X-Zone-Id | X-Zone-Code | X-Tenant-Type | org_id Range |
|--------|----------|-----------|-------------|---------------|-------------|
| UnivPrepAI.com | api.univprepai.com | 100 | univ | academic | 1000-1999 |
| CollegePrepAI.com | api.collegeprepai.com | 200 | college | vocational | 2000-2999 |
| SkillPrepAI.com | api.skillprepai.com | 300 | skill | vocational | 3000-3999 |
| MediPrepAI.com | api.mediprepai.com | 400 | medi | medical | 4000-4999 |
| MajorPrepAI.com | api.majorprepai.com | 500 | major | academic | 5000-5999 |
| My-Ktube.com | api.my-ktube.com | 600 | ktube | k-culture | 6000-6099 |
| My-Ktube.ai | api.my-ktube.ai | 610 | ktube-ai | k-culture | 6100-6199 |
| mpcstudy.com | api.mpcstudy.com | 900 | mpc | public | 9000-9099 |
| DreamSeedAI.com | api.dreamseedai.com | 999 | core | core | 9900-9999 |

**사용 예시:**

```bash
# UnivPrep API 호출
curl -H "X-Zone-Id: 100" \
     -H "X-Zone-Code: univ" \
     -H "Authorization: Bearer <token>" \
     https://api.univprepai.com/api/v1/exams

# K-Zone AI API 호출
curl -H "X-Zone-Id: 610" \
     -H "X-Zone-Code: ktube-ai" \
     -H "Authorization: Bearer <token>" \
     https://api.my-ktube.ai/api/v1/voice/analyze
```

**API Gateway 검증 스크립트:**

```bash
#!/bin/bash
# scripts/validate_zone_routing.sh

DOMAINS=(
  "api.univprepai.com:100:univ"
  "api.skillprepai.com:300:skill"
  "api.my-ktube.ai:610:ktube-ai"
)

for entry in "${DOMAINS[@]}"; do
  IFS=":" read -r domain zone_id zone_code <<< "$entry"
  
  echo "Testing $domain..."
  
  response=$(curl -s -H "X-Zone-Id: $zone_id" \
                   -H "X-Zone-Code: $zone_code" \
                   "https://$domain/health")
  
  if echo "$response" | grep -q "ok"; then
    echo "✅ $domain: Zone routing OK"
  else
    echo "❌ $domain: Zone routing FAILED"
  fi
done
```

**Traefik Dynamic Routing (Zone-aware)**

```yaml
# traefik/dynamic/zone-routers.yml
http:
  routers:
    # UnivPrep Zone
    univ-router:
      rule: "Host(`app.univprepai.com`) || Host(`api.univprepai.com`)"
      middlewares:
        - zone-inject-univ
      service: backend-univ
    
    # SkillPrep Zone
    skill-router:
      rule: "Host(`app.skillprepai.com`) || Host(`api.skillprepai.com`)"
      middlewares:
        - zone-inject-skill
      service: backend-skill
    
    # K-Zone AI
    kzone-router:
      rule: "Host(`app.my-ktube.ai`) || Host(`api.my-ktube.ai`)"
      middlewares:
        - zone-inject-kzone
      service: backend-kzone

  middlewares:
    zone-inject-univ:
      headers:
        customRequestHeaders:
          X-Zone-Id: "100"
          X-Zone-Code: "univ"
          X-Tenant-Type: "academic"
    
    zone-inject-skill:
      headers:
        customRequestHeaders:
          X-Zone-Id: "300"
          X-Zone-Code: "skill"
          X-Tenant-Type: "vocational"
    
    zone-inject-kzone:
      headers:
        customRequestHeaders:
          X-Zone-Id: "610"
          X-Zone-Code: "ktube-ai"
          X-Tenant-Type: "k-culture"

  services:
    backend-univ:
      loadBalancer:
        servers:
          - url: "http://backend-api:8000"
    
    backend-skill:
      loadBalancer:
        servers:
          - url: "http://backend-api:8000"
    
    backend-kzone:
      loadBalancer:
        servers:
          - url: "http://kzone-ai-api:8100"
```

---

### 6.3 Backend (FastAPI) - Zone Auto-detection

**FastAPI Dependency로 Zone 자동 추출**

```python
from fastapi import Request, Depends, HTTPException
from typing import Optional

# Zone 정보 추출
async def get_zone_from_request(request: Request) -> dict:
    """Request 헤더에서 Zone 정보 추출"""
    zone_id = request.headers.get("x-zone-id")
    zone_code = request.headers.get("x-zone-code")
    tenant_type = request.headers.get("x-tenant-type")
    
    # Fallback: Host 헤더에서 추출
    if not zone_id:
        host = request.headers.get("host", "")
        zone_info = DOMAIN_ZONE_MAP.get(host)
        if zone_info:
            zone_id = zone_info["zone_id"]
            zone_code = zone_info["zone_code"]
            tenant_type = zone_info["tenant_type"]
    
    if not zone_id:
        raise HTTPException(status_code=400, detail="Zone not detected")
    
    return {
        "zone_id": int(zone_id),
        "zone_code": zone_code,
        "tenant_type": tenant_type
    }

# Multi-tenant Context
async def get_tenant_context(
    request: Request,
    zone: dict = Depends(get_zone_from_request),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Multi-tenant Context 생성"""
    
    # RLS 설정
    db.execute(f"SET app.current_org_id = {current_user['org_id']}")
    db.execute(f"SET app.current_zone_id = '{zone['zone_code']}'")
    db.execute(f"SET app.current_user_id = {current_user['id']}")
    
    return {
        "zone_id": zone["zone_id"],
        "zone_code": zone["zone_code"],
        "tenant_type": zone["tenant_type"],
        "org_id": current_user["org_id"],
        "user_id": current_user["id"],
        "user_role": current_user["role"]
    }

# API 엔드포인트에서 사용
@app.get("/api/v1/exams")
async def get_exams(
    context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Zone + org_id + role 기반 시험 목록 조회"""
    
    # 자동으로 RLS 적용됨 (org_id 필터링)
    exams = db.query(Exam).filter(
        Exam.zone_id == context["zone_code"]
    ).all()
    
    # Role 기반 추가 필터링
    if context["user_role"] == "student":
        exams = [e for e in exams if e.is_public or e.created_by == context["user_id"]]
    
    return exams
```

**Policy 자동 적용 예시**

```python
# Policy Engine
class PolicyEngine:
    @staticmethod
    def apply_zone_policy(context: dict, resource: str, action: str) -> bool:
        """Zone + org_id + role 기반 정책 적용"""
        
        # 1. Super Admin은 모든 것 허용
        if context["user_role"] == "super_admin":
            return True
        
        # 2. Zone별 특수 정책
        if context["zone_code"] == "mpc":
            # MPCStudy는 모든 콘텐츠 무료 공개
            if action == "read":
                return True
        
        # 3. Role별 정책
        if context["user_role"] == "teacher":
            if action in ["create", "update"] and resource == "exam":
                return True
        
        # 4. org_id 기반 정책 (같은 조직만 접근)
        if resource == "student" and action == "read":
            return context["user_role"] in ["teacher", "org_admin"]
        
        return False

# API에서 Policy 체크
@app.post("/api/v1/exams")
async def create_exam(
    exam: ExamCreate,
    context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """시험 생성 (Policy 자동 체크)"""
    
    # Policy 체크
    if not PolicyEngine.apply_zone_policy(context, "exam", "create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 시험 생성
    new_exam = Exam(
        title=exam.title,
        zone_id=context["zone_code"],
        org_id=context["org_id"],
        created_by=context["user_id"]
    )
    db.add(new_exam)
    db.commit()
    
    return new_exam
```

---

## 🧠 7. Multi-Zone AI 모델 선택 규칙

DreamSeedAI의 AI는 **Zone과 User locale**에 따라 서로 다른 **LLM/ASR/TTS 모델**을 선택합니다.

### 7.1 기본 규칙

| 조건 | AI 모델 | 특징 |
|------|---------|------|
| **한국어 학생** | Seoul-Medium-KR, HyperCortex-KR | 한국 교육과정 최적화 |
| **중국어 사용자** | DeepSeek-R1, Qwen2.5 | 중국어 NLP 특화 |
| **영어 사용자** | OpenAI GPT-4.2, Claude 3.5 Sonnet | 글로벌 표준 |
| **K-Culture (Z6/Z7)** | Multimodal Speech/Dance Model | 음성/영상/댄스 분석 |
| **MPCStudy.com (Z9)** | Phi-3.5, Llama-3.2-3B | 무료 모델 (경량) |
| **MediPrep (Z4)** | Claude 3.5 Sonnet (Medical) | 의료 전문 지식 |

### 7.2 AI 모델 선택 로직

```python
# AI Model Router
class AIModelRouter:
    MODEL_MAP = {
        # Zone별 기본 모델
        "univ": {
            "ko": "qwen2.5-72b-instruct",
            "en": "gpt-4o",
            "zh": "deepseek-v2.5"
        },
        "college": {
            "ko": "llama-3.1-70b",
            "en": "gpt-4o"
        },
        "skill": {
            "ko": "qwen2.5-72b-instruct",
            "en": "gpt-4o"
        },
        "medi": {
            "ko": "claude-3.5-sonnet",
            "en": "claude-3.5-sonnet"
        },
        "major": {
            "ko": "deepseek-v2.5",
            "en": "gpt-4o"
        },
        "ktube": {
            "ko": "whisper-large-v3",  # STT
            "en": "whisper-large-v3"
        },
        "ktube-ai": {
            "ko": "vllm-llama-3.1-70b",  # Multi-modal
            "en": "gpt-4o-vision"
        },
        "mpc": {
            "ko": "llama-3.2-3b",  # 무료 경량
            "en": "phi-3.5-mini"
        }
    }
    
    @classmethod
    def select_model(cls, zone_code: str, user_locale: str, task_type: str) -> str:
        """Zone + Locale + Task에 따라 AI 모델 선택"""
        
        # 1. Zone별 모델 매핑
        zone_models = cls.MODEL_MAP.get(zone_code, cls.MODEL_MAP["univ"])
        
        # 2. Locale 기반 선택
        model = zone_models.get(user_locale, zone_models.get("en"))
        
        # 3. Task별 특수 모델
        if task_type == "voice":
            model = "whisper-large-v3"
        elif task_type == "dance":
            model = "mediapipe-posenet"
        elif task_type == "video":
            model = "stable-video-diffusion"
        
        return model

# API 엔드포인트
@app.post("/api/v1/ai/completion")
async def ai_completion(
    prompt: str,
    context: dict = Depends(get_tenant_context),
    current_user: dict = Depends(get_current_user)
):
    """AI 완성 (Zone별 모델 자동 선택)"""
    
    # 모델 선택
    model = AIModelRouter.select_model(
        zone_code=context["zone_code"],
        user_locale=current_user.get("locale", "en"),
        task_type="text"
    )
    
    # vLLM 호출
    response = await vllm_client.complete(
        model=model,
        prompt=prompt,
        max_tokens=1024,
        temperature=0.7
    )
    
    # Audit Log
    log_ai_usage(
        user_id=current_user["id"],
        zone_id=context["zone_code"],
        org_id=context["org_id"],
        model=model,
        tokens=response["usage"]["total_tokens"]
    )
    
    return response
```

### 7.3 GPU / Local / Cloud 우선순위

**AI 요청 처리 우선순위**

```python
class AIInferenceRouter:
    @classmethod
    async def route_inference(cls, model: str, prompt: str, zone_code: str) -> dict:
        """AI 추론 라우팅 (GPU → Cloud)"""
        
        # 1. 로컬 GPU 서버 (vLLM, Whisper C++)
        if await cls.check_local_gpu_available(model):
            try:
                return await cls.call_local_gpu(model, prompt)
            except Exception as e:
                logger.warning(f"Local GPU failed: {e}")
        
        # 2. 클라우드 GPU 서버 (GCP/AWS)
        if await cls.check_cloud_gpu_available(model):
            try:
                return await cls.call_cloud_gpu(model, prompt)
            except Exception as e:
                logger.warning(f"Cloud GPU failed: {e}")
        
        # 3. 외부 API (OpenAI/Anthropic/Google)
        if model.startswith("gpt"):
            return await cls.call_openai(model, prompt)
        elif model.startswith("claude"):
            return await cls.call_anthropic(model, prompt)
        else:
            return await cls.call_google_ai(model, prompt)
    
    @classmethod
    async def check_local_gpu_available(cls, model: str) -> bool:
        """로컬 GPU 사용 가능 여부 확인"""
        # vLLM Health Check
        try:
            response = await http_client.get("http://localhost:8100/health")
            return response.status_code == 200
        except:
            return False
    
    @classmethod
    async def call_local_gpu(cls, model: str, prompt: str) -> dict:
        """로컬 vLLM 호출"""
        response = await http_client.post(
            "http://localhost:8100/v1/completions",
            json={
                "model": model,
                "prompt": prompt,
                "max_tokens": 1024
            }
        )
        return response.json()
```

### 7.4 Zone별 AI 특화 기능

| Zone | AI 특화 기능 | 모델 |
|------|------------|------|
| **UnivPrep** | SAT/ACT 예측, 수능 분석 | Qwen2.5-72B |
| **MediPrep** | NCLEX 문제 생성, 의료 용어 설명 | Claude 3.5 Sonnet |
| **K-Zone** | 음성 발음 분석, 댄스 동작 감지 | Whisper + MediaPipe |
| **K-Zone AI** | K-POP 가사 생성, 드라마 대본 분석 | vLLM Llama 3.1 70B |
| **SkillPrep** | 면접 답변 피드백, 자소서 첨삭 | GPT-4o |
| **MPCStudy** | 기초 수학/영어 문제 생성 | Llama 3.2 3B |

---

## 🔐 8. Multi-Zone Identity: Global DreamSeed ID

### 8.1 개념: 전 세계 단일 계정

**`user_id`는 전 세계에서 단 1개** → Zone 이동해도 계정은 1개

**예시 시나리오:**

```
John (user_id: 12345)
 ├── 2025-09-01: UnivPrepAI.com 학생 가입 (org_id: 1001)
 ├── 2025-10-15: SkillPrepAI.com 강의도 수강 (org_id: 3002)
 └── 2025-11-20: My-Ktube.com에서 K-Drama 학습 (org_id: 6001)

→ 모든 데이터가 하나의 Global Profile로 연결됩니다.
```

### 8.2 Global Identity 스키마

```sql
-- Users (Global Identity)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,                    -- Global user_id
    email VARCHAR(255) UNIQUE NOT NULL,       -- Global email
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    primary_org_id INTEGER REFERENCES organizations(id),  -- 주 소속
    primary_zone_id VARCHAR(20),              -- 주 Zone
    locale VARCHAR(10) DEFAULT 'en',          -- ko, en, zh, ja, es
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- User-Zone 연결 (Multi-zone Access)
CREATE TABLE user_zone_access (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    zone_id VARCHAR(20) NOT NULL,
    access_granted_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',      -- active, suspended
    UNIQUE(user_id, zone_id)
);

-- User-Organization 연결 (Multi-org Membership)
CREATE TABLE user_organization_memberships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    zone_id VARCHAR(20) NOT NULL,
    role VARCHAR(50) NOT NULL,                -- student, teacher, org_admin
    joined_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE(user_id, org_id)
);

-- Global User Profile
CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    bio TEXT,
    avatar_url VARCHAR(255),
    phone_encrypted VARCHAR(255),
    date_of_birth DATE,
    gender VARCHAR(20),
    country_code VARCHAR(2),
    preferences JSONB,                        -- UI/언어/알림 설정
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 8.3 Cross-zone 사용자 데이터 통합 조회

```python
@app.get("/api/v1/users/me/global-profile")
async def get_global_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Global Profile 조회 (모든 Zone 데이터 통합)"""
    
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # 1. 모든 Zone 접근 이력
    zone_access = db.query(UserZoneAccess).filter(
        UserZoneAccess.user_id == user.id
    ).all()
    
    # 2. 모든 Organization 멤버십
    memberships = db.query(UserOrganizationMembership).filter(
        UserOrganizationMembership.user_id == user.id
    ).all()
    
    # 3. Zone별 성적/활동 요약
    zone_stats = {}
    for zone in zone_access:
        stats = db.query(
            func.count(Attempt.id).label('total_attempts'),
            func.avg(Attempt.score).label('avg_score')
        ).filter(
            Attempt.user_id == user.id,
            Attempt.zone_id == zone.zone_id
        ).first()
        
        zone_stats[zone.zone_id] = {
            "total_attempts": stats.total_attempts,
            "avg_score": float(stats.avg_score) if stats.avg_score else 0
        }
    
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "primary_zone": user.primary_zone_id,
        "zones_accessed": [z.zone_id for z in zone_access],
        "memberships": [
            {
                "org_id": m.org_id,
                "zone_id": m.zone_id,
                "role": m.role
            } for m in memberships
        ],
        "zone_statistics": zone_stats
    }
```

### 8.4 Cross-zone SSO 흐름

```
1. 사용자 → app.univprepai.com/login
   ↓ 이메일/비밀번호 입력
2. FastAPI → JWT 발급 (Global Token)
   {
     "sub": "12345",
     "email": "john@example.com",
     "primary_zone": "univ",
     "zones_access": ["univ", "skill", "ktube"]
   }
   ↓
3. Cookie 저장 (domain=.dreamseedai.com)
   ↓
4. 사용자 → app.skillprepai.com/dashboard (다른 Zone)
   ↓ Cookie 자동 전달
5. FastAPI → JWT 검증 (Zone 무관)
   ↓
6. Zone 접근 권한 확인 ("skill" in zones_access)
   ↓
7. ✅ 재로그인 없이 접근 허용
```

---

## 📌 9. Multi-Zone Policy Framework

### 9.1 시험 중 AI 탐지/차단 정책 (Zone 공통)

**모든 Zone에서 동일하게 적용되는 정책**

```python
class ExamIntegrityPolicy:
    """시험 중 AI 탐지/차단 정책 (Zone 무관)"""
    
    @staticmethod
    def detect_ai_cheating(attempt_id: int, context: dict) -> bool:
        """AI 부정행위 탐지"""
        
        # 1. 응답 시간 분석 (너무 빠르면 의심)
        response_time = get_response_time(attempt_id)
        if response_time < 5:  # 5초 이내 응답
            flag_suspicious(attempt_id, "too_fast")
        
        # 2. 응답 패턴 분석 (ChatGPT 스타일 감지)
        response_text = get_response_text(attempt_id)
        if detect_gpt_pattern(response_text):
            flag_suspicious(attempt_id, "gpt_detected")
        
        # 3. Copy-Paste 감지 (Frontend 이벤트)
        if has_paste_event(attempt_id):
            flag_suspicious(attempt_id, "paste_detected")
        
        # 4. 창 전환 감지 (Tab switch)
        if has_tab_switch(attempt_id):
            flag_suspicious(attempt_id, "tab_switch")
        
        return check_flags(attempt_id)
    
    @staticmethod
    def enforce_exam_lockdown(attempt_id: int):
        """시험 Lockdown 모드 강제"""
        # Frontend에서 전체 화면 강제
        # 다른 탭/창 열기 차단
        # Copy/Paste 차단
        pass
```

### 9.2 학부모 권한 (자녀 데이터 접근) - Zone 공통

```python
class ParentAccessPolicy:
    """학부모 권한 정책 (모든 Zone 동일)"""
    
    @staticmethod
    def check_parent_access(parent_id: int, student_id: int, zone_code: str) -> bool:
        """학부모가 자녀 데이터에 접근 가능한지 확인"""
        
        # 1. Parent-Student 관계 확인
        relationship = db.query(ParentStudentRelationship).filter(
            ParentStudentRelationship.parent_id == parent_id,
            ParentStudentRelationship.student_id == student_id,
            ParentStudentRelationship.status == "approved"
        ).first()
        
        if not relationship:
            return False
        
        # 2. Zone 무관하게 모든 데이터 접근 가능
        return True
    
    @staticmethod
    def get_child_data_cross_zone(parent_id: int, student_id: int) -> dict:
        """자녀의 모든 Zone 데이터 조회"""
        
        # 관계 확인
        if not ParentAccessPolicy.check_parent_access(parent_id, student_id, None):
            raise HTTPException(status_code=403, detail="Not your child")
        
        # 모든 Zone의 Attempt 조회
        attempts = db.query(Attempt).filter(
            Attempt.user_id == student_id
        ).all()
        
        # Zone별 그룹화
        zone_data = {}
        for attempt in attempts:
            if attempt.zone_id not in zone_data:
                zone_data[attempt.zone_id] = []
            zone_data[attempt.zone_id].append({
                "exam_id": attempt.exam_id,
                "score": attempt.score,
                "finished_at": attempt.finished_at
            })
        
        return zone_data
```

### 9.3 교사-학생 관계 승인 (org_id 기반)

```python
class TeacherStudentPolicy:
    """교사-학생 관계 정책 (org_id 기반)"""
    
    @staticmethod
    def check_teacher_student_access(teacher_id: int, student_id: int, org_id: int) -> bool:
        """교사가 학생 데이터에 접근 가능한지 확인"""
        
        # 1. 같은 조직(org_id) 확인
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.org_id == org_id,
            User.role == "teacher"
        ).first()
        
        student = db.query(User).filter(
            User.id == student_id,
            User.org_id == org_id,
            User.role == "student"
        ).first()
        
        if not (teacher and student):
            return False
        
        # 2. 반(Class) 연결 확인 (선택적)
        class_membership = db.query(ClassMembership).filter(
            ClassMembership.student_id == student_id,
            ClassMembership.class_id.in_(
                db.query(Class.id).filter(Class.teacher_id == teacher_id)
            )
        ).first()
        
        return bool(class_membership)
```

### 9.4 AI Explainability Logging (Zone/Domain 무관)

```python
class AIExplainabilityPolicy:
    """AI 설명 가능성 로깅 (Central Audit)"""
    
    @staticmethod
    def log_ai_decision(
        user_id: int,
        zone_code: str,
        org_id: int,
        model: str,
        input_prompt: str,
        output_text: str,
        decision_context: dict
    ):
        """AI 결정 로깅 (Central Audit)"""
        
        audit_log = AIAuditLog(
            user_id=user_id,
            zone_id=zone_code,
            org_id=org_id,
            model_name=model,
            input_prompt=input_prompt,
            output_text=output_text,
            decision_context=decision_context,  # JSON
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_log)
        db.commit()
        
        # Elasticsearch에도 저장 (검색 가능하도록)
        es_client.index(
            index="ai-audit-logs",
            body={
                "user_id": user_id,
                "zone_id": zone_code,
                "org_id": org_id,
                "model": model,
                "prompt": input_prompt,
                "output": output_text,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# API 사용 예시
@app.post("/api/v1/ai/tutoring")
async def ai_tutoring(
    question: str,
    context: dict = Depends(get_tenant_context),
    current_user: dict = Depends(get_current_user)
):
    """AI 튜터링 (Explainability 로깅)"""
    
    # AI 호출
    model = AIModelRouter.select_model(context["zone_code"], current_user["locale"], "text")
    response = await vllm_client.complete(model=model, prompt=question)
    
    # AI 결정 로깅
    AIExplainabilityPolicy.log_ai_decision(
        user_id=current_user["id"],
        zone_code=context["zone_code"],
        org_id=context["org_id"],
        model=model,
        input_prompt=question,
        output_text=response["text"],
        decision_context={
            "temperature": 0.7,
            "max_tokens": 1024,
            "zone": context["zone_code"]
        }
    )
    
    return {"answer": response["text"]}
```

---

## ⚙️ 10. Multi-Zone Architecture 그림

```
                ┌────────────────────────────────┐
                │   DreamSeed Core City (Z999)   │
                │      dreamseedai.com           │
                │   SSO / Auth / Policy Engine   │
                └────────────┬───────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
──────────────────────────────────────────────────────────
Zone 100         Zone 200         Zone 300       Zone 400
UnivPrepAI    CollegePrepAI    SkillPrepAI    MediPrepAI
org 1000-1999  org 2000-2999   org 3000-3999  org 4000-4999
──────────────────────────────────────────────────────────
Zone 500         Zone 600        Zone 610       Zone 900
MajorPrepAI    My-Ktube.com    My-Ktube.ai    mpcstudy.com
org 5000-5999  org 6000-6099   org 6100-6199  org 9000-9099
──────────────────────────────────────────────────────────
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────┐         ┌──────────┐         ┌──────────┐
  │ Shared   │         │ Central  │         │  Redis   │
  │ AI Engine│         │ Database │         │ Cluster  │
  │ (vLLM)   │         │(PostgreSQL)│        │ (Cache)  │
  └──────────┘         └──────────┘         └──────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ API Gateway    │
                    │ (Nginx/Traefik)│
                    └────────────────┘
```

**계층 구조:**
1. **Core Layer (Z999)**: SSO, Auth, Policy Engine
2. **Zone Layer (Z100-Z900)**: 9개 독립 구역 (Domain)
3. **Tenant Layer (org_id)**: 조직/학교/학원
4. **Infrastructure Layer**: AI, DB, Redis, Gateway (모든 Zone 공유)

---

## ✔️ 11. Multi-Tenant 체크리스트

### 개발 시
```
□ 1. 항상 org_id, zone_id, user.role 체크
□ 2. DB 쿼리에서 RLS 활성화
□ 3. Redis key prefix: zone:<id>:org:<id>:...
□ 4. FastAPI dependency로 current_tenant() 사용
□ 5. Zone 감지 미들웨어 적용 (Frontend/Backend)
□ 6. AI 모델 선택 로직 구현 (Zone + Locale)
□ 7. Cross-zone SSO JWT 구조 설계
□ 8. Policy Engine 공통 정책 적용
□ 9. Audit Log 자동 기록 (AI 결정 포함)
□ 10. Unit Test (Multi-tenant 시나리오)
```

### 배포 시
```
□ 1. Zone별 도메인 DNS 설정 (9개)
□ 2. Nginx/Traefik Zone 라우팅 설정
□ 3. PostgreSQL RLS 활성화 (모든 테이블)
□ 4. Redis Cluster (Namespace 분리)
□ 5. JWT Secret 보안 설정 (환경 변수)
□ 6. Cross-zone 권한 테스트 (SSO)
□ 7. 성능 테스트 (Tenant 격리)
□ 8. Backup/복구 (Tenant별)
□ 9. 모니터링 (Tenant별 메트릭)
□ 10. 문서화 (Tenant 가이드)
```

### 운영 시
```
□ 1. Tenant 추가 프로세스 자동화
□ 2. Zone간 데이터 이관 도구
□ 3. Tenant별 리소스 모니터링
□ 4. Cross-zone 사용자 분석
□ 5. RLS 정책 검증 (월간)
□ 6. Redis 캐시 효율 분석
□ 7. AI 모델 사용량 추적 (Zone별)
□ 8. Tenant Isolation 감사
□ 9. 성능 최적화 (Partitioning)
□ 10. 보안 감사 (Cross-tenant 누출 방지)
```

---

## 🧭 12. 결론

이 문서는 **DreamSeedAI MegaCity 전체의 Zone(도메인)**과 **각 도메인 내부의 Tenant(학교/학원)** 구조를 하나로 통합한 **최상위 멀티테넌트 설계 문서**입니다.

### 핵심 설계 원칙

1. **Single Identity (Global DreamSeed ID)**
   - `user_id`는 전 세계에서 단 1개
   - Zone 이동해도 계정 유지
   - Cross-zone SSO 지원

2. **Multi-Zone Isolation (Zone별 독립)**
   - 9개 Zone = 9개 독립 도메인
   - Zone별 AI 모델 특화
   - Zone별 독립 운영 가능

3. **Multi-Tenant Security (org_id 격리)**
   - PostgreSQL RLS (Row-Level Security)
   - Redis Namespace 분리
   - Cross-tenant 데이터 누출 방지

4. **Shared Infrastructure (공유 인프라)**
   - 중앙 DB/Redis/AI Engine
   - Global API Gateway
   - Unified Policy Engine

5. **Zone-aware AI Routing**
   - Zone + Locale 기반 모델 선택
   - GPU → Cloud → API 우선순위
   - AI 사용량 추적 및 로깅

### 이 문서를 기반으로 구현할 시스템

✅ **SSO (Single Sign-On)**: Cross-zone 인증  
✅ **Multi-domain Auth**: 9개 도메인 통합 인증  
✅ **Policy Engine**: Zone 공통 정책 적용  
✅ **Service Topology**: Zone별 서비스 라우팅  
✅ **Multi-Zone AI Routing**: AI 모델 자동 선택  
✅ **Tenant Isolation**: org_id 기반 데이터 격리  
✅ **Global Identity**: 단일 계정으로 모든 Zone 접근  

---

## 📚 13. 관련 문서

### 내부 문서
- `MEGACITY_DOMAIN_ARCHITECTURE.md` - 도메인 전략 및 DNS 설정
- `MEGACITY_NETWORK_ARCHITECTURE.md` - 네트워크 아키텍처 및 보안
- `backend/API_GUIDE.md` - FastAPI Multi-tenant 구현 가이드
- `docs/RBAC_GUIDE.md` - 권한 관리 상세 가이드

### 외부 참고
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Multi-tenant Architecture Patterns](https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/multi-tenant-architecture.html)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Redis Multi-tenant Patterns](https://redis.io/docs/manual/patterns/multi-tenancy/)

---

**MEGACITY_TENANT_ARCHITECTURE v1.0 완성** 🏛️

DreamSeedAI MegaCity의 Multi-Zone / Multi-Tenant 구조가 완전히 문서화되었습니다. 이 문서를 기반으로 확장 가능하고 안전한 멀티테넌트 플랫폼을 구축하세요!