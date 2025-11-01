from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class SessionBase(BaseModel):
    classroom_id: str | None = Field(None)
    exam_id: str | None = Field(None)
    user_id: str | None = Field(
        None, description="Owner user id; defaults to caller when omitted"
    )
    org_id: int | None = Field(
        None, description="Organization id; defaults to caller's org when omitted"
    )
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: str | None = None


class SessionCreate(SessionBase):
    id: str


class SessionOut(SessionBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "id": "sess_123",
                    "classroom_id": "cls_001",
                    "exam_id": "exam_789",
                    "user_id": "stu_001",
                    "org_id": 10,
                    "status": "in_progress",
                }
            ]
        }
