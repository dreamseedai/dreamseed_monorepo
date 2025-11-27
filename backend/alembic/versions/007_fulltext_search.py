"""add_fulltext_search_indexes

Revision ID: 007_fulltext_search
Revises: 006_device_tokens
Create Date: 2024-01-15 16:00:00.000000

Add PostgreSQL full-text search indexes for message content.
Enables fast text search with relevance ranking.
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_fulltext_search"
down_revision: Union[str, None] = "006_device_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tsvector column for full-text search
    op.execute(
        """
        ALTER TABLE messages
        ADD COLUMN content_tsv tsvector
        GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED;
    """
    )

    # Create GIN index for full-text search
    op.create_index(
        "idx_messages_content_tsv", "messages", ["content_tsv"], postgresql_using="gin"
    )

    # Create index for conversation title search
    op.create_index(
        "idx_conversations_title",
        "conversations",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )

    # Create index for user search
    op.create_index(
        "idx_users_username",
        "users",
        ["username"],
        postgresql_using="gin",
        postgresql_ops={"username": "gin_trgm_ops"},
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_users_username", table_name="users")
    op.drop_index("idx_conversations_title", table_name="conversations")
    op.drop_index("idx_messages_content_tsv", table_name="messages")

    # Drop tsvector column
    op.execute("ALTER TABLE messages DROP COLUMN content_tsv;")
