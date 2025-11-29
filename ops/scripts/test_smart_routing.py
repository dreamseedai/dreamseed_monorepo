#!/usr/bin/env python3
"""
LLM 스마트 라우팅 테스트 스크립트
=================================
Accept-Language 기반 언어 감지 및 모델 라우팅 테스트.

Usage:
    python ops/scripts/test_smart_routing.py
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from shared.llm.lang_detect import (
    parse_accept_language,
    normalize_lang_code,
    detect_language,
    is_chinese,
    is_local_model,
    is_cloud_model,
)


def test_parse_accept_language():
    """Accept-Language 헤더 파싱 테스트"""
    print("\n=== Accept-Language 파싱 테스트 ===")

    test_cases = [
        (
            "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            [("ko-KR", 1.0), ("ko", 0.9), ("en-US", 0.8), ("en", 0.7)],
        ),
        ("zh-Hans,zh;q=0.9,en;q=0.8", [("zh-Hans", 1.0), ("zh", 0.9), ("en", 0.8)]),
        ("en-US,en;q=0.9", [("en-US", 1.0), ("en", 0.9)]),
        ("", []),
    ]

    for header, expected in test_cases:
        result = parse_accept_language(header)
        status = "✓" if result == expected else "✗"
        print(f"{status} {header!r}")
        if result != expected:
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")


def test_normalize_lang_code():
    """언어 코드 정규화 테스트"""
    print("\n=== 언어 코드 정규화 테스트 ===")

    test_cases = [
        ("ko", "ko"),
        ("ko-KR", "ko"),
        ("ko-kr", "ko"),
        ("en", "en"),
        ("en-US", "en"),
        ("en-GB", "en"),
        ("zh", "zh-Hans"),
        ("zh-Hans", "zh-Hans"),
        ("zh-CN", "zh-Hans"),
        ("zh-Hant", "zh-Hant"),
        ("zh-TW", "zh-Hant"),
        ("zh-HK", "zh-Hant"),
        ("ja", None),  # 지원하지 않는 언어
        ("fr", None),
    ]

    for code, expected in test_cases:
        result = normalize_lang_code(code)
        status = "✓" if result == expected else "✗"
        print(f"{status} {code!r:15} → {result!r}")
        if result != expected:
            print(f"  Expected: {expected!r}")


def test_detect_language():
    """언어 감지 테스트"""
    print("\n=== 언어 감지 테스트 ===")

    test_cases = [
        # (accept_language, forced_lang, cookie_lang, jwt_lang, expected)
        ("ko-KR,ko;q=0.9", None, None, None, "ko"),
        ("zh-Hans,zh;q=0.9", None, None, None, "zh-Hans"),
        ("zh-TW,zh-Hant;q=0.9", None, None, None, "zh-Hant"),
        ("en-US,en;q=0.9", None, None, None, "en"),
        # 강제 언어 우선
        ("ko-KR", "zh-Hans", None, None, "zh-Hans"),
        ("en-US", "ko", None, None, "ko"),
        # 쿠키 폴백
        (None, None, "en", None, "en"),
        ("", None, "zh-Hans", None, "zh-Hans"),
        # JWT 폴백
        (None, None, None, "ko", "ko"),
        ("", None, "", "zh-Hant", "zh-Hant"),
        # 우선순위 테스트 (강제 > Accept-Language > 쿠키 > JWT)
        ("ko-KR", "en", "zh-Hans", "zh-Hant", "en"),
        ("ko-KR", None, "en", "zh-Hans", "ko"),
        (None, None, "en", "zh-Hans", "en"),
        # 기본값 폴백
        (None, None, None, None, "ko"),
        ("", "", "", "", "ko"),
    ]

    for accept, forced, cookie, jwt, expected in test_cases:
        result = detect_language(
            accept_language=accept, forced_lang=forced, cookie_lang=cookie, jwt_lang=jwt
        )
        status = "✓" if result == expected else "✗"
        print(f"{status} Accept={accept!r:20} Forced={forced!r:10} → {result!r}")
        if result != expected:
            print(f"  Expected: {expected!r}")


def test_language_checks():
    """언어 타입 체크 함수 테스트"""
    print("\n=== 언어 타입 체크 테스트 ===")

    test_cases = [
        ("ko", False, True, False),  # (is_chinese, is_local, is_cloud)
        ("en", False, True, False),
        ("zh-Hans", True, False, True),
        ("zh-Hant", True, False, True),
    ]

    for lang, expect_chinese, expect_local, expect_cloud in test_cases:
        chinese = is_chinese(lang)
        local = is_local_model(lang)
        cloud = is_cloud_model(lang)

        status = (
            "✓"
            if (
                chinese == expect_chinese
                and local == expect_local
                and cloud == expect_cloud
            )
            else "✗"
        )

        print(f"{status} {lang:10} → Chinese={chinese}, Local={local}, Cloud={cloud}")
        if status == "✗":
            print(
                f"  Expected: Chinese={expect_chinese}, Local={expect_local}, Cloud={expect_cloud}"
            )


def test_routing_decision():
    """라우팅 결정 테스트"""
    print("\n=== 라우팅 결정 테스트 ===")

    from shared.llm.smart_router import SmartRouter
    from shared.config.llm import CFG

    router = SmartRouter()

    test_cases = [
        ("ko", "local", CFG.model_ko),
        ("en", "local", CFG.model_en),
        ("zh-Hans", "cloud", CFG.model_zh),
        ("zh-Hant", "cloud", CFG.model_zh),
    ]

    for lang, expected_type, expected_model in test_cases:
        client, model = router.choose_client(lang)

        actual_type = "cloud" if is_chinese(lang) else "local"
        status = (
            "✓" if (actual_type == expected_type and model == expected_model) else "✗"
        )

        print(f"{status} {lang:10} → {actual_type:6} / {model}")
        if status == "✗":
            print(f"  Expected: {expected_type} / {expected_model}")


def main():
    """모든 테스트 실행"""
    print("=" * 60)
    print("LLM 스마트 라우팅 테스트")
    print("=" * 60)

    try:
        test_parse_accept_language()
        test_normalize_lang_code()
        test_detect_language()
        test_language_checks()
        test_routing_decision()

        print("\n" + "=" * 60)
        print("✓ 모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
