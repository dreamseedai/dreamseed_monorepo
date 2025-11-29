"""add helpful indexes for questions

Revision ID: 20251025_0002
Revises: 20251025_0001
Create Date: 2025-10-25

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251025_0002"
down_revision = "20251025_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_questions_updated_at", "questions", ["updated_at"])
    op.create_index("ix_questions_created_at", "questions", ["created_at"])
    op.create_index("ix_questions_topic", "questions", ["topic"])
    op.create_index("ix_questions_difficulty", "questions", ["difficulty"])
    op.create_index(
        "ix_questions_status_updated_at", "questions", ["status", "updated_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_questions_status_updated_at", table_name="questions")
    op.drop_index("ix_questions_difficulty", table_name="questions")
    op.drop_index("ix_questions_topic", table_name="questions")
    op.drop_index("ix_questions_created_at", table_name="questions")
    op.drop_index("ix_questions_updated_at", table_name="questions")
