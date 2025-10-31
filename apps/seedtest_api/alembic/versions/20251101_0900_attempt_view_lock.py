"""Lock attempt VIEW spec with explicit casting and null handling

Revision ID: 20251101_0900_attempt_view_lock
Revises: 20251031_2120_features_kpi_cols
Create Date: 2025-11-01 09:00:00

This migration recreates the attempt VIEW with explicit:
- NULL handling (NULLIF for empty strings, COALESCE for defaults)
- Type casting (::bigint, ::uuid, ::int, ::boolean)
- Deterministic student_id generation (md5-based UUID if user_id not UUID)
- Response time rounding (time_spent_sec * 1000 → int)
- Attempt numbering (ROW_NUMBER partitioned by student_id + item_id)

Locks the schema for V1 analytics stability.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251101_0900_attempt_view_lock"
down_revision = "20251031_2120_features_kpi_cols"
branch_labels = None
depends_on = None


VIEW_SQL = r"""
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
"""


def _table_exists(conn, table_name: str) -> bool:
    """Check if a table exists."""
    result = conn.execute(
        text(f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = '{table_name}'
        )
        """)
    )
    return result.scalar()


def upgrade():
    conn = op.get_bind()
    
    # Only create attempt VIEW if exam_results table exists
    if not _table_exists(conn, "exam_results"):
        return  # Skip if exam_results doesn't exist yet
    
    conn.execute(text("DROP VIEW IF EXISTS attempt CASCADE;"))
    conn.execute(text(VIEW_SQL))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DROP VIEW IF EXISTS attempt;"))

