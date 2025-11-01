"""Create attempt VIEW from exam_results

Revision ID: 20251031_2110_attempt_view
Revises: 20251031_2100_question_table
Create Date: 2025-10-31 21:10:00

This migration creates a standardized `attempt` VIEW that maps exam_results
to a uniform schema for use by metrics/analysis code.

Standard attempt schema:
- id: BIGSERIAL (from exam_results.id cast to bigint hash)
- student_id: UUID (from exam_results.user_id)
- item_id: BIGINT (from question_id in result_json.questions array)
- correct: BOOLEAN (from is_correct or correct field)
- response_time_ms: INT (from time_spent_sec * 1000)
- hint_used: BOOLEAN (from used_hints > 0)
- attempt_no: INT (ROW_NUMBER per student+item)
- started_at: TIMESTAMPTZ (calculated from updated_at - response_time)
- completed_at: TIMESTAMPTZ (from exam_results.updated_at)
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "20251031_2110_attempt_view"
down_revision = "20251031_2100_question_table"
branch_labels = None
depends_on = None


def _view_exists(conn: Connection, view_name: str) -> bool:
    """Check if a view exists."""
    from sqlalchemy import text

    result = conn.execute(
        text(
            f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name = '{view_name}'
        )
        """
        )
    )
    return result.scalar()


def _table_exists(conn: Connection, table_name: str) -> bool:
    """Check if a table exists."""
    from sqlalchemy import text

    result = conn.execute(
        text(
            f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = '{table_name}'
        )
        """
        )
    )
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # Only create attempt VIEW if exam_results table exists
    if not _table_exists(conn, "exam_results"):
        return  # Skip if exam_results doesn't exist yet

    # Drop view if it exists (to allow idempotent re-creation)
    if _view_exists(conn, "attempt"):
        conn.execute(text("DROP VIEW IF EXISTS attempt CASCADE"))

    # Create attempt VIEW by unnesting exam_results.result_json.questions
    conn.execute(
        text(
            """
        CREATE VIEW attempt AS
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
            -- Synthetic ID: hash of exam_result_id + question array index
            ('x' || substr(md5(
                qu.exam_result_id::text || 
                COALESCE((qu.question_doc->>'question_id')::text, '0')
            ), 1, 15))::bit(60)::bigint AS id,
            
            -- Student identifier (cast user_id to UUID if needed)
            CASE
                WHEN qu.user_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN qu.user_id::uuid
                ELSE ('00000000-0000-0000-0000-' || lpad(substr(md5(qu.user_id), 1, 12), 12, '0'))::uuid
            END AS student_id,
            
            -- Item (question) ID
            COALESCE(
                (qu.question_doc->>'question_id')::bigint,
                0
            ) AS item_id,
            
            -- Correctness
            COALESCE(
                (qu.question_doc->>'is_correct')::boolean,
                (qu.question_doc->>'correct')::boolean,
                false
            ) AS correct,
            
            -- Response time in milliseconds
            COALESCE(
                ROUND((qu.question_doc->>'time_spent_sec')::numeric * 1000)::int,
                0
            ) AS response_time_ms,
            
            -- Hint usage
            COALESCE(
                (qu.question_doc->>'used_hints')::int > 0,
                false
            ) AS hint_used,
            
            -- Attempt number (ordered by completion time per student+item)
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
            qu.completed_at,
            
            -- Session reference (for joins)
            qu.session_id,
            
            -- Topic from question metadata
            qu.question_doc->>'topic' AS topic_id
            
        FROM questions_unnested qu
        WHERE (qu.question_doc->>'question_id') IS NOT NULL
        """
        )
    )

    # Create indexes on the view using materialized view pattern (optional)
    # For now, we rely on underlying table indexes
    # If performance requires, convert to MATERIALIZED VIEW and add:
    # CREATE INDEX ix_attempt_student_time ON attempt(student_id, completed_at);
    # CREATE INDEX ix_attempt_item ON attempt(item_id);


def downgrade() -> None:
    conn = op.get_bind()
    if _view_exists(conn, "attempt"):
        conn.execute(text("DROP VIEW IF EXISTS attempt CASCADE"))
