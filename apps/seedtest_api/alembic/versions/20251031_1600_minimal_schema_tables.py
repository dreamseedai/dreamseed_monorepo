"""Minimal schema tables for classroom/session/interest_goal/features_topic_daily

Revision ID: 20251031_1600_minimal_schema_tables
Revises: 20251030_1510_bf_metrics
Create Date: 2025-10-31 16:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "20251031_1600_minimal_schema_tables"
down_revision = "20251030_1510_bf_metrics"
branch_labels = None
depends_on = None


def table_exists(conn, name: str) -> bool:
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    conn = op.get_bind()

    # classroom: basic org-scoped grouping
    if not table_exists(conn, "classroom"):
        op.create_table(
            "classroom",
            sa.Column("id", sa.Text, primary_key=True),
            sa.Column("org_id", sa.Text, nullable=False),
            sa.Column("name", sa.Text, nullable=False),
            sa.Column("grade", sa.SmallInteger, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_unique_constraint("uq_classroom_org_name", "classroom", ["org_id", "name"])  # type: ignore
        op.create_index("ix_classroom_org", "classroom", ["org_id"])  # type: ignore

    # session: learning/assessment session metadata
    if not table_exists(conn, "session"):
        op.create_table(
            "session",
            sa.Column("id", sa.Text, primary_key=True),
            sa.Column(
                "classroom_id", sa.Text, nullable=True
            ),  # no FK by design (app-level integrity)
            sa.Column("exam_id", sa.Text, nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.Text, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_index("ix_session_classroom", "session", ["classroom_id"])  # type: ignore
        op.create_index("ix_session_status_started", "session", ["status", "started_at"])  # type: ignore

    # interest_goal: user-topic targets
    if not table_exists(conn, "interest_goal"):
        op.create_table(
            "interest_goal",
            sa.Column("user_id", sa.Text, nullable=False),
            sa.Column("topic_id", sa.Text, nullable=False),
            sa.Column("target_level", sa.Numeric(6, 3), nullable=True),
            sa.Column(
                "priority", sa.SmallInteger, server_default=sa.text("0"), nullable=False
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("user_id", "topic_id", name="pk_interest_goal"),
        )
        op.create_index("ix_interest_goal_user", "interest_goal", ["user_id"])  # type: ignore
        op.create_index("ix_interest_goal_topic", "interest_goal", ["topic_id"])  # type: ignore

    # features_topic_daily: daily aggregates per user/topic
    if not table_exists(conn, "features_topic_daily"):
        op.create_table(
            "features_topic_daily",
            sa.Column("user_id", sa.Text, nullable=False),
            sa.Column("topic_id", sa.Text, nullable=False),
            sa.Column("date", sa.Date, nullable=False),
            sa.Column(
                "attempts", sa.Integer, server_default=sa.text("0"), nullable=False
            ),
            sa.Column(
                "correct", sa.Integer, server_default=sa.text("0"), nullable=False
            ),
            sa.Column("avg_time_ms", sa.Integer, nullable=True),
            sa.Column("theta_estimate", sa.Numeric(6, 3), nullable=True),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "computed_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint(
                "user_id", "topic_id", "date", name="pk_features_topic_daily"
            ),
        )
        op.create_index("ix_ftd_topic_date", "features_topic_daily", ["topic_id", "date"])  # type: ignore
        op.create_index("ix_ftd_user_date", "features_topic_daily", ["user_id", "date"])  # type: ignore


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "features_topic_daily"):
        op.drop_index("ix_ftd_user_date", table_name="features_topic_daily")
        op.drop_index("ix_ftd_topic_date", table_name="features_topic_daily")
        op.drop_table("features_topic_daily")

    if table_exists(conn, "interest_goal"):
        op.drop_index("ix_interest_goal_topic", table_name="interest_goal")
        op.drop_index("ix_interest_goal_user", table_name="interest_goal")
        op.drop_table("interest_goal")

    if table_exists(conn, "session"):
        op.drop_index("ix_session_status_started", table_name="session")
        op.drop_index("ix_session_classroom", table_name="session")
        op.drop_table("session")

    if table_exists(conn, "classroom"):
        op.drop_index("ix_classroom_org", table_name="classroom")
        op.drop_constraint("uq_classroom_org_name", "classroom", type_="unique")  # type: ignore
        op.drop_table("classroom")
