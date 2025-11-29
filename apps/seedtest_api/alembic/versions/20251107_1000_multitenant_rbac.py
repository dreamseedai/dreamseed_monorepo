"""Add tenant_id to analytics tables and create risk_threshold table.

Revision ID: 20251107_1000_multitenant_rbac
Revises: 20251107_0900_teacher_dashboard
Create Date: 2025-11-07 10:00:00.000000

This migration adds multitenancy support by:
1. Adding tenant_id column to all analytics tables
2. Creating risk_threshold table for hierarchical threshold config
3. Adding composite indexes for tenant-scoped queries
4. Updating unique constraints to include tenant_id
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251107_1000_multitenant_rbac"
down_revision = "20251107_0900_teacher_dashboard"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    """Check if table already exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Step 1: Add tenant_id columns with default value for backfill
    tables = ["attendance", "risk_flag", "class_summary"]

    for tbl in tables:
        if _table_exists(tbl) and not _column_exists(tbl, "tenant_id"):
            op.add_column(
                tbl,
                sa.Column(
                    "tenant_id",
                    sa.Text(),
                    nullable=False,
                    server_default="default-tenant-id",  # Temporary for backfill
                ),
            )
            op.create_index(f"ix_{tbl}_tenant_id", tbl, ["tenant_id"])

    # Step 2: Update unique constraints to include tenant_id
    if _table_exists("class_summary"):
        # Drop old unique constraint
        try:
            op.drop_constraint(
                "ix_class_summary_classroom_week", "class_summary", type_="unique"
            )
        except Exception:
            pass  # Constraint may not exist

        # Create new tenant-scoped unique constraint
        op.create_unique_constraint(
            "uq_class_summary_tenant_classroom_week",
            "class_summary",
            ["tenant_id", "classroom_id", "week_start"],
        )

    # Step 3: Add composite indexes for tenant-scoped queries
    if _table_exists("attendance"):
        op.create_index(
            "ix_attendance_tenant_classroom_date",
            "attendance",
            ["tenant_id", "classroom_id", "date"],
        )
        op.create_index(
            "ix_attendance_tenant_student_date",
            "attendance",
            ["tenant_id", "student_id", "date"],
        )

    if _table_exists("risk_flag"):
        op.create_index(
            "ix_risk_flag_tenant_classroom_week",
            "risk_flag",
            ["tenant_id", "classroom_id", "week_start"],
        )
        op.create_index(
            "ix_risk_flag_tenant_student_week",
            "risk_flag",
            ["tenant_id", "student_id", "week_start"],
        )

    if _table_exists("class_summary"):
        op.create_index(
            "ix_class_summary_tenant_classroom_week",
            "class_summary",
            ["tenant_id", "classroom_id", "week_start"],
        )

    # Step 4: Create risk_threshold table
    if not _table_exists("risk_threshold"):
        op.create_table(
            "risk_threshold",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("tenant_id", sa.Text(), nullable=False),
            sa.Column("type", sa.String(length=64), nullable=False),
            sa.Column("class_id", sa.Text(), nullable=True),
            sa.Column("grade", sa.String(length=16), nullable=True),
            sa.Column("low_growth_delta", sa.Float(), nullable=True),
            sa.Column("low_growth_nonpos_weeks", sa.Integer(), nullable=True),
            sa.Column("absent_rate_threshold", sa.Float(), nullable=True),
            sa.Column("late_rate_threshold", sa.Float(), nullable=True),
            sa.Column("response_anomaly_c_top_pct", sa.Float(), nullable=True),
            sa.Column("no_response_rate_threshold", sa.Float(), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_risk_threshold_tenant_id", "risk_threshold", ["tenant_id"])
        op.create_index("ix_risk_threshold_type", "risk_threshold", ["type"])
        op.create_index("ix_risk_threshold_class_id", "risk_threshold", ["class_id"])
        op.create_index("ix_risk_threshold_grade", "risk_threshold", ["grade"])
        op.create_index(
            "ix_risk_threshold_updated_at", "risk_threshold", ["updated_at"]
        )
        op.create_index(
            "ix_risk_threshold_tenant_type", "risk_threshold", ["tenant_id", "type"]
        )

    # Step 5: Remove server_default after backfill
    # NOTE: Before running this in production, execute:
    #   UPDATE attendance SET tenant_id = '<your-actual-tenant-id>' WHERE tenant_id = 'default-tenant-id';
    #   UPDATE risk_flag SET tenant_id = '<your-actual-tenant-id>' WHERE tenant_id = 'default-tenant-id';
    #   UPDATE class_summary SET tenant_id = '<your-actual-tenant-id>' WHERE tenant_id = 'default-tenant-id';

    for tbl in tables:
        if _table_exists(tbl) and _column_exists(tbl, "tenant_id"):
            op.alter_column(tbl, "tenant_id", server_default=None)


def downgrade():
    # Drop risk_threshold table
    if _table_exists("risk_threshold"):
        op.drop_table("risk_threshold")

    # Drop composite indexes
    indexes_to_drop = [
        ("ix_class_summary_tenant_classroom_week", "class_summary"),
        ("ix_risk_flag_tenant_student_week", "risk_flag"),
        ("ix_risk_flag_tenant_classroom_week", "risk_flag"),
        ("ix_attendance_tenant_student_date", "attendance"),
        ("ix_attendance_tenant_classroom_date", "attendance"),
    ]

    for idx_name, tbl_name in indexes_to_drop:
        if _table_exists(tbl_name):
            try:
                op.drop_index(idx_name, table_name=tbl_name)
            except Exception:
                pass

    # Restore old unique constraint on class_summary
    if _table_exists("class_summary"):
        try:
            op.drop_constraint(
                "uq_class_summary_tenant_classroom_week",
                "class_summary",
                type_="unique",
            )
        except Exception:
            pass

        op.create_unique_constraint(
            "ix_class_summary_classroom_week",
            "class_summary",
            ["classroom_id", "week_start"],
        )

    # Drop tenant_id columns
    for tbl in ["attendance", "risk_flag", "class_summary"]:
        if _table_exists(tbl) and _column_exists(tbl, "tenant_id"):
            try:
                op.drop_index(f"ix_{tbl}_tenant_id", table_name=tbl)
            except Exception:
                pass
            op.drop_column(tbl, "tenant_id")
