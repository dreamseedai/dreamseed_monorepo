"""Teacher dashboard tables: attendance, risk_flag, class_summary

Revision ID: 20251107_0900_teacher_dashboard
Revises: 20251031_2100_question_table
Create Date: 2025-11-07 09:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "20251107_0900_teacher_dashboard"
down_revision = "20251031_2100_question_table"
branch_labels = None
depends_on = None


def _table_exists(conn: Connection, name: str) -> bool:
    """Check if table exists."""
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    conn = op.get_bind()

    # attendance: student attendance tracking
    if not _table_exists(conn, "attendance"):
        op.create_table(
            "attendance",
            sa.Column("id", sa.Text, primary_key=True),
            sa.Column("student_id", sa.Text, nullable=False),
            sa.Column("classroom_id", sa.Text, nullable=False),
            sa.Column("session_id", sa.Text, nullable=False),
            sa.Column("date", sa.Date, nullable=False),
            sa.Column("status", sa.String(16), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_index("ix_attendance_student_id", "attendance", ["student_id"])  # type: ignore
        op.create_index("ix_attendance_classroom_id", "attendance", ["classroom_id"])  # type: ignore
        op.create_index("ix_attendance_session_id", "attendance", ["session_id"])  # type: ignore
        op.create_index("ix_attendance_date", "attendance", ["date"])  # type: ignore
        op.create_index("ix_attendance_classroom_date", "attendance", ["classroom_id", "date"])  # type: ignore
        op.create_index("ix_attendance_student_date", "attendance", ["student_id", "date"])  # type: ignore

    # risk_flag: student risk detection flags
    if not _table_exists(conn, "risk_flag"):
        op.create_table(
            "risk_flag",
            sa.Column("id", sa.Text, primary_key=True),
            sa.Column("student_id", sa.Text, nullable=False),
            sa.Column("classroom_id", sa.Text, nullable=False),
            sa.Column("week_start", sa.Date, nullable=False),
            sa.Column("type", sa.String(64), nullable=False),
            sa.Column("score", sa.Numeric(5, 2), nullable=False, server_default="0"),
            sa.Column(
                "details_json", JSONB, nullable=True, server_default=sa.text("'{}'")
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_index("ix_risk_flag_student_id", "risk_flag", ["student_id"])  # type: ignore
        op.create_index("ix_risk_flag_classroom_id", "risk_flag", ["classroom_id"])  # type: ignore
        op.create_index("ix_risk_flag_week_start", "risk_flag", ["week_start"])  # type: ignore
        op.create_index("ix_risk_flag_type", "risk_flag", ["type"])  # type: ignore
        op.create_index("ix_risk_classroom_week", "risk_flag", ["classroom_id", "week_start"])  # type: ignore
        op.create_index("ix_risk_student_week", "risk_flag", ["student_id", "week_start"])  # type: ignore
        op.create_index("ix_risk_type_week", "risk_flag", ["type", "week_start"])  # type: ignore

    # class_summary: weekly class-level aggregated metrics
    if not _table_exists(conn, "class_summary"):
        op.create_table(
            "class_summary",
            sa.Column("id", sa.Text, primary_key=True),
            sa.Column("classroom_id", sa.Text, nullable=False),
            sa.Column("week_start", sa.Date, nullable=False),
            sa.Column("mean_theta", sa.Numeric(6, 3), nullable=False),
            sa.Column("median_theta", sa.Numeric(6, 3), nullable=False),
            sa.Column("top10_theta", sa.Numeric(6, 3), nullable=False),
            sa.Column("bottom10_theta", sa.Numeric(6, 3), nullable=False),
            sa.Column(
                "delta_theta_7d", sa.Numeric(6, 3), nullable=False, server_default="0"
            ),
            sa.Column(
                "attendance_absent_rate",
                sa.Numeric(5, 4),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "attendance_late_rate",
                sa.Numeric(5, 4),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "stability_score", sa.Numeric(6, 3), nullable=False, server_default="0"
            ),
            sa.Column("risks_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_index("ix_class_summary_classroom_id", "class_summary", ["classroom_id"])  # type: ignore
        op.create_index("ix_class_summary_week_start", "class_summary", ["week_start"])  # type: ignore
        op.create_index(
            "ix_class_summary_classroom_week",
            "class_summary",
            ["classroom_id", "week_start"],
            unique=True,
        )  # type: ignore


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "class_summary"):
        op.drop_index("ix_class_summary_classroom_week", table_name="class_summary")
        op.drop_index("ix_class_summary_week_start", table_name="class_summary")
        op.drop_index("ix_class_summary_classroom_id", table_name="class_summary")
        op.drop_table("class_summary")

    if _table_exists(conn, "risk_flag"):
        op.drop_index("ix_risk_type_week", table_name="risk_flag")
        op.drop_index("ix_risk_student_week", table_name="risk_flag")
        op.drop_index("ix_risk_classroom_week", table_name="risk_flag")
        op.drop_index("ix_risk_flag_type", table_name="risk_flag")
        op.drop_index("ix_risk_flag_week_start", table_name="risk_flag")
        op.drop_index("ix_risk_flag_classroom_id", table_name="risk_flag")
        op.drop_index("ix_risk_flag_student_id", table_name="risk_flag")
        op.drop_table("risk_flag")

    if _table_exists(conn, "attendance"):
        op.drop_index("ix_attendance_student_date", table_name="attendance")
        op.drop_index("ix_attendance_classroom_date", table_name="attendance")
        op.drop_index("ix_attendance_date", table_name="attendance")
        op.drop_index("ix_attendance_session_id", table_name="attendance")
        op.drop_index("ix_attendance_classroom_id", table_name="attendance")
        op.drop_index("ix_attendance_student_id", table_name="attendance")
        op.drop_table("attendance")
