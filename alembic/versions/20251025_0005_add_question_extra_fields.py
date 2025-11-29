"""add title/explanation/discrimination/guessing to questions

Revision ID: 20251025_0005
Revises: 20251025_0004
Create Date: 2025-10-25

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251025_0005"
down_revision = "20251025_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.add_column(sa.Column("title", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("explanation", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("discrimination", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("guessing", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.drop_column("guessing")
        batch_op.drop_column("discrimination")
        batch_op.drop_column("explanation")
        batch_op.drop_column("title")
