"""add message threading

Revision ID: 010_add_message_threading
Revises: 009_notification_tables
Create Date: 2025-11-26 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "010_add_message_threading"
down_revision = "009_notification_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add threading columns to messages table
    op.add_column(
        "messages", sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "messages", sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "messages",
        sa.Column("reply_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("messages", sa.Column("last_reply_at", sa.DateTime(), nullable=True))

    # Add foreign key constraint for parent_id (self-referential)
    op.create_foreign_key(
        "fk_messages_parent_id",
        "messages",
        "messages",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add foreign key constraint for thread_id (references root message)
    op.create_foreign_key(
        "fk_messages_thread_id",
        "messages",
        "messages",
        ["thread_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create indexes for efficient thread queries
    op.create_index("ix_messages_parent_id", "messages", ["parent_id"], unique=False)

    op.create_index("ix_messages_thread_id", "messages", ["thread_id"], unique=False)

    # Index for finding threads with most replies (hot threads)
    op.create_index(
        "ix_messages_reply_count", "messages", ["reply_count"], unique=False
    )

    # Composite index for thread pagination
    op.create_index(
        "ix_messages_thread_id_created_at",
        "messages",
        ["thread_id", "created_at"],
        unique=False,
    )

    # Create materialized view for thread summaries (optional optimization)
    op.execute(
        """
        CREATE MATERIALIZED VIEW thread_summaries AS
        SELECT 
            m.id as thread_id,
            m.conversation_id,
            m.sender_id,
            m.content,
            m.created_at as thread_created_at,
            m.reply_count,
            m.last_reply_at,
            COUNT(DISTINCT r.sender_id) as unique_participants,
            MAX(r.created_at) as latest_reply_at
        FROM messages m
        LEFT JOIN messages r ON r.thread_id = m.id
        WHERE m.thread_id IS NULL
        GROUP BY m.id, m.conversation_id, m.sender_id, m.content, m.created_at, m.reply_count, m.last_reply_at;
        
        CREATE UNIQUE INDEX ix_thread_summaries_thread_id ON thread_summaries(thread_id);
        CREATE INDEX ix_thread_summaries_conversation_id ON thread_summaries(conversation_id);
        CREATE INDEX ix_thread_summaries_reply_count ON thread_summaries(reply_count DESC);
    """
    )


def downgrade() -> None:
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS thread_summaries;")

    # Drop indexes
    op.drop_index("ix_messages_thread_id_created_at", table_name="messages")
    op.drop_index("ix_messages_reply_count", table_name="messages")
    op.drop_index("ix_messages_thread_id", table_name="messages")
    op.drop_index("ix_messages_parent_id", table_name="messages")

    # Drop foreign keys
    op.drop_constraint("fk_messages_thread_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_messages_parent_id", "messages", type_="foreignkey")

    # Drop columns
    op.drop_column("messages", "last_reply_at")
    op.drop_column("messages", "reply_count")
    op.drop_column("messages", "thread_id")
    op.drop_column("messages", "parent_id")
