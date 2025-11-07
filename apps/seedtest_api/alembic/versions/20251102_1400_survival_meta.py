"""Create survival_fit_meta table

Revision ID: 20251102_1400_survival_meta
Revises: 20251102_1100_glmm_meta
Create Date: 2025-11-02 14:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251102_1400_survival_meta"
down_revision = "20251102_1100_glmm_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Check if table exists
    result = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'survival_fit_meta'
            )
            """
        )
    )
    table_exists = result.scalar()
    
    if not table_exists:
        conn.execute(
            text(
                """
                CREATE TABLE survival_fit_meta (
                    run_id TEXT PRIMARY KEY,
                    formula TEXT NOT NULL,
                    coefficients JSONB NOT NULL DEFAULT '{}'::jsonb,
                    hazard_ratios JSONB NOT NULL DEFAULT '{}'::jsonb,
                    fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        
        # Create index on fitted_at for querying recent fits
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_survival_fit_meta_fitted_at
                ON survival_fit_meta (fitted_at DESC)
                """
            )
        )
        print("[INFO] Created survival_fit_meta table")
    else:
        print("[INFO] survival_fit_meta table already exists, skipping")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS survival_fit_meta"))

