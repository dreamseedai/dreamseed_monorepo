"""
Pydantic schemas for Progress-related requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ProgressResponse(BaseModel):
    """진행도 응답"""
    id: UUID
    user_id: UUID
    problem_id: UUID
    status: str
    attempts: int
    last_attempt_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProgressWithDetails(ProgressResponse):
    """상세 정보 포함 진행도"""
    problem_title: str
    problem_difficulty: str
    problem_category: Optional[str] = None


class ProgressListResponse(BaseModel):
    """진행도 목록 응답"""
    total: int
    progress: list[ProgressResponse]


class ProgressStats(BaseModel):
    """진행도 통계"""
    total_problems: int
    not_started: int
    in_progress: int
    completed: int
    completion_rate: float
