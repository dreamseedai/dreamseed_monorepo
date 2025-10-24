#!/usr/bin/env python3
"""
실제 OpenAI API를 사용한 AI MathML to MathLive 변환기
"""

import hashlib
import json
import os
import re
from datetime import datetime
from typing import Optional

from ai_client import get_model, get_openai_client


# .env 파일에서 환경변수 로드
def load_env_file():
    """Load environment variables from .env file"""
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass  # .env 파일이 없어도 계속 진행


# .env 파일 로드
load_env_file()


class RealAIMathMLConverter:
    """실제 OpenAI API를 사용한 MathML 변환기"""

    def __init__(self, api_key: Optional[str] = None):
        """초기화"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경변수를 설정하거나 api_key 매개변수를 제공하세요."
            )

        # ai_client.get_openai_client() internally respects OPENAI_BASE_URL/USE_LOCAL_LLM
        self.client = get_openai_client(self.api_key)
        self.cache = {}
        self.conversion_count = 0

    def convert_mathml_to_mathlive(self, mathml_content: str) -> dict:
        """MathML을 MathLive 호환 LaTeX로 변환"""
        self.conversion_count += 1

        # 캐시 확인
        # Use a stable cache key (hashlib) instead of Python's randomized hash()
        cache_key = hashlib.sha1(mathml_content.encode("utf-8")).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # GPT 프롬프트 구성
            prompt = self._create_conversion_prompt(mathml_content)

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=get_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in mathematical notation conversion from MathML to LaTeX suitable for MathLive rendering. Provide only the LaTeX output without any explanations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.1,  # 낮은 온도로 일관성 있는 결과
            )

            latex_output = response.choices[0].message.content.strip()

            # 결과 검증 및 후처리
            latex_output = self._post_process_latex(latex_output)
            confidence = self._calculate_confidence(mathml_content, latex_output)

            usage = getattr(response, "usage", None) or {}
            result = {
                "original_mathml": mathml_content,
                "converted_latex": latex_output,
                "confidence": confidence,
                "status": "success" if confidence > 0.7 else "needs_review",
                "api_usage": {
                    "prompt_tokens": (
                        getattr(usage, "prompt_tokens", 0)
                        if hasattr(usage, "prompt_tokens")
                        else usage.get("prompt_tokens", 0)
                    ),
                    "completion_tokens": (
                        getattr(usage, "completion_tokens", 0)
                        if hasattr(usage, "completion_tokens")
                        else usage.get("completion_tokens", 0)
                    ),
                    "total_tokens": (
                        getattr(usage, "total_tokens", 0)
                        if hasattr(usage, "total_tokens")
                        else usage.get("total_tokens", 0)
                    ),
                },
            }

            # 캐시에 저장
            self.cache[cache_key] = result
            return result

        except Exception as e:
            return {
                "original_mathml": mathml_content,
                "converted_latex": f"Error: {str(e)}",
                "confidence": 0.0,
                "status": "error",
                "error": str(e),
            }

    def _create_conversion_prompt(self, mathml_content: str) -> str:
        """변환을 위한 프롬프트 생성"""
        return f"""
Convert the following MathML to LaTeX suitable for MathLive rendering:

MathML:
{mathml_content}

Instructions:
1. Parse and understand the mathematical expression
2. Convert to standard LaTeX syntax
3. Use display mode (\\[ ... \\]) for complex expressions like matrices, summations, integrals
4. Use inline mode ($ ... $) for simple expressions
5. Ensure MathLive compatibility
6. Provide ONLY the LaTeX output, no explanations

LaTeX Output:
"""

    def _post_process_latex(self, latex: str) -> str:
        """LaTeX 후처리"""
        # 불필요한 텍스트 제거
        latex = re.sub(r"^LaTeX Output:\s*", "", latex, flags=re.IGNORECASE)
        latex = re.sub(r"^Output:\s*", "", latex, flags=re.IGNORECASE)
        latex = latex.strip()

        # 따옴표 제거
        if latex.startswith('"') and latex.endswith('"'):
            latex = latex[1:-1]
        if latex.startswith("'") and latex.endswith("'"):
            latex = latex[1:-1]

        return latex

    def _calculate_confidence(self, mathml: str, latex: str) -> float:
        """신뢰도 계산"""
        confidence = 0.8  # 기본 신뢰도

        # 에러 체크
        if "error" in latex.lower():
            return 0.0

        # 복잡도에 따른 조정
        complexity_indicators = ["<mtable>", "<munderover>", "<msubsup>", "<mfrac>"]
        complexity = sum(
            1 for indicator in complexity_indicators if indicator in mathml
        )

        if complexity > 2:
            confidence -= 0.1
        elif complexity == 0:
            confidence += 0.1

        # LaTeX 품질 체크
        if "\\[" in latex or "\\(" in latex:
            confidence += 0.05  # 수학 모드 사용

        return min(1.0, max(0.0, confidence))

    def process_html_with_mathml(self, html_content: str) -> str:
        """HTML 내용에서 MathML을 찾아 변환"""
        mathml_pattern = r"<math[^>]*>.*?</math>"
        mathml_tags = re.findall(mathml_pattern, html_content, re.DOTALL)

        processed_content = html_content
        for mathml in mathml_tags:
            result = self.convert_mathml_to_mathlive(mathml)
            if result["status"] == "success":
                processed_content = processed_content.replace(
                    mathml, result["converted_latex"]
                )
            else:
                print(f"Warning: MathML conversion failed for: {mathml[:100]}...")

        return processed_content

    def get_stats(self) -> dict:
        """변환 통계 반환"""
        return {
            "total_conversions": self.conversion_count,
            "cache_size": len(self.cache),
            "successful_conversions": sum(
                1 for result in self.cache.values() if result["status"] == "success"
            ),
            "total_tokens_used": sum(
                result.get("api_usage", {}).get("total_tokens", 0)
                for result in self.cache.values()
            ),
        }


def test_real_converter():
    """실제 API를 사용한 테스트"""
    print("=" * 80)
    print("실제 OpenAI API를 사용한 AI MathML 변환 테스트")
    print("=" * 80)
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 변환기 초기화
        converter = RealAIMathMLConverter()
        print("✅ OpenAI API 연결 성공!")
        print()

        # ID 1997의 실제 MathML 테스트
        test_cases = [
            {
                "name": "ID 1997 - 속도 (ds/dt)",
                "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mstyle displaystyle="false"><mfrac><mrow><mi>d</mi><mi>s</mi></mrow><mrow><mi>d</mi><mi>t</mi></mrow></mfrac></mstyle></math>',
                "description": "위치의 시간에 대한 1차 도함수",
            },
            {
                "name": "ID 1997 - 가속도 (d²s/dt²)",
                "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mstyle displaystyle="false"><mfrac><mrow><msup><mi>d</mi><mn>2</mn></msup><mi>s</mi></mrow><mrow><mi>d</mi><msup><mi>t</mi><mn>2</mn></msup></mrow></mfrac></mstyle></math>',
                "description": "위치의 시간에 대한 2차 도함수",
            },
        ]

        results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"테스트 {i}: {test_case['name']}")
            print("-" * 60)
            print(f"설명: {test_case['description']}")
            print()
            print("원본 MathML:")
            print(f"  {test_case['mathml']}")
            print()

            # 변환 실행
            result = converter.convert_mathml_to_mathlive(test_case["mathml"])

            print("AI 변환 결과:")
            print(f"  LaTeX 출력: {result['converted_latex']}")
            print(f"  신뢰도: {result['confidence']:.2f}")
            print(f"  상태: {result['status']}")
            if "api_usage" in result:
                print(f"  API 사용량: {result['api_usage']['total_tokens']} 토큰")
            print()

            results.append(
                {
                    "test_name": test_case["name"],
                    "original_mathml": test_case["mathml"],
                    "converted_latex": result["converted_latex"],
                    "confidence": result["confidence"],
                    "status": result["status"],
                }
            )

            print("=" * 60)
            print()

        # 통계 출력
        stats = converter.get_stats()
        print("변환 통계:")
        print(f"  총 변환 횟수: {stats['total_conversions']}")
        print(f"  성공한 변환: {stats['successful_conversions']}")
        print(f"  총 사용 토큰: {stats['total_tokens_used']}")
        print()

        # 결과 저장
        output_file = "real_ai_conversion_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "test_time": datetime.now().isoformat(),
                    "stats": stats,
                    "results": results,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"상세 결과가 저장되었습니다: {output_file}")
        print()
        print("🎉 실제 AI 변환 테스트 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        print("API 키 설정과 네트워크 연결을 확인해주세요.")


if __name__ == "__main__":
    test_real_converter()
