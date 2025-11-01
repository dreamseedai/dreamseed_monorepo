# Dev Contract — 최소 스키마 미구현 테이블 추가

## Goal

현재 미구현인 테이블들(classroom, session, interest_goal, features_topic_daily)을 안전하게 추가한다. 
기존 스키마와의 충돌을 피하고, 기존 코드에 영향을 주지 않도록 설계한다.

## Change Summary

- **classroom**: 교실/학급 관리 테이블
- **session**: 학습 세션 메타데이터 테이블 (exam_results의 session_id와는 별도)
- **interest_goal**: 학생 관심사/목표 저장 테이블
- **features_topic_daily**: 일별 토픽별 피처 집계 테이블

모든 테이블은 idempotent 생성(IF NOT EXISTS) 및 downgrade 지원 포함.

## Files

- **add**: `apps/seedtest_api/alembic/versions/YYYYMMDD_HHMM_minimal_schema_tables.py`
- (optional) **add**: `apps/seedtest_api/models/classroom.py`, `models/session.py`, `models/interest_goal.py`, `models/features_topic_daily.py`

## Public Interfaces (DDL Spec)

### classroom

```
- classroom_id TEXT NOT NULL PRIMARY KEY
- name TEXT NOT NULL
- org_id INTEGER NULL (인덱스)
- teacher_id TEXT NULL
- grade_level TEXT NULL
- created_at TIMESTAMPTZ DEFAULT now()
- updated_at TIMESTAMPTZ DEFAULT now()
- metadata JSONB NULL (선택적 메타데이터)

INDEX ix_classroom_org_id ON (org_id)
INDEX ix_classroom_teacher_id ON (teacher_id)
```

### session

```
- session_id TEXT NOT NULL PRIMARY KEY (exam_results.session_id와 동일 형식)
- user_id TEXT NOT NULL (인덱스)
- classroom_id TEXT NULL (FK 없음, 참조만)
- started_at TIMESTAMPTZ NOT NULL DEFAULT now()
- ended_at TIMESTAMPTZ NULL
- session_type TEXT NULL (예: 'exam', 'practice', 'review')
- metadata JSONB NULL

INDEX ix_session_user_id ON (user_id)
INDEX ix_session_classroom_id ON (classroom_id)
INDEX ix_session_started_at ON (started_at DESC)
```

**참고**: exam_results.session_id와는 별도로, 더 넓은 범위의 학습 세션을 추적.

### interest_goal

```
- user_id TEXT NOT NULL
- topic_id TEXT NOT NULL
- interest_level NUMERIC NULL (0-1 스케일)
- goal_target NUMERIC NULL (목표 점수/능력치)
- set_at TIMESTAMPTZ NOT NULL DEFAULT now()
- updated_at TIMESTAMPTZ DEFAULT now()

PRIMARY KEY (user_id, topic_id)
INDEX ix_interest_goal_user_set_at ON (user_id, set_at DESC)
```

### features_topic_daily

```
- user_id TEXT NOT NULL
- topic_id TEXT NOT NULL
- date DATE NOT NULL
- features JSONB NOT NULL (집계된 피처들: 예: {accuracy, attempts, time_spent, ...})
- created_at TIMESTAMPTZ DEFAULT now()
- updated_at TIMESTAMPTZ DEFAULT now()

PRIMARY KEY (user_id, topic_id, date)
INDEX ix_features_topic_daily_user_date ON (user_id, date DESC)
INDEX ix_features_topic_daily_topic_date ON (topic_id, date DESC)
```

## Data Access Guidance

- 기존 코드는 `exam_results`의 `session_id`를 사용 중. `session` 테이블은 별도 추적용이며 충돌 없음.
- `classroom`은 `org_id`로 기존 `exam_results.org_id`와 연결 가능하지만 FK 없음(참조만).
- `features_topic_daily`는 메트릭스 계산의 집계 캐시로 활용 가능.

## Constraints / Non-goals

- **FK 제약 없음**: 참조 무결성은 애플리케이션 레벨에서 관리 (유연성 유지)
- **기존 테이블 변경 없음**: exam_results, questions 등 기존 스키마 영향 없음
- **선택적 채움**: 컬럼 대부분 NULL 허용 (점진적 채움 가능)

## Migration Skeleton

```python
"""Minimal schema tables: classroom, session, interest_goal, features_topic_daily

Revision ID: 20251031_1600_minimal_schema_tables
Revises: 20251030_1510_bf_metrics
Create Date: 2025-10-31 16:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "YYYYMMDD_HHMM_minimal_schema_tables"
down_revision = "<latest_revision_id>"  # 최신 마이그레이션 ID로 교체
branch_labels = None
depends_on = None


def table_exists(conn, name: str) -> bool:
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    conn = op.get_bind()
    
    # classroom
    if not table_exists(conn, "classroom"):
        op.create_table(
            "classroom",
            sa.Column("classroom_id", sa.Text(), primary_key=True, nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("teacher_id", sa.Text(), nullable=True),
            sa.Column("grade_level", sa.Text(), nullable=True),
            sa.Column("metadata", psql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_classroom_org_id", "classroom", ["org_id"])
        op.create_index("ix_classroom_teacher_id", "classroom", ["teacher_id"])
    
    # session
    if not table_exists(conn, "session"):
        op.create_table(
            "session",
            sa.Column("session_id", sa.Text(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("classroom_id", sa.Text(), nullable=True),
            sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column("session_type", sa.Text(), nullable=True),
            sa.Column("metadata", psql.JSONB(astext_type=sa.Text()), nullable=True),
        )
        op.create_index("ix_session_user_id", "session", ["user_id"])
        op.create_index("ix_session_classroom_id", "session", ["classroom_id"])
        op.create_index("ix_session_started_at", "session", ["started_at"], postgresql_ops={"started_at": "DESC"})
    
    # interest_goal
    if not table_exists(conn, "interest_goal"):
        op.create_table(
            "interest_goal",
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("topic_id", sa.Text(), nullable=False),
            sa.Column("interest_level", sa.Numeric(), nullable=True),
            sa.Column("goal_target", sa.Numeric(), nullable=True),
            sa.Column("set_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("user_id", "topic_id", name="pk_interest_goal"),
        )
        op.create_index("ix_interest_goal_user_set_at", "interest_goal", ["user_id", "set_at"], postgresql_ops={"set_at": "DESC"})
    
    # features_topic_daily
    if not table_exists(conn, "features_topic_daily"):
        op.create_table(
            "features_topic_daily",
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("topic_id", sa.Text(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("features", psql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("user_id", "topic_id", "date", name="pk_features_topic_daily"),
        )
        op.create_index("ix_features_topic_daily_user_date", "features_topic_daily", ["user_id", "date"], postgresql_ops={"date": "DESC"})
        op.create_index("ix_features_topic_daily_topic_date", "features_topic_daily", ["topic_id", "date"], postgresql_ops={"date": "DESC"})


def downgrade() -> None:
    conn = op.get_bind()
    
    if table_exists(conn, "features_topic_daily"):
        op.drop_index("ix_features_topic_daily_topic_date", table_name="features_topic_daily")
        op.drop_index("ix_features_topic_daily_user_date", table_name="features_topic_daily")
        op.drop_table("features_topic_daily")
    
    if table_exists(conn, "interest_goal"):
        op.drop_index("ix_interest_goal_user_set_at", table_name="interest_goal")
        op.drop_table("interest_goal")
    
    if table_exists(conn, "session"):
        op.drop_index("ix_session_started_at", table_name="session")
        op.drop_index("ix_session_classroom_id", table_name="session")
        op.drop_index("ix_session_user_id", table_name="session")
        op.drop_table("session")
    
    if table_exists(conn, "classroom"):
        op.drop_index("ix_classroom_teacher_id", table_name="classroom")
        op.drop_index("ix_classroom_org_id", table_name="classroom")
        op.drop_table("classroom")
```

## Tests Checklist

- [ ] alembic upgrade head 성공
- [ ] 테이블/컬럼/PK/인덱스 존재 확인
- [ ] 샘플 데이터 삽입/조회 검증
- [ ] alembic downgrade 후 테이블 삭제 확인
- [ ] 기존 코드 영향 없음 확인 (exam_results, questions 등)

## Implementation Notes

- `down_revision`은 현재 최신 마이그레이션 ID로 교체 필요 (예: `20251030_1510_metrics_backfill_tables`)
- 모든 테이블은 `table_exists` 체크로 idempotent 생성
- JSONB 컬럼은 메타데이터/피처 저장용 (확장 가능)
- 인덱스는 조회 패턴 고려 (user_id, date DESC 등)

## Hand-off to Copilot

**작업 지시**: Implement the following exactly. Do:

1. Create `apps/seedtest_api/alembic/versions/20251031_1600_minimal_schema_tables.py` with the migration above.
2. Revision ID: `20251031_1600_minimal_schema_tables` (이미 반영됨)
3. Down revision: `20251030_1510_bf_metrics` (이미 반영됨)
4. Keep DDL as specified (types, PK, indexes).
5. Add minimal comments and correct down_revision.

Do NOT:
- Change other files
- Add new dependencies
- Modify existing tables

After changes, show a compact diff per file.

