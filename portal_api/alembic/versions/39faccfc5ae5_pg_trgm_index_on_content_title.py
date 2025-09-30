"""pg_trgm index on content.title

Revision ID: 39faccfc5ae5
Revises: c50f5d136f2d
Create Date: 2025-09-25 00:05:49.935635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39faccfc5ae5'
down_revision: Union[str, None] = 'c50f5d136f2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_title_trgm ON content USING GIN (title gin_trgm_ops);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_content_title_trgm;")
