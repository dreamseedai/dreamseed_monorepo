"""Create report_artifacts table for storing report URLs

Revision ID: 20251101_1700_report_artifacts
Revises: 20251031_2110_attempt_view
Create Date: 2025-11-01 17:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql


# revision identifiers, used by Alembic.
revision = "20251101_1700_report_artifacts"
down_revision = "20251031_2110_attempt_view"  # Adjust based on actual last revision
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    """Check if a table exists."""
    from sqlalchemy import inspect
    insp = inspect(conn)
    return insp.has_table(table_name)


def upgrade() -> None:
    conn = op.get_bind()
    
    if not _table_exists(conn, "report_artifacts"):
        op.create_table(
            "report_artifacts",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Text, nullable=False),
            sa.Column("week_start", sa.Date, nullable=False),
            sa.Column("format", sa.Text, nullable=False, server_default="html"),  # html, pdf
            sa.Column("url", sa.Text, nullable=False),
            sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        
        # Unique constraint: one report per user/week/format
        op.create_unique_constraint(
            "uq_report_artifacts_user_week_format",
            "report_artifacts",
            ["user_id", "week_start", "format"],
        )
        
        # Indexes
        op.create_index("ix_report_artifacts_user_week", "report_artifacts", ["user_id", "week_start"])
        op.create_index("ix_report_artifacts_generated_at", "report_artifacts", ["generated_at"])


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "report_artifacts"):
        op.drop_index("ix_report_artifacts_generated_at", table_name="report_artifacts")
        op.drop_index("ix_report_artifacts_user_week", table_name="report_artifacts")
        op.drop_constraint("uq_report_artifacts_user_week_format", "report_artifacts", type_="unique")
        op.drop_table("report_artifacts")

