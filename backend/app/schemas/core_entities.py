"""Pydantic schemas for core INTEGER-based entities.

This module defines minimal request/response models for:
- Organization
- Teacher profile
- ExamSession
- Attempt

These are intentionally thin and can be extended later as needed.
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: Optional[str] = Field(None, max_length=50)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationRead(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeacherBase(BaseModel):
    user_id: int = Field(..., description="FK to users.id")
    org_id: Optional[int] = Field(None, description="FK to organizations.id")
    subject: Optional[str] = Field(None, max_length=100)


class TeacherCreate(TeacherBase):
    pass


class TeacherRead(TeacherBase):
    id: int

    class Config:
        from_attributes = True


class ExamSessionBase(BaseModel):
    student_id: int
    class_id: Optional[int] = None
    exam_type: str = Field(..., max_length=50)


class ExamSessionCreate(ExamSessionBase):
    pass


class ExamSessionRead(ExamSessionBase):
    id: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    score: Optional[float] = None
    duration_sec: Optional[int] = None
    theta: Optional[float] = None
    standard_error: Optional[float] = None

    class Config:
        from_attributes = True


class AttemptBase(BaseModel):
    student_id: int
    exam_session_id: int
    item_id: Optional[int] = None
    correct: bool
    submitted_answer: Optional[str] = None
    selected_choice: Optional[int] = None
    response_time_ms: Optional[int] = None


class AttemptCreate(AttemptBase):
    pass


class AttemptRead(AttemptBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExamSessionWithAttempts(ExamSessionRead):
    attempts: List[AttemptRead] = []
