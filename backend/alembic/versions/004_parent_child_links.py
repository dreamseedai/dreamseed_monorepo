"""Add parent_child_links table for Week 4

Revision ID: 004_parent_child_links
Revises: 2025_11_25_01_week3_exam_models
Create Date: 2025-11-25 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_parent_child_links"
down_revision: Union[str, None] = "2025_11_25_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create parent_child_links table"""
    op.create_table(
        "parent_child_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["users.id"],
            name="fk_parent_child_links_parent_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["child_id"],
            ["users.id"],
            name="fk_parent_child_links_child_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_parent_child_links"),
        sa.UniqueConstraint("parent_id", "child_id", name="uq_parent_child_link"),
    )

    # Create indexes for faster lookups
    op.create_index(
        "ix_parent_child_links_parent_id",
        "parent_child_links",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        "ix_parent_child_links_child_id",
        "parent_child_links",
        ["child_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop parent_child_links table"""
    op.drop_index("ix_parent_child_links_child_id", table_name="parent_child_links")
    op.drop_index("ix_parent_child_links_parent_id", table_name="parent_child_links")
    op.drop_table("parent_child_links")
