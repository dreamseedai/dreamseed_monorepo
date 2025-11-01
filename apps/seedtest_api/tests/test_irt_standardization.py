"""Integration tests for IRT standardization: question.meta, attempt VIEW, features KPI.

Tests cover:
1. Question table with IRT parameters in meta JSONB
2. Attempt VIEW mapping from exam_results
3. Features_topic_daily with extended KPI columns
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import Question, FeaturesTopicDaily
from ..services.db import get_session


# Use real PostgreSQL database
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/dreamseed"
)


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    with get_session() as session:
        yield session


def test_question_meta_irt_params(db_session: Session):
    """Test question.meta JSONB with IRT parameters."""
    # Clean up test data
    db_session.execute(text("DELETE FROM question WHERE id = 9001"))
    db_session.commit()

    # Create question with IRT params
    question = Question(
        id=9001,
        content="Test question: What is 2 + 2?",
        difficulty=0.3,
        topic_id="arithmetic",
        meta={
            "irt": {
                "a": 1.5,
                "b": -0.8,
                "c": 0.15,
                "model": "3PL",
                "version": "2025-01",
            },
            "tags": ["arithmetic", "addition", "basic"],
        },
    )
    db_session.add(question)
    db_session.commit()

    # Query back and verify IRT params
    result = (
        db_session.execute(
            text(
                """
            SELECT 
                (meta->'irt'->>'a')::float AS irt_a,
                (meta->'irt'->>'b')::float AS irt_b,
                (meta->'irt'->>'c')::float AS irt_c,
                meta->'irt'->>'model' AS irt_model,
                jsonb_array_length(meta->'tags') AS tag_count
            FROM question
            WHERE id = 9001
        """
            )
        )
        .mappings()
        .first()
    )

    assert result is not None
    assert result["irt_a"] == 1.5
    assert result["irt_b"] == -0.8
    assert result["irt_c"] == 0.15
    assert result["irt_model"] == "3PL"
    assert result["tag_count"] == 3

    # Clean up
    db_session.execute(text("DELETE FROM question WHERE id = 9001"))
    db_session.commit()


def test_attempt_view_mapping(db_session: Session):
    """Test that attempt VIEW correctly maps exam_results."""
    # Query attempt view
    result = (
        db_session.execute(
            text(
                """
            SELECT 
                id,
                student_id,
                item_id,
                correct,
                response_time_ms,
                hint_used,
                attempt_no,
                topic_id
            FROM attempt
            LIMIT 1
        """
            )
        )
        .mappings()
        .first()
    )

    # Verify view returns data with expected schema
    if result:
        assert "id" in result
        assert "student_id" in result
        assert "item_id" in result
        assert "correct" in result
        assert "response_time_ms" in result
        assert "hint_used" in result
        assert "attempt_no" in result
        assert isinstance(result["correct"], bool)
        assert isinstance(result["response_time_ms"], int)
        assert isinstance(result["hint_used"], bool)
        assert isinstance(result["attempt_no"], int)


def test_attempt_view_aggregation(db_session: Session):
    """Test aggregating attempt VIEW data (typical analytics query)."""
    result = (
        db_session.execute(
            text(
                """
            SELECT 
                topic_id,
                COUNT(*) AS total_attempts,
                SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_count,
                ROUND(AVG(response_time_ms)) AS avg_rt_ms
            FROM attempt
            WHERE topic_id IS NOT NULL
            GROUP BY topic_id
            ORDER BY total_attempts DESC
            LIMIT 3
        """
            )
        )
        .mappings()
        .all()
    )

    # Should return aggregated data if any attempts exist
    assert isinstance(result, list)
    for row in result:
        assert "topic_id" in row
        assert "total_attempts" in row
        assert row["total_attempts"] > 0


def test_features_topic_daily_kpi_columns(db_session: Session):
    """Test features_topic_daily with all KPI columns."""
    # Clean up test data
    db_session.execute(
        text("DELETE FROM features_topic_daily WHERE user_id = 'test_kpi_user'")
    )
    db_session.commit()

    # Insert daily feature record with all KPI columns
    feature = FeaturesTopicDaily(
        user_id="test_kpi_user",
        topic_id="geometry",
        date=date(2025, 10, 31),
        attempts=20,
        correct=15,
        avg_time_ms=5200,
        hints=3,
        theta_estimate=Decimal("1.45"),
        theta_sd=Decimal("0.30"),
        rt_median=5000,
        improvement=Decimal("0.12"),
    )
    db_session.add(feature)
    db_session.commit()

    # Query back and verify all columns
    result = (
        db_session.execute(
            text(
                """
            SELECT 
                user_id,
                topic_id,
                date,
                attempts,
                correct,
                avg_time_ms,
                hints,
                theta_estimate,
                theta_sd,
                rt_median,
                improvement
            FROM features_topic_daily
            WHERE user_id = 'test_kpi_user'
        """
            )
        )
        .mappings()
        .first()
    )

    assert result is not None
    assert result["user_id"] == "test_kpi_user"
    assert result["topic_id"] == "geometry"
    assert result["attempts"] == 20
    assert result["correct"] == 15
    assert result["avg_time_ms"] == 5200
    assert result["hints"] == 3
    assert float(result["theta_estimate"]) == 1.45
    assert float(result["theta_sd"]) == 0.30
    assert result["rt_median"] == 5000
    assert float(result["improvement"]) == 0.12

    # Clean up
    db_session.execute(
        text("DELETE FROM features_topic_daily WHERE user_id = 'test_kpi_user'")
    )
    db_session.commit()


def test_features_topic_daily_upsert_idempotency(db_session: Session):
    """Test that upsert on features_topic_daily is idempotent."""
    # Clean up
    db_session.execute(
        text("DELETE FROM features_topic_daily WHERE user_id = 'idempotent_test'")
    )
    db_session.commit()

    # First insert
    db_session.execute(
        text(
            """
            INSERT INTO features_topic_daily 
            (user_id, topic_id, date, attempts, correct, hints)
            VALUES ('idempotent_test', 'physics', '2025-10-31', 5, 4, 1)
        """
        )
    )
    db_session.commit()

    # Upsert (should update)
    db_session.execute(
        text(
            """
            INSERT INTO features_topic_daily 
            (user_id, topic_id, date, attempts, correct, hints, improvement)
            VALUES ('idempotent_test', 'physics', '2025-10-31', 10, 8, 2, 0.25)
            ON CONFLICT (user_id, topic_id, date)
            DO UPDATE SET
                attempts = EXCLUDED.attempts,
                correct = EXCLUDED.correct,
                hints = EXCLUDED.hints,
                improvement = EXCLUDED.improvement
        """
        )
    )
    db_session.commit()

    # Verify updated values
    result = (
        db_session.execute(
            text(
                """
            SELECT attempts, correct, hints, improvement
            FROM features_topic_daily
            WHERE user_id = 'idempotent_test'
        """
            )
        )
        .mappings()
        .first()
    )

    assert result["attempts"] == 10
    assert result["correct"] == 8
    assert result["hints"] == 2
    assert float(result["improvement"]) == 0.25

    # Clean up
    db_session.execute(
        text("DELETE FROM features_topic_daily WHERE user_id = 'idempotent_test'")
    )
    db_session.commit()


def test_question_meta_gin_index_query(db_session: Session):
    """Test GIN index on question.meta for tag queries."""
    # Clean up
    db_session.execute(text("DELETE FROM question WHERE id BETWEEN 9100 AND 9102"))
    db_session.commit()

    # Insert questions with different tags
    db_session.execute(
        text(
            """
            INSERT INTO question (id, content, topic_id, meta)
            VALUES 
                (9100, 'Q1', 'algebra', '{"tags": ["algebra", "quadratic"]}'::jsonb),
                (9101, 'Q2', 'algebra', '{"tags": ["algebra", "linear"]}'::jsonb),
                (9102, 'Q3', 'geometry', '{"tags": ["geometry", "circles"]}'::jsonb)
        """
        )
    )
    db_session.commit()

    # Query using JSON containment (uses GIN index)
    result = (
        db_session.execute(
            text(
                """
            SELECT id, topic_id
            FROM question
            WHERE meta @> '{"tags": ["algebra"]}'::jsonb
            AND id BETWEEN 9100 AND 9102
            ORDER BY id
        """
            )
        )
        .mappings()
        .all()
    )

    assert len(result) == 2
    assert result[0]["id"] == 9100
    assert result[1]["id"] == 9101

    # Clean up
    db_session.execute(text("DELETE FROM question WHERE id BETWEEN 9100 AND 9102"))
    db_session.commit()
