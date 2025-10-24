"""create exam_results table

Revision ID: 20251021_1010_exam_results_table
Revises: 20251021_0004_tags_column
Create Date: 2025-10-21 10:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251021_1010_exam_results_table'
down_revision = '20251021_0004_tags_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgcrypto extension for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        'exam_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.Text(), nullable=False, unique=True),
    sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('exam_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('score_raw', sa.Numeric(), nullable=True),
        sa.Column('score_scaled', sa.Numeric(), nullable=True),
        sa.Column('standard_error', sa.Numeric(), nullable=True),
        sa.Column('percentile', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_exam_results_session_id', 'exam_results', ['session_id'], unique=True)
    op.create_index('ix_exam_results_result_json', 'exam_results', ['result_json'], postgresql_using='gin')
    op.create_index('ix_exam_results_user_exam', 'exam_results', ['user_id', 'exam_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_exam_results_user_exam', table_name='exam_results')
    op.drop_index('ix_exam_results_result_json', table_name='exam_results')
    op.drop_index('ix_exam_results_session_id', table_name='exam_results')
    op.drop_table('exam_results')
