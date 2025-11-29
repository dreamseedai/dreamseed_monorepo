"""student emotive dashboard tables

Revision ID: 20251107_student_emotive
Revises:
Create Date: 2025-11-07

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251107_student_emotive"
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # student_mood table
    op.create_table(
        "student_mood",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column(
            "student_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("day", sa.Date(), nullable=False, index=True),
        sa.Column("mood", sa.String(length=8), nullable=False),
        sa.Column("note", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "tenant_id", "student_id", "day", name="uq_mood_tenant_student_day"
        ),
    )
    op.create_index(
        "ix_mood_tenant_student_day", "student_mood", ["tenant_id", "student_id", "day"]
    )

    # student_daily_log table
    op.create_table(
        "student_daily_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column(
            "student_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("day", sa.Date(), nullable=False, index=True),
        sa.Column("study_minutes", sa.Integer(), server_default="0"),
        sa.Column("tasks_done", sa.Integer(), server_default="0"),
        sa.Column("theta_delta", sa.Float(), server_default="0"),
        sa.Column("reflections", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
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
    op.create_table(
        "student_goal",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column(
            "student_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("done", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_goal_tenant_student_created",
        "student_goal",
        ["tenant_id", "student_id", "created_at"],
    )

    # student_ai_message table
    op.create_table(
        "student_ai_message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column(
            "student_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("day", sa.Date(), nullable=False, index=True),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("tone", sa.String(length=24), server_default="warm"),
        sa.Column("meta", postgresql.JSON(astext_type=sa.Text()), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
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
    for table_name in [
        "student_ai_message",
        "student_goal",
        "student_daily_log",
        "student_mood",
    ]:
        op.drop_table(table_name)
