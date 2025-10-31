from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel


class FeaturesTopicDailyBase(BaseModel):
    user_id: str
    topic_id: str
    date: date
    attempts: int = 0
    correct: int = 0
    avg_time_ms: int | None = None
    theta_estimate: float | None = None
    last_seen_at: datetime | None = None


class FeaturesTopicDailyCreate(FeaturesTopicDailyBase):
    pass


class FeaturesTopicDailyOut(FeaturesTopicDailyBase):
    computed_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "user_id": "stu_001",
                    "topic_id": "topic_algebra",
                    "date": "2025-11-01",
                    "attempts": 12,
                    "correct": 9,
                    "avg_time_ms": 4800,
                    "theta_estimate": 1.3,
                }
            ]
        }
