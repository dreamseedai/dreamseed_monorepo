"""
Quick test to verify Pydantic schemas work correctly

Run with: pytest backend/tests/test_schemas_validation.py -v
"""
import pytest
from datetime import datetime
from decimal import Decimal

from app.schemas.core_schemas import (
    # Aliases (backward compatible)
    UserOut,
    StudentOut,
    ClassOut,
    ExamSessionOut,
    AttemptOut,
    # Full names
    UserResponse,
    StudentResponse,
    ClassResponse,
    ExamSessionResponse,
    AttemptResponse,
    # Create schemas
    ExamSessionCreate,
    AnswerSubmit,
)


def test_schema_aliases():
    """Verify aliases work correctly"""
    assert UserOut == UserResponse
    assert StudentOut == StudentResponse
    assert ClassOut == ClassResponse
    assert ExamSessionOut == ExamSessionResponse
    assert AttemptOut == AttemptResponse


def test_exam_session_create():
    """Test ExamSessionCreate schema validation"""
    # Valid payload
    payload = ExamSessionCreate(
        exam_type="placement",
        class_id=1,
        meta={"max_items": 30}
    )
    assert payload.exam_type == "placement"
    assert payload.class_id == 1
    assert payload.meta is not None and payload.meta["max_items"] == 30
    
    # Without optional fields
    payload2 = ExamSessionCreate(exam_type="practice", class_id=None, meta=None)
    assert payload2.exam_type == "practice"
    assert payload2.class_id is None
    assert payload2.meta is None


def test_answer_submit():
    """Test AnswerSubmit schema validation"""
    # Multiple choice
    answer = AnswerSubmit(
        exam_session_id=1,
        item_id=100,
        answer=None,
        selected_choice=3,
        response_time_ms=5000,
        correct=True
    )
    assert answer.exam_session_id == 1
    assert answer.item_id == 100
    assert answer.selected_choice == 3
    assert answer.correct is True
    
    # Open-ended
    answer2 = AnswerSubmit(
        exam_session_id=1,
        item_id=101,
        answer="x = 5",
        selected_choice=None,
        response_time_ms=10000,
        correct=False
    )
    assert answer2.answer == "x = 5"
    assert answer2.selected_choice is None


def test_exam_session_response():
    """Test ExamSessionResponse schema serialization"""
    data = {
        "student_id": 1,
        "class_id": 1,
        "exam_type": "placement",
        "meta": {},
        "id": 1,
        "status": "completed",
        "started_at": datetime(2024, 11, 20, 10, 0, 0),
        "ended_at": datetime(2024, 11, 20, 10, 30, 0),
        "score": Decimal("85.50"),
        "duration_sec": 1800,
        "theta": Decimal("1.234"),
        "standard_error": Decimal("0.456")
    }
    
    session = ExamSessionResponse(**data)
    assert session.id == 1
    assert session.student_id == 1
    assert session.status == "completed"
    assert session.score == Decimal("85.50")
    assert session.theta == Decimal("1.234")


def test_user_response():
    """Test UserResponse (UserOut) schema"""
    data = {
        "email": "student@example.com",
        "username": "student1",
        "role": "student",
        "id": 1,
        "org_id": 1,
        "is_active": True,
        "created_at": datetime(2024, 11, 1, 0, 0, 0),
        "updated_at": datetime(2024, 11, 20, 0, 0, 0)
    }
    
    user = UserResponse(**data)
    assert user.email == "student@example.com"
    assert user.role == "student"
    assert user.is_active is True
    
    # Test alias
    user_alias = UserOut(**data)
    assert user_alias.email == "student@example.com"


def test_student_response():
    """Test StudentResponse (StudentOut) schema"""
    data = {
        "user_id": 1,
        "grade": "10",
        "birth_year": 2008,
        "locale": "ko-KR",
        "id": 1,
        "org_id": 1,
        "created_at": datetime(2024, 11, 1, 0, 0, 0)
    }
    
    student = StudentResponse(**data)
    assert student.user_id == 1
    assert student.grade == "10"
    assert student.locale == "ko-KR"
    
    # Test alias
    student_alias = StudentOut(**data)
    assert student_alias.grade == "10"


def test_class_response():
    """Test ClassResponse (ClassOut) schema"""
    data = {
        "name": "고2-1반 수학",
        "grade": "10",
        "subject": "math",
        "id": 1,
        "org_id": 1,
        "teacher_id": 1,
        "created_at": datetime(2024, 11, 1, 0, 0, 0)
    }
    
    clazz = ClassResponse(**data)
    assert clazz.name == "고2-1반 수학"
    assert clazz.subject == "math"
    
    # Test alias
    clazz_alias = ClassOut(**data)
    assert clazz_alias.name == "고2-1반 수학"


def test_attempt_response():
    """Test AttemptResponse (AttemptOut) schema"""
    data = {
        "student_id": 1,
        "exam_session_id": 1,
        "item_id": 100,
        "correct": True,
        "submitted_answer": None,
        "selected_choice": 3,
        "response_time_ms": 5000,
        "meta": {"difficulty": 0.5},
        "id": 1,
        "created_at": datetime(2024, 11, 20, 10, 5, 0)
    }
    
    attempt = AttemptResponse(**data)
    assert attempt.id == 1
    assert attempt.correct is True
    assert attempt.selected_choice == 3
    
    # Test alias
    attempt_alias = AttemptOut(**data)
    assert attempt_alias.correct is True


def test_field_validation():
    """Test field validation rules"""
    # Invalid email
    with pytest.raises(Exception):  # ValidationError
        UserResponse(
            email="not-an-email",  # Invalid email format
            username="test",
            role="student",
            id=1,
            org_id=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    # Birth year out of range
    with pytest.raises(Exception):  # ValidationError
        StudentResponse(
            user_id=1,
            grade="10",
            birth_year=1800,  # Too old
            locale="ko-KR",
            id=1,
            org_id=1,
            created_at=datetime.now()
        )


if __name__ == "__main__":
    # Run basic smoke tests
    print("Testing schema aliases...")
    test_schema_aliases()
    print("✅ Aliases work correctly")
    
    print("\nTesting ExamSessionCreate...")
    test_exam_session_create()
    print("✅ ExamSessionCreate validates correctly")
    
    print("\nTesting AnswerSubmit...")
    test_answer_submit()
    print("✅ AnswerSubmit validates correctly")
    
    print("\nTesting ExamSessionResponse...")
    test_exam_session_response()
    print("✅ ExamSessionResponse serializes correctly")
    
    print("\nTesting UserResponse...")
    test_user_response()
    print("✅ UserResponse works correctly")
    
    print("\nTesting StudentResponse...")
    test_student_response()
    print("✅ StudentResponse works correctly")
    
    print("\nTesting ClassResponse...")
    test_class_response()
    print("✅ ClassResponse works correctly")
    
    print("\nTesting AttemptResponse...")
    test_attempt_response()
    print("✅ AttemptResponse works correctly")
    
    print("\n" + "="*50)
    print("✅ ALL SCHEMA TESTS PASSED!")
    print("="*50)
