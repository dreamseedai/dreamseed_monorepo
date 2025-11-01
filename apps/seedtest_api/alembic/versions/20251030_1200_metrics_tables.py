"""Create weekly_kpi and student_topic_theta tables

Revision ID: 20251030_1200_metrics_tables
Revises: 20251023_1100_exam_results_gin_index
Create Date: 2025-10-30 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251030_1200_metrics_tables"
down_revision = "20251023_1100_exam_results_gin_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables already exist
    conn = op.get_bind()

    # weekly_kpi: stores weekly rollups per user
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
            sa.Column(
                "kpis",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("user_id", "week_start", name="pk_weekly_kpi"),
        )

        # Helpful indexes for query patterns (recent 4–12 weeks per user)
        op.create_index(
            "ix_weekly_kpi_user_week",
            "weekly_kpi",
            ["user_id", "week_start"],
            unique=False,
        )
        op.create_index(
            "ix_weekly_kpi_week_start",
            "weekly_kpi",
            ["week_start"],
            unique=False,
        )

    # student_topic_theta: per-user per-topic latent trait estimates
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
            sa.Column("theta", sa.Numeric(), nullable=True),
            sa.Column("standard_error", sa.Numeric(), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint(
                "user_id", "topic_id", name="pk_student_topic_theta"
            ),
        )

        op.create_index(
            "ix_student_topic_theta_user",
            "student_topic_theta",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            "ix_student_topic_theta_topic",
            "student_topic_theta",
            ["topic_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_student_topic_theta_topic", table_name="student_topic_theta")
    op.drop_index("ix_student_topic_theta_user", table_name="student_topic_theta")
    op.drop_table("student_topic_theta")

    op.drop_index("ix_weekly_kpi_week_start", table_name="weekly_kpi")
    op.drop_index("ix_weekly_kpi_user_week", table_name="weekly_kpi")
    op.drop_table("weekly_kpi")
