"""
ETL 타입 정의 (Python)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

Domain = Literal["math", "chem"]


class GoldenExpected(TypedDict, total=False):
    """골든셋 예상 결과"""

    tex: str
    svg_hash: str
    speech: str


class GoldenPayload(TypedDict, total=False):
    """골든셋 페이로드"""

    mathml: str | None
    tex: str | None
    image_path: str | None


class GoldenItem(TypedDict, total=False):
    """골든셋 항목"""

    id: str
    domain: Domain
    locale: str
    source_format: str
    payload: GoldenPayload
    expected: GoldenExpected
    notes: str
    tags: list[str]


@dataclass
class MySQLRow:
    """MySQL 레거시 문항 행"""

    id: int
    title: str
    content_html: str
    solution_html: str | None = None
    lang: str = "ko"
