"""add_moderation_tables

Revision ID: 008_moderation_tables
Revises: 007_fulltext_search
Create Date: 2025-11-26 12:00:00.000000

Add moderation_logs and reports tables for admin and moderation features.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "008_moderation_tables"
down_revision: Union[str, None] = "007_fulltext_search"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create moderation_logs table
    op.create_table(
        "moderation_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for moderation_logs
    op.create_index("idx_moderation_logs_admin", "moderation_logs", ["admin_id"])
    op.create_index("idx_moderation_logs_target", "moderation_logs", ["target_user_id"])
    op.create_index("idx_moderation_logs_created", "moderation_logs", ["created_at"])

    # Create reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("reported_user_id", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("conversation_id", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["reported_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.conversation_id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for reports
    op.create_index("idx_reports_reporter", "reports", ["reporter_id"])
    op.create_index("idx_reports_reported_user", "reports", ["reported_user_id"])
    op.create_index("idx_reports_status", "reports", ["status"])
    op.create_index("idx_reports_created", "reports", ["created_at"])

    # Add messenger_restriction column to users table (if not exists)
    # This allows tracking user restrictions without separate table
    op.add_column(
        "users",
        sa.Column(
            "messenger_restriction",
            sa.String(length=20),
            nullable=True,
            server_default="none",
        ),
    )
    op.add_column(
        "users",
        sa.Column("messenger_restriction_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("messenger_restriction_expires_at", sa.DateTime(), nullable=True),
    )

    # Create index for restriction lookups
    op.create_index(
        "idx_users_messenger_restriction", "users", ["messenger_restriction"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_users_messenger_restriction", table_name="users")
    op.drop_index("idx_reports_created", table_name="reports")
    op.drop_index("idx_reports_status", table_name="reports")
    op.drop_index("idx_reports_reported_user", table_name="reports")
    op.drop_index("idx_reports_reporter", table_name="reports")
    op.drop_index("idx_moderation_logs_created", table_name="moderation_logs")
    op.drop_index("idx_moderation_logs_target", table_name="moderation_logs")
    op.drop_index("idx_moderation_logs_admin", table_name="moderation_logs")

    # Drop columns from users
    op.drop_column("users", "messenger_restriction_expires_at")
    op.drop_column("users", "messenger_restriction_reason")
    op.drop_column("users", "messenger_restriction")

    # Drop tables
    op.drop_table("reports")
    op.drop_table("moderation_logs")
