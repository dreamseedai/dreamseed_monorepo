"""Smoke tests for compute_daily_kpis job (Session type contract)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

# Ensure package imports resolve
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from seedtest_api.services.db import get_session  # noqa: E402


def test_get_session_returns_session_type():
    """Verify get_session returns a Session object."""
    with get_session() as session:
        assert isinstance(session, Session)


def test_distinct_recent_users_accepts_session():
    """Verify _distinct_recent_users accepts Session parameter."""
    # Import after path setup
    from portal_front.apps.seedtest_api.jobs.compute_daily_kpis import (
        _distinct_recent_users,
    )

    mock_session = MagicMock(spec=Session)
    mock_session.execute.return_value.fetchall.return_value = []

    # Should not raise TypeError
    users = _distinct_recent_users(mock_session)
    assert isinstance(users, list)
    assert mock_session.execute.called


def test_main_uses_session_not_connection():
    """Verify main() uses Session objects, not Connection."""
    from portal_front.apps.seedtest_api.jobs.compute_daily_kpis import main

    mock_session = MagicMock(spec=Session)
    mock_session.execute.return_value.fetchall.return_value = []

    with patch(
        "portal_front.apps.seedtest_api.jobs.compute_daily_kpis.get_session"
    ) as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = mock_session

        exit_code = main(anchor_date=date(2025, 11, 1), dry_run=True)

        # Should complete successfully
        assert exit_code == 0
        # Session should be used
        assert mock_get_session.called


def test_calculate_and_store_weekly_kpi_signature():
    """Verify calculate_and_store_weekly_kpi expects Session parameter."""
    from seedtest_api.services.metrics import calculate_and_store_weekly_kpi
    import inspect

    sig = inspect.signature(calculate_and_store_weekly_kpi)
    params = list(sig.parameters.keys())

    # First parameter should be 'session'
    assert params[0] == "session"

    # Verify type annotation is Session
    param_annotation = sig.parameters["session"].annotation
    assert "Session" in str(param_annotation)
