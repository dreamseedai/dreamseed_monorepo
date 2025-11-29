# backend/app/schemas/common.py
"""
공통 Pydantic 스키마
- PageResponse: 페이지네이션 응답 포맷
"""

from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """
    페이지네이션 응답 포맷
    
    Examples:
        >>> PageResponse[StudentSummary](total_count=42, page=1, page_size=20, items=[...])
    """
    total_count: int
    page: int
    page_size: int
    items: List[T]

    class Config:
        from_attributes = True
