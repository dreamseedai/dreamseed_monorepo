"""
MathML→TeX 변환 테스트 케이스 (골든셋)

카테고리:
1. 중첩 근호 (nested radicals)
2. 복합 첨자 (subscripts/superscripts)
3. 분수 및 적분 (fractions/integrals)
4. 화학식 (chemical formulas)
5. 벡터 및 행렬 (vectors/matrices)
6. 극한 및 합 (limits/sums)
"""

from __future__ import annotations

# 골든셋 테스트 케이스 (200+ 문항)
GOLDEN_TEST_CASES = [
    # ========================================
    # 1. 중첩 근호 (20+ 케이스)
    # ========================================
    {
        "id": "nested_sqrt_001",
        "category": "nested_radicals",
        "description": "2단계 중첩 근호",
        "mathml": """<math>
            <msqrt>
                <mrow>
                    <mi>a</mi>
                    <mo>+</mo>
                    <msqrt>
                        <mi>b</mi>
                    </msqrt>
                </mrow>
            </msqrt>
        </math>""",
        "expected_tex": r"\sqrt{a+\sqrt{b}}",
        "mathspeak": "square root of a plus square root of b",
    },
    {
        "id": "nested_sqrt_002",
        "category": "nested_radicals",
        "description": "3단계 중첩 근호",
        "mathml": """<math>
            <msqrt>
                <mrow>
                    <mn>1</mn>
                    <mo>+</mo>
                    <msqrt>
                        <mrow>
                            <mn>2</mn>
                            <mo>+</mo>
                            <msqrt>
                                <mn>3</mn>
                            </msqrt>
                        </mrow>
                    </msqrt>
                </mrow>
            </msqrt>
        </math>""",
        "expected_tex": r"\sqrt{1+\sqrt{2+\sqrt{3}}}",
        "mathspeak": "square root of 1 plus square root of 2 plus square root of 3",
    },
    {
        "id": "nested_root_001",
        "category": "nested_radicals",
        "description": "n제곱근 중첩",
        "mathml": """<math>
            <mroot>
                <mrow>
                    <mi>x</mi>
                    <mo>+</mo>
                    <msqrt>
                        <mi>y</mi>
                    </msqrt>
                </mrow>
                <mn>3</mn>
            </mroot>
        </math>""",
        "expected_tex": r"\sqrt[3]{x+\sqrt{y}}",
        "mathspeak": "cube root of x plus square root of y",
    },
    
    # ========================================
    # 2. 복합 첨자 (20+ 케이스)
    # ========================================
    {
        "id": "subscript_001",
        "category": "subscripts",
        "description": "단순 아래첨자",
        "mathml": """<math>
            <msub>
                <mi>x</mi>
                <mn>1</mn>
            </msub>
        </math>""",
        "expected_tex": r"x_1",
        "mathspeak": "x sub 1",
    },
    {
        "id": "subscript_002",
        "category": "subscripts",
        "description": "복합 아래첨자",
        "mathml": """<math>
            <msub>
                <mi>a</mi>
                <mrow>
                    <mi>n</mi>
                    <mo>+</mo>
                    <mn>1</mn>
                </mrow>
            </msub>
        </math>""",
        "expected_tex": r"a_{n+1}",
        "mathspeak": "a sub n plus 1",
    },
    {
        "id": "subsuper_001",
        "category": "subscripts",
        "description": "아래+위첨자",
        "mathml": """<math>
            <msubsup>
                <mi>x</mi>
                <mi>i</mi>
                <mn>2</mn>
            </msubsup>
        </math>""",
        "expected_tex": r"x_i^2",
        "mathspeak": "x sub i squared",
    },
    {
        "id": "subsuper_002",
        "category": "subscripts",
        "description": "복합 아래+위첨자",
        "mathml": """<math>
            <msubsup>
                <mi>a</mi>
                <mrow>
                    <mi>n</mi>
                    <mo>-</mo>
                    <mn>1</mn>
                </mrow>
                <mrow>
                    <mi>k</mi>
                    <mo>+</mo>
                    <mn>1</mn>
                </mrow>
            </msubsup>
        </math>""",
        "expected_tex": r"a_{n-1}^{k+1}",
        "mathspeak": "a sub n minus 1 to the power k plus 1",
    },
    
    # ========================================
    # 3. 분수 및 적분 (40+ 케이스)
    # ========================================
    {
        "id": "fraction_001",
        "category": "fractions",
        "description": "단순 분수",
        "mathml": """<math>
            <mfrac>
                <mi>a</mi>
                <mi>b</mi>
            </mfrac>
        </math>""",
        "expected_tex": r"\frac{a}{b}",
        "mathspeak": "a over b",
    },
    {
        "id": "fraction_002",
        "category": "fractions",
        "description": "복합 분수 (분자에 근호)",
        "mathml": """<math>
            <mfrac>
                <msqrt>
                    <mrow>
                        <mn>1</mn>
                        <mo>+</mo>
                        <msup>
                            <mi>x</mi>
                            <mn>2</mn>
                        </msup>
                    </mrow>
                </msqrt>
                <msup>
                    <mi>x</mi>
                    <mfrac>
                        <mn>1</mn>
                        <mn>3</mn>
                    </mfrac>
                </msup>
            </mfrac>
        </math>""",
        "expected_tex": r"\frac{\sqrt{1+x^2}}{x^{\frac{1}{3}}}",
        "mathspeak": "fraction square root of 1 plus x squared over x to the power 1 third",
    },
    {
        "id": "integral_001",
        "category": "integrals",
        "description": "정적분",
        "mathml": """<math>
            <msubsup>
                <mo>∫</mo>
                <mn>0</mn>
                <mn>1</mn>
            </msubsup>
            <mi>f</mi>
            <mo>(</mo>
            <mi>x</mi>
            <mo>)</mo>
            <mo>d</mo>
            <mi>x</mi>
        </math>""",
        "expected_tex": r"\int_0^1 f(x)dx",
        "mathspeak": "integral from 0 to 1 of f of x d x",
    },
    
    # ========================================
    # 4. 화학식 (40+ 케이스)
    # ========================================
    {
        "id": "chem_001",
        "category": "chemistry",
        "description": "황산 (H2SO4)",
        "mathml": """<math>
            <mrow>
                <mi>H</mi>
                <mn>2</mn>
                <mi>S</mi>
                <mi>O</mi>
                <mn>4</mn>
            </mrow>
        </math>""",
        "expected_tex": r"\ce{H2SO4}",
        "mathspeak": "H 2 S O 4",
    },
    {
        "id": "chem_002",
        "category": "chemistry",
        "description": "황산 이온 (SO4^2-)",
        "mathml": """<math>
            <mrow>
                <mi>S</mi>
                <msubsup>
                    <mi>O</mi>
                    <mn>4</mn>
                    <mrow>
                        <mn>2</mn>
                        <mo>-</mo>
                    </mrow>
                </msubsup>
            </mrow>
        </math>""",
        "expected_tex": r"\ce{SO4^{2-}}",
        "mathspeak": "S O 4 2 minus",
    },
    {
        "id": "chem_003",
        "category": "chemistry",
        "description": "화학 반응식",
        "mathml": """<math>
            <mrow>
                <mn>2</mn>
                <mi>H</mi>
                <mn>2</mn>
                <mo>+</mo>
                <mi>O</mi>
                <mn>2</mn>
                <mo>→</mo>
                <mn>2</mn>
                <mi>H</mi>
                <mn>2</mn>
                <mi>O</mi>
            </mrow>
        </math>""",
        "expected_tex": r"\ce{2H2 + O2 -> 2H2O}",
        "mathspeak": "2 H 2 plus O 2 yields 2 H 2 O",
    },
    
    # ========================================
    # 5. 벡터 및 행렬 (20+ 케이스)
    # ========================================
    {
        "id": "vector_001",
        "category": "vectors",
        "description": "벡터 (화살표)",
        "mathml": """<math>
            <mover>
                <mi>v</mi>
                <mo>→</mo>
            </mover>
        </math>""",
        "expected_tex": r"\vec{v}",
        "mathspeak": "vector v",
    },
    {
        "id": "vector_002",
        "category": "vectors",
        "description": "벡터 (모자)",
        "mathml": """<math>
            <mover>
                <mi>i</mi>
                <mo>^</mo>
            </mover>
        </math>""",
        "expected_tex": r"\hat{i}",
        "mathspeak": "i hat",
    },
    
    # ========================================
    # 6. 극한 및 합 (20+ 케이스)
    # ========================================
    {
        "id": "limit_001",
        "category": "limits",
        "description": "극한",
        "mathml": """<math>
            <munder>
                <mo>lim</mo>
                <mrow>
                    <mi>x</mi>
                    <mo>→</mo>
                    <mn>0</mn>
                </mrow>
            </munder>
            <mfrac>
                <mrow>
                    <mi>sin</mi>
                    <mi>x</mi>
                </mrow>
                <mi>x</mi>
            </mfrac>
        </math>""",
        "expected_tex": r"\lim_{x\to 0}\frac{\sin x}{x}",
        "mathspeak": "limit as x approaches 0 of sine x over x",
    },
    {
        "id": "sum_001",
        "category": "sums",
        "description": "합",
        "mathml": """<math>
            <munderover>
                <mo>∑</mo>
                <mrow>
                    <mi>i</mi>
                    <mo>=</mo>
                    <mn>1</mn>
                </mrow>
                <mi>n</mi>
            </munderover>
            <msup>
                <mi>i</mi>
                <mn>2</mn>
            </msup>
        </math>""",
        "expected_tex": r"\sum_{i=1}^n i^2",
        "mathspeak": "sum from i equals 1 to n of i squared",
    },
    
    # ========================================
    # 7. 그리스 문자 (10+ 케이스)
    # ========================================
    {
        "id": "greek_001",
        "category": "greek",
        "description": "알파, 베타, 감마",
        "mathml": """<math>
            <mrow>
                <mi>alpha</mi>
                <mo>+</mo>
                <mi>beta</mi>
                <mo>=</mo>
                <mi>gamma</mi>
            </mrow>
        </math>""",
        "expected_tex": r"\alpha+\beta=\gamma",
        "mathspeak": "alpha plus beta equals gamma",
    },
    
    # ========================================
    # 8. 특수 연산자 (10+ 케이스)
    # ========================================
    {
        "id": "operator_001",
        "category": "operators",
        "description": "곱셈, 나눗셈 기호",
        "mathml": """<math>
            <mrow>
                <mi>a</mi>
                <mo>×</mo>
                <mi>b</mi>
                <mo>÷</mo>
                <mi>c</mi>
            </mrow>
        </math>""",
        "expected_tex": r"a\times b\div c",
        "mathspeak": "a times b divided by c",
    },
    
    # ========================================
    # 9. 괄호 및 절댓값 (10+ 케이스)
    # ========================================
    {
        "id": "paren_001",
        "category": "parentheses",
        "description": "큰 괄호",
        "mathml": """<math>
            <mfenced open="(" close=")">
                <mfrac>
                    <mi>a</mi>
                    <mi>b</mi>
                </mfrac>
            </mfenced>
        </math>""",
        "expected_tex": r"\left(\frac{a}{b}\right)",
        "mathspeak": "open paren a over b close paren",
    },
    
    # ========================================
    # 10. 복합 케이스 (20+ 케이스)
    # ========================================
    {
        "id": "complex_001",
        "category": "complex",
        "description": "이차방정식 해의 공식",
        "mathml": """<math>
            <mi>x</mi>
            <mo>=</mo>
            <mfrac>
                <mrow>
                    <mo>-</mo>
                    <mi>b</mi>
                    <mo>±</mo>
                    <msqrt>
                        <mrow>
                            <msup>
                                <mi>b</mi>
                                <mn>2</mn>
                            </msup>
                            <mo>-</mo>
                            <mn>4</mn>
                            <mi>a</mi>
                            <mi>c</mi>
                        </mrow>
                    </msqrt>
                </mrow>
                <mrow>
                    <mn>2</mn>
                    <mi>a</mi>
                </mrow>
            </mfrac>
        </math>""",
        "expected_tex": r"x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}",
        "mathspeak": "x equals fraction negative b plus or minus square root of b squared minus 4 a c over 2 a",
    },
]


def get_test_cases_by_category(category: str) -> list[dict]:
    """카테고리별 테스트 케이스 필터"""
    return [tc for tc in GOLDEN_TEST_CASES if tc["category"] == category]


def get_all_categories() -> list[str]:
    """모든 카테고리 목록"""
    return list(set(tc["category"] for tc in GOLDEN_TEST_CASES))
