"""Add user_id and org_id to session table

Revision ID: 20251031_2000_session_user_org
Revises: 20251031_1600_minimal_schema_tables
Create Date: 2025-10-31 20:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "20251031_2000_session_user_org"
down_revision = "20251031_1600_minimal_schema_tables"
branch_labels = None
depends_on = None


def _column_exists(conn: Connection, table: str, column: str) -> bool:
    insp = inspect(conn)
    cols = [c.get("name") for c in insp.get_columns(table)]
    return column in cols


def _table_exists(conn: Connection, name: str) -> bool:
    insp = inspect(conn)
    return insp.has_table(name)


def upgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "session"):
        if not _column_exists(conn, "session", "user_id"):
            op.add_column("session", sa.Column("user_id", sa.Text(), nullable=True))
            try:
                op.create_index("ix_session_user_id", "session", ["user_id"])  # type: ignore
            except Exception:
                pass
        if not _column_exists(conn, "session", "org_id"):
            op.add_column("session", sa.Column("org_id", sa.Integer(), nullable=True))
            try:
                op.create_index("ix_session_org_id", "session", ["org_id"])  # type: ignore
            except Exception:
                pass


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "session"):
        if _column_exists(conn, "session", "org_id"):
            try:
                op.drop_index("ix_session_org_id", table_name="session")
            except Exception:
                pass
            op.drop_column("session", "org_id")
        if _column_exists(conn, "session", "user_id"):
            try:
                op.drop_index("ix_session_user_id", table_name="session")
            except Exception:
                pass
            op.drop_column("session", "user_id")
