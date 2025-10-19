"""
RLS backfill org_id and indexes

Revision ID: 20250101_0007
Revises: 20250101_0006
Create Date: 2025-01-01 00:07:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250101_0007'
down_revision = '20250101_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # backfill org_id on responses from attempts
    op.add_column('responses', sa.Column('org_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE responses r
        SET org_id = a.org_id
        FROM attempts a
        WHERE r.attempt_id = a.id
          AND (r.org_id IS NULL OR r.org_id <> a.org_id);
        """
    )
    # indexes
    op.create_index('idx_attempts_org_id', 'attempts', ['org_id'], if_not_exists=True)
    op.create_index('idx_responses_org_id', 'responses', ['org_id'], if_not_exists=True)
    op.create_index('idx_item_bank_owner', 'item_bank', ['owner_org_id'], if_not_exists=True)


def downgrade() -> None:
    op.drop_index('idx_item_bank_owner', table_name='item_bank')
    op.drop_index('idx_responses_org_id', table_name='responses')
    op.drop_index('idx_attempts_org_id', table_name='attempts')
    op.drop_column('responses', 'org_id')
