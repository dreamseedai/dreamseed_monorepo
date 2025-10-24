from typing import Any

from pydantic import BaseModel, Field


class ContentIn(BaseModel):
    title: str
    doc: dict[str, Any] = Field(..., description="TipTap JSON document")


class ContentOut(ContentIn):
    id: int


