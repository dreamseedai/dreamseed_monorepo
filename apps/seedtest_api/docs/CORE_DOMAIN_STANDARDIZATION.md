# Core Domain 스키마 표준화 가이드

이 문서는 IRT 파라미터 저장, KPI/지표 파이프라인, attempt 표준 스키마에 대한 표준화 규약을 정의합니다.

## A) IRT 파라미터 저장 규약 (question.meta JSONB)

### 구조

`question.meta` JSONB 컬럼에는 다음 키 구조를 권장합니다:

```json
{
  "irt": {
    "a": 1.2,           // discrimination parameter (float)
    "b": -0.6,          // difficulty parameter (float)
    "c": 0.2,           // guessing parameter (float, nullable, 3PL만)
    "model": "3PL",     // "2PL" | "3PL" | "Rasch"
    "version": "2025-01" // 파이프라인/런 버전
  },
  "tags": ["algebra", "one-step", "linear-eq", "word-problem"]
}
```

### 데이터베이스 스키마

```sql
-- question 테이블 구조 (이미 적용됨)
CREATE TABLE question (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  difficulty NUMERIC,
  topic_id TEXT,
  meta JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- GIN 인덱스 (이미 적용됨)
CREATE INDEX ix_question_meta_gin ON question USING GIN (meta);
```

### 사용 예시

#### IRT 파라미터 저장

```sql
-- 단일 문항에 IRT 파라미터 저장
UPDATE question
SET meta = jsonb_set(
  COALESCE(meta, '{}'::jsonb),
  '{irt}',
  '{"a": 1.2, "b": -0.6, "c": 0.2, "model": "3PL", "version": "2025-01"}'::jsonb,
  true
)
WHERE id = 123;

-- 태그 추가
UPDATE question
SET meta = jsonb_set(
  COALESCE(meta, '{}'::jsonb),
  '{tags}',
  '["algebra", "one-step"]'::jsonb,
  true
)
WHERE id = 123;
```

#### IRT 파라미터 조회

```sql
-- 문항별 IRT 파라미터 조회
SELECT 
  id,
  (meta->'irt'->>'a')::float AS discrimination,
  (meta->'irt'->>'b')::float AS difficulty,
  (meta->'irt'->>'c')::float AS guessing,
  meta->'irt'->>'model' AS model,
  meta->'tags' AS tags
FROM question
WHERE id = 123;

-- 태그로 필터링
SELECT id, content
FROM question
WHERE meta @> '{"tags": ["algebra"]}';

-- 3PL 모델만 조회
SELECT id, meta->'irt' AS irt_params
FROM question
WHERE meta->'irt'->>'model' = '3PL';
```

#### Python/SQLAlchemy 사용 예시

```python
from sqlalchemy import text
from sqlalchemy.orm import Session

def update_question_irt_params(
    session: Session,
    question_id: int,
    a: float,
    b: float,
    c: float | None = None,
    model: str = "2PL",
    version: str = "2025-01"
):
    """Update IRT parameters in question.meta JSONB."""
    irt_json = {
        "a": a,
        "b": b,
        "model": model,
        "version": version
    }
    if c is not None:
        irt_json["c"] = c
    
    session.execute(
        text("""
            UPDATE question
            SET meta = jsonb_set(
                COALESCE(meta, '{}'::jsonb),
                '{irt}',
                :irt_json::jsonb,
                true
            )
            WHERE id = :question_id
        """),
        {"irt_json": json.dumps(irt_json), "question_id": question_id}
    )
    session.commit()
```

---

## B) KPI/지표 파이프라인 (features_topic_daily 백필)

### 테이블 스펙

```sql
CREATE TABLE features_topic_daily (
  user_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  date DATE NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  correct INTEGER NOT NULL DEFAULT 0,
  avg_time_ms INTEGER,
  hints INTEGER NOT NULL DEFAULT 0,
  theta_estimate NUMERIC(6, 3),
  theta_sd NUMERIC(6, 3),
  rt_median INTEGER,
  improvement NUMERIC(6, 3),
  last_seen_at TIMESTAMPTZ,
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, topic_id, date)
);

-- 인덱스
CREATE INDEX ix_ftd_user_date ON features_topic_daily (user_id, date);
CREATE INDEX ix_ftd_topic_date ON features_topic_daily (topic_id, date);
```

### Upsert 예시

```sql
-- 일별 집계 데이터 upsert
INSERT INTO features_topic_daily
  (user_id, topic_id, date, attempts, correct, avg_time_ms, hints, 
   theta_estimate, theta_sd, rt_median, improvement)
VALUES
  (:user_id, :topic_id, :date, :attempts, :correct, :avg_time_ms, :hints,
   :theta_estimate, :theta_sd, :rt_median, :improvement)
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
  last_seen_at = NOW(),
  computed_at = NOW();
```

### 파이프라인 연결

- **weekly_kpi**: Dev 계약서 2~6에서 계산한 I_t, E_t, R_t, A_t, P, S를 주차별로 저장
- **features_topic_daily**: 토픽 단위 세부 지표를 일별로 백필
  - 실행 시점: 하루 한 번 (CronJob) 또는 세션 종료 시점 (실시간)
  - 계산 소스: `attempt` VIEW에서 집계 또는 IRT theta 계산 결과

### Python/SQLAlchemy 백필 예시

```python
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session

def backfill_features_topic_daily(
    session: Session,
    user_id: str,
    topic_id: str,
    target_date: date,
    attempts: int,
    correct: int,
    avg_time_ms: int | None,
    hints: int,
    theta_estimate: float | None = None,
    theta_sd: float | None = None,
    rt_median: int | None = None,
    improvement: float | None = None
):
    """Upsert daily topic features for a user."""
    session.execute(
        text("""
            INSERT INTO features_topic_daily
              (user_id, topic_id, date, attempts, correct, avg_time_ms, hints,
               theta_estimate, theta_sd, rt_median, improvement)
            VALUES
              (:user_id, :topic_id, :date, :attempts, :correct, :avg_time_ms, :hints,
               :theta_estimate, :theta_sd, :rt_median, :improvement)
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
              last_seen_at = NOW(),
              computed_at = NOW()
        """),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "date": target_date,
            "attempts": attempts,
            "correct": correct,
            "avg_time_ms": avg_time_ms,
            "hints": hints,
            "theta_estimate": theta_estimate,
            "theta_sd": theta_sd,
            "rt_median": rt_median,
            "improvement": improvement,
        }
    )
    session.commit()
```

---

## C) session/interest_goal 활용 (Engagement/Goal 계산)

### session 테이블 활용

**Engagement (A_t) 계산 시:**

```python
# 세션 빈도, 평균 간격, dwell_seconds 합 등을 활용
SELECT 
  COUNT(*) AS session_count,
  AVG(EXTRACT(EPOCH FROM (ended_at - started_at))) AS avg_dwell_seconds,
  AVG(EXTRACT(EPOCH FROM (started_at - LAG(started_at) OVER (PARTITION BY student_id ORDER BY started_at)))) AS mean_gap_seconds
FROM session
WHERE student_id = :user_id
  AND started_at >= :start_date
  AND started_at <= :end_date
GROUP BY student_id;
```

### interest_goal 테이블 활용

**Goal Attainment Probability (P) 계산 시:**

```python
# 목표 점수/날짜 조회
SELECT 
  target_level,
  target_date,
  priority
FROM interest_goal
WHERE user_id = :user_id
  AND topic_id = :topic_id
ORDER BY updated_at DESC
LIMIT 1;
```

---

## D) attempt 표준 스키마 (VIEW/매핑)

### 표준 스키마 정의

```sql
-- attempt VIEW 표준 컬럼
CREATE VIEW attempt AS
SELECT
  id BIGSERIAL,              -- Synthetic ID (hash of exam_result_id + question_id)
  student_id UUID,           -- 학생 식별자
  item_id BIGINT,            -- 문항 ID (question_id)
  correct BOOLEAN,           -- 정답 여부
  response_time_ms INT,      -- 응답 시간 (밀리초)
  hint_used BOOLEAN,         -- 힌트 사용 여부
  attempt_no INT,            -- 시도 번호 (같은 student+item에서 순서)
  started_at TIMESTAMPTZ,    -- 시작 시각
  completed_at TIMESTAMPTZ,  -- 완료 시각
  session_id TEXT,           -- 세션 ID
  topic_id TEXT              -- 토픽 ID
FROM ...;
```

### 현재 구현 (exam_results 기반)

현재 `attempt` VIEW는 `exam_results.result_json->'questions'` 배열을 unnest하여 생성됩니다:

```sql
-- 실제 VIEW 정의 (이미 적용됨)
WITH questions_unnested AS (
  SELECT
    er.id AS exam_result_id,
    er.user_id,
    er.session_id,
    COALESCE(er.updated_at, er.created_at) AS completed_at,
    jsonb_array_elements(
      COALESCE(er.result_json->'questions', '[]'::jsonb)
    ) AS question_doc
  FROM exam_results er
)
SELECT
  -- Synthetic ID
  (('x' || substr(md5(qu.exam_result_id::text || 
                      COALESCE(qu.question_doc->>'question_id', '0')), 1, 15)))::bit(60)::bigint AS id,
  -- Student ID (UUID 변환)
  CASE
    WHEN qu.user_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    THEN qu.user_id::uuid
    ELSE ('00000000-0000-0000-0000-' || lpad(substr(md5(qu.user_id), 1, 12), 12, '0'))::uuid
  END AS student_id,
  -- Item ID
  COALESCE((qu.question_doc->>'question_id')::bigint, 0) AS item_id,
  -- Correctness
  COALESCE(
    (qu.question_doc->>'is_correct')::boolean,
    (qu.question_doc->>'correct')::boolean,
    false
  ) AS correct,
  -- Response time (milliseconds)
  COALESCE(
    ROUND((qu.question_doc->>'time_spent_sec')::numeric * 1000)::int,
    0
  ) AS response_time_ms,
  -- Hint usage
  COALESCE(
    (qu.question_doc->>'used_hints')::int > 0,
    false
  ) AS hint_used,
  -- Attempt number
  ROW_NUMBER() OVER (
    PARTITION BY qu.user_id, (qu.question_doc->>'question_id')
    ORDER BY qu.completed_at
  ) AS attempt_no,
  -- Started timestamp (approximated)
  (qu.completed_at - 
    make_interval(secs => COALESCE(
      (qu.question_doc->>'time_spent_sec')::numeric,
      0
    ))
  ) AS started_at,
  -- Completed timestamp
  qu.completed_at AS completed_at,
  -- Session reference
  qu.session_id,
  -- Topic from question metadata
  qu.question_doc->>'topic' AS topic_id
FROM questions_unnested qu
WHERE (qu.question_doc->>'question_id') IS NOT NULL;
```

### 매핑 가이드

| 표준 컬럼 | 소스 (exam_results) | 변환 로직 |
|----------|---------------------|-----------|
| `id` | Synthetic | `md5(exam_result_id || question_id)` → bigint |
| `student_id` | `user_id` (TEXT) | UUID 패턴 매칭 또는 해시 기반 UUID 생성 |
| `item_id` | `result_json->'questions'[].question_id` | `question_id::bigint` |
| `correct` | `result_json->'questions'[].is_correct` | `is_correct` 또는 `correct` 필드 |
| `response_time_ms` | `result_json->'questions'[].time_spent_sec` | `time_spent_sec * 1000` |
| `hint_used` | `result_json->'questions'[].used_hints` | `used_hints > 0` |
| `attempt_no` | 계산 | `ROW_NUMBER() OVER (PARTITION BY user_id, question_id ORDER BY completed_at)` |
| `started_at` | 계산 | `completed_at - INTERVAL 'time_spent_sec seconds'` |
| `completed_at` | `updated_at` 또는 `created_at` | `COALESCE(updated_at, created_at)` |
| `session_id` | `session_id` | 직접 매핑 |
| `topic_id` | `result_json->'questions'[].topic` | 문자열 그대로 |

### 사용 예시

```sql
-- attempt VIEW 조회
SELECT 
  student_id,
  item_id,
  correct,
  response_time_ms,
  hint_used,
  attempt_no,
  completed_at
FROM attempt
WHERE student_id = '00000000-0000-0000-0000-000000000001'::uuid
  AND completed_at >= '2025-10-01'::date
ORDER BY completed_at DESC
LIMIT 100;

-- 학생별 토픽별 집계
SELECT
  student_id,
  topic_id,
  COUNT(*) AS total_attempts,
  SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_count,
  AVG(response_time_ms) AS avg_response_time_ms,
  SUM(CASE WHEN hint_used THEN 1 ELSE 0 END) AS hints_used_count
FROM attempt
WHERE completed_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY student_id, topic_id;
```

---

## E) 테스트/운영 체크리스트

### 1. Alembic 마이그레이션 검증

```bash
# 업그레이드
cd apps/seedtest_api
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
.venv/bin/alembic upgrade head

# 다운그레이드 테스트 (선택)
.venv/bin/alembic downgrade -1
.venv/bin/alembic upgrade head
```

### 2. attempt VIEW 검증

```sql
-- VIEW 존재 확인
\dv attempt

-- 데이터 조회 테스트
SELECT COUNT(*) FROM attempt LIMIT 10;

-- 매핑 검증
SELECT 
  student_id,
  item_id,
  correct,
  response_time_ms,
  hint_used,
  attempt_no,
  started_at,
  completed_at
FROM attempt
WHERE student_id IS NOT NULL
LIMIT 10;
```

### 3. question.meta JSON 테스트

```sql
-- IRT 파라미터 저장
UPDATE question
SET meta = jsonb_set(
  COALESCE(meta, '{}'::jsonb),
  '{irt}',
  '{"a": 1.2, "b": -0.6, "c": 0.2, "model": "3PL", "version": "2025-01"}'::jsonb,
  true
)
WHERE id = 1
RETURNING id, meta;

-- IRT 파라미터 조회
SELECT 
  id,
  (meta->'irt'->>'a')::float AS a,
  (meta->'irt'->>'b')::float AS b,
  (meta->'irt'->>'c')::float AS c,
  meta->'irt'->>'model' AS model
FROM question
WHERE meta->'irt' IS NOT NULL
LIMIT 10;
```

### 4. features_topic_daily 백필 테스트

```sql
-- 테스트 데이터 upsert
INSERT INTO features_topic_daily
  (user_id, topic_id, date, attempts, correct, avg_time_ms, hints,
   theta_estimate, theta_sd, rt_median, improvement)
VALUES
  ('user_001', 'topic_algebra', '2025-10-31', 10, 7, 4500, 2, 1.2, 0.3, 4200, 0.15)
ON CONFLICT (user_id, topic_id, date)
DO UPDATE SET
  attempts = EXCLUDED.attempts,
  correct = EXCLUDED.correct,
  avg_time_ms = EXCLUDED.avg_time_ms,
  hints = EXCLUDED.hints,
  theta_estimate = EXCLUDED.theta_estimate,
  theta_sd = EXCLUDED.theta_sd,
  rt_median = EXCLUDED.rt_median,
  improvement = EXCLUDED.improvement;

-- 조회 검증
SELECT * FROM features_topic_daily
WHERE user_id = 'user_001' AND topic_id = 'topic_algebra';
```

---

## F) 개발 계약서 적용 순서

1. ✅ **Alembic 마이그레이션**: question.meta JSONB, features_topic_daily, session, interest_goal, classroom 테이블 생성 완료
2. ✅ **VIEW 생성**: attempt VIEW 생성 완료 (exam_results 기반)
3. 🔄 **서비스 통합**: metrics/analysis 서비스에서 attempt VIEW와 features_topic_daily 사용
4. ✅ **문서화**: 이 문서 작성 완료

---

## 참고 링크

- [Dev Contract 1-7](../DEV_CONTRACT_MINIMAL_SCHEMA.md)
- [Metrics Pipeline Guide](./PIPELINE_RUN_GUIDE.md)
- [IRT Implementation Report](./IRT_IMPLEMENTATION_REPORT.md)

