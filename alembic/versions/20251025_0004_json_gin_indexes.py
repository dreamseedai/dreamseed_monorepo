"""postgres-only GIN indexes on tags/options JSON

Revision ID: 20251025_0004
Revises: 20251025_0003
Create Date: 2025-10-25

"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251025_0004"
down_revision = "20251025_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Ensure GIN is available (default in Postgres)
        op.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_questions_tags_gin ON questions USING GIN ((tags::jsonb))"
            )
        )
        op.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_questions_options_gin ON questions USING GIN ((options::jsonb))"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(text("DROP INDEX IF EXISTS ix_questions_options_gin"))
        op.execute(text("DROP INDEX IF EXISTS ix_questions_tags_gin"))
