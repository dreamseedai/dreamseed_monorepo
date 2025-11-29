"""
Week 3 Exam Flow Schemas - Pydantic models matching examClient.ts

These schemas define the API contract for the Week 3 exam flow.
They precisely match the TypeScript types in apps/student_front/src/lib/examClient.ts

Frontend Contract:
- ExamStatus: "upcoming" | "in_progress" | "completed"
- ExamSummary: Brief exam info
- ExamDetail: Full exam details
- ExamSession: Session metadata
- QuestionOption: Multiple choice option
- QuestionPayload: Question with options + progress
- SubmitAnswerPayload: Answer feedback
- ExamResultSummary: Final results
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ===== Type Definitions =====

ExamStatus = Literal["upcoming", "in_progress", "completed"]


# ===== Response Models (Frontend Contract) =====

class ExamSummaryResponse(BaseModel):
    """
    Brief exam info for list view
    Frontend: ExamSummary type
    """
    id: uuid.UUID
    title: str
    subject: Optional[str] = None
    status: ExamStatus
    scheduled_at: Optional[datetime] = Field(None, alias="scheduledAt")
    duration_minutes: int = Field(alias="durationMinutes")

    class Config:
        from_attributes = True
        populate_by_name = True


class ExamDetailResponse(BaseModel):
    """
    Full exam details for detail page
    Frontend: ExamDetail type
    """
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    duration_minutes: int = Field(alias="durationMinutes")
    total_questions: int = Field(alias="totalQuestions")
    status: ExamStatus

    class Config:
        from_attributes = True
        populate_by_name = True


class ExamSessionResponse(BaseModel):
    """
    Exam session metadata
    Frontend: ExamSession type
    """
    id: uuid.UUID
    exam_id: uuid.UUID = Field(alias="examId")
    started_at: str = Field(alias="startedAt")
    ends_at: Optional[str] = Field(None, alias="endsAt")
    status: str

    class Config:
        from_attributes = True
        populate_by_name = True


class QuestionOptionResponse(BaseModel):
    """
    Multiple choice option
    Frontend: QuestionOption type
    """
    id: uuid.UUID
    label: str  # "A", "B", "C", "D"
    text: str

    class Config:
        from_attributes = True


class QuestionPayloadResponse(BaseModel):
    """
    Complete question with options and progress info
    Frontend: QuestionPayload type
    """
    id: uuid.UUID
    stem_html: str = Field(alias="stemHtml")
    options: list[QuestionOptionResponse]
    question_index: int = Field(alias="questionIndex")
    total_questions: int = Field(alias="totalQuestions")
    time_remaining_seconds: Optional[int] = Field(None, alias="timeRemainingSeconds")

    class Config:
        from_attributes = True
        populate_by_name = True


class SubmitAnswerResponse(BaseModel):
    """
    Feedback after answer submission
    Frontend: SubmitAnswerPayload type
    """
    correct: bool
    explanation_html: Optional[str] = Field(None, alias="explanationHtml")

    class Config:
        from_attributes = True
        populate_by_name = True


class ExamResultSummaryResponse(BaseModel):
    """
    Final exam results
    Frontend: ExamResultSummary type
    """
    session_id: uuid.UUID = Field(alias="sessionId")
    exam_id: uuid.UUID = Field(alias="examId")
    score: float
    total_score: float = Field(alias="totalScore")
    correct_count: int = Field(alias="correctCount")
    wrong_count: int = Field(alias="wrongCount")
    omitted_count: int = Field(alias="omittedCount")

    class Config:
        from_attributes = True
        populate_by_name = True


# ===== Request Models =====

class SubmitAnswerRequest(BaseModel):
    """
    Answer submission from frontend
    Matches submitAnswer() payload in examClient.ts
    """
    question_id: uuid.UUID = Field(alias="questionId")
    selected_option_id: uuid.UUID = Field(alias="selectedOptionId")
    time_spent_seconds: Optional[int] = Field(None, alias="timeSpentSeconds")

    class Config:
        populate_by_name = True
