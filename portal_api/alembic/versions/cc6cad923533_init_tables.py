"""init tables

Revision ID: cc6cad923533
Revises: 
Create Date: 2025-09-24 22:19:44.947823

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc6cad923533"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("role", sa.String(length=32), server_default="user", nullable=False),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # users_profile
    op.create_table(
        "users_profile",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(length=8), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("grade_code", sa.String(length=16), nullable=True),
        sa.Column("goal", sa.String(length=64), nullable=True),
        sa.Column("subscribed", sa.Boolean(), nullable=False),
    )
    op.create_index(
        op.f("ix_users_profile_user_id"), "users_profile", ["user_id"], unique=True
    )

    # content
    op.create_table(
        "content",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("doc", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # attempts
    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "content_id",
            sa.Integer(),
            sa.ForeignKey("content.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_attempts_user_id"), "attempts", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_attempts_content_id"), "attempts", ["content_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_attempts_content_id"), table_name="attempts")
    op.drop_index(op.f("ix_attempts_user_id"), table_name="attempts")
    op.drop_table("attempts")

    op.drop_table("content")

    op.drop_index(op.f("ix_users_profile_user_id"), table_name="users_profile")
    op.drop_table("users_profile")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
