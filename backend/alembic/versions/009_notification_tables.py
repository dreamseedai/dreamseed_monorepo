"""add_notification_tables

Revision ID: 009_notification_tables
Revises: 008_moderation_tables
Create Date: 2025-11-26 14:00:00.000000

Add in_app_notifications and notification_preferences tables for enhanced notification system.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "009_notification_tables"
down_revision: Union[str, None] = "008_moderation_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create in_app_notifications table
    op.create_table(
        "in_app_notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("action_url", sa.String(length=500), nullable=True),
        sa.Column(
            "priority", sa.String(length=20), nullable=False, server_default="normal"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for in_app_notifications
    op.create_index("idx_notifications_user", "in_app_notifications", ["user_id"])
    op.create_index(
        "idx_notifications_unread", "in_app_notifications", ["user_id", "is_read"]
    )
    op.create_index("idx_notifications_created", "in_app_notifications", ["created_at"])
    op.create_index("idx_notifications_type", "in_app_notifications", ["type"])

    # Create notification_preferences table
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "channel", sa.String(length=20), nullable=False
        ),  # push, email, in_app
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "channel", "notification_type", name="uq_user_channel_type"
        ),
    )

    # Create indexes for notification_preferences
    op.create_index("idx_preferences_user", "notification_preferences", ["user_id"])
    op.create_index(
        "idx_preferences_lookup",
        "notification_preferences",
        ["user_id", "channel", "notification_type"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_preferences_lookup", table_name="notification_preferences")
    op.drop_index("idx_preferences_user", table_name="notification_preferences")
    op.drop_index("idx_notifications_type", table_name="in_app_notifications")
    op.drop_index("idx_notifications_created", table_name="in_app_notifications")
    op.drop_index("idx_notifications_unread", table_name="in_app_notifications")
    op.drop_index("idx_notifications_user", table_name="in_app_notifications")

    # Drop tables
    op.drop_table("notification_preferences")
    op.drop_table("in_app_notifications")
