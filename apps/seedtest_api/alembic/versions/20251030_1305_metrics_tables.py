"""Metrics tables: weekly_kpi and student_topic_theta

Revision ID: 20251030_1305_metrics_tables
Revises: 20251030_1200_metrics_tables
Create Date: 2025-10-30 13:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "20251030_1305_metrics_tables"
down_revision = "20251030_1200_metrics_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables already exist (may have been created by previous migration)
    conn = op.get_bind()

    # weekly_kpi: 주차 단위 KPI(JSONB) 저장, PK(user_id, week_start)
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='weekly_kpi')"
        )
    )
    if not result.scalar():
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
        op.create_index(
            "ix_weekly_kpi_user_date",
            "weekly_kpi",
            ["user_id", "week_start"],
            unique=False,
        )

    # student_topic_theta: 토픽별 θ/SE/모델 메타 저장, PK(user_id, topic_id)
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='student_topic_theta')"
        )
    )
    if not result.scalar():
        op.create_table(
            "student_topic_theta",
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("topic_id", sa.Text(), nullable=False),
            sa.Column("theta", sa.Float(), nullable=False),  # DOUBLE PRECISION
            sa.Column("se", sa.Float(), nullable=True),  # DOUBLE PRECISION
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
        op.create_index(
            "ix_theta_user_topic",
            "student_topic_theta",
            ["user_id", "topic_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_theta_user_topic", table_name="student_topic_theta")
    op.drop_table("student_topic_theta")

    op.drop_index("ix_weekly_kpi_user_date", table_name="weekly_kpi")
    op.drop_table("weekly_kpi")
