"""
Add created_by and updated_by columns to questions

- columns: created_by TEXT NULL, updated_by TEXT NULL
- optional backfill: created_by from author when present

Revision ID: 20251026_1000_questions_audit_cols
Revises: 20251025_1700_questions_add_topic_id
Create Date: 2025-10-26 10:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251026_1000_questions_audit_cols"
down_revision = "20251025_1700_questions_add_topic_id"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column("questions", sa.Column("created_by", sa.Text(), nullable=True))
    except Exception:
        pass
    try:
        op.add_column("questions", sa.Column("updated_by", sa.Text(), nullable=True))
    except Exception:
        pass
    # Create indexes to help audit queries
    try:
        op.create_index("ix_questions_created_by", "questions", ["created_by"], unique=False)
    except Exception:
        pass
    try:
        op.create_index("ix_questions_updated_by", "questions", ["updated_by"], unique=False)
    except Exception:
        pass
    # Optional backfill created_by from author where present
    try:
        op.execute(sa.text("""
            UPDATE questions
               SET created_by = COALESCE(created_by, author)
        """))
    except Exception:
        pass


def downgrade():
    try:
        op.drop_index("ix_questions_updated_by", table_name="questions")
    except Exception:
        pass
    try:
        op.drop_index("ix_questions_created_by", table_name="questions")
    except Exception:
        pass
    try:
        op.drop_column("questions", "updated_by")
    except Exception:
        pass
    try:
        op.drop_column("questions", "created_by")
    except Exception:
        pass
