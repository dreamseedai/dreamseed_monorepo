"""add assignment tables

Revision ID: 013_add_assignment_tables
Revises: 012_add_call_tables
Create Date: 2025-11-26 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "013_add_assignment_tables"
down_revision: Union[str, None] = "012_add_call_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assignments table
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.String(length=100), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("grade", sa.String(length=50), nullable=True),
        sa.Column(
            "assignment_type", sa.String(length=50), nullable=False
        ),  # homework, quiz, test, project
        sa.Column("template_id", sa.String(length=100), nullable=True),
        sa.Column("total_points", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("assigned_date", sa.DateTime(), nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="active"
        ),  # active, archived, draft
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column(
            "attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assignments_teacher_id", "assignments", ["teacher_id"])
    op.create_index("ix_assignments_class_id", "assignments", ["class_id"])
    op.create_index("ix_assignments_status", "assignments", ["status"])
    op.create_index("ix_assignments_due_date", "assignments", ["due_date"])
    op.create_index("ix_assignments_assigned_date", "assignments", ["assigned_date"])

    # Create assignment_students table (many-to-many relationship)
    op.create_table(
        "assignment_students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notified", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["assignments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id", "student_id", name="uq_assignment_student"
        ),
    )
    op.create_index(
        "ix_assignment_students_assignment_id", "assignment_students", ["assignment_id"]
    )
    op.create_index(
        "ix_assignment_students_student_id", "assignment_students", ["student_id"]
    )

    # Create submissions table
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("submission_text", sa.Text(), nullable=True),
        sa.Column(
            "attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("is_late", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="submitted"
        ),  # submitted, graded, returned
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("grade", sa.String(length=10), nullable=True),  # A, B+, etc.
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("graded_at", sa.DateTime(), nullable=True),
        sa.Column("graded_by", sa.Integer(), nullable=True),
        sa.Column(
            "rubric_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["assignments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["graded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id", "student_id", name="uq_submission_assignment_student"
        ),
    )
    op.create_index("ix_submissions_assignment_id", "submissions", ["assignment_id"])
    op.create_index("ix_submissions_student_id", "submissions", ["student_id"])
    op.create_index("ix_submissions_status", "submissions", ["status"])
    op.create_index("ix_submissions_submitted_at", "submissions", ["submitted_at"])
    op.create_index("ix_submissions_graded_by", "submissions", ["graded_by"])

    # Create submission_history table for tracking revisions
    op.create_table(
        "submission_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("submission_text", sa.Text(), nullable=True),
        sa.Column(
            "attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"], ["submissions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_submission_history_submission_id", "submission_history", ["submission_id"]
    )

    # Create materialized view for assignment statistics
    op.execute(
        """
        CREATE MATERIALIZED VIEW assignment_statistics AS
        SELECT 
            a.id as assignment_id,
            a.teacher_id,
            COUNT(DISTINCT ast.student_id) as total_students,
            COUNT(DISTINCT s.student_id) as submitted_count,
            COUNT(DISTINCT CASE WHEN s.status = 'graded' THEN s.student_id END) as graded_count,
            COUNT(DISTINCT CASE WHEN s.is_late = true THEN s.student_id END) as late_count,
            AVG(CASE WHEN s.score IS NOT NULL THEN s.score END) as avg_score,
            MAX(s.submitted_at) as last_submission_at
        FROM assignments a
        LEFT JOIN assignment_students ast ON a.id = ast.assignment_id
        LEFT JOIN submissions s ON a.id = s.assignment_id
        GROUP BY a.id, a.teacher_id
    """
    )
    op.create_index(
        "ix_assignment_statistics_assignment_id",
        "assignment_statistics",
        ["assignment_id"],
        unique=True,
    )
    op.create_index(
        "ix_assignment_statistics_teacher_id", "assignment_statistics", ["teacher_id"]
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS assignment_statistics")
    op.drop_index(
        "ix_submission_history_submission_id", table_name="submission_history"
    )
    op.drop_table("submission_history")
    op.drop_index("ix_submissions_graded_by", table_name="submissions")
    op.drop_index("ix_submissions_submitted_at", table_name="submissions")
    op.drop_index("ix_submissions_status", table_name="submissions")
    op.drop_index("ix_submissions_student_id", table_name="submissions")
    op.drop_index("ix_submissions_assignment_id", table_name="submissions")
    op.drop_table("submissions")
    op.drop_index("ix_assignment_students_student_id", table_name="assignment_students")
    op.drop_index(
        "ix_assignment_students_assignment_id", table_name="assignment_students"
    )
    op.drop_table("assignment_students")
    op.drop_index("ix_assignments_assigned_date", table_name="assignments")
    op.drop_index("ix_assignments_due_date", table_name="assignments")
    op.drop_index("ix_assignments_status", table_name="assignments")
    op.drop_index("ix_assignments_class_id", table_name="assignments")
    op.drop_index("ix_assignments_teacher_id", table_name="assignments")
    op.drop_table("assignments")
