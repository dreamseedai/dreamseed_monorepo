"""Add optional columns to prophet_fit_meta for per-user tracking

Revision ID: 20251103_1300
Revises: 20251102_1600_prophet_meta
Create Date: 2025-11-03 13:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251103_1300"
down_revision = "20251102_1600_prophet_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optional columns to prophet_fit_meta for enhanced tracking."""
    
    # Add optional columns to prophet_fit_meta
    # These are optional because the model can be global (no user_id) or per-user
    op.add_column(
        "prophet_fit_meta",
        sa.Column("user_id", sa.Text(), nullable=True, comment="User ID if this is a per-user model (NULL for global)"),
    )
    op.add_column(
        "prophet_fit_meta",
        sa.Column("lookback_weeks", sa.Integer(), nullable=True, comment="Number of weeks used for lookback"),
    )
    op.add_column(
        "prophet_fit_meta",
        sa.Column("horizon_weeks", sa.Integer(), nullable=True, comment="Forecast horizon in weeks"),
    )
    op.add_column(
        "prophet_fit_meta",
        sa.Column("anomaly_threshold", sa.Float(), nullable=True, comment="Anomaly detection threshold used"),
    )
    
    # Create index on user_id for per-user queries
    op.create_index(
        "ix_prophet_fit_meta_user_id",
        "prophet_fit_meta",
        ["user_id"],
        unique=False,
    )
    
    # Create index on user_id + fitted_at for efficient per-user lookups
    op.create_index(
        "ix_prophet_fit_meta_user_fitted",
        "prophet_fit_meta",
        ["user_id", "fitted_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove optional columns from prophet_fit_meta."""
    op.drop_index("ix_prophet_fit_meta_user_fitted", table_name="prophet_fit_meta")
    op.drop_index("ix_prophet_fit_meta_user_id", table_name="prophet_fit_meta")
    op.drop_column("prophet_fit_meta", "anomaly_threshold")
    op.drop_column("prophet_fit_meta", "horizon_weeks")
    op.drop_column("prophet_fit_meta", "lookback_weeks")
    op.drop_column("prophet_fit_meta", "user_id")

