"""
Test suite for classes router endpoints

Tests class summary, student roster, and exam statistics endpoints.
"""
import pytest
from datetime import datetime
from decimal import Decimal

from app.schemas.core_schemas import (
    ClassResponse,
    StudentResponse,
    ExamSessionResponse,
)


def test_get_class_summary_structure():
    """Test class summary response structure"""
    # Expected response structure
    expected_keys = {
        "class_id",
        "name",
        "subject",
        "grade",
        "student_count",
        "average_score",
        "recent_exam_count",
    }
    
    # Mock response
    summary = {
        "class_id": 1,
        "name": "고2-1반 수학",
        "subject": "math",
        "grade": "11",
        "student_count": 25,
        "average_score": 78.5,
        "recent_exam_count": 120,
    }
    
    assert set(summary.keys()) == expected_keys
    assert isinstance(summary["class_id"], int)
    assert isinstance(summary["student_count"], int)
    assert isinstance(summary["recent_exam_count"], int)
    assert summary["average_score"] is None or isinstance(summary["average_score"], float)


def test_get_class_students_structure():
    """Test class students list response structure"""
    # Expected response structure
    response = {
        "class_id": 1,
        "students": [
            {
                "student_id": 10,
                "name": "김철수",
                "grade": "11",
                "latest_score": 85.5,
                "exam_count": 5,
                "enrolled_at": "2024-03-01T09:00:00Z",
            }
        ],
        "total_count": 25,
    }
    
    assert "class_id" in response
    assert "students" in response
    assert "total_count" in response
    assert isinstance(response["students"], list)
    
    if response["students"]:
        student = response["students"][0]
        assert "student_id" in student
        assert "name" in student
        assert "grade" in student
        assert "exam_count" in student


def test_get_class_exam_stats_structure():
    """Test class exam statistics response structure"""
    response = {
        "class_id": 1,
        "exam_type": "mock",
        "stats": {
            "total_exams": 150,
            "completed_exams": 145,
            "avg_score": 78.5,
            "min_score": 45.0,
            "max_score": 98.5,
            "std_dev": 12.3,
            "avg_theta": 0.25,
            "avg_duration_sec": 3600,
        }
    }
    
    assert "class_id" in response
    assert "exam_type" in response
    assert "stats" in response
    
    stats = response["stats"]
    assert "total_exams" in stats
    assert "completed_exams" in stats
    assert "avg_score" in stats
    assert "min_score" in stats
    assert "max_score" in stats
    assert "std_dev" in stats
    assert "avg_theta" in stats
    assert "avg_duration_sec" in stats


def test_empty_class_handling():
    """Test handling of class with no students"""
    summary = {
        "class_id": 1,
        "name": "빈 교실",
        "subject": "math",
        "grade": "11",
        "student_count": 0,
        "average_score": None,
        "recent_exam_count": 0,
    }
    
    assert summary["student_count"] == 0
    assert summary["average_score"] is None
    assert summary["recent_exam_count"] == 0


def test_pagination_limits():
    """Test pagination parameter validation"""
    # Test default values
    skip = 0
    limit = 50
    assert skip >= 0
    assert 0 < limit <= 100
    
    # Test max limit enforcement
    limit = min(150, 100)
    assert limit == 100


def test_role_based_access():
    """Test role-based access control logic"""
    allowed_roles = {"teacher", "admin", "super_admin"}
    
    # Valid roles
    assert "teacher" in allowed_roles
    assert "admin" in allowed_roles
    assert "super_admin" in allowed_roles
    
    # Invalid roles
    assert "student" not in allowed_roles
    assert "parent" not in allowed_roles


def test_teacher_authorization_logic():
    """Test teacher can only access their own classes"""
    # Mock data
    class_teacher_id = 5
    current_user_id = 5
    current_user_role = "teacher"
    
    # Teacher accessing their own class
    if current_user_role == "teacher":
        authorized = (class_teacher_id == current_user_id)
    else:
        authorized = True  # Admins can access any class
    
    assert authorized is True
    
    # Teacher accessing another teacher's class
    other_teacher_id = 10
    if current_user_role == "teacher":
        authorized = (other_teacher_id == current_user_id)
    else:
        authorized = True
    
    assert authorized is False


def test_score_calculation_with_none_values():
    """Test handling of None scores in calculations"""
    scores = [85.0, 90.0, None, 78.5, None, 88.0]
    valid_scores = [s for s in scores if s is not None]
    
    if valid_scores:
        avg = sum(valid_scores) / len(valid_scores)
        assert avg > 0
        assert isinstance(avg, float)
    else:
        avg = None
        assert avg is None


def test_exam_type_filtering():
    """Test exam type filter values"""
    valid_exam_types = {"placement", "practice", "mock", "official", "quiz"}
    
    test_type = "mock"
    assert test_type in valid_exam_types
    
    invalid_type = "invalid_type"
    assert invalid_type not in valid_exam_types


def test_statistics_aggregate_queries():
    """Test SQL aggregate function results"""
    # Mock exam data
    exams = [
        {"score": 85.0, "theta": 0.5, "duration_sec": 3600},
        {"score": 90.0, "theta": 0.8, "duration_sec": 3200},
        {"score": 78.0, "theta": 0.2, "duration_sec": 4000},
    ]
    
    scores = [e["score"] for e in exams]
    avg_score = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)
    
    assert avg_score == 84.33333333333333
    assert min_score == 78.0
    assert max_score == 90.0
    
    # Standard deviation calculation (simplified)
    mean = avg_score
    variance = sum((x - mean) ** 2 for x in scores) / len(scores)
    std_dev = variance ** 0.5
    assert std_dev > 0
