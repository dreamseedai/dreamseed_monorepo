"""
Test dashboard API endpoints

Tests for teacher/tutor/parent dashboard APIs that display
CAT exam results with scores and grades.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from main import app
from app.core.database import Base, get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.student import Student, Class, StudentClass
from app.models.core_entities import Teacher, ExamSession
from decimal import Decimal


# Test database setup
TEST_DATABASE_URL = "postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed_test"

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create test client with mocked dependencies"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    def override_get_current_user():
        # Return mock teacher user
        return User(
            id=1,
            email="teacher@test.com",
            hashed_password="fake",
            full_name="Test Teacher",
            role="teacher",
            is_active=True,
        )
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()


@pytest.fixture
def seed_test_data(db_session):
    """Seed database with test data"""
    # Create users first (to satisfy FK constraints)
    teacher_user = User(
        id=1,
        email="teacher@test.com",
        hashed_password="fake",
        full_name="Test Teacher",
        role="teacher",
        is_active=True,
    )
    db_session.add(teacher_user)
    
    student_user = User(
        id=2,
        email="student@test.com",
        hashed_password="fake",
        full_name="Test Student",
        role="student",
        is_active=True,
    )
    db_session.add(student_user)
    db_session.commit()  # Commit users first
    
    # Now create teacher profile
    teacher = Teacher(
        id=1,
        user_id=1,
        subject="math",
    )
    db_session.add(teacher)
    
    # Create student
    student = Student(
        id=1,
        user_id=2,
        name="Test Student",
        grade="고1",
    )
    db_session.add(student)
    
    # Create class
    clazz = Class(
        id=1,
        teacher_id=1,
        name="수학 1반",
        subject="math",
        grade="고1",
    )
    db_session.add(clazz)
    db_session.commit()  # Commit before creating relationships
    
    # Enroll student in class
    enrollment = StudentClass(
        student_id=1,
        class_id=1,
    )
    db_session.add(enrollment)
    
    # Create completed exam session with score/grade
    exam_session = ExamSession(
        id=1,
        student_id=1,
        class_id=1,
        exam_type="mock",
        status="completed",
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        theta=Decimal("0.5"),
        standard_error=Decimal("0.3"),
        score=Decimal("58.3"),  # Calculated from theta
        duration_sec=300,
        meta={
            "t_score": 55.0,
            "percentile": 69.1,
            "grade_numeric": 2,
            "grade_letter": "B",
        },
    )
    db_session.add(exam_session)
    
    db_session.commit()
    
    return {
        "teacher_id": 1,
        "student_id": 1,
        "class_id": 1,
        "exam_session_id": 1,
    }


def test_teacher_class_exam_summary(client, seed_test_data):
    """Test GET /api/dashboard/teacher/classes/{class_id}/exams"""
    class_id = seed_test_data["class_id"]
    
    response = client.get(f"/api/dashboard/teacher/classes/{class_id}/exams")
    
    assert response.status_code == 200, f"Failed: {response.text}"
    
    data = response.json()
    
    # Verify class info
    assert data["class_id"] == class_id
    assert data["name"] == "수학 1반"
    assert data["subject"] == "math"
    assert data["student_count"] == 1
    
    # Verify exam sessions
    assert len(data["exam_sessions"]) == 1
    exam = data["exam_sessions"][0]
    assert exam["exam_session_id"] == 1
    assert exam["score"] == 58.3
    assert exam["grade_numeric"] == 2
    assert exam["grade_letter"] == "B"
    
    # Verify student summary
    assert len(data["students"]) == 1
    student = data["students"][0]
    assert student["student_id"] == 1
    assert student["name"] == "Test Student"
    assert student["exam_count"] == 1
    assert student["latest_exam"] is not None
    
    print("✅ Teacher class exam summary test passed")


def test_teacher_student_exam_history(client, seed_test_data):
    """Test GET /api/dashboard/teacher/students/{student_id}/exams"""
    student_id = seed_test_data["student_id"]
    
    response = client.get(f"/api/dashboard/teacher/students/{student_id}/exams")
    
    assert response.status_code == 200, f"Failed: {response.text}"
    
    data = response.json()
    
    # Verify student info
    assert data["student_id"] == student_id
    assert data["student_name"] == "Test Student"
    assert data["student_grade"] == "고1"
    
    # Verify exams
    assert len(data["exams"]) == 1
    exam = data["exams"][0]
    assert exam["exam_session_id"] == 1
    assert exam["exam_type"] == "mock"
    assert exam["score"] == 58.3
    assert exam["grade_numeric"] == 2
    assert exam["grade_letter"] == "B"
    assert exam["theta"] == 0.5
    assert exam["standard_error"] == 0.3
    
    # Verify statistics
    assert data["statistics"] is not None
    stats = data["statistics"]
    assert stats["total_exams"] == 1
    assert stats["avg_score"] == 58.3
    assert stats["max_score"] == 58.3
    assert stats["min_score"] == 58.3
    
    print("✅ Teacher student exam history test passed")


def test_exam_session_detail(client, seed_test_data):
    """Test GET /api/dashboard/exams/{exam_session_id}"""
    exam_session_id = seed_test_data["exam_session_id"]
    
    response = client.get(f"/api/dashboard/exams/{exam_session_id}")
    
    assert response.status_code == 200, f"Failed: {response.text}"
    
    data = response.json()
    
    # Verify exam session
    exam = data["exam_session"]
    assert exam["exam_session_id"] == exam_session_id
    assert exam["exam_type"] == "mock"
    assert exam["score"] == 58.3
    assert exam["grade_numeric"] == 2
    assert exam["grade_letter"] == "B"
    assert exam["percentile"] == 69.1
    assert exam["t_score"] == 55.0
    
    # Verify student info
    student = data["student"]
    assert student["id"] == 1
    assert student["name"] == "Test Student"
    
    # Verify attempts (should be empty for this test)
    assert data["attempt_count"] == 0
    
    print("✅ Exam session detail test passed")


def test_parent_child_exam_history(client, db_session, seed_test_data):
    """Test GET /api/dashboard/parent/children/{student_id}/exams"""
    # Override current user to be a parent
    def override_get_current_user():
        return User(
            id=3,
            email="parent@test.com",
            hashed_password="fake",
            full_name="Test Parent",
            role="parent",
            is_active=True,
        )
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    student_id = seed_test_data["student_id"]
    
    response = client.get(f"/api/dashboard/parent/children/{student_id}/exams")
    
    assert response.status_code == 200, f"Failed: {response.text}"
    
    data = response.json()
    
    # Verify student info
    assert data["student_id"] == student_id
    assert data["student_name"] == "Test Student"
    
    # Verify exams (no theta/SE for parents)
    assert len(data["exams"]) == 1
    exam = data["exams"][0]
    assert exam["score"] == 58.3
    assert exam["grade_numeric"] == 2
    assert exam["grade_letter"] == "B"
    assert exam["percentile"] == 69.1
    assert "theta" not in exam  # Parents shouldn't see theta
    assert "standard_error" not in exam  # Parents shouldn't see SE
    
    print("✅ Parent child exam history test passed")


def test_tutor_all_students(client, db_session, seed_test_data):
    """Test GET /api/dashboard/tutor/students/exams"""
    # Override current user to be a tutor
    def override_get_current_user():
        return User(
            id=1,
            email="tutor@test.com",
            hashed_password="fake",
            full_name="Test Tutor",
            role="tutor",
            is_active=True,
        )
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    response = client.get("/api/dashboard/tutor/students/exams")
    
    assert response.status_code == 200, f"Failed: {response.text}"
    
    data = response.json()
    
    # Verify tutor info
    assert data["tutor_id"] == 1
    
    # Verify students
    assert len(data["students"]) >= 1
    student = data["students"][0]
    assert student["student_id"] == 1
    assert student["name"] == "Test Student"
    assert student["exam_count"] == 1
    assert student["latest_exam"] is not None
    
    # Verify statistics
    if data["statistics"]:
        stats = data["statistics"]
        assert stats["total_students"] >= 1
        assert stats["avg_score"] > 0
    
    print("✅ Tutor all students test passed")


if __name__ == "__main__":
    print("Dashboard API Tests")
    print("=" * 50)
    pytest.main([__file__, "-v", "-s"])
