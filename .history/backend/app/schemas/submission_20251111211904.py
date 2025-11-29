"""
Pydantic schemas for Submission-related requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class SubmissionBase(BaseModel):
    """제출 기본 스키마"""
    answer: str = Field(..., min_length=1)


class SubmissionCreate(SubmissionBase):
    """제출 생성 요청"""
    problem_id: UUID


class SubmissionResponse(SubmissionBase):
    """제출 응답"""
    id: UUID
    problem_id: UUID
    user_id: UUID
    is_correct: Optional[bool] = None
    ai_feedback: Optional[str] = None
    score: Optional[int] = None
    submitted_at: datetime
    
    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    """제출 목록 응답"""
    total: int
    submissions: list[SubmissionResponse]


class SubmissionWithProblem(SubmissionResponse):
    """문제 정보 포함 제출 응답"""
    problem_title: str
    problem_difficulty: str
