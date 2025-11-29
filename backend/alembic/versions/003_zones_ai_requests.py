"""Add zones and ai_requests tables

Revision ID: 003_zones_ai_requests
Revises: 002_core_entities
Create Date: 2025-11-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "003_zones_ai_requests"
down_revision = "002_core_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) zones - Hierarchical content organization
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("zones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("zone_type", sa.String(length=50), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=True),
        sa.Column("meta", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_zones_id", "zones", ["id"], unique=False)
    op.create_index("ix_zones_parent_id", "zones", ["parent_id"], unique=False)
    op.create_index("ix_zones_level", "zones", ["level"], unique=False)
    op.create_index("ix_zones_name", "zones", ["name"], unique=False)
    op.create_index("ix_zones_code", "zones", ["code"], unique=True)

    # 2) ai_requests - AI API call tracking
    op.create_table(
        "ai_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("session_id", sa.BigInteger(), nullable=True),
        sa.Column("request_type", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("meta", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_requests_id", "ai_requests", ["id"], unique=False)
    op.create_index("ix_ai_requests_user_id", "ai_requests", ["user_id"], unique=False)
    op.create_index(
        "ix_ai_requests_student_id", "ai_requests", ["student_id"], unique=False
    )
    op.create_index(
        "ix_ai_requests_session_id", "ai_requests", ["session_id"], unique=False
    )
    op.create_index(
        "ix_ai_requests_request_type", "ai_requests", ["request_type"], unique=False
    )
    op.create_index("ix_ai_requests_model", "ai_requests", ["model"], unique=False)
    op.create_index(
        "ix_ai_requests_created_at", "ai_requests", ["created_at"], unique=False
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_index("ix_ai_requests_created_at", table_name="ai_requests")
    op.drop_index("ix_ai_requests_model", table_name="ai_requests")
    op.drop_index("ix_ai_requests_request_type", table_name="ai_requests")
    op.drop_index("ix_ai_requests_session_id", table_name="ai_requests")
    op.drop_index("ix_ai_requests_student_id", table_name="ai_requests")
    op.drop_index("ix_ai_requests_user_id", table_name="ai_requests")
    op.drop_index("ix_ai_requests_id", table_name="ai_requests")
    op.drop_table("ai_requests")

    op.drop_index("ix_zones_code", table_name="zones")
    op.drop_index("ix_zones_name", table_name="zones")
    op.drop_index("ix_zones_level", table_name="zones")
    op.drop_index("ix_zones_parent_id", table_name="zones")
    op.drop_index("ix_zones_id", table_name="zones")
    op.drop_table("zones")
