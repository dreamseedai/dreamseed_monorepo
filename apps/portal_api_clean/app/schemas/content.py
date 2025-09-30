from pydantic import BaseModel, Field
from typing import Any


class ContentIn(BaseModel):
    title: str
    doc: dict[str, Any] = Field(..., description="TipTap JSON document")


class ContentOut(ContentIn):
    id: int
