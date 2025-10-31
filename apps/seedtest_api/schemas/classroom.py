from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ClassroomBase(BaseModel):
    org_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Classroom name within org")
    grade: int | None = Field(None, ge=0, le=12)


class ClassroomCreate(ClassroomBase):
    id: str = Field(..., description="Client-supplied classroom id")


class ClassroomOut(ClassroomBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "id": "cls_001",
                    "org_id": "org_123",
                    "name": "5th Grade Math A",
                    "grade": 5,
                }
            ]
        }
