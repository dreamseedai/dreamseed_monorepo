"""postgres-only partial index on updated_at where status <> 'deleted'

Revision ID: 20251025_0003
Revises: 20251025_0002
Create Date: 2025-10-25

"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251025_0003"
down_revision = "20251025_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_questions_updated_at_not_deleted\n"
                "  ON questions (updated_at DESC)\n"
                "  WHERE status <> 'deleted'"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(text("DROP INDEX IF EXISTS ix_questions_updated_at_not_deleted"))
