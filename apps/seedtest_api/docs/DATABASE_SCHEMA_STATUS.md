# 데이터베이스 스키마 상태 요약

## 📊 현재 스키마 상태

### ✅ 핵심 도메인 테이블

#### 1. `question` - 문항 테이블
**상태:** ✅ 생성 완료

**컬럼:**
- `id` BIGINT PRIMARY KEY
- `content` TEXT NOT NULL
- `difficulty` NUMERIC
- `topic_id` TEXT
- `meta` JSONB DEFAULT '{}'::jsonb (IRT 파라미터 저장)
- `created_at` TIMESTAMPTZ
- `updated_at` TIMESTAMPTZ

**인덱스:**
- `ix_question_meta_gin` (GIN 인덱스)
- `ix_question_topic_id`

**IRT 파라미터 구조:**
```json
{
  "irt": {
    "a": 1.2,           // discrimination
    "b": -0.6,          // difficulty
    "c": 0.2,           // guessing (3PL만)
    "model": "3PL",     // "2PL" | "3PL" | "Rasch"
    "version": "2025-01"
  },
  "tags": ["algebra", "one-step"]
}
```

#### 2. `classroom` - 교실/학급 관리
**상태:** ✅ 마이그레이션 준비 완료

**컬럼:**
- `id` TEXT PRIMARY KEY
- `org_id` TEXT NOT NULL
- `name` TEXT NOT NULL
- `grade` SMALLINT (nullable)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

**제약조건:**
- UNIQUE (`org_id`, `name`) - `uq_classroom_org_name`

**인덱스:**
- `ix_classroom_org` (org_id)

**마이그레이션:** `20251031_1600_minimal_schema_tables.py`

#### 3. `session` - 학습 세션 메타데이터
**상태:** ✅ 마이그레이션 준비 완료

**컬럼:**
- `id` TEXT PRIMARY KEY
- `classroom_id` TEXT (nullable, no FK)
- `exam_id` TEXT (nullable)
- `started_at` TIMESTAMPTZ (nullable)
- `ended_at` TIMESTAMPTZ (nullable)
- `status` TEXT (nullable)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

**인덱스:**
- `ix_session_classroom` (classroom_id)
- `ix_session_status_started` (status, started_at)

**마이그레이션:** `20251031_1600_minimal_schema_tables.py`

**참고:** `exam_results.session_id`와는 별도로 더 넓은 범위의 학습 세션 추적

#### 4. `interest_goal` - 학생 관심사/목표
**상태:** ✅ 마이그레이션 준비 완료

**컬럼:**
- `user_id` TEXT NOT NULL
- `topic_id` TEXT NOT NULL
- `target_level` NUMERIC(6,3) (nullable)
- `priority` SMALLINT NOT NULL DEFAULT 0
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

**Primary Key:** (`user_id`, `topic_id`)

**인덱스:**
- `ix_interest_goal_user` (user_id)
- `ix_interest_goal_topic` (topic_id)

**마이그레이션:** `20251031_1600_minimal_schema_tables.py`

#### 5. `features_topic_daily` - 일별 토픽별 피처 집계
**상태:** ✅ 마이그레이션 준비 완료

**컬럼:**
- `user_id` TEXT NOT NULL
- `topic_id` TEXT NOT NULL
- `date` DATE NOT NULL
- `attempts` INTEGER NOT NULL DEFAULT 0
- `correct` INTEGER NOT NULL DEFAULT 0
- `avg_time_ms` INTEGER (nullable)
- `theta_estimate` NUMERIC(6,3) (nullable)
- `hints` INTEGER NOT NULL DEFAULT 0 (추가됨)
- `theta_sd` NUMERIC(6,3) (nullable, 추가됨)
- `rt_median` INTEGER (nullable, 추가됨)
- `improvement` NUMERIC(6,3) (nullable, 추가됨)
- `last_seen_at` TIMESTAMPTZ (nullable)
- `computed_at` TIMESTAMPTZ NOT NULL DEFAULT now()

**Primary Key:** (`user_id`, `topic_id`, `date`)

**인덱스:**
- `ix_ftd_user_date` (user_id, date)
- `ix_ftd_topic_date` (topic_id, date)

**마이그레이션:**
- 기본 테이블: `20251031_1600_minimal_schema_tables.py`
- KPI 컬럼 추가: `20251031_2120_features_kpi_cols.py`

### ✅ 기존 테이블

#### `exam_results` - 시험 결과
**상태:** ✅ 생성 완료

**컬럼:**
- `id` UUID PRIMARY KEY
- `session_id` TEXT UNIQUE NOT NULL
- `user_id` TEXT
- `exam_id` INTEGER
- `org_id` INTEGER
- `status` TEXT NOT NULL DEFAULT 'ready'
- `result_json` JSONB NOT NULL
- `score_raw`, `score_scaled`, `standard_error`, `percentile`
- `created_at`, `updated_at` TIMESTAMPTZ

**인덱스:**
- `ix_exam_results_session_id` (UNIQUE)
- `ix_exam_results_user_exam` (user_id, exam_id)
- `ix_exam_results_org_id`
- `ix_exam_results_result_json` (GIN)

### ✅ VIEW

#### `attempt` - 표준 attempt 스키마 VIEW
**상태:** ✅ 생성 완료 (마이그레이션: `20251031_2110_attempt_view.py`)

**컬럼:**
- `id` BIGINT (Synthetic hash ID)
- `student_id` UUID
- `item_id` BIGINT
- `correct` BOOLEAN
- `response_time_ms` INT
- `hint_used` BOOLEAN
- `attempt_no` INT
- `started_at` TIMESTAMPTZ
- `completed_at` TIMESTAMPTZ
- `session_id` TEXT
- `topic_id` TEXT

**소스:** `exam_results.result_json->'questions'` 배열을 unnest하여 생성

**마이그레이션:** `20251101_0900_attempt_view_lock.py` (V1 schema lock)

## 🔄 마이그레이션 상태 확인

### Alembic 리비전 확인
```bash
cd apps/seedtest_api
export DATABASE_URL='postgresql+psycopg://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed'
.venv/bin/alembic current
.venv/bin/alembic heads
```

### 테이블 존재 확인
```sql
-- Core domain tables
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('question', 'classroom', 'session', 'interest_goal', 'features_topic_daily')
ORDER BY tablename;

-- View 확인
SELECT viewname FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname = 'attempt';
```

## 📝 데이터베이스 연결 정보

### DSN (URL 인코딩 필요)
```
postgresql+psycopg://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed
```

**특수문자 인코딩:**
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`
- `#` → `%23`

### 직접 연결 (psql)
```bash
# 방법 1: PGPASSWORD 환경 변수
PGPASSWORD="DreamSeedAi@0908" psql -h 127.0.0.1 -p 5432 -U postgres -d dreamseed

# 방법 2: 패스워드 입력 (안전)
psql -h 127.0.0.1 -p 5432 -U postgres -d dreamseed
# Password: DreamSeedAi@0908
```

## 🚀 다음 단계

### 1. 마이그레이션 적용 (아직 적용 안 된 경우)
```bash
cd apps/seedtest_api
export DATABASE_URL='postgresql+psycopg://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed'
.venv/bin/alembic upgrade head
```

### 2. 스키마 검증
```sql
-- 테이블 존재 확인
\dt classroom session interest_goal features_topic_daily question exam_results

-- VIEW 확인
\dv attempt

-- 컬럼 구조 확인
\d question
\d classroom
\d session
\d interest_goal
\d features_topic_daily
```

### 3. 데이터 테스트
```sql
-- IRT 파라미터 저장 테스트
UPDATE question
SET meta = jsonb_set(
  COALESCE(meta, '{}'::jsonb),
  '{irt}',
  '{"a": 1.2, "b": -0.6, "c": 0.2, "model": "3PL", "version": "2025-01"}'::jsonb,
  true
)
WHERE id = 1
RETURNING id, meta;

-- attempt VIEW 조회 테스트
SELECT COUNT(*) FROM attempt LIMIT 10;
```

## 📚 참고 문서

- **표준화 가이드**: `docs/CORE_DOMAIN_STANDARDIZATION.md`
- **사용 예시**: `docs/USAGE_EXAMPLES.md`
- **IRT 구현**: `docs/IRT_IMPLEMENTATION_REPORT.md`
- **Dev Contract**: `DEV_CONTRACT_MINIMAL_SCHEMA.md`

---

**마지막 업데이트:** 2025-11-01  
**마이그레이션 리비전:** `20251031_1705_core_domain_ext` → `20251101_0900_attempt_view_lock`

