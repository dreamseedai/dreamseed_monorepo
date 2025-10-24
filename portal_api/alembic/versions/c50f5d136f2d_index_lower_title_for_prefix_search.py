"""index lower(title) for prefix search

Revision ID: c50f5d136f2d
Revises: e4d76eef2dcf
Create Date: 2025-09-25 00:02:54.941626

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c50f5d136f2d"
down_revision: Union[str, None] = "e4d76eef2dcf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_lower_title ON content (LOWER(title));"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_content_lower_title;")
