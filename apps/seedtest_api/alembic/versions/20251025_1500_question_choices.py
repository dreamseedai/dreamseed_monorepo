"""
Create question_choices table with constraints and indexes

- Table: question_choices
  - choice_id BIGSERIAL PK
  - question_id TEXT FK -> questions(id) ON DELETE CASCADE
  - sort_order SMALLINT NOT NULL
  - content TEXT NOT NULL CHECK (length(btrim(content)) > 0)
  - is_correct BOOLEAN NOT NULL DEFAULT false
- Unique (question_id, sort_order)
- Unique partial index for single correct choice (PostgreSQL): WHERE is_correct = true
- Read-order index on (question_id, sort_order)
- Optional backfill from questions.options/answer for PostgreSQL

Revision ID: 20251025_1500_question_choices
Revises: 20251025_1400_questions_perf_indexes
Create Date: 2025-10-25 15:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251025_1500_question_choices"
down_revision = "20251025_1400_questions_perf_indexes"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    # Create table
    op.create_table(
        "question_choices",
        sa.Column("choice_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
    )

    # Constraints and indexes
    try:
        op.create_unique_constraint(
            "uq_question_choice_order",
            "question_choices",
            ["question_id", "sort_order"],
        )
    except Exception:
        pass

    try:
        op.create_check_constraint(
            "chk_choice_content_nonempty",
            "question_choices",
            sa.text("length(btrim(content)) > 0"),
        )
    except Exception:
        pass

    try:
        op.create_index(
            "ix_question_choices_qid_order",
            "question_choices",
            ["question_id", "sort_order"],
            unique=False,
        )
    except Exception:
        pass

    # PostgreSQL-specific: partial unique index to allow at most one correct choice per question
    if dialect == "postgresql":
        try:
            op.execute(sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_correct_choice_once ON question_choices (question_id) WHERE is_correct = true"
            ))
        except Exception:
            pass

        # Optional backfill from questions.options/answer when present
        # Uses json_array_elements_text WITH ORDINALITY to extract options preserving order
        try:
            op.execute(sa.text(
                """
                INSERT INTO question_choices (question_id, sort_order, content, is_correct)
                SELECT q.id AS question_id,
                       (t.ord - 1)::smallint AS sort_order,
                       t.elem AS content,
                       CASE WHEN q.answer = (t.ord - 1) THEN true ELSE false END AS is_correct
                FROM (
                    SELECT id, answer, options FROM questions
                    WHERE options IS NOT NULL
                ) AS q,
                LATERAL json_array_elements_text(q.options) WITH ORDINALITY AS t(elem, ord)
                ON CONFLICT (question_id, sort_order) DO NOTHING
                """
            ))
        except Exception:
            # If options column/type or json funcs are not available, skip backfill silently
            pass


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    if dialect == "postgresql":
        try:
            op.execute(sa.text("DROP INDEX IF EXISTS uq_correct_choice_once"))
        except Exception:
            pass

    try:
        op.drop_index("ix_question_choices_qid_order", table_name="question_choices")
    except Exception:
        pass

    try:
        op.drop_constraint("chk_choice_content_nonempty", "question_choices", type_="check")
    except Exception:
        pass

    try:
        op.drop_constraint("uq_question_choice_order", "question_choices", type_="unique")
    except Exception:
        pass

    try:
        op.drop_table("question_choices")
    except Exception:
        pass
