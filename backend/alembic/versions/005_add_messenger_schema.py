"""Add messenger schema: conversations, conversation_participants, messages, read_receipts, notification_settings

Revision ID: 005_add_messenger_schema
Revises: 004_parent_child_links
Create Date: 2025-11-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_add_messenger_schema"
down_revision: Union[str, None] = "004_parent_child_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create messenger schema tables with proper constraints and indexes."""
    # Ensure pgcrypto extension is available for gen_random_uuid()
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 1. Create conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column(
            "zone_id",
            sa.Integer,
            sa.ForeignKey("zones.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "org_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "created_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.CheckConstraint(
            "type IN ('direct', 'group', 'announcement')", name="ck_conversations_type"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Add index on zone_id, org_id for conversations (for querying by zone/org)
    op.create_index(
        "idx_conversations_zone_org", "conversations", ["zone_id", "org_id"]
    )

    # 2. Create conversation_participants table
    op.create_table(
        "conversation_participants",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "joined_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("NOW()")
        ),
        sa.Column("last_read_at", sa.TIMESTAMP(timezone=False)),
        sa.CheckConstraint(
            "role IN ('admin', 'member', 'observer')", name="ck_participants_role"
        ),
        sa.UniqueConstraint(
            "conversation_id", "user_id", name="uq_conversation_participant"
        ),
    )
    op.create_index("idx_participants_user", "conversation_participants", ["user_id"])
    op.create_index(
        "idx_participants_conversation",
        "conversation_participants",
        ["conversation_id"],
    )

    # 3. Create messages table
    op.create_table(
        "messages",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "sender_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("content", sa.Text),
        sa.Column("message_type", sa.String(20), nullable=False),
        sa.Column("file_url", sa.Text),
        sa.Column("file_size", sa.Integer),
        sa.Column("file_name", sa.String(255)),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("NOW()")
        ),
        sa.Column("edited_at", sa.TIMESTAMP(timezone=False)),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=False)),
        sa.CheckConstraint(
            "message_type IN ('text', 'image', 'file', 'system')",
            name="ck_messages_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
    )
    op.create_index("idx_messages_sender", "messages", ["sender_id"])
    # Partial index for undeleted messages (deleted_at IS NULL)
    op.create_index(
        "idx_messages_deleted",
        "messages",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # 4. Create read_receipts table
    op.create_table(
        "read_receipts",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "message_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "read_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("NOW()")
        ),
        sa.UniqueConstraint("message_id", "user_id", name="uq_read_receipt"),
    )
    op.create_index("idx_read_receipts_message", "read_receipts", ["message_id"])
    op.create_index("idx_read_receipts_user", "read_receipts", ["user_id"])

    # 5. Create notification_settings table
    op.create_table(
        "notification_settings",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
        ),
        sa.Column("muted", sa.Boolean, server_default=sa.text("FALSE")),
        sa.Column("push_enabled", sa.Boolean, server_default=sa.text("TRUE")),
        sa.Column("email_enabled", sa.Boolean, server_default=sa.text("TRUE")),
        sa.UniqueConstraint(
            "user_id", "conversation_id", name="uq_notification_setting"
        ),
    )


def downgrade() -> None:
    """Drop messenger schema tables in reverse order."""
    # Drop tables in reverse order of creation to maintain FK integrity
    op.drop_table("notification_settings")
    op.drop_index("idx_read_receipts_user", table_name="read_receipts")
    op.drop_index("idx_read_receipts_message", table_name="read_receipts")
    op.drop_table("read_receipts")
    op.drop_index("idx_messages_deleted", table_name="messages")
    op.drop_index("idx_messages_sender", table_name="messages")
    op.drop_index("idx_messages_conversation_created", table_name="messages")
    op.drop_table("messages")
    op.drop_index(
        "idx_participants_conversation", table_name="conversation_participants"
    )
    op.drop_index("idx_participants_user", table_name="conversation_participants")
    op.drop_table("conversation_participants")
    op.drop_index("idx_conversations_zone_org", table_name="conversations")
    op.drop_table("conversations")
