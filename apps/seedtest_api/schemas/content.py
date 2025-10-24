from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ContentItem(BaseModel):
    id: str
    title: str
    url: Optional[str] = Field(default=None, description="HTTP/HTTPS URL to resource")
    topic_tags: List[str] = Field(default_factory=list)
    difficulty: Optional[float] = Field(
        default=None, description="Relative difficulty (e.g., 1..5 or 0..1)"
    )
    format: Optional[str] = Field(
        default=None, description="video | article | problems | book | other"
    )
    language: Optional[str] = Field(default=None, description="e.g., ko, en")
    provider: Optional[str] = None
    popularity_score: Optional[float] = Field(
        default=None, description="Relative popularity or quality score"
    )


class ContentSearchResult(BaseModel):
    items: List[ContentItem] = Field(default_factory=list)
