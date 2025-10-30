"""
Add performance indexes for questions table

- BTREE indexes: topic, difficulty, status, updated_at
- Optional: pg_trgm extension and GIN trigram index on stem (PostgreSQL only)

Revision ID: 20251025_1400_questions_perf_indexes
Revises: 20251025_1200_questions_add_org_id
Create Date: 2025-10-25 14:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251025_1400_questions_perf_indexes"
down_revision = "20251025_1200_questions_add_org_id"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    if dialect == "postgresql":
        # Create basic BTREE indexes
        statements = [
            "CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions (topic)",
            "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions (difficulty)",
            "CREATE INDEX IF NOT EXISTS idx_questions_status ON questions (status)",
            "CREATE INDEX IF NOT EXISTS idx_questions_updated_at ON questions (updated_at)",
        ]
        for sql in statements:
            try:
                op.execute(sa.text(sql))
            except Exception:
                # Best-effort; continue if already exists or other non-fatal error
                pass
        # Try to enable pg_trgm and add trigram index on stem
        try:
            op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_questions_stem_trgm ON questions USING GIN (stem gin_trgm_ops)"))
        except Exception:
            # Extension might be unavailable; skip
            pass
    else:
        # SQLite / others: create simple indexes if possible
        stmts = [
            "CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions (topic)",
            "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions (difficulty)",
            "CREATE INDEX IF NOT EXISTS idx_questions_status ON questions (status)",
            "CREATE INDEX IF NOT EXISTS idx_questions_updated_at ON questions (updated_at)",
        ]
        for sql in stmts:
            try:
                op.execute(sa.text(sql))
            except Exception:
                pass


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    if dialect == "postgresql":
        for name in [
            "idx_questions_stem_trgm",
            "idx_questions_updated_at",
            "idx_questions_status",
            "idx_questions_difficulty",
            "idx_questions_topic",
        ]:
            try:
                op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
            except Exception:
                pass
    else:
        for name in [
            "idx_questions_updated_at",
            "idx_questions_status",
            "idx_questions_difficulty",
            "idx_questions_topic",
        ]:
            try:
                op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
            except Exception:
                pass
