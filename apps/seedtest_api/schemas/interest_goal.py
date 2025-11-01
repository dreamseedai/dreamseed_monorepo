from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InterestGoalBase(BaseModel):
    user_id: str
    topic_id: str
    target_level: float | None = Field(None, description="Desired target level")
    priority: int = Field(0, ge=0, le=100)


class InterestGoalCreate(InterestGoalBase):
    pass


class InterestGoalOut(InterestGoalBase):
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "user_id": "stu_001",
                    "topic_id": "topic_algebra",
                    "target_level": 2.5,
                    "priority": 10,
                }
            ]
        }
