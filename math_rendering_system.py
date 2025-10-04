"""
수학 공식 렌더링 시스템
기존 PHP의 MathJax + Wiris MathML을 FastAPI + TipTap + MathLive로 변환
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from html import unescape

logger = logging.getLogger(__name__)

@dataclass
class MathExpression:
    """수학 표현식 데이터 클래스"""
    original: str
    mathml: Optional[str] = None
    latex: Optional[str] = None
    rendered_html: Optional[str] = None
    expression_type: str = "inline"  # inline, display
    confidence: float = 1.0

class MathRenderingSystem:
    """수학 공식 렌더링 시스템"""
    
    def __init__(self):
        self.mathml_patterns = [
            r'<math[^>]*>.*?</math>',
            r'<m:math[^>]*>.*?</m:math>',
            r'<math xmlns[^>]*>.*?</math>',
        ]
        self.latex_patterns = [
            r'\$([^$]+)\$',  # inline LaTeX
            r'\$\$([^$]+)\$\$',  # display LaTeX
            r'\\\[([^\]]+)\\\]',  # display LaTeX alternative
            r'\\\(([^)]+)\\\)',  # inline LaTeX alternative
        ]
        self.wiris_patterns = [
            r'<img[^>]*class="wirisformula"[^>]*>',
            r'<img[^>]*data-mathml="([^"]*)"[^>]*>',
            r'<img[^>]*alt="([^"]*<math[^>]*>.*?)"[^>]*>',
        ]
        
        # MathML to LaTeX 변환 매핑
        self.mathml_to_latex_map = {
            'mi': self._convert_identifier,
            'mn': self._convert_number,
            'mo': self._convert_operator,
            'mfrac': self._convert_fraction,
            'msup': self._convert_superscript,
            'msub': self._convert_subscript,
            'msubsup': self._convert_subsup,
            'mroot': self._convert_root,
            'msqrt': self._convert_sqrt,
            'mtext': self._convert_text,
            'mspace': self._convert_space,
            'mrow': self._convert_row,
            'mtable': self._convert_table,
            'mtr': self._convert_table_row,
            'mtd': self._convert_table_cell,
        }

    def process_content(self, content: str) -> str:
        """콘텐츠의 모든 수학 표현식을 처리"""
        if not content:
            return content
            
        try:
            # 1. 이미지 경로 변환
            content = self._process_image_references(content)
            
            # 2. Wiris 이미지 태그 처리
            content = self._process_wiris_images(content)
            
            # 3. MathML 태그 처리
            content = self._process_mathml_tags(content)
            
            # 4. LaTeX 표현식 처리
            content = self._process_latex_expressions(content)
            
            # 5. HTML 엔티티 디코딩
            content = unescape(content)
            
            return content
            
        except Exception as e:
            logger.error(f"수학 표현식 처리 오류: {e}")
            return content

    def _process_image_references(self, content: str) -> str:
        """이미지 참조를 새로운 경로로 변환"""
        import re
        
        # 기존 이미지 경로 패턴들
        old_patterns = [
            r'/images/editor/([^"\'>\s]+)',
            r'images/editor/([^"\'>\s]+)',
            r'editor/([^"\'>\s]+)',
        ]
        
        for pattern in old_patterns:
            def replace_image(match):
                filename = match.group(1)
                return f'/static/images/questions/{filename}'
            
            content = re.sub(pattern, replace_image, content)
        
        return content

    def _process_wiris_images(self, content: str) -> str:
        """Wiris 이미지 태그를 LaTeX로 변환"""
        def replace_wiris_image(match):
            img_tag = match.group(0)
            
            # data-mathml 속성에서 MathML 추출
            mathml_match = re.search(r'data-mathml="([^"]*)"', img_tag)
            if mathml_match:
                mathml = unescape(mathml_match.group(1))
                latex = self._mathml_to_latex(mathml)
                if latex:
                    return f"\\[{latex}\\]"
            
            # alt 속성에서 MathML 추출
            alt_match = re.search(r'alt="([^"]*<math[^>]*>.*?)"', img_tag)
            if alt_match:
                mathml = unescape(alt_match.group(1))
                latex = self._mathml_to_latex(mathml)
                if latex:
                    return f"\\[{latex}\\]"
            
            return img_tag  # 변환 실패 시 원본 반환
        
        for pattern in self.wiris_patterns:
            content = re.sub(pattern, replace_wiris_image, content, flags=re.DOTALL)
        
        return content

    def _process_mathml_tags(self, content: str) -> str:
        """MathML 태그를 LaTeX로 변환"""
        def replace_mathml(match):
            mathml = match.group(0)
            latex = self._mathml_to_latex(mathml)
            if latex:
                return f"\\[{latex}\\]"
            return mathml
        
        for pattern in self.mathml_patterns:
            content = re.sub(pattern, replace_mathml, content, flags=re.DOTALL)
        
        return content

    def _process_latex_expressions(self, content: str) -> str:
        """LaTeX 표현식을 정규화"""
        # 이미 올바른 형식인 LaTeX는 그대로 유지
        return content

    def _mathml_to_latex(self, mathml: str) -> Optional[str]:
        """MathML을 LaTeX로 변환"""
        try:
            # MathML 파싱
            root = ET.fromstring(mathml)
            
            # LaTeX 변환
            latex = self._convert_element(root)
            
            return latex if latex else None
            
        except ET.ParseError as e:
            logger.error(f"MathML 파싱 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"MathML to LaTeX 변환 오류: {e}")
            return None

    def _convert_element(self, element: ET.Element) -> str:
        """MathML 요소를 LaTeX로 변환"""
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if tag in self.mathml_to_latex_map:
            return self.mathml_to_latex_map[tag](element)
        else:
            # 알 수 없는 태그는 자식 요소들을 처리
            return ''.join(self._convert_element(child) for child in element)

    def _convert_identifier(self, element: ET.Element) -> str:
        """식별자 변환 (mi)"""
        text = element.text or ''
        # 그리스 문자나 특수 기호 처리
        greek_letters = {
            'alpha': '\\alpha', 'beta': '\\beta', 'gamma': '\\gamma',
            'delta': '\\delta', 'epsilon': '\\epsilon', 'zeta': '\\zeta',
            'eta': '\\eta', 'theta': '\\theta', 'iota': '\\iota',
            'kappa': '\\kappa', 'lambda': '\\lambda', 'mu': '\\mu',
            'nu': '\\nu', 'xi': '\\xi', 'omicron': '\\omicron',
            'pi': '\\pi', 'rho': '\\rho', 'sigma': '\\sigma',
            'tau': '\\tau', 'upsilon': '\\upsilon', 'phi': '\\phi',
            'chi': '\\chi', 'psi': '\\psi', 'omega': '\\omega'
        }
        return greek_letters.get(text.lower(), text)

    def _convert_number(self, element: ET.Element) -> str:
        """숫자 변환 (mn)"""
        return element.text or ''

    def _convert_operator(self, element: ET.Element) -> str:
        """연산자 변환 (mo)"""
        text = element.text or ''
        operators = {
            '+': '+', '-': '-', '*': '\\cdot', '/': '/',
            '=': '=', '<': '<', '>': '>', '≤': '\\leq',
            '≥': '\\geq', '≠': '\\neq', '±': '\\pm',
            '×': '\\times', '÷': '\\div', '∞': '\\infty',
            '∑': '\\sum', '∏': '\\prod', '∫': '\\int',
            '√': '\\sqrt', '∂': '\\partial', '∇': '\\nabla'
        }
        return operators.get(text, text)

    def _convert_fraction(self, element: ET.Element) -> str:
        """분수 변환 (mfrac)"""
        children = list(element)
        if len(children) >= 2:
            numerator = self._convert_element(children[0])
            denominator = self._convert_element(children[1])
            return f"\\frac{{{numerator}}}{{{denominator}}}"
        return ""

    def _convert_superscript(self, element: ET.Element) -> str:
        """위첨자 변환 (msup)"""
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            sup = self._convert_element(children[1])
            return f"{{{base}}}^{{{sup}}}"
        return ""

    def _convert_subscript(self, element: ET.Element) -> str:
        """아래첨자 변환 (msub)"""
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            sub = self._convert_element(children[1])
            return f"{{{base}}}_{{{sub}}}"
        return ""

    def _convert_subsup(self, element: ET.Element) -> str:
        """아래첨자+위첨자 변환 (msubsup)"""
        children = list(element)
        if len(children) >= 3:
            base = self._convert_element(children[0])
            sub = self._convert_element(children[1])
            sup = self._convert_element(children[2])
            return f"{{{base}}}_{{{sub}}}^{{{sup}}}"
        return ""

    def _convert_root(self, element: ET.Element) -> str:
        """근호 변환 (mroot)"""
        children = list(element)
        if len(children) >= 2:
            radicand = self._convert_element(children[0])
            index = self._convert_element(children[1])
            return f"\\sqrt[{index}]{{{radicand}}}"
        return ""

    def _convert_sqrt(self, element: ET.Element) -> str:
        """제곱근 변환 (msqrt)"""
        children = list(element)
        if children:
            radicand = ''.join(self._convert_element(child) for child in children)
            return f"\\sqrt{{{radicand}}}"
        return ""

    def _convert_text(self, element: ET.Element) -> str:
        """텍스트 변환 (mtext)"""
        return element.text or ''

    def _convert_space(self, element: ET.Element) -> str:
        """공백 변환 (mspace)"""
        width = element.get('width', '0.2em')
        return f"\\hspace{{{width}}}"

    def _convert_row(self, element: ET.Element) -> str:
        """행 변환 (mrow)"""
        return ''.join(self._convert_element(child) for child in element)

    def _convert_table(self, element: ET.Element) -> str:
        """표 변환 (mtable)"""
        rows = []
        for child in element:
            if child.tag.split('}')[-1] == 'mtr':
                row_content = self._convert_table_row(child)
                rows.append(row_content)
        
        if rows:
            return "\\begin{matrix}\n" + " \\\\\n".join(rows) + "\n\\end{matrix}"
        return ""

    def _convert_table_row(self, element: ET.Element) -> str:
        """표 행 변환 (mtr)"""
        cells = []
        for child in element:
            if child.tag.split('}')[-1] == 'mtd':
                cell_content = self._convert_table_cell(child)
                cells.append(cell_content)
        
        return " & ".join(cells)

    def _convert_table_cell(self, element: ET.Element) -> str:
        """표 셀 변환 (mtd)"""
        return ''.join(self._convert_element(child) for child in element)

    def extract_math_expressions(self, content: str) -> List[MathExpression]:
        """콘텐츠에서 수학 표현식 추출"""
        expressions = []
        
        # MathML 표현식 추출
        for pattern in self.mathml_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                mathml = match.group(0)
                latex = self._mathml_to_latex(mathml)
                expressions.append(MathExpression(
                    original=mathml,
                    mathml=mathml,
                    latex=latex,
                    expression_type="display"
                ))
        
        # LaTeX 표현식 추출
        for pattern in self.latex_patterns:
            for match in re.finditer(pattern, content):
                latex = match.group(1)
                expressions.append(MathExpression(
                    original=match.group(0),
                    latex=latex,
                    expression_type="display" if "$$" in match.group(0) else "inline"
                ))
        
        return expressions

    def validate_math_expression(self, expression: str) -> Dict[str, Any]:
        """수학 표현식 유효성 검사"""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            # LaTeX 문법 검사
            if expression.startswith('\\[') and expression.endswith('\\]'):
                latex_content = expression[2:-2]
            elif expression.startswith('$$') and expression.endswith('$$'):
                latex_content = expression[2:-2]
            else:
                latex_content = expression
            
            # 기본 문법 검사
            if not latex_content.strip():
                result["is_valid"] = False
                result["errors"].append("빈 수학 표현식")
            
            # 괄호 균형 검사
            if latex_content.count('{') != latex_content.count('}'):
                result["warnings"].append("괄호가 균형을 이루지 않습니다")
            
            # 일반적인 오류 패턴 검사
            error_patterns = [
                (r'\\[a-zA-Z]+\s*$', "명령어가 완성되지 않았습니다"),
                (r'\\[a-zA-Z]+\s*\\[a-zA-Z]+', "명령어 사이에 공백이 필요합니다"),
            ]
            
            for pattern, message in error_patterns:
                if re.search(pattern, latex_content):
                    result["warnings"].append(message)
            
        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"검증 중 오류: {str(e)}")
        
        return result

    def get_math_preview(self, expression: str) -> str:
        """수학 표현식 미리보기 HTML 생성"""
        try:
            # LaTeX를 HTML로 변환 (MathJax 형식)
            if expression.startswith('\\[') and expression.endswith('\\]'):
                return f'<div class="math-display">\\[{expression[2:-2]}\\]</div>'
            elif expression.startswith('$$') and expression.endswith('$$'):
                return f'<div class="math-display">$${expression[2:-2]}$$</div>'
            elif expression.startswith('\\(') and expression.endswith('\\)'):
                return f'<span class="math-inline">\\({expression[2:-2]}\\)</span>'
            elif expression.startswith('$') and expression.endswith('$'):
                return f'<span class="math-inline">${expression[1:-1]}$</span>'
            else:
                return f'<span class="math-inline">${expression}$</span>'
                
        except Exception as e:
            logger.error(f"수학 표현식 미리보기 생성 오류: {e}")
            return f'<span class="math-error">수학 표현식 오류: {expression}</span>'

# 전역 인스턴스
math_renderer = MathRenderingSystem()

def process_math_content(content: str) -> str:
    """수학 콘텐츠 처리 (편의 함수)"""
    return math_renderer.process_content(content)

def extract_math_expressions(content: str) -> List[MathExpression]:
    """수학 표현식 추출 (편의 함수)"""
    return math_renderer.extract_math_expressions(content)

def validate_math_expression(expression: str) -> Dict[str, Any]:
    """수학 표현식 유효성 검사 (편의 함수)"""
    return math_renderer.validate_math_expression(expression)

# 테스트 함수
def test_math_rendering():
    """수학 렌더링 시스템 테스트"""
    test_cases = [
        # MathML 테스트
        '<math><mi>x</mi><mo>+</mo><mn>1</mn></math>',
        '<math><mfrac><mi>x</mi><mn>2</mn></mfrac></math>',
        '<math><msup><mi>x</mi><mn>2</mn></msup></math>',
        
        # LaTeX 테스트
        '$x + 1$',
        '$$\\frac{x}{2}$$',
        '$x^2$',
        
        # Wiris 이미지 테스트
        '<img class="wirisformula" data-mathml="&lt;math&gt;&lt;mi&gt;x&lt;/mi&gt;&lt;mo&gt;+&lt;/mo&gt;&lt;mn&gt;1&lt;/mn&gt;&lt;/math&gt;">',
    ]
    
    print("=== 수학 렌더링 시스템 테스트 ===")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n테스트 {i}: {test_case}")
        result = process_math_content(test_case)
        print(f"결과: {result}")
        
        expressions = extract_math_expressions(test_case)
        print(f"추출된 표현식 수: {len(expressions)}")
        for expr in expressions:
            print(f"  - {expr.latex}")

if __name__ == "__main__":
    test_math_rendering()
