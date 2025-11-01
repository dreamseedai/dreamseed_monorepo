"""Backfill metrics tables if missing (weekly_kpi, student_topic_theta)

Revision ID: 20251030_1510_bf_metrics
Revises: 20251030_1500_irt_tables
Create Date: 2025-10-30 15:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "20251030_1510_bf_metrics"
down_revision = "20251030_1500_irt_tables"
branch_labels = None
depends_on = None


def _has_table(conn, name: str) -> bool:
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    conn = op.get_bind()

    if not _has_table(conn, "weekly_kpi"):
        op.create_table(
            "weekly_kpi",
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("week_start", sa.Date(), nullable=False),
            sa.Column("kpis", psql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("user_id", "week_start", name="pk_weekly_kpi"),
        )
        op.create_index("ix_weekly_kpi_user_date", "weekly_kpi", ["user_id", "week_start"])  # type: ignore

    if not _has_table(conn, "student_topic_theta"):
        op.create_table(
            "student_topic_theta",
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("topic_id", sa.Text(), nullable=False),
            sa.Column("theta", sa.Float(), nullable=False),
            sa.Column("se", sa.Float(), nullable=True),
            sa.Column("model", sa.Text(), nullable=False),
            sa.Column("version", sa.Text(), nullable=True),
            sa.Column(
                "fitted_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint(
                "user_id", "topic_id", name="pk_student_topic_theta"
            ),
        )
        op.create_index("ix_theta_user_topic", "student_topic_theta", ["user_id", "topic_id"])  # type: ignore


def downgrade() -> None:
    conn = op.get_bind()
    if _has_table(conn, "student_topic_theta"):
        op.drop_index("ix_theta_user_topic", table_name="student_topic_theta")
        op.drop_table("student_topic_theta")
    if _has_table(conn, "weekly_kpi"):
        op.drop_index("ix_weekly_kpi_user_date", table_name="weekly_kpi")
        op.drop_table("weekly_kpi")
