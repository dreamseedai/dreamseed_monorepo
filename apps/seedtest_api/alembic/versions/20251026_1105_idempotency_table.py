"""
Create idempotency_records table

Revision ID: 20251026_1105_idempotency_table
Revises: 20251026_1010_exam_results_result_gin
Create Date: 2025-10-26 11:05:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251026_1105_idempotency_table"
down_revision = "20251026_1010_exam_results_result_gin"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_table(
            "idempotency_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("method", sa.Text(), nullable=False),
            sa.Column("path", sa.Text(), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=True),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.Text(), nullable=False),
            sa.Column("req_hash", sa.Text(), nullable=False),
            sa.Column("status_code", sa.Integer(), nullable=False),
            sa.Column("response_body", sa.Text(), nullable=False),
            sa.Column("response_headers", sa.Text(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        )
    except Exception:
        pass
    try:
        op.create_unique_constraint(
            "uq_idem_scope_key",
            "idempotency_records",
            ["method", "path", "user_id", "org_id", "idempotency_key"],
        )
    except Exception:
        pass


def downgrade():
    try:
        op.drop_constraint("uq_idem_scope_key", "idempotency_records", type_="unique")
    except Exception:
        pass
    try:
        op.drop_table("idempotency_records")
    except Exception:
        pass
