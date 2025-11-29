"""
ETL 스키마 테스트
"""

from shared_etl.mysql_to_postgres_hooks import build_plain_text


def test_plain_from_min_doc():
    """최소 문서 플레인 텍스트 추출"""
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "hello"}]}
        ],
    }
    assert build_plain_text(doc) == "hello"


def test_plain_with_math():
    """수식 포함 플레인 텍스트 추출"""
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "이차방정식: "},
                    {"type": "math-inline", "attrs": {"tex": "x^2", "lang": "math"}},
                ],
            }
        ],
    }
    plain = build_plain_text(doc)
    assert "이차방정식" in plain
    assert "x^2" in plain
