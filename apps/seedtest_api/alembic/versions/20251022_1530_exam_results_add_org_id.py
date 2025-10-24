"""add org_id to exam_results

Revision ID: 20251022_1530_exam_results_add_org_id
Revises: 20251022_0900_exam_results_userid_text
Create Date: 2025-10-22 15:30:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251022_1530_exam_results_add_org_id"
down_revision = "20251022_0900_exam_results_userid_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exam_results", sa.Column("org_id", sa.Integer(), nullable=True))
    op.create_index("ix_exam_results_org_id", "exam_results", ["org_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_exam_results_org_id", table_name="exam_results")
    op.drop_column("exam_results", "org_id")
