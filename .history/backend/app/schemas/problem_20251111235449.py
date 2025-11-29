"""
Pydantic schemas for Problem-related requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ProblemBase(BaseModel):
    """문제 기본 스키마"""
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    difficulty: Optional[str] = Field(
        default="medium",
        pattern="^(easy|medium|hard)$"
    )
    category: Optional[str] = Field(default=None, max_length=50)


class ProblemCreate(ProblemBase):
    """문제 생성 요청"""
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class ProblemUpdate(BaseModel):
    """문제 수정 요청"""
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    category: Optional[str] = Field(None, max_length=50)


class ProblemResponse(ProblemBase):
    """문제 응답"""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class ProblemListResponse(BaseModel):
    """문제 목록 응답"""
    total: int
    problems: list[ProblemResponse]
