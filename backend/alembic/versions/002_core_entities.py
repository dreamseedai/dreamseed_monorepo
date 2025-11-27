"""Core entities for organizations, teachers, exam_sessions, attempts

Revision ID: 002_core_entities
Revises: 001_create_platform_tables
Create Date: 2025-11-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_core_entities"
down_revision = "001_create_platform_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0) organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 1) teachers (profile linked to users)
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_teachers_org_id", "teachers", ["org_id"], unique=False)

    # 2) student_classroom (N:N between students and classes)
    # NOTE: This is a new join table, in addition to existing student_classes.
    # It uses a composite primary key as in the proposed DDL.
    op.create_table(
        "student_classroom",
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "class_id",
            sa.Integer(),
            sa.ForeignKey("classes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_student_classroom_class_id",
        "student_classroom",
        ["class_id"],
        unique=False,
    )

    # 3) exam_sessions
    op.create_table(
        "exam_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "class_id",
            sa.Integer(),
            sa.ForeignKey("classes.id"),
            nullable=True,
        ),
        sa.Column("exam_type", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("theta", sa.Numeric(6, 3), nullable=True),
        sa.Column("standard_error", sa.Numeric(6, 3), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_exam_sessions_student_id",
        "exam_sessions",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_exam_sessions_class_id",
        "exam_sessions",
        ["class_id"],
        unique=False,
    )
    op.create_index(
        "ix_exam_sessions_status",
        "exam_sessions",
        ["status"],
        unique=False,
    )

    # 4) attempts
    op.create_table(
        "attempts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exam_session_id",
            sa.BigInteger(),
            sa.ForeignKey("exam_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_id", sa.BigInteger(), nullable=True),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("submitted_answer", sa.Text(), nullable=True),
        sa.Column("selected_choice", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("meta", sa.JSON(), nullable=True),
    )
    op.create_index("ix_attempts_student_id", "attempts", ["student_id"], unique=False)
    op.create_index(
        "ix_attempts_exam_session_id",
        "attempts",
        ["exam_session_id"],
        unique=False,
    )
    op.create_index("ix_attempts_item_id", "attempts", ["item_id"], unique=False)


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_attempts_item_id", table_name="attempts")
    op.drop_index("ix_attempts_exam_session_id", table_name="attempts")
    op.drop_index("ix_attempts_student_id", table_name="attempts")
    op.drop_table("attempts")

    op.drop_index("ix_exam_sessions_status", table_name="exam_sessions")
    op.drop_index("ix_exam_sessions_class_id", table_name="exam_sessions")
    op.drop_index("ix_exam_sessions_student_id", table_name="exam_sessions")
    op.drop_table("exam_sessions")

    op.drop_index(
        "ix_student_classroom_class_id",
        table_name="student_classroom",
    )
    op.drop_table("student_classroom")

    op.drop_index("ix_teachers_org_id", table_name="teachers")
    op.drop_table("teachers")

    op.drop_table("organizations")
