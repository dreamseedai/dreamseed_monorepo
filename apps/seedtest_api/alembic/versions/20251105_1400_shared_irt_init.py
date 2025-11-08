"""Initialize shared_irt schema with comprehensive IRT tables.

Revision ID: 20251105_1400_shared_irt_init
Revises: 20251105_1000_irt_drift_tables
Create Date: 2025-11-05 14:00:00.000000

Creates shared_irt schema with:
- items: item bank with metadata
- item_parameters_current: active IRT parameters
- windows: calibration time windows
- item_calibration: historical calibration results
- drift_alerts: parameter drift detection
- item_responses: response data for calibration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251105_1400_shared_irt_init"
down_revision = "20251105_1000_irt_drift_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS shared_irt")

    # items: item bank with rich content
    op.create_table(
        "items",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("id_str", sa.Text, unique=True, nullable=False, comment="Human-readable item ID"),
        sa.Column("bank_id", sa.Text, nullable=False, comment="Item bank identifier"),
        sa.Column("lang", sa.Text, nullable=False, comment="Language: en, ko, zh-Hans, zh-Hant"),
        sa.CheckConstraint("lang IN ('en','ko','zh-Hans','zh-Hant')", name="items_lang_chk"),
        sa.Column("stem_rich", postgresql.JSONB, comment="Item stem with HTML/LaTeX"),
        sa.Column("options_rich", postgresql.JSONB, comment="Answer choices with rich content"),
        sa.Column("answer_key", postgresql.JSONB, comment="Correct answer(s)"),
        sa.Column("topic_tags", postgresql.ARRAY(sa.Text), server_default=sa.text("'{}'"), comment="Topic classifications"),
        sa.Column("subtopic_tags", postgresql.ARRAY(sa.Text), server_default=sa.text("'{}'"), comment="Subtopic classifications"),
        sa.Column("curriculum_tags", postgresql.ARRAY(sa.Text), server_default=sa.text("'{}'"), comment="Curriculum alignments"),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'"), comment="Additional metadata"),
        sa.Column("is_anchor", sa.Boolean, server_default=sa.text("false"), comment="Anchor item for equating"),
        sa.Column("exposure_count", sa.Integer, server_default=sa.text("0"), comment="Total exposure count for CAT"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="shared_irt",
        comment="IRT item bank with metadata"
    )

    op.create_index(
        "idx_items_bank_lang",
        "items",
        ["bank_id", "lang"],
        schema="shared_irt"
    )
    op.create_index(
        "idx_items_id_str",
        "items",
        ["id_str"],
        unique=True,
        schema="shared_irt"
    )
    op.create_index(
        "idx_items_anchor",
        "items",
        ["is_anchor"],
        schema="shared_irt",
        postgresql_where=sa.text("is_anchor = true")
    )

    # item_parameters_current: active IRT parameters for CAT/scoring
    op.create_table(
        "item_parameters_current",
        sa.Column("item_id", sa.BigInteger, sa.ForeignKey("shared_irt.items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("model", sa.Text, nullable=False, comment="IRT model: 1PL, 2PL, 3PL"),
        sa.CheckConstraint("model IN ('1PL','2PL','3PL')", name="ipc_model_chk"),
        sa.Column("a", sa.Float, comment="Discrimination parameter"),
        sa.Column("b", sa.Float, nullable=False, comment="Difficulty parameter"),
        sa.Column("c", sa.Float, comment="Guessing parameter"),
        sa.Column("a_se", sa.Float, comment="Standard error of a"),
        sa.Column("b_se", sa.Float, comment="Standard error of b"),
        sa.Column("c_se", sa.Float, comment="Standard error of c"),
        sa.Column("theta_min", sa.Float, server_default=sa.text("-4.0"), comment="Min theta for info curve"),
        sa.Column("theta_max", sa.Float, server_default=sa.text("4.0"), comment="Max theta for info curve"),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1"), comment="Parameter version"),
        sa.Column("effective_from", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()"), comment="Effective date"),
        sa.Column("note", sa.Text, comment="Version notes"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="shared_irt",
        comment="Current active IRT parameters for operational use"
    )

    # windows: calibration time windows
    op.create_table(
        "windows",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("label", sa.Text, nullable=False, comment="Human-readable label (e.g., '2025-Q1')"),
        sa.Column("start_at", sa.TIMESTAMP(timezone=True), nullable=False, comment="Window start (inclusive)"),
        sa.Column("end_at", sa.TIMESTAMP(timezone=True), nullable=False, comment="Window end (exclusive)"),
        sa.Column("population_tags", postgresql.ARRAY(sa.Text), server_default=sa.text("'{}'"), comment="Population filters"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="shared_irt",
        comment="Calibration time windows for drift monitoring"
    )

    op.create_index(
        "idx_windows_times",
        "windows",
        ["start_at", "end_at"],
        schema="shared_irt"
    )
    op.create_index(
        "idx_windows_label",
        "windows",
        ["label"],
        unique=True,
        schema="shared_irt"
    )

    # item_calibration: windowed calibration results
    op.create_table(
        "item_calibration",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.BigInteger, sa.ForeignKey("shared_irt.items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("window_id", sa.BigInteger, sa.ForeignKey("shared_irt.windows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model", sa.Text, nullable=False, comment="IRT model used"),
        sa.CheckConstraint("model IN ('1PL','2PL','3PL')", name="ic_model_chk"),
        # Parameter estimates
        sa.Column("a_hat", sa.Float, comment="Discrimination estimate"),
        sa.Column("b_hat", sa.Float, nullable=False, comment="Difficulty estimate"),
        sa.Column("c_hat", sa.Float, comment="Guessing estimate"),
        # Confidence/credible intervals
        sa.Column("a_ci_low", sa.Float, comment="Lower 95% CI for a"),
        sa.Column("a_ci_high", sa.Float, comment="Upper 95% CI for a"),
        sa.Column("b_ci_low", sa.Float, comment="Lower 95% CI for b"),
        sa.Column("b_ci_high", sa.Float, comment="Upper 95% CI for b"),
        sa.Column("c_ci_low", sa.Float, comment="Lower 95% CI for c"),
        sa.Column("c_ci_high", sa.Float, comment="Upper 95% CI for c"),
        # Diagnostics
        sa.Column("n_responses", sa.Integer, nullable=False, comment="Sample size"),
        sa.Column("loglik", sa.Float, comment="Log-likelihood"),
        sa.Column("converged", sa.Boolean, server_default=sa.text("true"), comment="Convergence flag"),
        sa.Column("drift_flag", sa.Text, comment="Drift severity: low, medium, high"),
        sa.Column("dif_metadata", postgresql.JSONB, server_default=sa.text("'{}'"), comment="DIF analysis results"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="shared_irt",
        comment="Historical IRT calibration results by window"
    )

    op.create_index(
        "idx_item_calibration_item_window",
        "item_calibration",
        ["item_id", "window_id"],
        unique=True,
        schema="shared_irt"
    )
    op.create_index(
        "idx_item_calibration_window",
        "item_calibration",
        ["window_id"],
        schema="shared_irt"
    )
    op.create_index(
        "idx_item_calibration_drift",
        "item_calibration",
        ["drift_flag"],
        schema="shared_irt",
        postgresql_where=sa.text("drift_flag IS NOT NULL")
    )

    # drift_alerts: parameter drift detection
    op.create_table(
        "drift_alerts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.BigInteger, sa.ForeignKey("shared_irt.items.id", ondelete="CASCADE"), nullable=True, comment="Item ID (NULL for test-level alerts)"),
        sa.Column("window_id", sa.BigInteger, sa.ForeignKey("shared_irt.windows.id", ondelete="CASCADE"), nullable=False, comment="Window where drift detected"),
        sa.Column("metric", sa.Text, nullable=False, comment="Metric: delta_b, delta_a, delta_c, dif_*, info_drop_*"),
        sa.Column("value", sa.Float, comment="Observed metric value"),
        sa.Column("threshold", sa.Float, comment="Threshold exceeded"),
        sa.Column("severity", sa.Text, nullable=False, comment="Severity: low, medium, high"),
        sa.CheckConstraint("severity IN ('low','medium','high')", name="da_severity_chk"),
        sa.Column("message", sa.Text, comment="Human-readable alert message"),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), comment="When alert was resolved"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="shared_irt",
        comment="Parameter drift and DIF alerts"
    )

    op.create_index(
        "idx_drift_alerts_item_window",
        "drift_alerts",
        ["item_id", "window_id"],
        schema="shared_irt"
    )
    op.create_index(
        "idx_drift_alerts_severity_unresolved",
        "drift_alerts",
        ["severity", "created_at"],
        schema="shared_irt",
        postgresql_where=sa.text("resolved_at IS NULL")
    )
    op.create_index(
        "idx_drift_alerts_window",
        "drift_alerts",
        ["window_id"],
        schema="shared_irt"
    )

    # item_responses: response data for calibration
    op.create_table(
        "item_responses",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Text, nullable=False, comment="Organization identifier"),
        sa.Column("user_id_hash", sa.Text, nullable=False, comment="Hashed user ID for privacy"),
        sa.Column("session_id", sa.Text, comment="Test session identifier"),
        sa.Column("item_id", sa.BigInteger, sa.ForeignKey("shared_irt.items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), comment="When item was presented"),
        sa.Column("answered_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False, comment="When response submitted"),
        sa.Column("is_correct", sa.Boolean, comment="Correctness flag"),
        sa.Column("score", sa.Float, comment="Polytomous score"),
        sa.Column("response_payload", postgresql.JSONB, server_default=sa.text("'{}'"), comment="Full response data"),
        sa.Column("lang", sa.Text, nullable=False, comment="Response language"),
        sa.CheckConstraint("lang IN ('en','ko','zh-Hans','zh-Hant')", name="ir_lang_chk"),
        sa.Column("extra", postgresql.JSONB, server_default=sa.text("'{}'"), comment="Additional metadata"),
        schema="shared_irt",
        comment="Item response data for IRT calibration"
    )

    op.create_index(
        "idx_item_responses_item",
        "item_responses",
        ["item_id"],
        schema="shared_irt"
    )
    op.create_index(
        "idx_item_responses_answered_at",
        "item_responses",
        ["answered_at"],
        schema="shared_irt"
    )
    op.create_index(
        "idx_item_responses_session",
        "item_responses",
        ["session_id"],
        schema="shared_irt"
    )
    op.create_index(
        "idx_item_responses_user_hash",
        "item_responses",
        ["user_id_hash"],
        schema="shared_irt"
    )


def downgrade():
    # Drop tables in reverse order (respect foreign keys)
    op.drop_index("idx_item_responses_user_hash", table_name="item_responses", schema="shared_irt")
    op.drop_index("idx_item_responses_session", table_name="item_responses", schema="shared_irt")
    op.drop_index("idx_item_responses_answered_at", table_name="item_responses", schema="shared_irt")
    op.drop_index("idx_item_responses_item", table_name="item_responses", schema="shared_irt")
    op.drop_table("item_responses", schema="shared_irt")

    op.drop_index("idx_drift_alerts_window", table_name="drift_alerts", schema="shared_irt")
    op.drop_index("idx_drift_alerts_severity_unresolved", table_name="drift_alerts", schema="shared_irt")
    op.drop_index("idx_drift_alerts_item_window", table_name="drift_alerts", schema="shared_irt")
    op.drop_table("drift_alerts", schema="shared_irt")

    op.drop_index("idx_item_calibration_drift", table_name="item_calibration", schema="shared_irt")
    op.drop_index("idx_item_calibration_window", table_name="item_calibration", schema="shared_irt")
    op.drop_index("idx_item_calibration_item_window", table_name="item_calibration", schema="shared_irt")
    op.drop_table("item_calibration", schema="shared_irt")

    op.drop_index("idx_windows_label", table_name="windows", schema="shared_irt")
    op.drop_index("idx_windows_times", table_name="windows", schema="shared_irt")
    op.drop_table("windows", schema="shared_irt")

    op.drop_table("item_parameters_current", schema="shared_irt")

    op.drop_index("idx_items_anchor", table_name="items", schema="shared_irt")
    op.drop_index("idx_items_id_str", table_name="items", schema="shared_irt")
    op.drop_index("idx_items_bank_lang", table_name="items", schema="shared_irt")
    op.drop_table("items", schema="shared_irt")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS shared_irt CASCADE")
