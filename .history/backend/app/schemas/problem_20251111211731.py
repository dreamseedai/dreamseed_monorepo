"""
Pydantic schemas for Problem-related requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ProblemBase(BaseModel):
    """문제 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    difficulty: Optional[str] = Field(
        default="medium",
        pattern="^(easy|medium|hard)$"
    )
    category: Optional[str] = Field(default=None, max_length=50)


class ProblemCreate(ProblemBase):
    """문제 생성 요청"""
    pass


class ProblemUpdate(BaseModel):
    """문제 수정 요청"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    category: Optional[str] = Field(None, max_length=50)


class ProblemResponse(ProblemBase):
    """문제 응답"""
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProblemListResponse(BaseModel):
    """문제 목록 응답"""
    total: int
    problems: list[ProblemResponse]
