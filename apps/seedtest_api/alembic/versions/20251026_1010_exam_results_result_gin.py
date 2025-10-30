"""
Optional index on exam_results.result_json for containment queries

Revision ID: 20251026_1010_exam_results_result_gin
Revises: 20251026_1000_questions_audit_cols
Create Date: 2025-10-26 10:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251026_1010_exam_results_result_gin"
down_revision = "20251026_1000_questions_audit_cols"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None
    if dialect == "postgresql":
        try:
            op.execute(sa.text("CREATE INDEX IF NOT EXISTS exam_results_result_gin ON exam_results USING GIN (result_json)"))
        except Exception:
            pass


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None
    if dialect == "postgresql":
        try:
            op.execute(sa.text("DROP INDEX IF EXISTS exam_results_result_gin"))
        except Exception:
            pass
