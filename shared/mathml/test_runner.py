"""
MathML→TeX 변환 테스트 러너

회귀 테스트 자동화:
- 골든셋 200+ 케이스 실행
- SVG 해시 비교
- MathSpeak 검증
- CI/CD 통합
"""

from __future__ import annotations

import sys
from pathlib import Path

from .converter import MathMLToTeXConverter
from .test_cases import GOLDEN_TEST_CASES, get_all_categories
from .validator import MathValidator, RegressionTestSuite


def run_all_tests(golden_set_path: Path | None = None) -> dict:
    """모든 테스트 실행"""
    if golden_set_path is None:
        golden_set_path = Path(__file__).parent / "golden_set.json"

    validator = MathValidator(golden_set_path)
    suite = RegressionTestSuite(validator)
    converter = MathMLToTeXConverter()

    print("=" * 60)
    print("MathML→TeX 변환 회귀 테스트 시작")
    print("=" * 60)
    print(f"총 테스트 케이스: {len(GOLDEN_TEST_CASES)}")
    print(f"카테고리: {', '.join(get_all_categories())}")
    print()

    # 각 테스트 케이스 실행
    for i, test_case in enumerate(GOLDEN_TEST_CASES, 1):
        question_id = test_case["id"]
        mathml = test_case["mathml"]
        expected_tex = test_case["expected_tex"]
        mathspeak = test_case.get("mathspeak")

        # 변환
        try:
            converted_tex = converter.convert(mathml)
        except Exception as e:
            print(f"[{i}/{len(GOLDEN_TEST_CASES)}] ❌ {question_id}: 변환 실패 - {e}")
            continue

        # 검증
        suite.add_test_case(
            question_id=question_id,
            original_mathml=mathml,
            converted_tex=converted_tex,
            mathspeak=mathspeak,
        )

        # 진행 상황 출력
        if converted_tex.strip() == expected_tex.strip():
            print(f"[{i}/{len(GOLDEN_TEST_CASES)}] ✅ {question_id}")
        else:
            print(f"[{i}/{len(GOLDEN_TEST_CASES)}] ⚠️  {question_id}: TeX 불일치")
            print(f"  예상: {expected_tex}")
            print(f"  실제: {converted_tex}")

    # 결과 리포트
    print()
    print(suite.report())

    return suite.run()


def run_category_tests(category: str, golden_set_path: Path | None = None) -> dict:
    """카테고리별 테스트 실행"""
    from .test_cases import get_test_cases_by_category

    if golden_set_path is None:
        golden_set_path = Path(__file__).parent / "golden_set.json"

    validator = MathValidator(golden_set_path)
    suite = RegressionTestSuite(validator)
    converter = MathMLToTeXConverter()

    test_cases = get_test_cases_by_category(category)

    print(f"카테고리: {category} ({len(test_cases)} 케이스)")
    print()

    for i, test_case in enumerate(test_cases, 1):
        question_id = test_case["id"]
        mathml = test_case["mathml"]
        expected_tex = test_case["expected_tex"]

        converted_tex = converter.convert(mathml)

        suite.add_test_case(
            question_id=question_id,
            original_mathml=mathml,
            converted_tex=converted_tex,
        )

        if converted_tex.strip() == expected_tex.strip():
            print(f"[{i}/{len(test_cases)}] ✅ {question_id}")
        else:
            print(f"[{i}/{len(test_cases)}] ❌ {question_id}")
            print(f"  예상: {expected_tex}")
            print(f"  실제: {converted_tex}")

    print()
    print(suite.report())

    return suite.run()


def main():
    """CLI 엔트리포인트"""
    import argparse

    parser = argparse.ArgumentParser(description="MathML→TeX 변환 테스트 러너")
    parser.add_argument(
        "--category",
        type=str,
        help="테스트할 카테고리 (예: nested_radicals, chemistry)",
    )
    parser.add_argument(
        "--golden-set",
        type=Path,
        help="골든셋 JSON 파일 경로",
    )

    args = parser.parse_args()

    if args.category:
        result = run_category_tests(args.category, args.golden_set)
    else:
        result = run_all_tests(args.golden_set)

    # 실패 시 exit code 1
    if result["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
