"""IRT drift monitoring schema

Revision ID: 20251105_0813_irt_drift
Revises:
Create Date: 2025-11-05 08:13:00

Creates shared_irt schema with:
- items: Master item bank with rich content
- item_parameters_current: Active IRT parameters (1PL/2PL/3PL)
- windows: Time-based calibration cohorts
- item_calibration: Historical calibration results
- drift_alerts: Parameter drift alerts
- item_responses: Anonymized response data
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251105_0813_irt_drift"
down_revision = None  # Update this if there are prior migrations
branch_labels = None
depends_on = None


def upgrade():
    """Create shared_irt schema and all tables"""

    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS shared_irt;")

    # ============================================================================
    # Items Master Table
    # ============================================================================
    op.create_table(
        "items",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("id_str", sa.Text(), nullable=True),
        sa.Column("bank_id", sa.Text(), nullable=False),
        sa.Column("lang", sa.Text(), nullable=False),
        sa.Column("stem_rich", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "options_rich", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("answer_key", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "topic_tags",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column(
            "subtopic_tags",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column(
            "curriculum_tags",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column("is_anchor", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("exposure_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "lang IN ('en','ko','zh-Hans','zh-Hant')", name="items_lang_check"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_str"),
        schema="shared_irt",
    )

    # ============================================================================
    # Current Item Parameters
    # ============================================================================
    op.create_table(
        "item_parameters_current",
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("a", sa.Double(), nullable=True),
        sa.Column("b", sa.Double(), nullable=False),
        sa.Column("c", sa.Double(), nullable=True),
        sa.Column("a_se", sa.Double(), nullable=True),
        sa.Column("b_se", sa.Double(), nullable=True),
        sa.Column("c_se", sa.Double(), nullable=True),
        sa.Column("theta_min", sa.Double(), server_default="-4.0", nullable=True),
        sa.Column("theta_max", sa.Double(), server_default="4.0", nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "effective_from",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "model IN ('1PL','2PL','3PL')", name="item_parameters_model_check"
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["shared_irt.items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("item_id"),
        schema="shared_irt",
    )

    # ============================================================================
    # Windows (Observation Periods)
    # ============================================================================
    op.create_table(
        "windows",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("start_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "population_tags",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("end_at > start_at", name="windows_dates_valid"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label", name="windows_label_unique"),
        schema="shared_irt",
    )

    # ============================================================================
    # Item Calibration History
    # ============================================================================
    op.create_table(
        "item_calibration",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("window_id", sa.BigInteger(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("a_hat", sa.Double(), nullable=True),
        sa.Column("b_hat", sa.Double(), nullable=False),
        sa.Column("c_hat", sa.Double(), nullable=True),
        sa.Column("a_ci_low", sa.Double(), nullable=True),
        sa.Column("a_ci_high", sa.Double(), nullable=True),
        sa.Column("b_ci_low", sa.Double(), nullable=True),
        sa.Column("b_ci_high", sa.Double(), nullable=True),
        sa.Column("c_ci_low", sa.Double(), nullable=True),
        sa.Column("c_ci_high", sa.Double(), nullable=True),
        sa.Column("n_responses", sa.Integer(), nullable=False),
        sa.Column("loglik", sa.Double(), nullable=True),
        sa.Column("drift_flag", sa.Text(), nullable=True),
        sa.Column(
            "dif_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "model IN ('1PL','2PL','3PL')", name="item_calibration_model_check"
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["shared_irt.items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["window_id"], ["shared_irt.windows.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "item_id", "window_id", name="item_calibration_window_unique"
        ),
        schema="shared_irt",
    )

    # ============================================================================
    # Drift Alerts
    # ============================================================================
    op.create_table(
        "drift_alerts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("window_id", sa.BigInteger(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("value", sa.Double(), nullable=True),
        sa.Column("threshold", sa.Double(), nullable=True),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "severity IN ('low','medium','high')", name="drift_alerts_severity_check"
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["shared_irt.items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["window_id"], ["shared_irt.windows.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="shared_irt",
    )

    # ============================================================================
    # Item Responses (Anonymized)
    # ============================================================================
    op.create_table(
        "item_responses",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("org_id", sa.Text(), nullable=False),
        sa.Column("user_id_hash", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=True),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "answered_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("score", sa.Double(), nullable=True),
        sa.Column(
            "response_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column("lang", sa.Text(), nullable=False),
        sa.Column(
            "extra",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.CheckConstraint(
            "lang IN ('en','ko','zh-Hans','zh-Hant')", name="item_responses_lang_check"
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["shared_irt.items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="shared_irt",
    )

    # ============================================================================
    # Performance Indexes
    # ============================================================================
    op.create_index(
        "idx_item_responses_item", "item_responses", ["item_id"], schema="shared_irt"
    )
    op.create_index(
        "idx_item_responses_window",
        "item_responses",
        ["answered_at"],
        schema="shared_irt",
    )
    op.create_index(
        "idx_item_responses_org_user",
        "item_responses",
        ["org_id", "user_id_hash"],
        schema="shared_irt",
    )
    op.create_index(
        "idx_items_bank_lang", "items", ["bank_id", "lang"], schema="shared_irt"
    )
    op.create_index(
        "idx_drift_alerts_unresolved",
        "drift_alerts",
        ["item_id", "window_id"],
        postgresql_where=sa.text("resolved_at IS NULL"),
        schema="shared_irt",
    )
    op.create_index(
        "idx_item_calibration_item_window",
        "item_calibration",
        ["item_id", "window_id"],
        schema="shared_irt",
    )

    # ============================================================================
    # Utility Views
    # ============================================================================
    op.execute(
        """
    CREATE OR REPLACE VIEW shared_irt.v_items_with_params AS
    SELECT 
      i.id,
      i.id_str,
      i.bank_id,
      i.lang,
      i.topic_tags,
      i.subtopic_tags,
      i.is_anchor,
      i.exposure_count,
      p.model,
      p.a,
      p.b,
      p.c,
      p.a_se,
      p.b_se,
      p.c_se,
      p.version AS param_version,
      p.effective_from,
      i.created_at,
      i.updated_at
    FROM shared_irt.items i
    LEFT JOIN shared_irt.item_parameters_current p ON i.id = p.item_id;
    """
    )

    op.execute(
        """
    CREATE OR REPLACE VIEW shared_irt.v_active_drift_alerts AS
    SELECT 
      da.id,
      da.item_id,
      i.id_str,
      i.bank_id,
      da.window_id,
      w.label AS window_label,
      da.metric,
      da.value,
      da.threshold,
      da.severity,
      da.message,
      da.created_at
    FROM shared_irt.drift_alerts da
    JOIN shared_irt.items i ON da.item_id = i.id
    JOIN shared_irt.windows w ON da.window_id = w.id
    WHERE da.resolved_at IS NULL
    ORDER BY da.severity DESC, da.created_at DESC;
    """
    )


def downgrade():
    """Drop shared_irt schema and all tables"""
    op.execute("DROP SCHEMA IF EXISTS shared_irt CASCADE;")
