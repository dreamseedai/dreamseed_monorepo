"""Add question table with meta JSONB for IRT parameters

Revision ID: 20251031_2100_question_table
Revises: 20251031_2000_session_user_org
Create Date: 2025-10-31 21:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "20251031_2100_question_table"
down_revision = "20251031_2000_session_user_org"
branch_labels = None
depends_on = None


def _table_exists(conn: Connection, name: str) -> bool:
    insp = inspect(conn)
    return insp.has_table(name)


def _column_exists(conn: Connection, table: str, column: str) -> bool:
    insp = inspect(conn)
    cols = [c.get("name") for c in insp.get_columns(table)]
    return column in cols


def _index_exists(conn: Connection, index_name: str) -> bool:
    insp = inspect(conn)
    # Check all tables for the index
    for table_name in insp.get_table_names():
        indexes = insp.get_indexes(table_name)
        if any(idx["name"] == index_name for idx in indexes):
            return True
    return False


def upgrade() -> None:
    conn = op.get_bind()

    # Create question table if it doesn't exist
    if not _table_exists(conn, "question"):
        op.create_table(
            "question",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("difficulty", sa.Numeric(), nullable=True),
            sa.Column("topic_id", sa.Text(), nullable=True),
            sa.Column(
                "meta", JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # Create GIN index on meta for efficient JSON queries
        op.create_index(
            "ix_question_meta_gin",
            "question",
            ["meta"],
            postgresql_using="gin",
        )

        # Create index on topic_id for filtering
        op.create_index(
            "ix_question_topic_id",
            "question",
            ["topic_id"],
        )
    else:
        # If table exists, ensure meta column exists
        if not _column_exists(conn, "question", "meta"):
            op.add_column(
                "question",
                sa.Column(
                    "meta",
                    JSONB(),
                    nullable=True,
                    server_default=sa.text("'{}'::jsonb"),
                ),
            )

            # Add GIN index if not exists
            if not _index_exists(conn, "ix_question_meta_gin"):
                op.create_index(
                    "ix_question_meta_gin",
                    "question",
                    ["meta"],
                    postgresql_using="gin",
                )


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "question"):
        if _index_exists(conn, "ix_question_meta_gin"):
            op.drop_index("ix_question_meta_gin", table_name="question")

        if _index_exists(conn, "ix_question_topic_id"):
            op.drop_index("ix_question_topic_id", table_name="question")

        op.drop_table("question")
