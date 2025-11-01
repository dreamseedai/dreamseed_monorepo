"""Tests for core domain models: classroom, session, interest_goal, features_topic_daily."""

from __future__ import annotations

import os
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ..db.base import Base
from ..models import Classroom, FeaturesTopicDaily, InterestGoal
from ..models import Session as LearningSession


@pytest.fixture
def db_session():
    """Create a DB session against Postgres if DATABASE_URL is set, else skip.

    Using SQLite is incompatible due to PostgreSQL-specific types (JSONB).
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set; skipping DB integration tests")
    engine = create_engine(db_url, future=True)
    # Reflective create_all with checkfirst should be safe on Postgres
    Base.metadata.create_all(engine, checkfirst=True)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def test_classroom_creation(db_session):
    """Test creating and querying a classroom."""
    # Cleanup to make test idempotent
    db_session.execute(text("DELETE FROM classroom WHERE id = 'cls_001'"))
    db_session.commit()

    classroom = Classroom(
        id="cls_001",
        org_id="org_123",
        name="5th Grade Math A",
        grade=5,
    )
    db_session.add(classroom)
    db_session.commit()

    retrieved = db_session.query(Classroom).filter_by(id="cls_001").first()
    assert retrieved is not None
    assert retrieved.org_id == "org_123"
    assert retrieved.name == "5th Grade Math A"
    assert retrieved.grade == 5


def test_classroom_unique_constraint(db_session):
    """Test that org_id + name must be unique."""
    # Cleanup to make test idempotent
    db_session.execute(text("DELETE FROM classroom WHERE id IN ('cls_001','cls_002')"))
    db_session.commit()
    classroom1 = Classroom(
        id="cls_001",
        org_id="org_123",
        name="Math A",
        grade=5,
    )
    classroom2 = Classroom(
        id="cls_002",
        org_id="org_123",
        name="Math A",  # Duplicate name in same org
        grade=6,
    )
    db_session.add(classroom1)
    db_session.commit()

    db_session.add(classroom2)
    with pytest.raises(Exception):  # SQLite will raise IntegrityError
        db_session.commit()


def test_session_creation(db_session):
    """Test creating a learning session."""
    # Cleanup to make test idempotent
    db_session.execute(text("DELETE FROM session WHERE id = 'sess_001'"))
    db_session.commit()

    session = LearningSession(
        id="sess_001",
        classroom_id="cls_001",
        exam_id="exam_456",
        started_at=datetime(2025, 10, 31, 10, 0, 0),
        status="in_progress",
    )
    db_session.add(session)
    db_session.commit()

    retrieved = db_session.query(LearningSession).filter_by(id="sess_001").first()
    assert retrieved is not None
    assert retrieved.classroom_id == "cls_001"
    assert retrieved.exam_id == "exam_456"
    assert retrieved.status == "in_progress"


def test_interest_goal_creation(db_session):
    """Test creating user interest goals."""
    # Cleanup
    db_session.execute(
        text(
            "DELETE FROM interest_goal WHERE user_id='user_001' AND topic_id='topic_algebra'"
        )
    )
    db_session.commit()
    goal = InterestGoal(
        user_id="user_001",
        topic_id="topic_algebra",
        target_level=2.5,
        priority=10,
    )
    db_session.add(goal)
    db_session.commit()

    retrieved = (
        db_session.query(InterestGoal)
        .filter_by(user_id="user_001", topic_id="topic_algebra")
        .first()
    )
    assert retrieved is not None
    assert float(retrieved.target_level) == 2.5
    assert retrieved.priority == 10


def test_features_topic_daily_creation(db_session):
    """Test creating daily topic features."""
    # Cleanup
    db_session.execute(
        text(
            "DELETE FROM features_topic_daily WHERE user_id='user_001' AND topic_id='topic_algebra' AND date='2025-10-31'"
        )
    )
    db_session.commit()
    feature = FeaturesTopicDaily(
        user_id="user_001",
        topic_id="topic_algebra",
        date=date(2025, 10, 31),
        attempts=10,
        correct=7,
        avg_time_ms=4500,
        theta_estimate=1.2,
    )
    db_session.add(feature)
    db_session.commit()

    retrieved = (
        db_session.query(FeaturesTopicDaily)
        .filter_by(
            user_id="user_001",
            topic_id="topic_algebra",
            date=date(2025, 10, 31),
        )
        .first()
    )
    assert retrieved is not None
    assert retrieved.attempts == 10
    assert retrieved.correct == 7
    assert retrieved.avg_time_ms == 4500
    assert float(retrieved.theta_estimate) == 1.2
