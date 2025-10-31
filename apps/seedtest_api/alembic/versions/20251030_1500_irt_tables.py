"""Create IRT tables if not exist.

Revision ID: 20251030_1500_irt_tables
Revises: 20251030_1305_metrics_tables
Create Date: 2025-10-30 15:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "20251030_1500_irt_tables"
down_revision = "20251030_1400_metrics_tables"
branch_labels = None
depends_on = None


def table_exists(conn, name: str) -> bool:
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    conn = op.get_bind()

    if not table_exists(conn, "mirt_item_params"):
        op.create_table(
            "mirt_item_params",
            sa.Column("item_id", sa.Text, primary_key=True),
            sa.Column("model", sa.Text, nullable=True),
            sa.Column("params", psql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("version", sa.Text, nullable=True),
            sa.Column("fitted_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )

    if not table_exists(conn, "mirt_ability"):
        op.create_table(
            "mirt_ability",
            sa.Column("user_id", sa.Text, nullable=False),
            sa.Column("theta", sa.Float, nullable=False),
            sa.Column("se", sa.Float, nullable=True),
            sa.Column("model", sa.Text, nullable=True),
            sa.Column("version", sa.Text, nullable=True),
            sa.Column("fitted_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )
        op.create_primary_key("pk_mirt_ability_user_version", "mirt_ability", ["user_id", "version"])  # type: ignore
        op.create_index("ix_mirt_ability_user_fitted_at", "mirt_ability", ["user_id", "fitted_at"])  # type: ignore

    if not table_exists(conn, "mirt_fit_meta"):
        op.create_table(
            "mirt_fit_meta",
            sa.Column("run_id", sa.Text, primary_key=True),
            sa.Column("model_spec", psql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("metrics", psql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("fitted_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if table_exists(conn, "mirt_fit_meta"):
        op.drop_table("mirt_fit_meta")
    if table_exists(conn, "mirt_ability"):
        op.drop_index("ix_mirt_ability_user_fitted_at", table_name="mirt_ability")
        op.drop_constraint("pk_mirt_ability_user_version", "mirt_ability", type_="primary")  # type: ignore
        op.drop_table("mirt_ability")
    if table_exists(conn, "mirt_item_params"):
        op.drop_table("mirt_item_params")
