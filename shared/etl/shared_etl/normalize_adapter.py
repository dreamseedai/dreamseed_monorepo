"""
Math-ETL normalize 함수 래핑
"""

import sys
from pathlib import Path

# shared/mathml/scripts 경로 추가
mathml_path = Path(__file__).parent.parent.parent / "mathml" / "scripts"
sys.path.insert(0, str(mathml_path))

from normalize_tex import normalize_tex as _normalize
from convert_wiris import mathml_to_tex as _mml_to_tex


def normalize_tex(tex: str) -> str:
    """TeX 정규화"""
    return _normalize(tex)


def mathml_to_tex(mml: str) -> str:
    """MathML → TeX 변환"""
    return _mml_to_tex(mml)
