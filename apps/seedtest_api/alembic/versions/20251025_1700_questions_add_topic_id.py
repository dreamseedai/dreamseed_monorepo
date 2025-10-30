"""
Add topic_id to questions with backfill

- Adds nullable questions.topic_id (FK -> topics.id)
- Creates index on topic_id
- Backfills topic_id from existing questions.topic by matching topics.name (org-scoped then global)

Revision ID: 20251025_1700_questions_add_topic_id
Revises: 20251025_1600_topics_table
Create Date: 2025-10-25 17:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251025_1700_questions_add_topic_id"
down_revision = "20251025_1600_topics_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    try:
        op.add_column("questions", sa.Column("topic_id", sa.BigInteger(), nullable=True))
    except Exception:
        pass

    try:
        op.create_foreign_key(
            "fk_questions_topic_id_topics",
            source_table="questions",
            referent_table="topics",
            local_cols=["topic_id"],
            remote_cols=["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    except Exception:
        pass

    try:
        op.create_index("ix_questions_topic_id", "questions", ["topic_id"], unique=False)
    except Exception:
        pass

    if dialect == "postgresql":
        # Backfill topic_id using case-insensitive name match, prefer org match then global
        try:
            op.execute(sa.text(
                """
                WITH matched_org AS (
                  SELECT q.id AS qid, t.id AS tid
                  FROM questions q
                  JOIN topics t
                    ON t.org_id = q.org_id
                   AND lower(t.name) = lower(q.topic)
                ),
                matched_global AS (
                  SELECT q.id AS qid, t.id AS tid
                  FROM questions q
                  JOIN topics t
                    ON t.org_id IS NULL
                   AND lower(t.name) = lower(q.topic)
                  LEFT JOIN matched_org mo ON mo.qid = q.id
                  WHERE mo.qid IS NULL
                )
                UPDATE questions q
                   SET topic_id = COALESCE(mo.tid, mg.tid)
                  FROM matched_org mo
                  FULL OUTER JOIN matched_global mg ON mg.qid = q.id
                 WHERE q.id = COALESCE(mo.qid, mg.qid) AND q.topic_id IS NULL
                """
            ))
        except Exception:
            pass


def downgrade():
    try:
        op.drop_index("ix_questions_topic_id", table_name="questions")
    except Exception:
        pass
    try:
        op.drop_constraint("fk_questions_topic_id_topics", "questions", type_="foreignkey")
    except Exception:
        pass
    try:
        op.drop_column("questions", "topic_id")
    except Exception:
        pass
