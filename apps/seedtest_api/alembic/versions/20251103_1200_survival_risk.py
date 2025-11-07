"""Add survival_risk table for individual user risk scores

Revision ID: 20251103_1200_survival_risk
Revises: 20251102_1600_prophet_meta
Create Date: 2025-11-03 12:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251103_1200_survival_risk"
down_revision = "20251102_1600_prophet_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Check if survival_risk exists
    result = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'survival_risk'
            )
            """
        )
    )
    table_exists = result.scalar()
    
    if not table_exists:
        conn.execute(
            text(
                """
                CREATE TABLE survival_risk (
                    user_id TEXT PRIMARY KEY,
                    risk_score FLOAT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 1),
                    hazard_ratio FLOAT,
                    rank_percentile FLOAT CHECK (rank_percentile >= 0 AND rank_percentile <= 1),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_survival_risk_updated_at
                ON survival_risk (updated_at DESC)
                """
            )
        )
        
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_survival_risk_risk_score
                ON survival_risk (risk_score DESC)
                """
            )
        )
        print("[INFO] Created survival_risk table")
    else:
        print("[INFO] survival_risk table already exists, skipping")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS survival_risk"))

