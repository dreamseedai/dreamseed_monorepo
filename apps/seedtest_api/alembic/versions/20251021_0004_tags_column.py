from alembic import op, context
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision = '20251021_0004_tags_column'
down_revision = '20251021_0003_seed_data'
branch_labels = None
depends_on = None


def upgrade():
    # Determine tags kind from -x tags_kind=... or env ALEMBIC_TAGS_KIND
    x = context.get_x_argument(as_dictionary=True)
    raw = x.get('tags_kind', os.getenv('ALEMBIC_TAGS_KIND', '')).lower()
    if raw in ('text', 'text[]', 'array'):
        kind = 'text[]'
    else:
        kind = 'jsonb'

    if kind == 'text[]':
        op.add_column('questions', sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True))
        # Recommended GIN index for text[]
        op.execute("CREATE INDEX IF NOT EXISTS idx_questions_tags_gin ON questions USING GIN (tags);")
    else:
        op.add_column('questions', sa.Column('tags', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        # Recommended GIN index for jsonb '?|' queries
        op.execute("CREATE INDEX IF NOT EXISTS idx_questions_tags_gin ON questions USING GIN (tags);")


def downgrade():
    op.drop_index('idx_questions_tags_gin', table_name='questions', if_exists=True)
    op.drop_column('questions', 'tags')
