"""
Test suite for Adaptive Exam Router

Tests the IRT/CAT endpoints:
- POST /api/adaptive/start
- POST /api/adaptive/answer
- GET /api/adaptive/next
- GET /api/adaptive/status
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.api.routers.adaptive_exam import (
    router,
    get_student_by_user,
    get_or_create_engine,
    restore_engine_state,
    StartExamRequest,
    SubmitAnswerRequest,
)
from app.models.student import Student, Class
from app.models.core_entities import ExamSession, Attempt
from app.models.item import Item, ItemChoice
from app.models.user import User
from app.core.services.exam_engine import AdaptiveEngine


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_get_student_by_user_found():
    """Test get_student_by_user returns student when found"""
    mock_db = Mock()
    mock_student = Student(id=1, user_id=100, name="Test Student", grade="8")
    mock_db.query().filter().first.return_value = mock_student
    
    student = get_student_by_user(user_id=100, db=mock_db)
    
    assert student.id == 1
    assert student.user_id == 100
    assert student.name == "Test Student"


def test_get_student_by_user_not_found():
    """Test get_student_by_user raises HTTPException when not found"""
    from fastapi import HTTPException
    
    mock_db = Mock()
    mock_db.query().filter().first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        get_student_by_user(user_id=999, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Student record not found" in exc_info.value.detail


def test_get_or_create_engine_creates_new():
    """Test get_or_create_engine creates new engine when not cached"""
    from app.api.routers.adaptive_exam import ENGINE_CACHE
    ENGINE_CACHE.clear()
    
    engine = get_or_create_engine(exam_session_id=1, initial_theta=0.5)
    
    assert isinstance(engine, AdaptiveEngine)
    assert 1 in ENGINE_CACHE
    assert engine.theta == 0.5


def test_get_or_create_engine_returns_cached():
    """Test get_or_create_engine returns cached engine"""
    from app.api.routers.adaptive_exam import ENGINE_CACHE
    ENGINE_CACHE.clear()
    
    # Create first engine
    engine1 = get_or_create_engine(exam_session_id=2, initial_theta=0.0)
    
    # Get same engine
    engine2 = get_or_create_engine(exam_session_id=2, initial_theta=1.0)
    
    assert engine1 is engine2
    assert engine1.theta == 0.0  # Initial theta unchanged


def test_restore_engine_state():
    """Test restore_engine_state updates engine with previous attempts"""
    mock_db = Mock()
    
    # Create mock items
    item1 = Item(id=1, a=1.5, b=0.5, c=0.2, question_text="Q1", topic="algebra")
    item2 = Item(id=2, a=1.2, b=-0.3, c=0.1, question_text="Q2", topic="geometry")
    
    # Create mock attempts
    attempt1 = Attempt(id=1, item_id=1, correct=True)
    attempt2 = Attempt(id=2, item_id=2, correct=False)
    attempts = [attempt1, attempt2]
    
    # Mock db.query to return items
    def mock_query_side_effect(model):
        if model == Item:
            mock_query = Mock()
            def filter_side_effect(condition):
                # Extract item_id from filter condition
                if hasattr(condition, 'right'):
                    item_id = condition.right.value
                else:
                    item_id = 1
                    
                mock_filtered = Mock()
                if item_id == 1:
                    mock_filtered.first.return_value = item1
                elif item_id == 2:
                    mock_filtered.first.return_value = item2
                else:
                    mock_filtered.first.return_value = None
                return mock_filtered
            
            mock_query.filter = filter_side_effect
            return mock_query
        return Mock()
    
    mock_db.query = mock_query_side_effect
    
    # Create engine and restore state
    engine = AdaptiveEngine(initial_theta=0.0)
    restore_engine_state(engine, attempts, mock_db)
    
    # Verify engine processed attempts
    assert len(engine.responses) == 2


def test_restore_engine_state_skips_null_item_id():
    """Test restore_engine_state skips attempts with null item_id"""
    mock_db = Mock()
    
    # Create attempt with null item_id
    attempt = Attempt(id=1, item_id=None, correct=True)
    attempts = [attempt]
    
    engine = AdaptiveEngine(initial_theta=0.0)
    restore_engine_state(engine, attempts, mock_db)
    
    # Verify engine did not process attempt
    assert len(engine.responses) == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Request/Response Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_start_exam_request_model():
    """Test StartExamRequest model validation"""
    request = StartExamRequest(exam_type="practice", class_id=5)
    assert request.exam_type == "practice"
    assert request.class_id == 5


def test_start_exam_request_optional_class():
    """Test StartExamRequest with optional class_id"""
    request = StartExamRequest(exam_type="placement")
    assert request.exam_type == "placement"
    assert request.class_id is None


def test_submit_answer_request_model():
    """Test SubmitAnswerRequest model validation"""
    request = SubmitAnswerRequest(
        exam_session_id=1,
        item_id=10,
        correct=True,
        selected_choice=2,
        response_time_ms=5000
    )
    assert request.exam_session_id == 1
    assert request.item_id == 10
    assert request.correct is True
    assert request.selected_choice == 2
    assert request.response_time_ms == 5000


def test_submit_answer_request_optional_fields():
    """Test SubmitAnswerRequest with optional fields"""
    request = SubmitAnswerRequest(
        exam_session_id=1,
        item_id=10,
        correct=False
    )
    assert request.selected_choice is None
    assert request.submitted_answer is None
    assert request.response_time_ms is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Pydantic Response Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_start_exam_response_model():
    """Test StartExamResponse model"""
    from app.api.routers.adaptive_exam import StartExamResponse
    
    response = StartExamResponse(
        exam_session_id=123,
        message="Exam started",
        initial_theta=0.0
    )
    assert response.exam_session_id == 123
    assert response.message == "Exam started"
    assert response.initial_theta == 0.0


def test_submit_answer_response_model():
    """Test SubmitAnswerResponse model"""
    from app.api.routers.adaptive_exam import SubmitAnswerResponse
    
    response = SubmitAnswerResponse(
        attempt_id=456,
        theta=0.5,
        standard_error=0.25,
        completed=False,
        message="Answer submitted"
    )
    assert response.attempt_id == 456
    assert response.theta == 0.5
    assert response.standard_error == 0.25
    assert response.completed is False


def test_item_choice_response_model():
    """Test ItemChoiceResponse model"""
    from app.api.routers.adaptive_exam import ItemChoiceResponse
    
    choice = ItemChoiceResponse(
        choice_num=1,
        choice_text="Paris"
    )
    assert choice.choice_num == 1
    assert choice.choice_text == "Paris"


def test_next_item_response_model():
    """Test NextItemResponse model"""
    from app.api.routers.adaptive_exam import NextItemResponse, ItemChoiceResponse
    
    response = NextItemResponse(
        item_id=789,
        question_text="What is 2+2?",
        topic="arithmetic",
        choices=[
            ItemChoiceResponse(choice_num=1, choice_text="3"),
            ItemChoiceResponse(choice_num=2, choice_text="4"),
        ],
        current_theta=0.3,
        current_se=0.28,
        attempt_count=5,
        completed=False
    )
    assert response.item_id == 789
    assert response.question_text == "What is 2+2?"
    assert len(response.choices) == 2
    assert response.current_theta == 0.3
    assert response.attempt_count == 5


def test_exam_status_response_model():
    """Test ExamStatusResponse model"""
    from app.api.routers.adaptive_exam import ExamStatusResponse
    
    now = datetime.utcnow()
    response = ExamStatusResponse(
        exam_session_id=100,
        status="in_progress",
        exam_type="practice",
        started_at=now,
        ended_at=None,
        theta=0.2,
        standard_error=0.3,
        score=None,
        duration_sec=None,
        attempt_count=3,
        completed=False
    )
    assert response.exam_session_id == 100
    assert response.status == "in_progress"
    assert response.attempt_count == 3
    assert response.completed is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Integration Test Markers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.skip(reason="Requires database and authentication setup")
def test_start_adaptive_exam_endpoint():
    """Integration test for POST /api/adaptive/start"""
    # TODO: Implement when authentication is ready
    pass


@pytest.mark.skip(reason="Requires database and authentication setup")
def test_submit_adaptive_answer_endpoint():
    """Integration test for POST /api/adaptive/answer"""
    # TODO: Implement when authentication is ready
    pass


@pytest.mark.skip(reason="Requires database and authentication setup")
def test_get_next_item_endpoint():
    """Integration test for GET /api/adaptive/next"""
    # TODO: Implement when authentication is ready
    pass


@pytest.mark.skip(reason="Requires database and authentication setup")
def test_get_exam_status_endpoint():
    """Integration test for GET /api/adaptive/status"""
    # TODO: Implement when authentication is ready
    pass
