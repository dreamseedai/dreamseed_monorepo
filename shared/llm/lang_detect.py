"""
언어 감지 유틸리티
==================
Accept-Language 헤더 파싱 및 우선순위 기반 언어 감지.

지원 언어:
- ko: 한국어
- en: 영어
- zh-Hans: 중국어 간체
- zh-Hant: 중국어 번체

우선순위:
1. 강제 언어 (쿼리 파라미터 ?lang= 또는 헤더 X-Lang)
2. Accept-Language 헤더
3. 세션/쿠키 (선택)
4. JWT 클레임 (선택)
5. 기본값 (ko)

Example:
    >>> detect_language("zh-Hans,zh;q=0.9,en;q=0.8")
    'zh-Hans'

    >>> detect_language("ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
    'ko'
"""

from __future__ import annotations
import re
from typing import Optional

from .types import SUPPORTED_LANGS, DEFAULT_LANG


# 문자 패턴 (혼합 언어 감지용)
RE_HANGUL = re.compile(r"[가-힣]")
RE_LATIN = re.compile(r"[A-Za-z]")
RE_CJK = re.compile(r"[\u4E00-\u9FFF]")  # CJK 통합 한자


def parse_accept_language(header: str) -> list[tuple[str, float]]:
    """
    Accept-Language 헤더를 파싱하여 (언어, 우선순위) 리스트 반환.

    Args:
        header: Accept-Language 헤더 값
            예: "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"

    Returns:
        (언어코드, 우선순위) 튜플 리스트, 우선순위 내림차순 정렬
        예: [('ko-KR', 1.0), ('ko', 0.9), ('en-US', 0.8), ('en', 0.7)]

    Example:
        >>> parse_accept_language("ko-KR,ko;q=0.9,en;q=0.8")
        [('ko-KR', 1.0), ('ko', 0.9), ('en', 0.8)]
    """
    if not header:
        return []

    langs = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue

        # q 값 파싱 (기본값 1.0)
        if ";q=" in part:
            lang, q_str = part.split(";q=", 1)
            try:
                q = float(q_str)
            except ValueError:
                q = 1.0
        else:
            lang = part
            q = 1.0

        langs.append((lang.strip(), q))

    # 우선순위 내림차순 정렬
    langs.sort(key=lambda x: x[1], reverse=True)
    return langs


def normalize_lang_code(code: str) -> Optional[str]:
    """
    언어 코드를 정규화하여 지원 언어로 매핑.

    Args:
        code: 언어 코드 (예: 'ko-KR', 'zh-Hans', 'en-US')

    Returns:
        정규화된 언어 코드 또는 None (지원하지 않는 언어)

    Mapping:
        - ko, ko-KR, ko-* → ko
        - en, en-US, en-GB, en-* → en
        - zh-Hans, zh-CN, zh-SG → zh-Hans
        - zh-Hant, zh-TW, zh-HK, zh-MO → zh-Hant
        - zh (단독) → zh-Hans (기본값)

    Example:
        >>> normalize_lang_code('ko-KR')
        'ko'
        >>> normalize_lang_code('zh-TW')
        'zh-Hant'
        >>> normalize_lang_code('zh')
        'zh-Hans'
    """
    code = code.lower().strip()

    # 한국어
    if code.startswith("ko"):
        return "ko"

    # 영어
    if code.startswith("en"):
        return "en"

    # 중국어 간체
    if code in ("zh-hans", "zh-cn", "zh-sg", "zh-cmn-hans"):
        return "zh-Hans"

    # 중국어 번체
    if code in ("zh-hant", "zh-tw", "zh-hk", "zh-mo", "zh-cmn-hant"):
        return "zh-Hant"

    # 중국어 (기본값: 간체)
    if code == "zh":
        return "zh-Hans"

    return None


def detect_language(
    accept_language: Optional[str] = None,
    forced_lang: Optional[str] = None,
    cookie_lang: Optional[str] = None,
    jwt_lang: Optional[str] = None,
    default: str = DEFAULT_LANG,
) -> str:
    """
    우선순위 기반 언어 감지.

    Args:
        accept_language: Accept-Language 헤더 값
        forced_lang: 강제 언어 (쿼리 파라미터 또는 X-Lang 헤더)
        cookie_lang: 쿠키에 저장된 언어
        jwt_lang: JWT 클레임의 언어
        default: 기본 언어 (기본값: 'ko')

    Returns:
        감지된 언어 코드 (ko, en, zh-Hans, zh-Hant 중 하나)

    우선순위:
        1. forced_lang (강제 지정)
        2. accept_language (브라우저 설정)
        3. cookie_lang (세션 저장값)
        4. jwt_lang (사용자 선호)
        5. default (기본값)

    Example:
        >>> detect_language(accept_language="zh-Hans,zh;q=0.9")
        'zh-Hans'

        >>> detect_language(
        ...     accept_language="en-US,en;q=0.9",
        ...     forced_lang="ko"
        ... )
        'ko'
    """
    # 1. 강제 언어 (최우선)
    if forced_lang:
        normalized = normalize_lang_code(forced_lang)
        if normalized in SUPPORTED_LANGS:
            return normalized

    # 2. Accept-Language 헤더
    if accept_language:
        parsed = parse_accept_language(accept_language)
        for lang_code, _ in parsed:
            normalized = normalize_lang_code(lang_code)
            if normalized in SUPPORTED_LANGS:
                return normalized

    # 3. 쿠키
    if cookie_lang:
        normalized = normalize_lang_code(cookie_lang)
        if normalized in SUPPORTED_LANGS:
            return normalized

    # 4. JWT 클레임
    if jwt_lang:
        normalized = normalize_lang_code(jwt_lang)
        if normalized in SUPPORTED_LANGS:
            return normalized

    # 5. 기본값
    return default


def is_chinese(lang: str) -> bool:
    """중국어 여부 확인 (zh-Hans 또는 zh-Hant)"""
    return lang.startswith("zh-")


def is_local_model(lang: str) -> bool:
    """로컬 모델 사용 여부 (ko, en)"""
    return lang in ("ko", "en")


def is_cloud_model(lang: str) -> bool:
    """클라우드 모델 사용 여부 (zh-Hans, zh-Hant)"""
    return is_chinese(lang)


def detect_from_text(
    sample: str, browser_hint: Optional[str] = None, min_chars: int = 3
) -> str:
    """
    텍스트 샘플에서 언어 감지 (혼합 언어 지원).

    문자 비율 기반 간단 감지:
    - 한글 비율이 가장 높으면 → ko
    - 영문 비율이 가장 높으면 → en
    - 중문 비율이 가장 높으면 → zh-Hans 또는 zh-Hant (브라우저 힌트 참고)

    Args:
        sample: 분석할 텍스트 샘플 (최대 200자 권장)
        browser_hint: Accept-Language 헤더 (중문 간/번 구분용)
        min_chars: 최소 문자 수 (이하면 browser_hint 사용)

    Returns:
        감지된 언어 코드

    Example:
        >>> detect_from_text("안녕하세요")
        'ko'
        >>> detect_from_text("Hello world")
        'en'
        >>> detect_from_text("你好世界", browser_hint="zh-TW")
        'zh-Hant'
        >>> detect_from_text("이 문장은 한국어. This is English. 这是中文。")
        'ko'  # 한글 비율이 가장 높음
    """
    if not sample or len(sample) < min_chars:
        if browser_hint:
            normalized = normalize_lang_code(browser_hint)
            return normalized if normalized else DEFAULT_LANG
        return DEFAULT_LANG

    # 샘플 길이 제한 (성능)
    sample = sample[:200]

    # 각 언어 문자 카운트
    hangul_count = len(RE_HANGUL.findall(sample))
    latin_count = len(RE_LATIN.findall(sample))
    cjk_count = len(RE_CJK.findall(sample))

    total = hangul_count + latin_count + cjk_count
    if total == 0:
        if browser_hint:
            normalized = normalize_lang_code(browser_hint)
            return normalized if normalized else DEFAULT_LANG
        return DEFAULT_LANG

    # 비율 계산
    ratio_hangul = hangul_count / total
    ratio_latin = latin_count / total
    ratio_cjk = cjk_count / total

    # 가장 높은 비율의 언어 선택
    max_ratio = max(ratio_hangul, ratio_latin, ratio_cjk)

    if max_ratio == ratio_cjk:
        # 중국어: 브라우저 힌트로 간/번 구분
        hint_lang = normalize_lang_code(browser_hint) if browser_hint else None
        if hint_lang and hint_lang.startswith("zh-"):
            return hint_lang
        return "zh-Hans"  # 기본값: 간체
    elif max_ratio == ratio_hangul:
        return "ko"
    else:
        return "en"


def clamp_supported(lang: str) -> str:
    """
    언어 코드를 지원 언어로 제한.

    Args:
        lang: 언어 코드

    Returns:
        지원하는 언어 코드 또는 기본값

    Example:
        >>> clamp_supported('ko')
        'ko'
        >>> clamp_supported('ja')
        'ko'  # 기본값
    """
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
