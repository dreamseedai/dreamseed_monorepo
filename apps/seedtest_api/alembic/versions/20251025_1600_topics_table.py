"""
Create topics table with hierarchy and org scoping

- Table: topics
  - id BIGSERIAL PRIMARY KEY
  - name TEXT NOT NULL
  - parent_topic_id BIGINT NULL REFERENCES topics(id) ON DELETE SET NULL ON UPDATE CASCADE
  - org_id INTEGER NULL  -- NULL means global topic, else org-scoped
- Uniqueness:
  - PostgreSQL: enforce uniqueness of lower(name) among global topics (org_id IS NULL)
    and uniqueness of (org_id, lower(name)) for org-scoped topics
  - Other dialects: fallback uniqueness on (org_id, name) (case-sensitive)
- Indexes: org_id, parent_topic_id, (org_id, parent_topic_id)
- Optional backfill: insert distinct questions.topic values as global topics

Revision ID: 20251025_1600_topics_table
Revises: 20251025_1500_question_choices
Create Date: 2025-10-25 16:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251025_1600_topics_table"
down_revision = "20251025_1500_question_choices"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    # Create topics table
    op.create_table(
        "topics",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("parent_topic_id", sa.BigInteger(), nullable=True),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_topic_id"], ["topics.id"], onupdate="CASCADE", ondelete="SET NULL"),
    )

    # Indexes
    try:
        op.create_index("ix_topics_org_id", "topics", ["org_id"], unique=False)
    except Exception:
        pass
    try:
        op.create_index("ix_topics_parent_topic_id", "topics", ["parent_topic_id"], unique=False)
    except Exception:
        pass
    try:
        op.create_index("ix_topics_org_parent", "topics", ["org_id", "parent_topic_id"], unique=False)
    except Exception:
        pass

    if dialect == "postgresql":
        # Case-insensitive uniqueness using lower(name)
        try:
            op.execute(sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_topics_global_name_ci ON topics (lower(name)) WHERE org_id IS NULL"
            ))
        except Exception:
            pass
        try:
            op.execute(sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_topics_org_name_ci ON topics (org_id, lower(name)) WHERE org_id IS NOT NULL"
            ))
        except Exception:
            pass
        # Optional backfill: distinct non-null, non-empty questions.topic into global topics
        try:
            op.execute(sa.text(
                """
                INSERT INTO topics (name)
                SELECT DISTINCT trim(topic) AS name
                FROM questions
                WHERE topic IS NOT NULL AND length(trim(topic)) > 0
                ON CONFLICT DO NOTHING
                """
            ))
        except Exception:
            pass
    else:
        # Fallback uniqueness (case-sensitive)
        try:
            op.create_unique_constraint("uq_topics_org_name", "topics", ["org_id", "name"])
        except Exception:
            pass
        # Best-effort backfill (SQL standard)
        try:
            op.execute(sa.text(
                """
                INSERT INTO topics (name)
                SELECT DISTINCT topic AS name
                FROM questions
                WHERE topic IS NOT NULL AND topic <> ''
                """
            ))
        except Exception:
            pass


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    if dialect == "postgresql":
        for name in [
            "uq_topics_org_name_ci",
            "uq_topics_global_name_ci",
        ]:
            try:
                op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
            except Exception:
                pass
    else:
        try:
            op.drop_constraint("uq_topics_org_name", "topics", type_="unique")
        except Exception:
            pass

    for idx in [
        "ix_topics_org_parent",
        "ix_topics_parent_topic_id",
        "ix_topics_org_id",
    ]:
        try:
            op.drop_index(idx, table_name="topics")
        except Exception:
            pass

    try:
        op.drop_table("topics")
    except Exception:
        pass
