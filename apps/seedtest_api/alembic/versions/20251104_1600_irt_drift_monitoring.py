"""Add IRT drift monitoring tables.

Revision ID: 20251104_1600_irt_drift_monitoring
Revises: 20251103_1300_prophet_survival_columns
Create Date: 2025-11-04 16:00:00.000000

Adds tables for Bayesian IRT parameter drift detection:
- items: full item bank with anchor status, versioning
- drift_windows: time-window definitions (baseline/recent)
- item_calibration: windowed Bayesian re-estimation results
- drift_alerts: automated drift detection alerts

Supports:
- Anchor-based equating with strong priors
- DIF analysis by demographic groups
- Information function tracking
- CAT exposure adjustment hooks
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as psql

revision = "20251104_1600_irt_drift_monitoring"
down_revision = "20251103_1300_prophet_survival_columns"
branch_labels = None
depends_on = None


def table_exists(conn, name: str) -> bool:
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    conn = op.get_bind()

    # Items table: comprehensive item bank with anchor tracking
    if not table_exists(conn, "items"):
        op.create_table(
            "items",
            sa.Column("id", sa.Text, primary_key=True, comment="Item identifier"),
            sa.Column("a", sa.Float, nullable=False, comment="Discrimination (baseline)"),
            sa.Column("b", sa.Float, nullable=False, comment="Difficulty (baseline)"),
            sa.Column("c", sa.Float, nullable=False, server_default="0.0", comment="Guessing"),
            sa.Column("version", sa.Text, nullable=True, comment="Parameter version tag"),
            sa.Column(
                "is_anchor",
                sa.Boolean,
                nullable=False,
                server_default="false",
                comment="Anchor item for equating",
            ),
            sa.Column(
                "effective_from",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                comment="When these params became effective",
            ),
            sa.Column(
                "tags",
                psql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Topic/language/level tags",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                onupdate=sa.text("NOW()"),
            ),
        )
        op.create_index("ix_items_is_anchor", "items", ["is_anchor"])
        op.create_index("ix_items_effective_from", "items", ["effective_from"])
        op.create_index(
            "ix_items_tags_gin",
            "items",
            ["tags"],
            postgresql_using="gin",
        )

    # Drift windows: time-period definitions for drift analysis
    if not table_exists(conn, "drift_windows"):
        op.create_table(
            "drift_windows",
            sa.Column(
                "id",
                sa.Integer,
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "start_at",
                sa.DateTime(timezone=True),
                nullable=False,
                comment="Window start (inclusive)",
            ),
            sa.Column(
                "end_at",
                sa.DateTime(timezone=True),
                nullable=False,
                comment="Window end (exclusive)",
            ),
            sa.Column(
                "population_tags",
                psql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Cohort filters (e.g., grade/school/language)",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
            ),
        )
        op.create_index("ix_drift_windows_times", "drift_windows", ["start_at", "end_at"])

    # Item calibration: windowed Bayesian re-estimation results
    if not table_exists(conn, "item_calibration"):
        op.create_table(
            "item_calibration",
            sa.Column(
                "id",
                sa.Integer,
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "item_id",
                sa.Text,
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "window_id",
                sa.Integer,
                sa.ForeignKey("drift_windows.id", ondelete="CASCADE"),
                nullable=False,
            ),
            # Bayesian posterior estimates (EAP)
            sa.Column("a_hat", sa.Float, nullable=False, comment="Posterior a (EAP)"),
            sa.Column("b_hat", sa.Float, nullable=False, comment="Posterior b (EAP)"),
            sa.Column("c_hat", sa.Float, nullable=False, comment="Posterior c (EAP)"),
            # 95% credible intervals
            sa.Column("a_l95", sa.Float, nullable=True, comment="a lower 95% CI"),
            sa.Column("a_u95", sa.Float, nullable=True, comment="a upper 95% CI"),
            sa.Column("b_l95", sa.Float, nullable=True, comment="b lower 95% CI"),
            sa.Column("b_u95", sa.Float, nullable=True, comment="b upper 95% CI"),
            sa.Column("c_l95", sa.Float, nullable=True, comment="c lower 95% CI"),
            sa.Column("c_u95", sa.Float, nullable=True, comment="c upper 95% CI"),
            # Sample size & diagnostics
            sa.Column("n", sa.Integer, nullable=False, comment="Response count"),
            sa.Column(
                "dif",
                psql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="DIF results by group (Δb/Δa, BF, P>threshold)",
            ),
            sa.Column(
                "info",
                psql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="θ-information function summary",
            ),
            sa.Column("run_id", sa.Text, nullable=True, comment="Job run identifier"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
            ),
        )
        op.create_index(
            "ix_item_calibration_item_window",
            "item_calibration",
            ["item_id", "window_id"],
            unique=True,
        )
        op.create_index(
            "ix_item_calibration_run_id",
            "item_calibration",
            ["run_id"],
        )

    # Drift alerts: automated drift detection results
    if not table_exists(conn, "drift_alerts"):
        op.create_table(
            "drift_alerts",
            sa.Column(
                "id",
                sa.Integer,
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "item_id",
                sa.Text,
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "window_id",
                sa.Integer,
                sa.ForeignKey("drift_windows.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "metric",
                sa.Text,
                nullable=False,
                comment="Metric name (delta_a, delta_b, delta_c, dif_*)",
            ),
            sa.Column(
                "value",
                sa.Float,
                nullable=False,
                comment="Observed metric value",
            ),
            sa.Column(
                "threshold",
                sa.Float,
                nullable=False,
                comment="Threshold that was exceeded",
            ),
            sa.Column(
                "severity",
                sa.Text,
                nullable=False,
                comment="Alert severity: minor, moderate, severe",
            ),
            sa.Column("run_id", sa.Text, nullable=True, comment="Job run identifier"),
            sa.Column(
                "resolved_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="When action was taken",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
            ),
        )
        op.create_index(
            "ix_drift_alerts_item_created",
            "drift_alerts",
            ["item_id", "created_at"],
        )
        op.create_index(
            "ix_drift_alerts_severity",
            "drift_alerts",
            ["severity", "resolved_at"],
        )
        op.create_index(
            "ix_drift_alerts_run_id",
            "drift_alerts",
            ["run_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if table_exists(conn, "drift_alerts"):
        op.drop_index("ix_drift_alerts_run_id", table_name="drift_alerts")
        op.drop_index("ix_drift_alerts_severity", table_name="drift_alerts")
        op.drop_index("ix_drift_alerts_item_created", table_name="drift_alerts")
        op.drop_table("drift_alerts")
    if table_exists(conn, "item_calibration"):
        op.drop_index("ix_item_calibration_run_id", table_name="item_calibration")
        op.drop_index("ix_item_calibration_item_window", table_name="item_calibration")
        op.drop_table("item_calibration")
    if table_exists(conn, "drift_windows"):
        op.drop_index("ix_drift_windows_times", table_name="drift_windows")
        op.drop_table("drift_windows")
    if table_exists(conn, "items"):
        op.drop_index("ix_items_tags_gin", table_name="items")
        op.drop_index("ix_items_effective_from", table_name="items")
        op.drop_index("ix_items_is_anchor", table_name="items")
        op.drop_table("items")
