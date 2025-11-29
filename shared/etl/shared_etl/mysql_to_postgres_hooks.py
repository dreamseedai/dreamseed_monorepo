"""
MySQL(TinyMCE+Wiris) → Postgres(TipTap JSON + TeX 정규화)

ETL 훅:
1. Wiris 이미지/MathML → TeX 변환
2. TinyMCE HTML → TipTap JSON 문서
3. Inline/Block 수식 노드 생성
4. 화학식 자동 감지 (lang: 'math'|'chem')
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text

# 재사용: 앞서 만든 normalize, mathml→tex
import sys
from pathlib import Path

# shared/mathml 경로 추가 (절대 경로로 해결)
mathml_path = (Path(__file__).parent.parent.parent / "mathml" / "scripts").resolve()
if mathml_path.exists():
    sys.path.insert(0, str(mathml_path))

from normalize_tex import normalize_tex
from convert_wiris import mathml_to_tex

CHEM_LIKE = re.compile(r"(?:[A-Z][a-z]?\d*(?:[+-]?\d*)?){2,}")


@dataclass
class MySQLRow:
    """MySQL 레거시 문항 행"""

    id: int
    title: str
    content_html: str  # TinyMCE + Wiris HTML
    solution_html: str | None = None
    lang: str = "ko"


def _html_to_tiptap_doc(html: str, default_locale="ko") -> dict[str, Any]:
    """
    TinyMCE + Wiris HTML → TipTap JSON 문서

    변환 규칙:
    1. Wiris 수식: <img class="Wirisformula" data-mathml="..."> → math-inline 노드
    2. 직접 MathML: <math>...</math> → math-inline 노드
    3. 블록 수식: p 안의 단독 수식 → math-block 노드
    4. 텍스트: paragraph 노드
    """
    soup = BeautifulSoup(html or "", "html.parser")

    # Wiris 이미지를 MathML로 복원
    for img in soup.find_all("img", class_=lambda c: c and "wiris" in c.lower()):
        mml = img.get("data-mathml") or img.get("alt") or ""
        tex = normalize_tex(mathml_to_tex(mml)) if mml else ""
        span = soup.new_tag("span")
        span.string = tex or ""
        span["data-type"] = "math-inline"
        span["data-lang"] = (
            "chem"
            if (tex and "\\ce{" in tex) or CHEM_LIKE.search(tex.replace(" ", ""))
            else "math"
        )
        span["data-tex"] = tex
        img.replace_with(span)

    # 직접 MathML 태그 처리
    for mml in soup.find_all("math"):
        mml_str = str(mml)
        tex = normalize_tex(mathml_to_tex(mml_str))
        span = soup.new_tag("span")
        span.string = tex or ""
        span["data-type"] = "math-inline"
        span["data-lang"] = (
            "chem"
            if (tex and "\\ce{" in tex) or CHEM_LIKE.search(tex.replace(" ", ""))
            else "math"
        )
        span["data-tex"] = tex
        mml.replace_with(span)

    blocks: list[dict[str, Any]] = []

    def push_paragraph(text_runs: list[Any]):
        if not text_runs:
            blocks.append({"type": "paragraph", "content": [{"type": "text", "text": ""}]})
            return
        blocks.append({"type": "paragraph", "content": text_runs})

    for node in soup.body.contents if soup.body else soup.contents:
        # 블록 판단: p, div, li, h*, pre ...
        if getattr(node, "name", None) in {"p", "div", "li", "pre", "h1", "h2", "h3", "h4"}:
            inlines = []
            for child in node.children:
                if getattr(child, "name", None) is None:  # NavigableString
                    txt = str(child)
                    if txt.strip():
                        inlines.append({"type": "text", "text": txt})
                elif child.name == "span" and child.get("data-type") == "math-inline":
                    tex = child.get("data-tex", "").strip()
                    lang = child.get("data-lang", "math")
                    inlines.append({"type": "math-inline", "attrs": {"tex": tex, "lang": lang}})
                else:
                    # 기타 인라인은 텍스트로 폴백
                    txt = child.get_text(" ", strip=False)
                    if txt:
                        inlines.append({"type": "text", "text": txt})

            # 단독 수식만 있고 텍스트가 없으면 block으로 승격
            only_math = all(n.get("type") == "math-inline" for n in inlines) and len(inlines) > 0
            has_text = any(
                n.get("type") == "text" and (n.get("text") or "").strip() for n in inlines
            )
            if only_math and not has_text and len(inlines) == 1:
                mi = inlines[0]["attrs"]
                blocks.append({"type": "math-block", "attrs": {"tex": mi["tex"], "lang": mi["lang"]}})
            else:
                push_paragraph(inlines)
        elif getattr(node, "name", None) == "span" and node.get("data-type") == "math-inline":
            # 루트에 인라인 수식이 바로 오는 경우
            mi = {
                "type": "math-inline",
                "attrs": {"tex": node.get("data-tex", ""), "lang": node.get("data-lang", "math")},
            }
            push_paragraph([mi])
        else:
            # 텍스트 노드 등
            text_content = getattr(node, "string", None)
            if text_content:
                push_paragraph([{"type": "text", "text": str(text_content)}])

    doc = {
        "type": "doc",
        "content": blocks or [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}],
    }
    return doc


def build_plain_text(tiptap_doc: dict[str, Any]) -> str:
    """TipTap JSON → 플레인 텍스트 (검색용)"""
    parts = []
    for blk in tiptap_doc.get("content", []):
        if blk["type"] in ("paragraph",):
            for n in blk.get("content", []) or []:
                if n["type"] == "text":
                    parts.append(n.get("text", ""))
                elif n["type"] in ("math-inline",):
                    parts.append(f" {n['attrs']['tex']} ")
        elif blk["type"] == "math-block":
            parts.append(f"\n{blk['attrs']['tex']}\n")
    return re.sub(r"\n{3,}", "\n\n", "".join(parts)).strip()


def fetch_mysql_rows(mysql_url: str, limit: int = 1000) -> list[MySQLRow]:
    """MySQL에서 레거시 문항 조회"""
    eng = create_engine(mysql_url)
    q = text(
        """SELECT id, title, content_html, solution_html 
           FROM problems 
           ORDER BY id 
           LIMIT :lim"""
    )
    rows = []
    with eng.begin() as conn:
        for r in conn.execute(q, {"lim": limit}):
            rows.append(
                MySQLRow(
                    id=r.id,
                    title=r.title,
                    content_html=r.content_html or "",
                    solution_html=r.solution_html or None,
                )
            )
    return rows


def upsert_postgres_rows(pg_url: str, items: list[dict[str, Any]]):
    """Postgres에 TipTap JSON 문항 저장"""
    eng = create_engine(pg_url)
    q = text(
        """
    INSERT INTO problems (id, title, body_json, body_plain, locale)
    VALUES (:id, :title, CAST(:body_json AS jsonb), :body_plain, :locale)
    ON CONFLICT (id) DO UPDATE
      SET title=EXCLUDED.title, 
          body_json=EXCLUDED.body_json, 
          body_plain=EXCLUDED.body_plain, 
          locale=EXCLUDED.locale
    """
    )
    with eng.begin() as conn:
        for it in items:
            conn.execute(q, it)


def run_etl(mysql_url: str, pg_url: str, limit: int = 1000, default_locale="ko"):
    """
    MySQL → Postgres ETL 실행

    Args:
        mysql_url: MySQL 연결 문자열 (예: mysql+pymysql://user:pass@localhost:3306/mpc_legacy)
        pg_url: Postgres 연결 문자열 (예: postgresql+psycopg://user:pass@localhost:5432/dreamseed)
        limit: 처리할 문항 수
        default_locale: 기본 언어 (ko, en, zh-Hans, zh-Hant)
    """
    rows = fetch_mysql_rows(mysql_url, limit=limit)
    out: list[dict[str, Any]] = []

    for r in rows:
        doc = _html_to_tiptap_doc(r.content_html, default_locale)
        body_plain = build_plain_text(doc)
        out.append(
            {
                "id": r.id,
                "title": r.title,
                "body_json": json.dumps(doc, ensure_ascii=False),
                "body_plain": body_plain,
                "locale": default_locale,
            }
        )

    upsert_postgres_rows(pg_url, out)
    print(f"✅ ETL 완료: {len(out)}개 문항 변환")
