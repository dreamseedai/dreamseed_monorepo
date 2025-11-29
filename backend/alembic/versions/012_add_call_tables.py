"""add call tables

Revision ID: 012_add_call_tables
Revises: 011_add_message_reactions
Create Date: 2025-11-26 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "012_add_call_tables"
down_revision = "011_add_message_reactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create calls table
    op.create_table(
        "calls",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiator_id", sa.Integer(), nullable=False),
        sa.Column("call_type", sa.String(20), nullable=False),  # 'audio' or 'video'
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="initiated"
        ),  # initiated, ringing, active, ended, missed, rejected, failed
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "end_reason", sa.String(50), nullable=True
        ),  # completed, declined, no_answer, failed, timeout
        sa.Column("recording_url", sa.String(500), nullable=True),
        sa.Column("quality_rating", sa.Integer(), nullable=True),  # 1-5 stars
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["initiator_id"], ["users.id"], ondelete="CASCADE"),
        # Check constraints
        sa.CheckConstraint("call_type IN ('audio', 'video')", name="valid_call_type"),
        sa.CheckConstraint(
            "status IN ('initiated', 'ringing', 'active', 'ended', 'missed', 'rejected', 'failed')",
            name="valid_call_status",
        ),
        sa.CheckConstraint(
            "quality_rating IS NULL OR (quality_rating >= 1 AND quality_rating <= 5)",
            name="valid_quality_rating",
        ),
    )

    # Create call_participants table (many-to-many: calls <-> users)
    op.create_table(
        "call_participants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("is_initiator", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("answered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "video_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("audio_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "screen_share_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "connection_quality", sa.String(20), nullable=True
        ),  # excellent, good, fair, poor
        sa.Column("peer_id", sa.String(100), nullable=True),  # WebRTC peer identifier
        # Foreign keys
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # Unique constraint: one participation record per user per call
        sa.UniqueConstraint("call_id", "user_id", name="uq_call_participant"),
    )

    # Create indexes for efficient queries
    op.create_index("ix_calls_conversation_id", "calls", ["conversation_id"])
    op.create_index("ix_calls_initiator_id", "calls", ["initiator_id"])
    op.create_index("ix_calls_status", "calls", ["status"])
    op.create_index("ix_calls_started_at", "calls", ["started_at"])
    op.create_index("ix_calls_call_type", "calls", ["call_type"])

    op.create_index("ix_call_participants_call_id", "call_participants", ["call_id"])
    op.create_index("ix_call_participants_user_id", "call_participants", ["user_id"])
    op.create_index("ix_call_participants_answered", "call_participants", ["answered"])

    # Create composite index for active call queries
    op.create_index(
        "ix_calls_active",
        "calls",
        ["conversation_id", "status"],
        postgresql_where=sa.text("status IN ('initiated', 'ringing', 'active')"),
    )

    # Create materialized view for call statistics
    op.execute(
        """
        CREATE MATERIALIZED VIEW call_statistics AS
        SELECT 
            conversation_id,
            COUNT(*) as total_calls,
            COUNT(*) FILTER (WHERE status = 'ended') as completed_calls,
            COUNT(*) FILTER (WHERE status = 'missed') as missed_calls,
            COUNT(*) FILTER (WHERE status = 'rejected') as rejected_calls,
            COUNT(*) FILTER (WHERE call_type = 'audio') as audio_calls,
            COUNT(*) FILTER (WHERE call_type = 'video') as video_calls,
            AVG(duration_seconds) FILTER (WHERE duration_seconds IS NOT NULL) as avg_duration_seconds,
            MAX(started_at) as last_call_at
        FROM calls
        GROUP BY conversation_id;
        
        CREATE UNIQUE INDEX ix_call_statistics_conversation_id 
        ON call_statistics(conversation_id);
    """
    )


def downgrade() -> None:
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS call_statistics")

    # Drop indexes
    op.drop_index("ix_calls_active", table_name="calls")
    op.drop_index("ix_call_participants_answered", table_name="call_participants")
    op.drop_index("ix_call_participants_user_id", table_name="call_participants")
    op.drop_index("ix_call_participants_call_id", table_name="call_participants")

    op.drop_index("ix_calls_call_type", table_name="calls")
    op.drop_index("ix_calls_started_at", table_name="calls")
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_index("ix_calls_initiator_id", table_name="calls")
    op.drop_index("ix_calls_conversation_id", table_name="calls")

    # Drop tables
    op.drop_table("call_participants")
    op.drop_table("calls")
