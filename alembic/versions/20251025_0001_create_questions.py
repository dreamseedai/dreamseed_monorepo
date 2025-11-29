"""create questions table

Revision ID: 20251025_0001
Revises: 
Create Date: 2025-10-25

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251025_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'questions',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('stem', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('answer', sa.Integer(), nullable=False),
        sa.Column('difficulty', sa.Text(), nullable=False),
        sa.Column('topic', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('author', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_questions_status', 'questions', ['status'])


def downgrade() -> None:
    op.drop_index('ix_questions_status', table_name='questions')
    op.drop_table('questions')
