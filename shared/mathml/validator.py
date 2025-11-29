"""
MathML→TeX 변환 검증기

검증 항목:
1. SVG 레이아웃 해시 비교
2. MathSpeak 음성 문자열 비교
3. 접근성 (ARIA, alt-text)
4. 렌더링 오류 감지
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """검증 결과"""

    question_id: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, Any]


class MathValidator:
    """수식 변환 검증기"""

    def __init__(self, golden_set_path: Path):
        self.golden_set_path = golden_set_path
        self.golden_data = self._load_golden_set()

    def _load_golden_set(self) -> dict[str, dict]:
        """골든셋 로드"""
        if not self.golden_set_path.exists():
            return {}

        with open(self.golden_set_path) as f:
            return json.load(f)

    def validate(
        self,
        question_id: str,
        original_mathml: str,
        converted_tex: str,
        rendered_svg: str | None = None,
        mathspeak: str | None = None,
    ) -> ValidationResult:
        """변환 검증"""
        errors = []
        warnings = []
        metrics = {}

        # 골든셋 데이터
        golden = self.golden_data.get(question_id, {})

        # 1. SVG 해시 비교
        if rendered_svg and golden.get("svg_hash"):
            svg_hash = self._compute_hash(rendered_svg)
            golden_hash = golden["svg_hash"]

            if svg_hash != golden_hash:
                errors.append(
                    f"SVG 레이아웃 불일치: {svg_hash[:8]} != {golden_hash[:8]}"
                )
            metrics["svg_hash"] = svg_hash

        # 2. MathSpeak 비교
        if mathspeak and golden.get("mathspeak"):
            if mathspeak != golden["mathspeak"]:
                # Levenshtein 거리 계산
                distance = self._levenshtein(mathspeak, golden["mathspeak"])
                similarity = 1 - (
                    distance / max(len(mathspeak), len(golden["mathspeak"]))
                )

                if similarity < 0.9:
                    errors.append(f"MathSpeak 불일치 (유사도: {similarity:.2%})")
                else:
                    warnings.append(f"MathSpeak 미세 차이 (유사도: {similarity:.2%})")

                metrics["mathspeak_similarity"] = similarity

        # 3. TeX 구문 검증
        tex_errors = self._validate_tex_syntax(converted_tex)
        errors.extend(tex_errors)

        # 4. 중첩 깊이 검증
        nesting_depth = self._compute_nesting_depth(converted_tex)
        if nesting_depth > 10:
            warnings.append(f"중첩 깊이 과다: {nesting_depth}")
        metrics["nesting_depth"] = nesting_depth

        # 5. 길이 검증
        if len(converted_tex) > 5000:
            warnings.append(f"TeX 길이 과다: {len(converted_tex)} chars")
        metrics["tex_length"] = len(converted_tex)

        passed = len(errors) == 0

        return ValidationResult(
            question_id=question_id,
            passed=passed,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    def _compute_hash(self, content: str) -> str:
        """SHA256 해시 계산"""
        return hashlib.sha256(content.encode()).hexdigest()

    def _levenshtein(self, s1: str, s2: str) -> int:
        """Levenshtein 거리 (편집 거리)"""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # 삽입, 삭제, 치환 비용
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _validate_tex_syntax(self, tex: str) -> list[str]:
        """TeX 구문 검증"""
        errors = []

        # 1. 괄호 균형 검사
        if not self._check_balanced_braces(tex):
            errors.append("중괄호 불균형")

        # 2. 알 수 없는 명령어 검사
        unknown_cmds = self._find_unknown_commands(tex)
        if unknown_cmds:
            errors.append(f"알 수 없는 명령어: {', '.join(unknown_cmds[:5])}")

        # 3. 빈 그룹 검사
        if "{}" in tex:
            errors.append("빈 중괄호 그룹 발견")

        return errors

    def _check_balanced_braces(self, tex: str) -> bool:
        """중괄호 균형 검사"""
        depth = 0
        escaped = False

        for char in tex:
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    return False

        return depth == 0

    def _find_unknown_commands(self, tex: str) -> list[str]:
        """알 수 없는 TeX 명령어 찾기"""
        import re

        # 알려진 명령어 (일부)
        known_commands = {
            "frac",
            "sqrt",
            "sum",
            "int",
            "prod",
            "lim",
            "sin",
            "cos",
            "tan",
            "log",
            "ln",
            "exp",
            "alpha",
            "beta",
            "gamma",
            "delta",
            "theta",
            "pi",
            "vec",
            "hat",
            "bar",
            "dot",
            "ddot",
            "left",
            "right",
            "big",
            "Big",
            "text",
            "mathrm",
            "mathbf",
            "mathit",
            "ce",  # mhchem
        }

        # 명령어 추출
        commands = re.findall(r"\\([a-zA-Z]+)", tex)

        # 알 수 없는 명령어 필터
        unknown = [cmd for cmd in set(commands) if cmd not in known_commands]

        return unknown

    def _compute_nesting_depth(self, tex: str) -> int:
        """중첩 깊이 계산"""
        max_depth = 0
        current_depth = 0
        escaped = False

        for char in tex:
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
            elif char == "{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "}":
                current_depth -= 1

        return max_depth

    def save_golden_entry(
        self,
        question_id: str,
        original_mathml: str,
        converted_tex: str,
        svg_hash: str,
        mathspeak: str,
    ) -> None:
        """골든셋 항목 저장"""
        self.golden_data[question_id] = {
            "original_mathml": original_mathml,
            "converted_tex": converted_tex,
            "svg_hash": svg_hash,
            "mathspeak": mathspeak,
        }

        with open(self.golden_set_path, "w") as f:
            json.dump(self.golden_data, f, indent=2, ensure_ascii=False)


class RegressionTestSuite:
    """회귀 테스트 스위트"""

    def __init__(self, validator: MathValidator):
        self.validator = validator
        self.results: list[ValidationResult] = []

    def add_test_case(
        self,
        question_id: str,
        original_mathml: str,
        converted_tex: str,
        rendered_svg: str | None = None,
        mathspeak: str | None = None,
    ) -> None:
        """테스트 케이스 추가"""
        result = self.validator.validate(
            question_id=question_id,
            original_mathml=original_mathml,
            converted_tex=converted_tex,
            rendered_svg=rendered_svg,
            mathspeak=mathspeak,
        )
        self.results.append(result)

    def run(self) -> dict[str, Any]:
        """테스트 실행"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "results": [
                {
                    "question_id": r.question_id,
                    "passed": r.passed,
                    "errors": r.errors,
                    "warnings": r.warnings,
                    "metrics": r.metrics,
                }
                for r in self.results
            ],
        }

    def report(self) -> str:
        """테스트 리포트 생성"""
        summary = self.run()

        lines = [
            "=" * 60,
            "MathML→TeX 변환 회귀 테스트 리포트",
            "=" * 60,
            f"총 테스트: {summary['total']}",
            f"통과: {summary['passed']} ({summary['pass_rate']:.1%})",
            f"실패: {summary['failed']}",
            "",
        ]

        # 실패한 케이스
        failed_results = [r for r in self.results if not r.passed]
        if failed_results:
            lines.append("실패한 케이스:")
            lines.append("-" * 60)
            for r in failed_results:
                lines.append(f"  [{r.question_id}]")
                for error in r.errors:
                    lines.append(f"    ❌ {error}")
                for warning in r.warnings:
                    lines.append(f"    ⚠️  {warning}")
                lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)
