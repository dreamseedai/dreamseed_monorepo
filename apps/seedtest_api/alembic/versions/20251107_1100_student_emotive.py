"""Alembic migration: Student Emotive Dashboard tables

Revision ID: 20251107_1100_student_emotive
Revises: 20251107_1000_multitenant_rbac
Create Date: 2025-11-07 11:00:00

Creates 4 tables for student-facing emotive dashboard:
- student_mood: Daily mood tracking
- student_daily_log: Study metrics and reflections
- student_goal: Personal learning goals
- student_ai_message: AI-generated encouragement

All tables use TEXT-based IDs with tenant_id + student_id scoping.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20251107_1100_student_emotive"
down_revision = "20251107_1000_multitenant_rbac"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    """Check if table exists"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=:name)"
        ),
        {"name": table_name},
    )
    return result.scalar()


def upgrade():
    """Create student emotive dashboard tables"""

    # student_mood table
    if not _table_exists("student_mood"):
        op.create_table(
            "student_mood",
            sa.Column(
                "id",
                sa.String(),
                nullable=False,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("tenant_id", sa.String(), nullable=False, index=True),
            sa.Column("student_id", sa.String(), nullable=False, index=True),
            sa.Column("day", sa.Date(), nullable=False, index=True),
            sa.Column("mood", sa.String(length=8), nullable=False),
            sa.Column("note", sa.String(length=512), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "tenant_id", "student_id", "day", name="uq_mood_tenant_student_day"
            ),
        )
        op.create_index(
            "ix_mood_tenant_student_day",
            "student_mood",
            ["tenant_id", "student_id", "day"],
        )

    # student_daily_log table
    if not _table_exists("student_daily_log"):
        op.create_table(
            "student_daily_log",
            sa.Column(
                "id",
                sa.String(),
                nullable=False,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("tenant_id", sa.String(), nullable=False, index=True),
            sa.Column("student_id", sa.String(), nullable=False, index=True),
            sa.Column("day", sa.Date(), nullable=False, index=True),
            sa.Column(
                "study_minutes", sa.Integer(), server_default="0", nullable=False
            ),
            sa.Column("tasks_done", sa.Integer(), server_default="0", nullable=False),
            sa.Column("theta_delta", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("reflections", sa.String(length=1000), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "tenant_id", "student_id", "day", name="uq_log_tenant_student_day"
            ),
        )
        op.create_index(
            "ix_log_tenant_student_day",
            "student_daily_log",
            ["tenant_id", "student_id", "day"],
        )

    # student_goal table
    if not _table_exists("student_goal"):
        op.create_table(
            "student_goal",
            sa.Column(
                "id",
                sa.String(),
                nullable=False,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("tenant_id", sa.String(), nullable=False, index=True),
            sa.Column("student_id", sa.String(), nullable=False, index=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("target_date", sa.Date(), nullable=True),
            sa.Column("done", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_goal_tenant_student_created",
            "student_goal",
            ["tenant_id", "student_id", "created_at"],
        )

    # student_ai_message table
    if not _table_exists("student_ai_message"):
        op.create_table(
            "student_ai_message",
            sa.Column(
                "id",
                sa.String(),
                nullable=False,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("tenant_id", sa.String(), nullable=False, index=True),
            sa.Column("student_id", sa.String(), nullable=False, index=True),
            sa.Column("day", sa.Date(), nullable=False, index=True),
            sa.Column("message", sa.String(length=1000), nullable=False),
            sa.Column(
                "tone", sa.String(length=24), server_default="'warm'", nullable=False
            ),
            sa.Column(
                "meta",
                postgresql.JSON(astext_type=sa.Text()),
                server_default="{}",
                nullable=False,
            ),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "tenant_id", "student_id", "day", name="uq_msg_tenant_student_day"
            ),
        )
        op.create_index(
            "ix_msg_tenant_student_day",
            "student_ai_message",
            ["tenant_id", "student_id", "day"],
        )


def downgrade():
    """Drop student emotive dashboard tables"""
    tables = ["student_ai_message", "student_goal", "student_daily_log", "student_mood"]

    for table in tables:
        if _table_exists(table):
            op.drop_table(table)
