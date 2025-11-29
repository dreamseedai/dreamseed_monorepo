"""
exam_schemas.py

Pydantic schemas for adaptive testing exam API endpoints.

These schemas define request/response models for:
 - Starting adaptive exams
 - Submitting answers
 - Getting next items
 - Viewing exam results
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class ExamStartRequest(BaseModel):
    """
    Request to start a new adaptive exam session.
    
    Attributes:
        student_id: ID of the student taking the exam
        class_id: Optional class ID if exam is part of a class
        exam_type: Type of exam (e.g., 'placement', 'practice', 'final')
        initial_theta: Optional initial ability estimate (default: 0.0)
        max_items: Optional maximum number of items (default: 20)
    """
    student_id: int = Field(..., description="Student ID")
    class_id: Optional[int] = Field(None, description="Class ID (optional)")
    exam_type: str = Field(..., description="Exam type", examples=["placement", "practice", "final"])
    initial_theta: Optional[float] = Field(0.0, description="Initial theta estimate")
    max_items: Optional[int] = Field(20, description="Maximum items in exam", ge=1, le=100)


class AnswerSubmitRequest(BaseModel):
    """
    Request to submit an answer for an item in an exam session.
    
    Attributes:
        exam_session_id: ID of the exam session
        item_id: ID of the item being answered
        correct: Whether the answer is correct
        submitted_answer: Raw answer text (optional)
        selected_choice: Choice index for MCQ (optional)
        response_time_ms: Time taken to answer in milliseconds (optional)
    """
    exam_session_id: int = Field(..., description="Exam session ID")
    item_id: int = Field(..., description="Item ID")
    correct: bool = Field(..., description="Whether answer is correct")
    submitted_answer: Optional[str] = Field(None, description="Raw answer text")
    selected_choice: Optional[int] = Field(None, description="Choice index for MCQ")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class NextItemRequest(BaseModel):
    """
    Request to get the next item in an adaptive exam session.
    
    Attributes:
        exam_session_id: ID of the exam session
        exclude_topics: Optional list of topics to exclude
        max_exposure: Optional max exposure count for item selection
    """
    exam_session_id: int = Field(..., description="Exam session ID")
    exclude_topics: Optional[List[str]] = Field(None, description="Topics to exclude")
    max_exposure: Optional[int] = Field(None, description="Max exposure count per item")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class ItemResponse(BaseModel):
    """
    Item/question response model.
    
    Attributes:
        id: Item ID
        topic: Subject area
        question_text: The question content
        meta: Additional metadata (choices, hints, etc.)
        a: Discrimination parameter (only for admin/debugging)
        b: Difficulty parameter (only for admin/debugging)
        c: Guessing parameter (only for admin/debugging)
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic: Optional[str] = None
    question_text: str
    meta: Optional[Dict[str, Any]] = None
    
    # IRT parameters (typically hidden from students)
    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None


class ExamStartResponse(BaseModel):
    """
    Response after starting an exam session.
    
    Attributes:
        exam_session_id: ID of the created exam session
        status: Session status
        started_at: Timestamp of session start
        current_theta: Current theta estimate
        standard_error: Current standard error
        max_items: Maximum items in exam
        next_item: The first item to present (optional)
    """
    exam_session_id: int
    status: str
    started_at: datetime
    current_theta: float
    standard_error: float
    max_items: int
    next_item: Optional[ItemResponse] = None


class AnswerSubmitResponse(BaseModel):
    """
    Response after submitting an answer.
    
    Attributes:
        attempt_id: ID of the created attempt record
        correct: Whether the answer was correct
        current_theta: Updated theta estimate
        standard_error: Updated standard error
        items_completed: Number of items completed so far
        should_terminate: Whether the exam should end
        termination_reason: Reason for termination (if applicable)
        next_item: Next item to present (if exam continues)
    """
    attempt_id: int
    correct: bool
    current_theta: float
    standard_error: float
    items_completed: int
    should_terminate: bool
    termination_reason: Optional[str] = None
    next_item: Optional[ItemResponse] = None


class NextItemResponse(BaseModel):
    """
    Response for next item request.
    
    Attributes:
        item: The next item to present
        current_theta: Current theta estimate
        standard_error: Current standard error
        items_completed: Number of items completed
        max_items: Maximum items allowed
    """
    item: ItemResponse
    current_theta: float
    standard_error: float
    items_completed: int
    max_items: int


class ExamSessionSummary(BaseModel):
    """
    Summary of a completed exam session.
    
    Attributes:
        exam_session_id: Session ID
        student_id: Student ID
        exam_type: Exam type
        status: Session status
        started_at: Start timestamp
        ended_at: End timestamp
        duration_sec: Total duration in seconds
        final_theta: Final theta estimate
        standard_error: Final standard error
        score: Final score/percentage
        items_completed: Total items completed
        termination_reason: Reason for ending
        attempts: List of all attempts in the session
    """
    model_config = ConfigDict(from_attributes=True)
    
    exam_session_id: int
    student_id: int
    exam_type: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    final_theta: Optional[float] = None
    standard_error: Optional[float] = None
    score: Optional[float] = None
    items_completed: int
    termination_reason: Optional[str] = None
    attempts: Optional[List["AttemptSummary"]] = None


class AttemptSummary(BaseModel):
    """
    Summary of a single attempt.
    
    Attributes:
        attempt_id: Attempt ID
        item_id: Item ID
        correct: Whether correct
        response_time_ms: Response time
        created_at: Timestamp
    """
    model_config = ConfigDict(from_attributes=True)
    
    attempt_id: int
    item_id: int
    correct: bool
    response_time_ms: Optional[int] = None
    created_at: datetime
