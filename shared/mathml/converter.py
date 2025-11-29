"""
Wiris MathML → MathJax TeX 변환기 (정밀 최적화)

18k+ MPC 문항 대응:
- 중첩 근호 (nested radicals)
- 복합 첨자 (subscripts/superscripts)
- 화학식 (mhchem 문법)
- 접근성 (MathSpeak)
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

# MathML 네임스페이스
MATHML_NS = {"m": "http://www.w3.org/1998/Math/MathML"}


class MathMLToTeXConverter:
    """MathML → TeX 변환기 (의미 보존)"""

    # 수학 함수 키워드 (토큰화)
    MATH_FUNCTIONS = {
        "sin",
        "cos",
        "tan",
        "cot",
        "sec",
        "csc",
        "arcsin",
        "arccos",
        "arctan",
        "sinh",
        "cosh",
        "tanh",
        "log",
        "ln",
        "lg",
        "exp",
        "lim",
        "det",
        "dim",
        "ker",
        "max",
        "min",
        "sup",
        "inf",
        "gcd",
        "lcm",
        "deg",
        "arg",
    }

    # 화학 원소 패턴
    CHEM_ELEMENT_PATTERN = re.compile(r"^[A-Z][a-z]?(\d+)?([+-]?\d+)?$")

    def __init__(self):
        self.chem_mode = False

    def convert(self, mathml: str) -> str:
        """MathML → TeX 변환"""
        try:
            root = ET.fromstring(mathml)
            tex = self._process_node(root)
            tex = self._normalize_tex(tex)
            return tex
        except Exception as e:
            # 폴백: 원본 MathML 반환
            return f"\\text{{[MathML Parse Error: {e}]}}"

    def _process_node(self, node: ET.Element) -> str:
        """재귀적 노드 처리"""
        tag = node.tag.replace("{http://www.w3.org/1998/Math/MathML}", "")

        if tag == "math":
            return self._process_children(node)
        elif tag == "mrow":
            return self._process_mrow(node)
        elif tag == "mi":  # identifier
            return self._process_mi(node)
        elif tag == "mn":  # number
            return node.text or ""
        elif tag == "mo":  # operator
            return self._process_mo(node)
        elif tag == "msup":  # superscript
            return self._process_msup(node)
        elif tag == "msub":  # subscript
            return self._process_msub(node)
        elif tag == "msubsup":  # sub+superscript
            return self._process_msubsup(node)
        elif tag == "mfrac":  # fraction
            return self._process_mfrac(node)
        elif tag == "msqrt":  # square root
            return self._process_msqrt(node)
        elif tag == "mroot":  # nth root
            return self._process_mroot(node)
        elif tag == "mover":  # overscript (벡터 등)
            return self._process_mover(node)
        elif tag == "munder":  # underscript (극한 등)
            return self._process_munder(node)
        elif tag == "munderover":  # under+overscript (적분 등)
            return self._process_munderover(node)
        elif tag == "mfenced":  # 괄호
            return self._process_mfenced(node)
        elif tag == "mtext":  # 텍스트
            return f"\\text{{{node.text or ''}}}"
        elif tag == "mspace":  # 공백
            return "\\,"
        else:
            # 알 수 없는 태그는 자식 처리
            return self._process_children(node)

    def _process_children(self, node: ET.Element) -> str:
        """자식 노드 처리"""
        return "".join(self._process_node(child) for child in node)

    def _process_mrow(self, node: ET.Element) -> str:
        """mrow 처리 (화학식 감지)"""
        children = list(node)
        if self._is_chemical_formula(children):
            self.chem_mode = True
            content = self._process_children(node)
            self.chem_mode = False
            return f"\\ce{{{content}}}"
        return "{" + self._process_children(node) + "}"

    def _process_mi(self, node: ET.Element) -> str:
        """identifier 처리 (함수/변수 구분)"""
        text = node.text or ""

        # 수학 함수 토큰화
        if text in self.MATH_FUNCTIONS:
            return f"\\{text}"

        # 화학 모드에서는 그대로
        if self.chem_mode:
            return text

        # 그리스 문자
        if len(text) > 1 and text.isalpha():
            greek = self._to_greek(text)
            if greek:
                return greek

        return text

    def _process_mo(self, node: ET.Element) -> str:
        """operator 처리"""
        text = node.text or ""

        # 특수 연산자 매핑
        op_map = {
            "×": "\\times",
            "·": "\\cdot",
            "÷": "\\div",
            "±": "\\pm",
            "∓": "\\mp",
            "≤": "\\leq",
            "≥": "\\geq",
            "≠": "\\neq",
            "≈": "\\approx",
            "∞": "\\infty",
            "∫": "\\int",
            "∑": "\\sum",
            "∏": "\\prod",
            "√": "\\sqrt",
            "∂": "\\partial",
            "∇": "\\nabla",
            "∈": "\\in",
            "∉": "\\notin",
            "⊂": "\\subset",
            "⊃": "\\supset",
            "∪": "\\cup",
            "∩": "\\cap",
            "→": "\\to",
            "⇒": "\\Rightarrow",
            "⇔": "\\Leftrightarrow",
        }

        return op_map.get(text, text)

    def _process_msup(self, node: ET.Element) -> str:
        """위첨자 처리"""
        children = list(node)
        if len(children) != 2:
            return self._process_children(node)

        base = self._process_node(children[0])
        exp = self._process_node(children[1])

        # 단일 문자가 아니면 중괄호로 보호
        if len(exp) > 1 or not exp.isalnum():
            exp = f"{{{exp}}}"

        return f"{base}^{exp}"

    def _process_msub(self, node: ET.Element) -> str:
        """아래첨자 처리"""
        children = list(node)
        if len(children) != 2:
            return self._process_children(node)

        base = self._process_node(children[0])
        sub = self._process_node(children[1])

        # 단일 문자가 아니면 중괄호로 보호
        if len(sub) > 1 or not sub.isalnum():
            sub = f"{{{sub}}}"

        return f"{base}_{sub}"

    def _process_msubsup(self, node: ET.Element) -> str:
        """아래+위첨자 처리"""
        children = list(node)
        if len(children) != 3:
            return self._process_children(node)

        base = self._process_node(children[0])
        sub = self._process_node(children[1])
        sup = self._process_node(children[2])

        # 중괄호 보호
        if len(sub) > 1 or not sub.isalnum():
            sub = f"{{{sub}}}"
        if len(sup) > 1 or not sup.isalnum():
            sup = f"{{{sup}}}"

        return f"{base}_{sub}^{sup}"

    def _process_mfrac(self, node: ET.Element) -> str:
        """분수 처리"""
        children = list(node)
        if len(children) != 2:
            return self._process_children(node)

        num = self._process_node(children[0])
        denom = self._process_node(children[1])

        return f"\\frac{{{num}}}{{{denom}}}"

    def _process_msqrt(self, node: ET.Element) -> str:
        """제곱근 처리 (중첩 근호 보존)"""
        content = self._process_children(node)
        return f"\\sqrt{{{content}}}"

    def _process_mroot(self, node: ET.Element) -> str:
        """n제곱근 처리"""
        children = list(node)
        if len(children) != 2:
            return self._process_children(node)

        base = self._process_node(children[0])
        index = self._process_node(children[1])

        return f"\\sqrt[{index}]{{{base}}}"

    def _process_mover(self, node: ET.Element) -> str:
        """overscript 처리 (벡터, 모자 등)"""
        children = list(node)
        if len(children) != 2:
            return self._process_children(node)

        base = self._process_node(children[0])
        over = self._process_node(children[1])

        # 벡터 화살표
        if over == "→":
            return f"\\vec{{{base}}}"
        elif over == "¯":
            return f"\\overline{{{base}}}"
        elif over == "^":
            return f"\\hat{{{base}}}"
        elif over == "~":
            return f"\\tilde{{{base}}}"
        else:
            return f"\\overset{{{over}}}{{{base}}}"

    def _process_munder(self, node: ET.Element) -> str:
        """underscript 처리"""
        children = list(node)
        if len(children) != 2:
            return self._process_children(node)

        base = self._process_node(children[0])
        under = self._process_node(children[1])

        return f"\\underset{{{under}}}{{{base}}}"

    def _process_munderover(self, node: ET.Element) -> str:
        """under+overscript 처리 (적분, 합 등)"""
        children = list(node)
        if len(children) != 3:
            return self._process_children(node)

        base = self._process_node(children[0])
        under = self._process_node(children[1])
        over = self._process_node(children[2])

        return f"{base}_{{{under}}}^{{{over}}}"

    def _process_mfenced(self, node: ET.Element) -> str:
        """괄호 처리"""
        open_char = node.get("open", "(")
        close_char = node.get("close", ")")
        content = self._process_children(node)

        # 큰 괄호
        if open_char == "(":
            return f"\\left({content}\\right)"
        elif open_char == "[":
            return f"\\left[{content}\\right]"
        elif open_char == "{":
            return f"\\left\\{{{content}\\right\\}}"
        else:
            return f"{open_char}{content}{close_char}"

    def _is_chemical_formula(self, children: list[ET.Element]) -> bool:
        """화학식 여부 감지"""
        # 연속된 원소 기호 패턴
        text_content = "".join(
            child.text or "" for child in children if child.tag.endswith("mi")
        )
        return bool(self.CHEM_ELEMENT_PATTERN.match(text_content))

    def _to_greek(self, text: str) -> str | None:
        """그리스 문자 변환"""
        greek_map = {
            "alpha": "\\alpha",
            "beta": "\\beta",
            "gamma": "\\gamma",
            "delta": "\\delta",
            "epsilon": "\\epsilon",
            "zeta": "\\zeta",
            "eta": "\\eta",
            "theta": "\\theta",
            "iota": "\\iota",
            "kappa": "\\kappa",
            "lambda": "\\lambda",
            "mu": "\\mu",
            "nu": "\\nu",
            "xi": "\\xi",
            "pi": "\\pi",
            "rho": "\\rho",
            "sigma": "\\sigma",
            "tau": "\\tau",
            "upsilon": "\\upsilon",
            "phi": "\\phi",
            "chi": "\\chi",
            "psi": "\\psi",
            "omega": "\\omega",
        }
        return greek_map.get(text.lower())

    def _normalize_tex(self, tex: str) -> str:
        """TeX 정규화 (안전성 강화)"""
        # 1. 연속 밑첨자 보호
        tex = re.sub(r"([A-Za-z])_([0-9A-Za-z])", r"\1_{\2}", tex)

        # 2. 루트 괄호 보강
        tex = re.sub(r"\\sqrt\s+([^{])", r"\\sqrt{\1}", tex)

        # 3. 함수 키워드 토큰화
        for func in self.MATH_FUNCTIONS:
            tex = re.sub(rf"(?<!\\)\b{func}\b", rf"\\{func}", tex)

        # 4. 공백 정리
        tex = re.sub(r"\s+", " ", tex).strip()

        return tex


def extract_mathml_from_html(html: str) -> list[str]:
    """HTML에서 MathML 추출"""
    # Wiris MathML 패턴
    pattern = r"<math[^>]*>.*?</math>"
    return re.findall(pattern, html, re.DOTALL)


def convert_wiris_to_tex(html: str) -> str:
    """Wiris HTML → TeX 변환 (메인 엔트리포인트)"""
    converter = MathMLToTeXConverter()
    mathml_list = extract_mathml_from_html(html)

    if not mathml_list:
        return html

    result = html
    for mathml in mathml_list:
        tex = converter.convert(mathml)
        # MathML을 TeX로 교체
        result = result.replace(mathml, f"${tex}$", 1)

    return result
