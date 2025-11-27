"""Create teacher/parent/tutor platform tables

Revision ID: 001_create_platform_tables
Revises: 
Create Date: 2025-11-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_create_platform_tables"
down_revision = None  # ⚠️ UPDATE THIS with actual last revision ID if needed
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) students
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),  # FK to users.id (INTEGER)
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("grade", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_students_id", "students", ["id"], unique=False)
    op.create_index("ix_students_user_id", "students", ["user_id"], unique=False)
    op.create_index("ix_students_name", "students", ["name"], unique=False)
    op.create_index("ix_students_external_id", "students", ["external_id"], unique=False)

    # 2) classes
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),  # FK to users.id (INTEGER)
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("grade", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classes_id", "classes", ["id"], unique=False)
    op.create_index("ix_classes_teacher_id", "classes", ["teacher_id"], unique=False)

    # 3) student_classes (many-to-many)
    op.create_table(
        "student_classes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "class_id",
            sa.Integer(),
            sa.ForeignKey("classes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "class_id", name="uq_student_class"),
    )
    op.create_index(
        "ix_student_classes_student_id", "student_classes", ["student_id"], unique=False
    )
    op.create_index(
        "ix_student_classes_class_id", "student_classes", ["class_id"], unique=False
    )

    # 4) tutor_sessions
    op.create_table(
        "tutor_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tutor_id", sa.Integer(), nullable=False),  # FK to users.id (INTEGER)
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Upcoming",
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["tutor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tutor_sessions_id", "tutor_sessions", ["id"], unique=False)
    op.create_index(
        "ix_tutor_sessions_tutor_id", "tutor_sessions", ["tutor_id"], unique=False
    )
    op.create_index(
        "ix_tutor_sessions_student_id", "tutor_sessions", ["student_id"], unique=False
    )
    op.create_index("ix_tutor_sessions_date", "tutor_sessions", ["date"], unique=False)
    op.create_index(
        "ix_tutor_sessions_status", "tutor_sessions", ["status"], unique=False
    )

    # 5) tutor_session_tasks
    op.create_table(
        "tutor_session_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("tutor_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column(
            "done",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tutor_session_tasks_session_id",
        "tutor_session_tasks",
        ["session_id"],
        unique=False,
    )

    # 6) student_ability_history
    op.create_table(
        "student_ability_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("theta", sa.Float(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "student_id", "as_of_date", name="uq_student_ability_history_student_date"
        ),
    )
    op.create_index(
        "ix_student_ability_history_student_date",
        "student_ability_history",
        ["student_id", "as_of_date"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse order (FK dependencies → parent tables)
    op.drop_index(
        "ix_student_ability_history_student_date",
        table_name="student_ability_history",
    )
    op.drop_table("student_ability_history")

    op.drop_index(
        "ix_tutor_session_tasks_session_id", table_name="tutor_session_tasks"
    )
    op.drop_table("tutor_session_tasks")

    op.drop_index("ix_tutor_sessions_status", table_name="tutor_sessions")
    op.drop_index("ix_tutor_sessions_date", table_name="tutor_sessions")
    op.drop_index("ix_tutor_sessions_student_id", table_name="tutor_sessions")
    op.drop_index("ix_tutor_sessions_tutor_id", table_name="tutor_sessions")
    op.drop_index("ix_tutor_sessions_id", table_name="tutor_sessions")
    op.drop_table("tutor_sessions")

    op.drop_index("ix_student_classes_class_id", table_name="student_classes")
    op.drop_index("ix_student_classes_student_id", table_name="student_classes")
    op.drop_table("student_classes")

    op.drop_index("ix_classes_teacher_id", table_name="classes")
    op.drop_index("ix_classes_id", table_name="classes")
    op.drop_table("classes")

    op.drop_index("ix_students_external_id", table_name="students")
    op.drop_index("ix_students_name", table_name="students")
    op.drop_index("ix_students_user_id", table_name="students")
    op.drop_index("ix_students_id", table_name="students")
    op.drop_table("students")
