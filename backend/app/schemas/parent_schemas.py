"""
Parent portal schemas - Children list and report downloads
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class ParentChild(BaseModel):
    """Single child in parent's children list"""
    id: uuid.UUID
    name: str
    school: Optional[str] = None
    grade: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ParentChildrenResponse(BaseModel):
    """Response for GET /api/parent/children"""
    parent_id: uuid.UUID = Field(..., alias="parentId")
    children: List[ParentChild]
    
    class Config:
        populate_by_name = True
