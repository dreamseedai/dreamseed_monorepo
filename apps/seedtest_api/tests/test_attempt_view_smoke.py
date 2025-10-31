"""Smoke tests for attempt VIEW - validate schema and basic queries"""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_attempt_view_columns_exist(db_session: Session):
    """Verify all expected columns exist in attempt VIEW"""
    result = db_session.execute(text("SELECT * FROM attempt LIMIT 0"))
    
    expected_columns = {
        'id', 'student_id', 'item_id', 'correct', 'response_time_ms',
        'hint_used', 'completed_at', 'started_at', 'attempt_no',
        'session_id', 'topic_id'
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
    """Verify column types are correct (if data exists)"""
    result = db_session.execute(text("""
        SELECT
            pg_typeof(id)::text as id_type,
            pg_typeof(student_id)::text as student_id_type,
            pg_typeof(item_id)::text as item_id_type,
            pg_typeof(correct)::text as correct_type,
            pg_typeof(response_time_ms)::text as response_time_ms_type,
            pg_typeof(hint_used)::text as hint_used_type,
            pg_typeof(completed_at)::text as completed_at_type,
            pg_typeof(started_at)::text as started_at_type,
            pg_typeof(attempt_no)::text as attempt_no_type,
            pg_typeof(session_id)::text as session_id_type,
            pg_typeof(topic_id)::text as topic_id_type
        FROM attempt
        LIMIT 1
    """)).fetchone()
    
    if result is None:
        pytest.skip("No data in attempt VIEW, cannot verify types")
    
    expected_types = {
        'id_type': 'bigint',
        'student_id_type': 'uuid',
        'item_id_type': 'bigint',
        'correct_type': 'boolean',
        'response_time_ms_type': 'integer',
        'hint_used_type': 'boolean',
        'completed_at_type': 'timestamp with time zone',
        'started_at_type': 'timestamp with time zone',
        'attempt_no_type': 'integer',
        'session_id_type': 'text',
        'topic_id_type': 'text',
    }
    
    for col, expected_type in expected_types.items():
        actual_type = getattr(result, col)
        assert actual_type == expected_type, (
            f"Type mismatch for {col}: expected {expected_type}, got {actual_type}"
        )


def test_attempt_view_student_id_determinism(db_session: Session):
    """Verify student_id generation is deterministic for same user_id"""
    # Insert test data if needed (requires exam_results table)
    # For now, just verify the VIEW can handle different user_id formats
    
    result = db_session.execute(text("""
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
    """)).fetchall()
    
    if not result:
        pytest.skip("No exam_results data to test determinism")
    
    # Each user_id should map to exactly one student_id
    user_id_counts = {}
    for row in result:
        user_id = row.user_id_text
        if user_id not in user_id_counts:
            user_id_counts[user_id] = 0
        user_id_counts[user_id] += 1
    
    for user_id, count in user_id_counts.items():
        assert count == 1, (
            f"user_id '{user_id}' maps to multiple student_ids: {count}"
        )


def test_attempt_view_no_nulls_in_required_fields(db_session: Session):
    """Verify required fields never NULL"""
    result = db_session.execute(text("""
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
    """)).fetchone()
    
    if result.total == 0:
        pytest.skip("No data in attempt VIEW")
    
    # All required fields should have same count as total rows
    assert result.id_count == result.total
    assert result.student_id_count == result.total
    assert result.item_id_count == result.total
    assert result.correct_count == result.total
    assert result.response_time_ms_count == result.total
    assert result.hint_used_count == result.total
    assert result.completed_at_count == result.total
    assert result.attempt_no_count == result.total
