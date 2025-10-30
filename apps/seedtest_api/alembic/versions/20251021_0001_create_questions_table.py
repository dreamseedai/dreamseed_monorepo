"""Create questions table

Revision ID: 20251021_0001_create_questions_table
Revises: 
Create Date: 2025-10-21 00:01:00

"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

# revision identifiers, used by Alembic.
revision = "2025102100001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create questions table
    op.create_table(
        "questions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("options", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("answer", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False, server_default=sa.text("'easy'")),
        sa.Column("topic", sa.String(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("author", sa.String(), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("discrimination", sa.Numeric(), nullable=True),
        sa.Column("guessing", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("questions")

