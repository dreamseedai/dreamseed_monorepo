"""Create users table with conditional logic

Revision ID: 000_create_users_table
Revises:
Create Date: 2025-11-28 12:10:00.000000

This migration creates the users table that was missing from the initial schema.
It uses conditional logic to safely handle existing production databases.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "000_create_users_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table if it doesn't exist (production-safe)."""
    bind = op.get_bind()
    inspector = inspect(bind)

    if "users" not in inspector.get_table_names():
        # Create users table matching the User model in backend/app/models/user.py
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("full_name", sa.String(100), nullable=True),
            sa.Column("role", sa.String(20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
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
        )

        # Create indices
        op.create_index("ix_users_id", "users", ["id"], unique=False)
        op.create_index("ix_users_email", "users", ["email"], unique=True)
        op.create_index("ix_users_role", "users", ["role"], unique=False)


def downgrade() -> None:
    """Drop users table and indices."""
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
