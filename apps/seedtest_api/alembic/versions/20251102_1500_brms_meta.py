"""Create growth_brms_meta table

Revision ID: 20251102_1500_brms_meta
Revises: 20251102_1400_survival_meta
Create Date: 2025-11-02 15:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251102_1500_brms_meta"
down_revision = "20251102_1400_survival_meta"
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
                  AND table_name = 'growth_brms_meta'
            )
            """
        )
    )
    table_exists = result.scalar()

    if not table_exists:
        conn.execute(
            text(
                """
                CREATE TABLE growth_brms_meta (
                    run_id TEXT PRIMARY KEY,
                    formula TEXT NOT NULL,
                    priors JSONB NOT NULL DEFAULT '{}'::jsonb,
                    posterior_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
                    diagnostics JSONB NOT NULL DEFAULT '{}'::jsonb,
                    fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )

        # Create index on fitted_at for querying recent fits
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_growth_brms_meta_fitted_at
                ON growth_brms_meta (fitted_at DESC)
                """
            )
        )
        print("[INFO] Created growth_brms_meta table")
    else:
        print("[INFO] growth_brms_meta table already exists, skipping")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS growth_brms_meta"))
