"""Week 3 exam & CAT models with IRT 3PL support + MPC mapping + Role-aware abilities

Revision ID: 2025_11_25_01
Revises: 
Create Date: 2025-11-25 12:00:00.000000

This migration creates the complete schema for:
- Adaptive exam sessions with CAT/IRT
- Item pools with 3PL parameters (a, b, c)
- Student responses with theta tracking
- Integration with MPCStudy question bank
- Student ability snapshots for Teacher/Tutor/Parent dashboards
- Optimized indexes for role-based queries
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2025_11_25_01"
down_revision = None  # TODO: Set to actual previous revision (e.g., "2025_11_10_01_core_users")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Week 3 exam and CAT tables"""
    
    # 1) Enum for exam session status
    exam_session_status = sa.Enum(
        "in_progress", "completed", "cancelled",
        name="exam_session_status",
    )
    exam_session_status.create(op.get_bind(), checkfirst=True)

    # 2) exams table - exam definitions
    op.create_table(
        "exams",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(length=50), nullable=True, index=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_questions", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("is_adaptive", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_exams_subject_active", "exams", ["subject", "is_adaptive"])

    # 3) items table - question items with IRT 3PL parameters
    op.create_table(
        "items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=50), nullable=True, index=True),
        sa.Column("stem_html", sa.Text(), nullable=False),
        # IRT 3PL parameters (mirt-compatible)
        sa.Column("a_discrimination", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("b_difficulty", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("c_guessing", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        # Metadata for content balancing
        sa.Column("chapter", sa.String(length=100), nullable=True),
        sa.Column("learning_objective", sa.Text(), nullable=True),
        sa.Column("exposure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_items_subject_active", "items", ["subject", "is_active"])
    op.create_index("ix_items_difficulty", "items", ["b_difficulty"])

    # 4) item_options table - multiple choice options
    op.create_table(
        "item_options",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("label", sa.String(length=10), nullable=False),  # A, B, C, D
        sa.Column("text_html", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # 5) exam_items table - exam to item pool mapping (many-to-many)
    op.create_table(
        "exam_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "exam_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fixed_order", sa.Integer(), nullable=True),  # NULL for CAT (adaptive order)
        sa.UniqueConstraint("exam_id", "item_id", name="uq_exam_item_exam_id_item_id"),
    )
    op.create_index("ix_exam_items_exam_id", "exam_items", ["exam_id"])

    # 6) exam_sessions table - student exam sessions with CAT state
    op.create_table(
        "exam_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "exam_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            # NOTE: Adjust FK target to match actual User table (e.g., "user" or "users")
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", exam_session_status, nullable=False, server_default="in_progress"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # IRT CAT state (EAP theta estimation)
        sa.Column("theta", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("theta_se", sa.Float(), nullable=True),  # Standard error
        # Counters
        sa.Column("questions_answered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wrong_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("omitted_count", sa.Integer(), nullable=False, server_default="0"),
        # Scores
        sa.Column("raw_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_score", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.create_index("ix_exam_sessions_user_status", "exam_sessions", ["user_id", "status"])
    op.create_index("ix_exam_sessions_exam_id", "exam_sessions", ["exam_id"])

    # 7) exam_session_responses table - individual question responses
    op.create_table(
        "exam_session_responses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exam_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "option_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("item_options.id", ondelete="SET NULL"),
            nullable=True,  # NULL if omitted
        ),
        sa.Column("question_index", sa.Integer(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        # Theta tracking for analysis
        sa.Column("theta_before", sa.Float(), nullable=False),
        sa.Column("theta_after", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_exam_session_responses_session", "exam_session_responses", ["session_id"])

    # 8) mpc_item_mapping table - track MPCStudy question migration
    op.create_table(
        "mpc_item_mapping",
        sa.Column("mpc_question_id", sa.Integer(), primary_key=True),  # PK for uniqueness
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_mpc_item_mapping_item_id", "mpc_item_mapping", ["item_id"])

    # 9) irt_student_abilities table - calibrated ability snapshots for dashboards
    op.create_table(
        "irt_student_abilities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=50), nullable=False),
        sa.Column("theta", sa.Float(), nullable=False),
        sa.Column("theta_se", sa.Float(), nullable=True),
        sa.Column(
            "exam_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exams.id", ondelete="SET NULL"),
            nullable=True,  # Null if calibrated across multiple exams
        ),
        sa.Column(
            "calibrated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    # Indexes for role-based queries
    op.create_index("ix_irt_student_abilities_user_subject", "irt_student_abilities", ["user_id", "subject"])
    op.create_index("ix_irt_student_abilities_subject", "irt_student_abilities", ["subject"])
    op.create_index("ix_irt_student_abilities_calibrated_at", "irt_student_abilities", ["calibrated_at"])



def downgrade() -> None:
    """Drop all Week 3 exam and CAT tables"""
    # Drop in reverse order of creation
    op.drop_index("ix_irt_student_abilities_calibrated_at", table_name="irt_student_abilities")
    op.drop_index("ix_irt_student_abilities_subject", table_name="irt_student_abilities")
    op.drop_index("ix_irt_student_abilities_user_subject", table_name="irt_student_abilities")
    op.drop_table("irt_student_abilities")
    
    op.drop_index("ix_mpc_item_mapping_item_id", table_name="mpc_item_mapping")
    op.drop_table("mpc_item_mapping")
    
    op.drop_index("ix_exam_session_responses_session", table_name="exam_session_responses")
    op.drop_table("exam_session_responses")
    
    op.drop_index("ix_exam_sessions_exam_id", table_name="exam_sessions")
    op.drop_index("ix_exam_sessions_user_status", table_name="exam_sessions")
    op.drop_table("exam_sessions")
    
    op.drop_index("ix_exam_items_exam_id", table_name="exam_items")
    op.drop_table("exam_items")
    
    op.drop_table("item_options")
    
    op.drop_index("ix_items_difficulty", table_name="items")
    op.drop_index("ix_items_subject_active", table_name="items")
    op.drop_table("items")
    
    op.drop_index("ix_exams_subject_active", table_name="exams")
    op.drop_table("exams")

    # Drop enum (only if not used by other tables)
    exam_session_status = sa.Enum(
        "in_progress", "completed", "cancelled",
        name="exam_session_status",
    )
    exam_session_status.drop(op.get_bind(), checkfirst=True)
