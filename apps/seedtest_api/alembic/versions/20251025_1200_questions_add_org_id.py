"""add org_id to questions

Revision ID: 20251025_1200_questions_add_org_id
Revises: 20251023_1100_exam_results_gin_index
Create Date: 2025-10-25 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251025_1200_questions_add_org_id"
down_revision = "20251023_1100_exam_results_gin_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.add_column("questions", sa.Column("org_id", sa.Integer(), nullable=True))
    except Exception:
        # If the column already exists (idempotence in some envs), ignore
        pass
    try:
        op.create_index("ix_questions_org_id", "questions", ["org_id"], unique=False)
    except Exception:
        # Index may already exist
        pass


def downgrade() -> None:
    try:
        op.drop_index("ix_questions_org_id", table_name="questions")
    except Exception:
        pass
    try:
        op.drop_column("questions", "org_id")
    except Exception:
        pass
