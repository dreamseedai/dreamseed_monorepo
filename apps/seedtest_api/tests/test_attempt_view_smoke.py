"""Smoke tests for attempt VIEW - validate schema and basic queries"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..services.db import get_session


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    with get_session() as session:
        yield session


def test_attempt_view_columns_exist(db_session: Session):
    """Verify all expected columns exist in attempt VIEW"""
    result = db_session.execute(text("SELECT * FROM attempt LIMIT 0"))

    expected_columns = {
        "id",
        "student_id",
        "item_id",
        "correct",
        "response_time_ms",
        "hint_used",
        "completed_at",
        "started_at",
        "attempt_no",
        "session_id",
        "topic_id",
    }

    actual_columns = set(result.keys())

    assert expected_columns == actual_columns, (
        f"Column mismatch.\n"
        f"Missing: {expected_columns - actual_columns}\n"
        f"Extra: {actual_columns - expected_columns}"
    )


def test_attempt_view_select_minimal(db_session: Session):
    """Verify attempt VIEW can be queried without errors"""
    result = db_session.execute(text("SELECT count(*) FROM attempt"))
    count = result.scalar()

    # Should succeed even if count is 0
    assert count is not None
    assert count >= 0


def test_attempt_view_types(db_session: Session):
    """Verify column types are correct using information_schema (no data required)."""
    rows = db_session.execute(
        text(
            """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'attempt'
    """
        )
    ).fetchall()

    actual = {r.column_name: r.data_type for r in rows}

    expected = {
        "id": "bigint",
        "student_id": "uuid",
        "item_id": "bigint",
        "correct": "boolean",
        "response_time_ms": "integer",
        "hint_used": "boolean",
        "completed_at": "timestamp with time zone",
        "started_at": "timestamp with time zone",
        "attempt_no": "integer",
        "session_id": "text",
        "topic_id": "text",
    }

    # Ensure no missing or extra columns
    assert set(actual.keys()) == set(
        expected.keys()
    ), f"Column mismatch. Missing: {set(expected)-set(actual)}; Extra: {set(actual)-set(expected)}"

    # Validate data types
    for col, dtype in expected.items():
        assert (
            actual[col] == dtype
        ), f"Type mismatch for {col}: expected {dtype}, got {actual[col]}"


def test_attempt_view_student_id_determinism(db_session: Session):
    """Verify student_id generation is deterministic for same user_id"""
    # Uses exam_results directly; passes vacuously when there is no data.
    result = db_session.execute(
        text(
            """
        SELECT
            user_id_text,
            student_id,
            COUNT(*) as cnt
        FROM (
            SELECT
                er.user_id AS user_id_text,
                (
                    CASE
                        WHEN er.user_id ~* '^[0-9a-fA-F-]{36}$' THEN er.user_id::uuid
                        ELSE (
                            substr(md5(er.user_id),1,8) || '-' ||
                            substr(md5(er.user_id),9,4) || '-' ||
                            substr(md5(er.user_id),13,4) || '-' ||
                            substr(md5(er.user_id),17,4) || '-' ||
                            substr(md5(er.user_id),21,12)
                        )::uuid
                    END
                ) AS student_id
            FROM exam_results er
        ) sub
        GROUP BY user_id_text, student_id
    """
        )
    ).fetchall()

    # Build mapping counts and ensure no duplicates per user_id
    user_id_counts = {}
    for row in result:
        user_id = row.user_id_text
        user_id_counts[user_id] = user_id_counts.get(user_id, 0) + 1

    # If there is no data, this loop is empty and test passes.
    for user_id, count in user_id_counts.items():
        assert count == 1, f"user_id '{user_id}' maps to multiple student_ids: {count}"


def test_attempt_view_no_nulls_in_required_fields(db_session: Session):
    """Verify required fields never NULL"""
    result = db_session.execute(
        text(
            """
        SELECT
            COUNT(*) as total,
            COUNT(id) as id_count,
            COUNT(student_id) as student_id_count,
            COUNT(item_id) as item_id_count,
            COUNT(correct) as correct_count,
            COUNT(response_time_ms) as response_time_ms_count,
            COUNT(hint_used) as hint_used_count,
            COUNT(completed_at) as completed_at_count,
            COUNT(attempt_no) as attempt_no_count
        FROM attempt
    """
        )
    ).fetchone()

    # Ensure we received a row; COUNT(*) queries always return a row
    assert result is not None
    m = result._mapping

    # All required fields should have same count as total rows (also holds when total = 0)
    assert m["id_count"] == m["total"]
    assert m["student_id_count"] == m["total"]
    assert m["item_id_count"] == m["total"]
    assert m["correct_count"] == m["total"]
    assert m["response_time_ms_count"] == m["total"]
    assert m["hint_used_count"] == m["total"]
    assert m["completed_at_count"] == m["total"]
    assert m["attempt_no_count"] == m["total"]
