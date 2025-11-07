"""Create growth_glmm_meta table

Revision ID: 20251102_1100_glmm_meta
Revises: 20251101_1700_report_artifacts
Create Date: 2025-11-02 11:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251102_1100_glmm_meta"
down_revision = "20251101_1700_report_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS growth_glmm_meta (
                run_id TEXT PRIMARY KEY,
                model_spec JSONB NOT NULL DEFAULT '{}'::jsonb,
                metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
                fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS growth_glmm_meta"))
