"""Enhance features_topic_daily with KPI columns

Revision ID: 20251031_2120_features_kpi_cols
Revises: 20251031_2110_attempt_view
Create Date: 2025-10-31 21:20:00

Adds KPI pipeline columns to features_topic_daily:
- hints: total hints used
- theta_sd: standard deviation of theta estimates
- rt_median: median response time (ms)
- improvement: improvement delta (accuracy gain, etc.)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "20251031_2120_features_kpi_cols"
down_revision = "20251031_2110_attempt_view"
branch_labels = None
depends_on = None


def _column_exists(conn: Connection, table: str, column: str) -> bool:
    insp = inspect(conn)
    cols = [c.get("name") for c in insp.get_columns(table)]
    return column in cols


def _table_exists(conn: Connection, name: str) -> bool:
    insp = inspect(conn)
    return insp.has_table(name)


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "features_topic_daily"):
        raise RuntimeError(
            "features_topic_daily table must exist before adding KPI columns"
        )

    # Add hints column if not exists
    if not _column_exists(conn, "features_topic_daily", "hints"):
        op.add_column(
            "features_topic_daily",
            sa.Column("hints", sa.Integer(), nullable=False, server_default="0"),
        )

    # Add theta_sd column if not exists
    if not _column_exists(conn, "features_topic_daily", "theta_sd"):
        op.add_column(
            "features_topic_daily",
            sa.Column(
                "theta_sd",
                sa.Numeric(6, 3),
                nullable=True,
                comment="Standard deviation of theta",
            ),
        )

    # Add rt_median column if not exists
    if not _column_exists(conn, "features_topic_daily", "rt_median"):
        op.add_column(
            "features_topic_daily",
            sa.Column(
                "rt_median",
                sa.Integer(),
                nullable=True,
                comment="Median response time (ms)",
            ),
        )

    # Add improvement column if not exists
    if not _column_exists(conn, "features_topic_daily", "improvement"):
        op.add_column(
            "features_topic_daily",
            sa.Column(
                "improvement",
                sa.Numeric(6, 3),
                nullable=True,
                comment="Improvement delta",
            ),
        )

    # Add comment to theta_estimate for clarity
    conn.execute(
        sa.text(
            "COMMENT ON COLUMN features_topic_daily.theta_estimate IS 'Mean theta for topic on date'"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "features_topic_daily"):
        return

    if _column_exists(conn, "features_topic_daily", "improvement"):
        op.drop_column("features_topic_daily", "improvement")

    if _column_exists(conn, "features_topic_daily", "rt_median"):
        op.drop_column("features_topic_daily", "rt_median")

    if _column_exists(conn, "features_topic_daily", "theta_sd"):
        op.drop_column("features_topic_daily", "theta_sd")

    if _column_exists(conn, "features_topic_daily", "hints"):
        op.drop_column("features_topic_daily", "hints")
