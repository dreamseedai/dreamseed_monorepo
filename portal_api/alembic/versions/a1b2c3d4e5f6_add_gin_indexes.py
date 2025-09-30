"""add gin indexes on jsonb columns

Revision ID: a1b2c3d4e5f6
Revises: cc6cad923533
Create Date: 2025-09-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "cc6cad923533"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF to_regclass('public.content') IS NOT NULL THEN
            CREATE INDEX IF NOT EXISTS ix_content_doc_gin ON content USING GIN (doc);
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
          IF to_regclass('public.attempts') IS NOT NULL THEN
            CREATE INDEX IF NOT EXISTS ix_attempts_response_gin ON attempts USING GIN (response);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_attempts_response_gin;")
    op.execute("DROP INDEX IF EXISTS ix_content_doc_gin;")


