"""add_device_tokens_table

Revision ID: 006_device_tokens
Revises: 005_add_messenger_schema
Create Date: 2024-01-15 15:00:00.000000

Add device_tokens table for push notification device registration.
Supports FCM, APNs, and Web Push.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006_device_tokens"
down_revision: Union[str, None] = "005_add_messenger_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create device_tokens table
    op.create_table(
        "device_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_device_tokens"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_device_tokens_user_id",
        ),
        sa.UniqueConstraint("token", name="uq_device_token"),
        sa.CheckConstraint(
            "platform IN ('ios', 'android', 'web')", name="ck_device_tokens_platform"
        ),
        sa.CheckConstraint(
            "provider IN ('fcm', 'apns', 'web_push')", name="ck_device_tokens_provider"
        ),
    )

    # Create indexes for efficient lookups
    op.create_index("idx_device_tokens_user", "device_tokens", ["user_id"])
    op.create_index(
        "idx_device_tokens_user_active", "device_tokens", ["user_id", "is_active"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_device_tokens_user_active", table_name="device_tokens")
    op.drop_index("idx_device_tokens_user", table_name="device_tokens")

    # Drop table
    op.drop_table("device_tokens")
