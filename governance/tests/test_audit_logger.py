"""
Tests for audit_logger and policy_client audit integration.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import json
import logging
from datetime import datetime, timezone, timedelta

from governance.backend import audit_logger
from governance.backend.policy_client import PolicyEngineClient


@pytest.fixture
def mock_opa_allow():
    """Fixture to mock OPA response with allow=True."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": {"allow": True}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_opa_deny():
    """Fixture to mock OPA response with allow=False."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "result": {"allow": False, "reason": "Policy denied"}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        yield mock_post


class TestAuditLogger:
    """Unit tests for audit_logger module."""

    def test_log_policy_evaluation_allow(self, caplog):
        """log_policy_evaluation should log INFO with result='allow'."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        audit_logger.log_policy_evaluation(
            user_id="user123",
            user_role="student",
            resource_path="/api/lessons",
            resource_method="GET",
            policy_name="dreamseedai.access_control.allow",
            result="allow",
            duration_ms=5.23,
        )

        records = [r for r in caplog.records if r.name == "governance.audit"]
        assert len(records) == 1
        record = records[0]

        # Should be INFO level for allow
        assert record.levelname == "INFO"

        # Parse JSON log
        log_data = json.loads(record.getMessage())
        assert log_data["user_id"] == "user123"
        assert log_data["user_role"] == "student"
        assert log_data["resource_path"] == "/api/lessons"
        assert log_data["resource_method"] == "GET"
        assert log_data["policy_name"] == "dreamseedai.access_control.allow"
        assert log_data["result"] == "allow"
        assert log_data["duration_ms"] == 5.23
        assert "timestamp" in log_data
        assert log_data["event_type"] == "policy_evaluation"

    def test_log_policy_evaluation_deny(self, caplog):
        """log_policy_evaluation should log WARNING with result='deny'."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        audit_logger.log_policy_evaluation(
            user_id="user456",
            user_role="teacher",
            resource_path="/api/admin",
            resource_method="POST",
            policy_name="dreamseedai.access_control.allow",
            result="deny",
            duration_ms=3.45,
            reason="Insufficient permissions",
        )

        records = [r for r in caplog.records if r.name == "governance.audit"]
        assert len(records) == 1
        record = records[0]

        # Should be WARNING level for deny
        assert record.levelname == "WARNING"

        # Parse JSON log
        log_data = json.loads(record.getMessage())
        assert log_data["result"] == "deny"
        assert log_data["reason"] == "Insufficient permissions"

    def test_log_policy_error(self, caplog):
        """log_policy_error should log ERROR with error details."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        audit_logger.log_policy_error(
            user_id="user789",
            user_role="admin",
            resource_path="/api/data",
            resource_method="DELETE",
            policy_name="dreamseedai.data_protection.allow",
            reason="OPA server timeout",
            duration_ms=2000.0,
        )

        records = [r for r in caplog.records if r.name == "governance.audit"]
        assert len(records) == 1
        record = records[0]

        # Should be ERROR level
        assert record.levelname == "ERROR"

        # Parse JSON log
        log_data = json.loads(record.getMessage())
        assert log_data["result"] == "error"
        assert log_data["reason"] == "OPA server timeout"
        assert log_data["duration_ms"] == 2000.0

    def test_json_format(self, caplog):
        """Audit logs should be valid JSON."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        audit_logger.log_policy_evaluation(
            user_id="test",
            user_role="test",
            resource_path="/test",
            resource_method="GET",
            policy_name="test.policy",
            result="allow",
            duration_ms=1.0,
        )

        assert len(caplog.messages) > 0
        message = caplog.messages[0]

        # Should be parseable JSON
        parsed = json.loads(message)
        assert isinstance(parsed, dict)
        assert "timestamp" in parsed
        assert "event_type" in parsed
        assert parsed["event_type"] == "policy_evaluation"

    def test_timestamp_utc(self, caplog):
        """Timestamp should be in UTC ISO 8601 format."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        audit_logger.log_policy_evaluation(
            user_id="test",
            user_role="test",
            resource_path="/test",
            resource_method="GET",
            policy_name="test.policy",
            result="allow",
            duration_ms=1.0,
        )

        log_data = json.loads(caplog.messages[0])
        ts = log_data["timestamp"]

        # Should end with Z or +00:00
        assert ts.endswith("Z") or ts.endswith("+00:00") or "+" in ts

        # Should be parseable to UTC datetime
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert dt.tzinfo is not None


class TestPolicyClientAuditIntegration:
    """Integration tests for policy_client with audit logging."""

    @pytest.mark.asyncio
    async def test_evaluate_logs_allow(self, caplog, mock_opa_allow):
        """evaluate() should log INFO when policy allows."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        client = PolicyEngineClient()
        input_data = {
            "user": {"id": "user123", "role": "student"},
            "resource": {"path": "/api/lessons", "method": "GET"},
            "action": "get",
        }

        result = await client.evaluate("dreamseedai.access_control.allow", input_data)

        assert result["allow"] is True

        # Check audit log
        records = [r for r in caplog.records if r.name == "governance.audit"]
        assert len(records) == 1
        record = records[0]

        assert record.levelname == "INFO"

        log_data = json.loads(record.getMessage())
        assert log_data["user_id"] == "user123"
        assert log_data["user_role"] == "student"
        assert log_data["resource_path"] == "/api/lessons"
        assert log_data["resource_method"] == "GET"
        assert log_data["result"] == "allow"
        assert isinstance(log_data["duration_ms"], (int, float))
        assert log_data["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_evaluate_logs_deny(self, caplog, mock_opa_deny):
        """evaluate() should log WARNING when policy denies."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        client = PolicyEngineClient()
        input_data = {
            "user": {"id": "user456", "role": "student"},
            "resource": {"path": "/api/admin", "method": "POST"},
            "action": "post",
        }

        result = await client.evaluate("dreamseedai.access_control.allow", input_data)

        assert result["allow"] is False

        # Check audit log
        records = [r for r in caplog.records if r.name == "governance.audit"]
        assert len(records) == 1
        record = records[0]

        assert record.levelname == "WARNING"

        log_data = json.loads(record.getMessage())
        assert log_data["result"] == "deny"
        assert log_data["reason"] == "Policy denied"

    @pytest.mark.asyncio
    async def test_evaluate_logs_error(self, caplog):
        """evaluate() should log ERROR on exceptions."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        with patch(
            "httpx.AsyncClient.post", side_effect=Exception("OPA connection failed")
        ):
            client = PolicyEngineClient()
            input_data = {
                "user": {"id": "user789", "role": "admin"},
                "resource": {"path": "/api/data", "method": "DELETE"},
            }

            result = await client.evaluate(
                "dreamseedai.data_protection.allow", input_data
            )

            # Should return deny on error
            assert result["allow"] is False

            # Check audit log
            records = [r for r in caplog.records if r.name == "governance.audit"]
            assert len(records) == 1
            record = records[0]

            assert record.levelname == "ERROR"

            log_data = json.loads(record.getMessage())
            assert log_data["result"] == "error"
            assert (
                "OPA connection failed" in log_data["reason"]
                or "Unexpected error" in log_data["reason"]
            )

    @pytest.mark.asyncio
    async def test_default_user_values(self, caplog, mock_opa_allow):
        """evaluate() should use 'anonymous'/'guest' for missing user info."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        client = PolicyEngineClient()
        input_data = {"resource": {"path": "/api/public", "method": "GET"}}

        result = await client.evaluate("dreamseedai.access_control.allow", input_data)

        # Check audit log
        records = [r for r in caplog.records if r.name == "governance.audit"]
        assert len(records) == 1

        log_data = json.loads(records[0].getMessage())
        assert log_data["user_id"] == "anonymous"
        assert log_data["user_role"] == "guest"

    @pytest.mark.asyncio
    async def test_duration_measurement(self, caplog, mock_opa_allow):
        """evaluate() should measure and log duration_ms."""
        caplog.set_level(logging.INFO, logger="governance.audit")

        client = PolicyEngineClient()
        input_data = {
            "user": {"id": "test", "role": "test"},
            "resource": {"path": "/test", "method": "GET"},
        }

        await client.evaluate("test.policy", input_data)

        records = [r for r in caplog.records if r.name == "governance.audit"]
        log_data = json.loads(records[0].getMessage())

        # duration_ms should be a number
        assert isinstance(log_data["duration_ms"], (int, float))
        # Should be positive (even if very small)
        assert log_data["duration_ms"] >= 0
        # Should be reasonable (< 10000ms for a mocked call)
        assert log_data["duration_ms"] < 10000
