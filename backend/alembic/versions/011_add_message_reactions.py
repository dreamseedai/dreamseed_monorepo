"""add message reactions

Revision ID: 011_add_message_reactions
Revises: 010_add_message_threading
Create Date: 2025-11-26 11:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "011_add_message_reactions"
down_revision = "010_add_message_threading"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create message_reactions table
    op.create_table(
        "message_reactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("emoji", sa.String(50), nullable=False),
        sa.Column("emoji_unicode", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # Foreign keys
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # Unique constraint: one emoji per user per message
        sa.UniqueConstraint(
            "message_id", "user_id", "emoji", name="uq_message_user_emoji"
        ),
    )

    # Create indexes for efficient queries
    op.create_index(
        "ix_message_reactions_message_id",
        "message_reactions",
        ["message_id"],
        unique=False,
    )

    op.create_index(
        "ix_message_reactions_user_id", "message_reactions", ["user_id"], unique=False
    )

    op.create_index(
        "ix_message_reactions_emoji", "message_reactions", ["emoji"], unique=False
    )

    # Composite index for message + emoji (for counting)
    op.create_index(
        "ix_message_reactions_message_emoji",
        "message_reactions",
        ["message_id", "emoji"],
        unique=False,
    )

    # Add reaction_count column to messages table
    op.add_column(
        "messages",
        sa.Column("reaction_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # Create index on reaction_count for finding popular messages
    op.create_index(
        "ix_messages_reaction_count", "messages", ["reaction_count"], unique=False
    )

    # Create materialized view for reaction summaries (optional optimization)
    op.execute(
        """
        CREATE MATERIALIZED VIEW message_reaction_summaries AS
        SELECT 
            message_id,
            emoji,
            COUNT(*) as reaction_count,
            ARRAY_AGG(user_id) as user_ids,
            MAX(created_at) as latest_reaction_at
        FROM message_reactions
        GROUP BY message_id, emoji;
        
        CREATE INDEX ix_reaction_summaries_message ON message_reaction_summaries(message_id);
        CREATE INDEX ix_reaction_summaries_emoji ON message_reaction_summaries(emoji);
        CREATE INDEX ix_reaction_summaries_count ON message_reaction_summaries(reaction_count DESC);
    """
    )

    # Create function to update message reaction_count
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_message_reaction_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE messages 
                SET reaction_count = reaction_count + 1
                WHERE id = NEW.message_id;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE messages 
                SET reaction_count = GREATEST(reaction_count - 1, 0)
                WHERE id = OLD.message_id;
                RETURN OLD;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trigger_update_reaction_count
        AFTER INSERT OR DELETE ON message_reactions
        FOR EACH ROW
        EXECUTE FUNCTION update_message_reaction_count();
    """
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_reaction_count ON message_reactions;"
    )
    op.execute("DROP FUNCTION IF EXISTS update_message_reaction_count();")

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS message_reaction_summaries;")

    # Drop indexes
    op.drop_index("ix_messages_reaction_count", table_name="messages")
    op.drop_index("ix_message_reactions_message_emoji", table_name="message_reactions")
    op.drop_index("ix_message_reactions_emoji", table_name="message_reactions")
    op.drop_index("ix_message_reactions_user_id", table_name="message_reactions")
    op.drop_index("ix_message_reactions_message_id", table_name="message_reactions")

    # Drop reaction_count column from messages
    op.drop_column("messages", "reaction_count")

    # Drop table
    op.drop_table("message_reactions")
