"""TeX 정규화 스크립트 - 함수/괄호/근호/첨자/화학 라우팅"""
import re

FUNC_TOKENS = r"(sin|cos|tan|log|ln|lim|det|arcsin|arccos|arctan|sinh|cosh|tanh|exp|max|min|sup|inf)"
FUNC_RE = re.compile(rf"(?<!\\)\b{FUNC_TOKENS}\b")
SUB_RE = re.compile(r"([A-Za-z])_([A-Za-z0-9])")
SQRT_MISS_BRACE = re.compile(r"(\\sqrt)\s*(?!\{)")
CHEM_LIKE = re.compile(r"(?:[A-Z][a-z]?\d*(?:[+-]?\d*)?){2,}")

def fix_functions(tex: str) -> str:
    """함수 키워드 토큰화"""
    return FUNC_RE.sub(lambda m: "\\" + m.group(0), tex)

def wrap_subscripts(tex: str) -> str:
    """연속 밑첨자 보호"""
    return SUB_RE.sub(r"\1_{\2}", tex)

def strengthen_sqrt(tex: str) -> str:
    """루트 괄호 보강"""
    tex = SQRT_MISS_BRACE.sub(r"\1{", tex)
    tex = re.sub(r"\\sqrt\{([^{}]+)\}", r"\\sqrt{\1}", tex)
    return tex

def route_chem(tex: str) -> str:
    """화학식 라우팅"""
    if r"\ce{" in tex:
        return tex
    if CHEM_LIKE.search(tex.replace(" ", "")):
        return f"\\ce{{{tex}}}"
    return tex

def normalize_tex(tex: str) -> str:
    """전체 정규화 파이프라인"""
    if not tex:
        return tex
    tex = fix_functions(tex)
    tex = wrap_subscripts(tex)
    tex = strengthen_sqrt(tex)
    tex = route_chem(tex)
    tex = tex.replace(r"x^{ 1/3}", r"x^{1/3}").replace("  ", " ")
    return tex.strip()
