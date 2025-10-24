"""trgm index on content.doc text

Revision ID: 7a3805fbeab4
Revises: 39faccfc5ae5
Create Date: 2025-09-25 00:15:34.486977

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7a3805fbeab4'
down_revision: Union[str, None] = '39faccfc5ae5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_doc_trgm ON content USING GIN ((doc::text) gin_trgm_ops);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_content_doc_trgm;")
