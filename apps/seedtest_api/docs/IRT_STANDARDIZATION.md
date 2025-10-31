# IRT 표준화 및 KPI 파이프라인 통합 가이드

## 개요

이 문서는 IRT(Item Response Theory) 파라미터 저장, attempt 표준 스키마, KPI 파이프라인 통합을 위한 데이터베이스 스키마 및 사용 가이드입니다.

## 구현 완료 항목

### 1. Question 테이블 + IRT 파라미터 (meta JSONB)

**테이블 구조:**
```sql
CREATE TABLE question (
    id BIGINT PRIMARY KEY,
    content TEXT NOT NULL,
    difficulty NUMERIC,
    topic_id TEXT,
    meta JSONB DEFAULT '{}'::jsonb,  -- IRT 파라미터 및 태그
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_question_meta_gin ON question USING GIN (meta);
CREATE INDEX ix_question_topic_id ON question(topic_id);
```

**meta JSONB 구조:**
```json
{
  "irt": {
    "a": 1.2,        // discrimination (2PL/3PL)
    "b": -0.6,       // difficulty
    "c": 0.2,        // guessing (3PL only, null for 2PL/Rasch)
    "model": "3PL",  // "Rasch" | "2PL" | "3PL"
    "version": "2025-01"  // calibration version
  },
  "tags": ["algebra", "one-step", "linear-eq"]
}
```

**사용 예시:**
```python
# Python (SQLAlchemy)
from models import Question

question = Question(
    id=1001,
    content="Solve for x: 2x + 5 = 13",
    difficulty=0.5,
    topic_id="algebra",
    meta={
        "irt": {
            "a": 1.2,
            "b": -0.6,
            "c": 0.2,
            "model": "3PL",
            "version": "2025-01"
        },
        "tags": ["algebra", "one-step", "linear-eq"]
    }
)
db.add(question)
db.commit()
```

```sql
-- SQL 직접 쿼리
-- IRT 파라미터 추출
SELECT 
    id,
    (meta->'irt'->>'a')::float AS discrimination,
    (meta->'irt'->>'b')::float AS difficulty,
    (meta->'irt'->>'c')::float AS guessing,
    meta->'irt'->>'model' AS model
FROM question
WHERE id = 1001;

-- 태그 기반 검색 (GIN 인덱스 사용)
SELECT id, content, topic_id
FROM question
WHERE meta @> '{"tags": ["algebra"]}'::jsonb;
```

---

### 2. Attempt VIEW (표준 스키마) - 🔒 V1 Spec Locked

**목적:** `exam_results` 테이블을 표준화된 attempt 스키마로 매핑하여 분석 코드의 일관성 확보.

**현재 상태:** ✅ **V1 스키마 고정 완료 (2025-11-01)**
- 명시적 타입 캐스팅 (`::bigint`, `::uuid`, `::boolean`, `::int`)
- NULL 처리 표준화 (`NULLIF`, `COALESCE`)
- `student_id` 결정론적 생성 (MD5 기반 UUID)
- `attempt_no` 순서 보장 (`ROW_NUMBER` + `PARTITION BY`)

**VIEW 정의 (20251101_0900_attempt_view_lock):**
```sql
CREATE OR REPLACE VIEW attempt AS
WITH q AS (
  SELECT
    er.id                  AS exam_result_id,
    er.user_id             AS user_id_text,
    er.session_id          AS session_id,
    COALESCE(er.updated_at, er.created_at) AS completed_at,
    jsonb_array_elements(er.result_json->'questions') AS qelem
  FROM exam_results er
)
SELECT
  -- Deterministic id: hash of exam_result_id + question_id
  (('x' || substr(md5(q.exam_result_id::text || '-' || (q.qelem->>'question_id')), 1, 16))::bit(64)::bigint) AS id,

  -- student_id: cast user_id if UUID format, else generate deterministic UUID from md5
  (
    CASE
      WHEN q.user_id_text ~* '^[0-9a-fA-F-]{36}$' THEN q.user_id_text::uuid
      ELSE (
        substr(md5(q.user_id_text),1,8) || '-' ||
        substr(md5(q.user_id_text),9,4) || '-' ||
        substr(md5(q.user_id_text),13,4) || '-' ||
        substr(md5(q.user_id_text),17,4) || '-' ||
        substr(md5(q.user_id_text),21,12)
      )::uuid
    END
  ) AS student_id,

  -- item_id: question identifier (NULL if empty)
  NULLIF(q.qelem->>'question_id','')::bigint AS item_id,

  -- correct: is_correct or correct field, default FALSE
  COALESCE(
    (q.qelem->>'is_correct')::boolean,
    (q.qelem->>'correct')::boolean,
    FALSE
  ) AS correct,

  -- response_time_ms: time_spent_sec * 1000, rounded to int, default 0
  COALESCE(
    ROUND((NULLIF(q.qelem->>'time_spent_sec','')::numeric) * 1000.0)::int,
    0
  ) AS response_time_ms,

  -- hint_used: used_hints > 0
  COALESCE((q.qelem->>'used_hints')::int, 0) > 0 AS hint_used,

  -- completed_at: from exam_results.updated_at or created_at
  q.completed_at AS completed_at,

  -- started_at: completed_at - response_time_ms
  (q.completed_at - make_interval(secs => COALESCE(ROUND((NULLIF(q.qelem->>'time_spent_sec','')::numeric))::int, 0))) AS started_at,

  -- attempt_no: ROW_NUMBER partitioned by student_id + item_id, ordered by completed_at
  ROW_NUMBER() OVER (
    PARTITION BY
      (
        CASE
          WHEN q.user_id_text ~* '^[0-9a-fA-F-]{36}$' THEN q.user_id_text::uuid
          ELSE (
            substr(md5(q.user_id_text),1,8) || '-' ||
            substr(md5(q.user_id_text),9,4) || '-' ||
            substr(md5(q.user_id_text),13,4) || '-' ||
            substr(md5(q.user_id_text),17,4) || '-' ||
            substr(md5(q.user_id_text),21,12)
          )::uuid
        END
      ),
      NULLIF(q.qelem->>'question_id','')::bigint
    ORDER BY q.completed_at ASC, q.exam_result_id ASC
  )::int AS attempt_no,

  -- session_id: for joins
  q.session_id AS session_id,

  -- topic_id: from questions array
  NULLIF(q.qelem->>'topic','')::text AS topic_id

FROM q
WHERE NULLIF(q.qelem->>'question_id','') IS NOT NULL;
```

**스키마 안정성 보장:**
- ✅ **타입 고정:** `id` (bigint), `student_id` (uuid), `correct` (boolean), `response_time_ms` (integer) 등
- ✅ **NULL 방지:** 모든 NOT NULL 컬럼은 `COALESCE` 기본값 제공
- ✅ **결정론적 ID:** 동일 `user_id` → 동일 `student_id` (멱등성 보장)
- ✅ **순서 보장:** `attempt_no`는 `(completed_at ASC, exam_result_id ASC)` 정렬로 일관성 유지

**Breaking Change 방지:**
- ❌ 컬럼명 변경 금지 (e.g., `response_time_ms` → `response_time`)
- ❌ 타입 변경 금지 (e.g., `bigint` → `integer`)
- ❌ `student_id` 해시 알고리즘 변경 금지
- ❌ `attempt_no` 정렬 로직 변경 금지

**표준 attempt 스키마:**

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `id` | BIGINT | 고유 ID (synthetic) |
| `student_id` | UUID | 학생 식별자 |
| `item_id` | BIGINT | 문항 ID |
| `correct` | BOOLEAN | 정답 여부 |
| `response_time_ms` | INT | 응답 시간 (밀리초) |
| `hint_used` | BOOLEAN | 힌트 사용 여부 |
| `attempt_no` | INT | 해당 문항의 N번째 시도 |
| `started_at` | TIMESTAMPTZ | 시작 시각 |
| `completed_at` | TIMESTAMPTZ | 완료 시각 |
| `session_id` | TEXT | 세션 ID |
| `topic_id` | TEXT | 주제/토픽 ID |

**사용 예시:**
```python
# Python (SQLAlchemy)
from sqlalchemy import text

# Attempt VIEW에서 최근 시도 조회
result = session.execute(
    text("""
        SELECT 
            student_id,
            item_id,
            correct,
            response_time_ms,
            topic_id
        FROM attempt
        WHERE student_id = :student_id
        ORDER BY completed_at DESC
        LIMIT 10
    """),
    {"student_id": "00000000-0000-0000-0000-958e2b33e695"}
)
```

```sql
-- SQL: 주제별 정답률 집계
SELECT 
    topic_id,
    COUNT(*) AS total_attempts,
    SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_count,
    ROUND(AVG(response_time_ms)) AS avg_response_time_ms
FROM attempt
WHERE topic_id IS NOT NULL
GROUP BY topic_id;
```

---

### 3. Features_topic_daily (KPI 파이프라인)

**확장된 테이블 구조:**
```sql
CREATE TABLE features_topic_daily (
    user_id TEXT,
    topic_id TEXT,
    date DATE,
    
    -- Core metrics
    attempts INT DEFAULT 0,
    correct INT DEFAULT 0,
    avg_time_ms INT,
    hints INT DEFAULT 0,
    
    -- IRT metrics
    theta_estimate NUMERIC(6,3),  -- Mean theta for topic on date
    theta_sd NUMERIC(6,3),         -- Standard deviation of theta
    
    -- Additional KPI metrics
    rt_median INT,                 -- Median response time (ms)
    improvement NUMERIC(6,3),      -- Improvement delta (accuracy gain, etc.)
    
    -- Metadata
    last_seen_at TIMESTAMPTZ,
    computed_at TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (user_id, topic_id, date)
);
```

**KPI 컬럼 설명:**

| 컬럼명 | 타입 | Dev Contract 매핑 | 설명 |
|--------|------|-------------------|------|
| `attempts` | INT | A_t | 해당 날짜의 총 시도 횟수 |
| `correct` | INT | - | 정답 개수 (accuracy 계산용) |
| `avg_time_ms` | INT | R_t | 평균 응답 시간 (밀리초) |
| `hints` | INT | - | 힌트 사용 횟수 |
| `theta_estimate` | NUMERIC | P (ability) | IRT 능력 추정치 (평균) |
| `theta_sd` | NUMERIC | S (uncertainty) | IRT 능력 추정치 표준편차 |
| `rt_median` | INT | R_t (median) | 응답 시간 중앙값 |
| `improvement` | NUMERIC | I_t | 이전 기간 대비 개선도 (정답률 증가 등) |

**Upsert 패턴 (Idempotent):**
```python
# Python
from models import FeaturesTopicDaily
from datetime import date
from decimal import Decimal

feature = FeaturesTopicDaily(
    user_id="student_001",
    topic_id="algebra",
    date=date(2025, 10, 31),
    attempts=20,
    correct=15,
    avg_time_ms=5200,
    hints=3,
    theta_estimate=Decimal("1.45"),
    theta_sd=Decimal("0.30"),
    rt_median=5000,
    improvement=Decimal("0.12"),
)
session.merge(feature)  # Upsert
session.commit()
```

```sql
-- SQL Upsert
INSERT INTO features_topic_daily (
    user_id, topic_id, date,
    attempts, correct, avg_time_ms, hints,
    theta_estimate, theta_sd, rt_median, improvement
)
VALUES (
    'student_001', 'algebra', '2025-10-31',
    20, 15, 5200, 3,
    1.45, 0.30, 5000, 0.12
)
ON CONFLICT (user_id, topic_id, date)
DO UPDATE SET
    attempts = EXCLUDED.attempts,
    correct = EXCLUDED.correct,
    avg_time_ms = EXCLUDED.avg_time_ms,
    hints = EXCLUDED.hints,
    theta_estimate = EXCLUDED.theta_estimate,
    theta_sd = EXCLUDED.theta_sd,
    rt_median = EXCLUDED.rt_median,
    improvement = EXCLUDED.improvement,
    computed_at = now();
```

---

## 데이터 파이프라인 흐름

```
[Student attempts] 
    → exam_results (raw JSON storage)
    → attempt VIEW (standardized schema)
    → Daily Aggregation Job
    → features_topic_daily (KPI metrics)
    → weekly_kpi (week-level rollup)
```

### Backfill 예시 (attempt → features_topic_daily)

```sql
-- 일일 집계: attempt VIEW에서 features_topic_daily로 백필
INSERT INTO features_topic_daily (
    user_id, topic_id, date,
    attempts, correct, avg_time_ms, hints, rt_median
)
SELECT 
    student_id::text AS user_id,
    topic_id,
    DATE(completed_at) AS date,
    COUNT(*) AS attempts,
    SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct,
    ROUND(AVG(response_time_ms))::int AS avg_time_ms,
    SUM(CASE WHEN hint_used THEN 1 ELSE 0 END) AS hints,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms)::int AS rt_median
FROM attempt
WHERE completed_at >= '2025-10-01'
  AND topic_id IS NOT NULL
GROUP BY student_id, topic_id, DATE(completed_at)
ON CONFLICT (user_id, topic_id, date)
DO UPDATE SET
    attempts = EXCLUDED.attempts,
    correct = EXCLUDED.correct,
    avg_time_ms = EXCLUDED.avg_time_ms,
    hints = EXCLUDED.hints,
    rt_median = EXCLUDED.rt_median,
    computed_at = now();
```

---

## 마이그레이션 적용 방법

### 순서:
1. `20251031_2100_question_table` - question 테이블 + meta JSONB
2. `20251031_2110_attempt_view` - attempt VIEW 생성 (초기 버전)
3. `20251031_2120_features_kpi_cols` - features_topic_daily KPI 컬럼 추가
4. **`20251101_0900_attempt_view_lock`** - 🔒 **attempt VIEW V1 스키마 고정 (명시적 캐스팅 + NULL 처리)**

### 실행:
```bash
cd apps/seedtest_api
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
.venv/bin/alembic upgrade head
```

### 확인:
```bash
# 테이블 확인
psql $DATABASE_URL -c "\d question"
psql $DATABASE_URL -c "\d+ attempt"
psql $DATABASE_URL -c "\d features_topic_daily"

# 샘플 데이터 확인
psql $DATABASE_URL -c "SELECT COUNT(*) FROM attempt;"

# Smoke 테스트 (attempt VIEW 스키마 검증)
pytest tests/test_attempt_view_smoke.py -v
```

---

## 테스트

### 통합 테스트 실행:
```bash
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/dreamseed"
.venv/bin/pytest tests/test_irt_standardization.py -v
```

### Attempt VIEW Smoke 테스트:
```bash
# 스키마 고정 검증 (20251101_0900 마이그레이션 후 실행)
pytest tests/test_attempt_view_smoke.py -v
```

**Smoke 테스트 커버리지:**
- ✅ `test_attempt_view_columns_exist`: 11개 필수 컬럼 존재 확인
- ✅ `test_attempt_view_select_minimal`: 기본 SELECT 쿼리 오류 없음
- ✅ `test_attempt_view_types`: PostgreSQL 타입 정합성 검증 (bigint, uuid, boolean, integer, timestamptz, text)
- ✅ `test_attempt_view_student_id_determinism`: 동일 user_id → 동일 student_id (멱등성)
- ✅ `test_attempt_view_no_nulls_in_required_fields`: NOT NULL 보장 확인 (id, student_id, item_id, correct, response_time_ms, hint_used, completed_at, attempt_no)

### IRT 통합 테스트 커버리지:
- ✅ Question.meta JSONB 삽입 및 IRT 파라미터 쿼리
- ✅ Attempt VIEW 매핑 검증
- ✅ Attempt VIEW 집계 쿼리
- ✅ Features_topic_daily 전체 KPI 컬럼 저장
- ✅ Features_topic_daily Upsert 멱등성
- ✅ Question.meta GIN 인덱스 태그 검색

---

## 다음 단계 (Future Work)

### 1. Backfill 자동화
- Airflow/Prefect DAG 작성
- Daily job: attempt → features_topic_daily
- Weekly job: features_topic_daily → weekly_kpi

### 2. IRT 캘리브레이션 파이프라인
- Python 스크립트: 새로운 문항에 대해 IRT 파라미터 추정
- 결과를 question.meta에 자동 업데이트

### 3. Engagement (A_t) 계산 확장
- session 테이블 연동 (user_id/org_id 활용)
- interest_goal 연동 (목표 기반 가중치)

### 4. P(goal|state) 베이지안 모델
- interest_goal.target_score/target_date 기반
- 시계열 예측 모델 통합

### 5. 실시간 업데이트
- Exam 세션 종료 시 자동으로 features_topic_daily 업데이트
- Streaming pipeline (Kafka/Kinesis) 검토

---

## 참고 자료

- **Alembic 마이그레이션:** `apps/seedtest_api/alembic/versions/20251031_21*.py`
- **모델 정의:** `apps/seedtest_api/models/question.py`, `features_topic_daily.py`
- **통합 테스트:** `apps/seedtest_api/tests/test_irt_standardization.py`
- **Dev Contract:** 프로젝트 루트의 개발 계약서 문서 참조

---

## 문의 및 기여

문제 발생 시:
1. Alembic 버전 확인: `alembic current`
2. 테스트 실행: `pytest tests/test_irt_standardization.py -v`
3. 로그 확인: Alembic 마이그레이션 로그, PostgreSQL 로그

---

*Last Updated: 2025-10-31*  
*Revisions: 20251031_2100, 20251031_2110, 20251031_2120*
