# Core Domain 사용 예시

이 문서는 표준화된 스키마(question.meta, features_topic_daily, attempt VIEW)의 실제 사용 예시를 제공합니다.

## 1. IRT 파라미터 저장/조회

### Python 코드 예시

```python
from apps.seedtest_api.services.question_meta import (
    update_irt_params,
    get_irt_params,
    add_tags,
    list_questions_by_tags,
)
from apps.seedtest_api.db import get_session

# IRT 파라미터 저장
with get_session() as session:
    update_irt_params(
        session,
        question_id=123,
        a=1.2,
        b=-0.6,
        c=0.2,
        model="3PL",
        version="2025-01",
    )
    
    # 태그 추가
    add_tags(session, question_id=123, tags=["algebra", "one-step"])
    
    # IRT 파라미터 조회
    irt = get_irt_params(session, question_id=123)
    print(f"IRT params: {irt}")
    # Output: {'a': 1.2, 'b': -0.6, 'c': 0.2, 'model': '3PL', 'version': '2025-01'}
    
    # 태그로 필터링
    question_ids = list_questions_by_tags(session, tags=["algebra"])
    print(f"Algebra questions: {question_ids}")
```

### SQL 직접 사용

```sql
-- IRT 파라미터 저장
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

-- 조회
SELECT 
  id,
  (meta->'irt'->>'a')::float AS discrimination,
  (meta->'irt'->>'b')::float AS difficulty,
  meta->'tags' AS tags
FROM question
WHERE id = 123;
```

---

## 2. features_topic_daily 백필

### Python 코드 예시

```python
from datetime import date
from apps.seedtest_api.services.features_backfill import (
    backfill_features_topic_daily,
    backfill_user_topic_range,
)
from apps.seedtest_api.db import get_session

# 단일 날짜 백필
with get_session() as session:
    backfill_features_topic_daily(
        session,
        user_id="user_001",
        topic_id="topic_algebra",
        target_date=date(2025, 10, 31),
        attempts=10,
        correct=7,
        avg_time_ms=4500,
        hints=2,
        theta_estimate=1.2,
        theta_sd=0.3,
        rt_median=4200,
        improvement=0.15,
    )

# 자동 계산 백필 (attempt VIEW에서 집계)
with get_session() as session:
    backfill_features_topic_daily(
        session,
        user_id="user_001",
        topic_id="topic_algebra",
        target_date=date(2025, 10, 31),
        # attempts, correct, avg_time_ms, hints는 자동 계산됨
        theta_estimate=1.2,  # IRT theta는 별도 제공
        improvement=0.15,    # 계산된 improvement
    )

# 날짜 범위 백필
with get_session() as session:
    count = backfill_user_topic_range(
        session,
        user_id="user_001",
        topic_id="topic_algebra",
        start_date=date(2025, 10, 1),
        end_date=date(2025, 10, 31),
        include_theta=True,  # IRT theta 자동 로드
    )
    print(f"Backfilled {count} days")
```

### SQL 직접 사용

```sql
-- Upsert
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

-- 조회
SELECT *
FROM features_topic_daily
WHERE user_id = 'user_001'
  AND topic_id = 'topic_algebra'
  AND date >= '2025-10-01'
ORDER BY date DESC;
```

---

## 3. attempt VIEW 사용

### Python 코드 예시

```python
from sqlalchemy import text
from apps.seedtest_api.db import get_session

# attempt VIEW 조회
with get_session() as session:
    result = session.execute(
        text("""
            SELECT 
              student_id,
              item_id,
              correct,
              response_time_ms,
              hint_used,
              attempt_no,
              completed_at
            FROM attempt
            WHERE student_id::text = :user_id
              AND completed_at >= :start_date
            ORDER BY completed_at DESC
            LIMIT 100
        """),
        {
            "user_id": "user_001",
            "start_date": "2025-10-01",
        }
    )
    
    for row in result:
        print(f"Item {row.item_id}: {'✓' if row.correct else '✗'} "
              f"(time: {row.response_time_ms}ms, attempt #{row.attempt_no})")

# 집계 쿼리
with get_session() as session:
    result = session.execute(
        text("""
            SELECT
              student_id,
              topic_id,
              COUNT(*) AS total_attempts,
              SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_count,
              AVG(response_time_ms) AS avg_response_time_ms,
              SUM(CASE WHEN hint_used THEN 1 ELSE 0 END) AS hints_used_count
            FROM attempt
            WHERE completed_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY student_id, topic_id
            ORDER BY total_attempts DESC
        """)
    )
    
    for row in result:
        accuracy = row.correct_count / row.total_attempts if row.total_attempts > 0 else 0
        print(f"Student {row.student_id}, Topic {row.topic_id}: "
              f"{accuracy:.1%} accuracy ({row.correct_count}/{row.total_attempts})")
```

### SQL 직접 사용

```sql
-- 기본 조회
SELECT 
  student_id,
  item_id,
  correct,
  response_time_ms,
  hint_used,
  attempt_no,
  completed_at
FROM attempt
WHERE student_id::text = 'user_001'
  AND completed_at >= '2025-10-01'
ORDER BY completed_at DESC
LIMIT 100;

-- 학생별 토픽별 집계
SELECT
  student_id,
  topic_id,
  COUNT(*) AS total_attempts,
  SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_count,
  AVG(response_time_ms) AS avg_response_time_ms,
  SUM(CASE WHEN hint_used THEN 1 ELSE 0 END) AS hints_used_count,
  MIN(completed_at) AS first_attempt,
  MAX(completed_at) AS last_attempt
FROM attempt
WHERE completed_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY student_id, topic_id
ORDER BY total_attempts DESC;
```

---

## 4. 통합 예시: 일별 집계 파이프라인

```python
from datetime import date, timedelta
from apps.seedtest_api.services.features_backfill import backfill_user_topic_range
from apps.seedtest_api.db import get_session

def daily_backfill_pipeline(user_id: str, topic_id: str, days: int = 7):
    """일별 집계 파이프라인 실행."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    with get_session() as session:
        count = backfill_user_topic_range(
            session,
            user_id,
            topic_id,
            start_date,
            end_date,
            include_theta=True,  # IRT theta 포함
        )
        print(f"Backfilled {count} days for user {user_id}, topic {topic_id}")

# 실행
daily_backfill_pipeline("user_001", "topic_algebra", days=30)
```

---

## 5. 메트릭 계산 연계

```python
from apps.seedtest_api.services.metrics import (
    compute_improvement_index,
    compute_engagement,
    calculate_and_store_weekly_kpi,
)
from apps.seedtest_api.db import get_session
from datetime import date

# 주차별 KPI 계산 (Dev Contract 2-6)
with get_session() as session:
    week_start = date(2025, 10, 28)  # ISO 주간 월요일
    
    kpi_result = calculate_and_store_weekly_kpi(
        session,
        user_id="user_001",
        week_start=week_start,
    )
    
    print(f"Weekly KPIs for {week_start}:")
    print(f"  I_t (Improvement): {kpi_result['kpis']['I_t']}")
    print(f"  E_t (Efficiency): {kpi_result['kpis']['E_t']}")
    print(f"  R_t (Recovery): {kpi_result['kpis']['R_t']}")
    print(f"  A_t (Engagement): {kpi_result['kpis']['A_t']}")
    print(f"  P (Goal Probability): {kpi_result['kpis']['P']}")
    print(f"  S (Churn Risk): {kpi_result['kpis']['S']}")

# 이후 features_topic_daily 백필로 토픽별 세부 지표 저장
```

---

## 6. IRT 파라미터 배치 업데이트

```python
from apps.seedtest_api.services.question_meta import update_irt_params
from apps.seedtest_api.db import get_session
from sqlalchemy import text

def batch_update_irt_from_mirt_item_params():
    """mirt_item_params 테이블의 파라미터를 question.meta에 반영."""
    with get_session() as session:
        # mirt_item_params에서 IRT 파라미터 조회
        result = session.execute(
            text("""
                SELECT 
                  item_id,
                  params->>'a' AS a,
                  params->>'b' AS b,
                  params->>'c' AS c,
                  model,
                  version
                FROM mirt_item_params
                WHERE params IS NOT NULL
            """)
        )
        
        for row in result:
            try:
                update_irt_params(
                    session,
                    question_id=row.item_id,
                    a=float(row.a) if row.a else None,
                    b=float(row.b) if row.b else None,
                    c=float(row.c) if row.c else None,
                    model=row.model or "2PL",
                    version=row.version,
                )
                print(f"Updated IRT params for question {row.item_id}")
            except Exception as e:
                print(f"Error updating question {row.item_id}: {e}")

# 실행
batch_update_irt_from_mirt_item_params()
```

---

## 참고

- [Core Domain 표준화 가이드](./CORE_DOMAIN_STANDARDIZATION.md)
- [Metrics Pipeline 가이드](./PIPELINE_RUN_GUIDE.md)

