#!/usr/bin/env python3
"""
MathML to LaTeX converter for DreamSeedAI
Converts MathML expressions from mpcstudy.com to LaTeX format
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import json

class MathMLToLaTeXConverter:
    """
    Converts MathML expressions to LaTeX format
    """
    
    def __init__(self):
        # MathML to LaTeX mapping for common elements
        self.element_mapping = {
            # Basic elements
            'mi': self._convert_identifier,
            'mn': self._convert_number,
            'mo': self._convert_operator,
            'mtext': self._convert_text,
            'mspace': self._convert_space,
            
            # Fractions and radicals
            'mfrac': self._convert_fraction,
            'msqrt': self._convert_sqrt,
            'mroot': self._convert_root,
            
            # Scripts and limits
            'msup': self._convert_superscript,
            'msub': self._convert_subscript,
            'msubsup': self._convert_subsup,
            'munder': self._convert_under,
            'mover': self._convert_over,
            'munderover': self._convert_underover,
            
            # Delimiters
            'mfenced': self._convert_fenced,
            'menclose': self._convert_enclose,
            
            # Tables and matrices
            'mtable': self._convert_table,
            'mtr': self._convert_table_row,
            'mtd': self._convert_table_cell,
            
            # Other elements
            'mrow': self._convert_row,
            'mstyle': self._convert_style,
            'merror': self._convert_error,
            'mpadded': self._convert_padded,
            'mphantom': self._convert_phantom,
        }
        
        # Operator mapping
        self.operator_mapping = {
            '+': '+',
            '-': '-',
            '*': '\\cdot',
            '×': '\\times',
            '÷': '\\div',
            '=': '=',
            '≠': '\\neq',
            '<': '<',
            '>': '>',
            '≤': '\\leq',
            '≥': '\\geq',
            '±': '\\pm',
            '∓': '\\mp',
            '∞': '\\infty',
            '∑': '\\sum',
            '∏': '\\prod',
            '∫': '\\int',
            '∂': '\\partial',
            '∇': '\\nabla',
            '∈': '\\in',
            '∉': '\\notin',
            '⊂': '\\subset',
            '⊃': '\\supset',
            '⊆': '\\subseteq',
            '⊇': '\\supseteq',
            '∪': '\\cup',
            '∩': '\\cap',
            '∅': '\\emptyset',
            '→': '\\rightarrow',
            '←': '\\leftarrow',
            '↔': '\\leftrightarrow',
            '⇒': '\\Rightarrow',
            '⇐': '\\Leftarrow',
            '⇔': '\\Leftrightarrow',
            '∀': '\\forall',
            '∃': '\\exists',
            '∧': '\\wedge',
            '∨': '\\vee',
            '¬': '\\neg',
            '⊥': '\\perp',
            '∥': '\\parallel',
            '∠': '\\angle',
            '△': '\\triangle',
            '□': '\\square',
            '○': '\\circ',
            '°': '^\\circ',
            'π': '\\pi',
            'α': '\\alpha',
            'β': '\\beta',
            'γ': '\\gamma',
            'δ': '\\delta',
            'ε': '\\varepsilon',
            'ζ': '\\zeta',
            'η': '\\eta',
            'θ': '\\theta',
            'ι': '\\iota',
            'κ': '\\kappa',
            'λ': '\\lambda',
            'μ': '\\mu',
            'ν': '\\nu',
            'ξ': '\\xi',
            'ο': '\\omicron',
            'ρ': '\\rho',
            'σ': '\\sigma',
            'τ': '\\tau',
            'υ': '\\upsilon',
            'φ': '\\phi',
            'χ': '\\chi',
            'ψ': '\\psi',
            'ω': '\\omega',
        }
    
    def convert(self, mathml_string: str) -> str:
        """
        Convert MathML string to LaTeX
        """
        try:
            # Clean up the MathML string
            mathml_string = self._clean_mathml(mathml_string)
            
            # Parse the MathML
            root = ET.fromstring(mathml_string)
            
            # Convert to LaTeX
            latex = self._convert_element(root)
            
            return latex
            
        except ET.ParseError as e:
            print(f"Error parsing MathML: {e}")
            return f"\\text{{Error: {str(e)}}}"
        except Exception as e:
            print(f"Error converting MathML: {e}")
            return f"\\text{{Error: {str(e)}}}"
    
    def _clean_mathml(self, mathml_string: str) -> str:
        """
        Clean up MathML string before parsing
        """
        # Fix escaped quotes
        mathml_string = mathml_string.replace('\\"', '"')
        
        # Remove XML namespace declarations if present
        mathml_string = re.sub(r'xmlns[^=]*="[^"]*"', '', mathml_string)
        
        # Decode HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&#160;': ' ',
            '&#8594;': '→',
            '&#8592;': '←',
            '&#8596;': '↔',
            '&#8593;': '↑',
            '&#8595;': '↓',
            '&#8800;': '≠',
            '&#8804;': '≤',
            '&#8805;': '≥',
            '&#8712;': '∈',
            '&#8713;': '∉',
            '&#8746;': '∪',
            '&#8745;': '∩',
            '&#8709;': '∅',
            '&#8721;': '∑',
            '&#8722;': '−',
            '&#8727;': '∗',
            '&#8730;': '√',
            '&#8734;': '∞',
            '&#8776;': '≈',
            '&#8801;': '≡',
            '&#8706;': '∂',
            '&#8711;': '∇',
            '&#8729;': '⋅',
            '&#215;': '×',
            '&#247;': '÷',
            '&#177;': '±',
            '&#8723;': '∓',
            '&#8943;': '⋯',
            '&#8942;': '⋮',
            '&#8944;': '⋰',
            '&#8945;': '⋱',
        }
        
        for entity, char in html_entities.items():
            mathml_string = mathml_string.replace(entity, char)
        
        # Ensure proper XML structure
        if not mathml_string.strip().startswith('<math'):
            mathml_string = f'<math>{mathml_string}</math>'
        
        return mathml_string
    
    def _convert_element(self, element: ET.Element) -> str:
        """
        Convert a MathML element to LaTeX
        """
        tag = element.tag
        
        # Remove namespace prefix if present
        if '}' in tag:
            tag = tag.split('}')[-1]
        
        if tag in self.element_mapping:
            return self.element_mapping[tag](element)
        else:
            # Default: convert children
            return self._convert_children(element)
    
    def _convert_children(self, element: ET.Element) -> str:
        """
        Convert all children of an element
        """
        result = []
        for child in element:
            result.append(self._convert_element(child))
        return ''.join(result)
    
    def _convert_identifier(self, element: ET.Element) -> str:
        """
        Convert mi (identifier) element
        """
        text = element.text or ''
        # Handle special identifiers
        if text in self.operator_mapping:
            return self.operator_mapping[text]
        return text
    
    def _convert_number(self, element: ET.Element) -> str:
        """
        Convert mn (number) element
        """
        return element.text or ''
    
    def _convert_operator(self, element: ET.Element) -> str:
        """
        Convert mo (operator) element
        """
        text = element.text or ''
        if text in self.operator_mapping:
            return self.operator_mapping[text]
        return text
    
    def _convert_text(self, element: ET.Element) -> str:
        """
        Convert mtext element
        """
        text = element.text or ''
        return f"\\text{{{text}}}"
    
    def _convert_space(self, element: ET.Element) -> str:
        """
        Convert mspace element
        """
        return ' '
    
    def _convert_fraction(self, element: ET.Element) -> str:
        """
        Convert mfrac (fraction) element
        """
        children = list(element)
        if len(children) >= 2:
            numerator = self._convert_element(children[0])
            denominator = self._convert_element(children[1])
            return f"\\frac{{{numerator}}}{{{denominator}}}"
        return ""
    
    def _convert_sqrt(self, element: ET.Element) -> str:
        """
        Convert msqrt (square root) element
        """
        content = self._convert_children(element)
        return f"\\sqrt{{{content}}}"
    
    def _convert_root(self, element: ET.Element) -> str:
        """
        Convert mroot (nth root) element
        """
        children = list(element)
        if len(children) >= 2:
            radicand = self._convert_element(children[1])
            index = self._convert_element(children[0])
            return f"\\sqrt[{index}]{{{radicand}}}"
        return ""
    
    def _convert_superscript(self, element: ET.Element) -> str:
        """
        Convert msup (superscript) element
        """
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            sup = self._convert_element(children[1])
            return f"{{{base}}}^{{{sup}}}"
        return ""
    
    def _convert_subscript(self, element: ET.Element) -> str:
        """
        Convert msub (subscript) element
        """
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            sub = self._convert_element(children[1])
            return f"{{{base}}}_{{{sub}}}"
        return ""
    
    def _convert_subsup(self, element: ET.Element) -> str:
        """
        Convert msubsup (subscript and superscript) element
        """
        children = list(element)
        if len(children) >= 3:
            base = self._convert_element(children[0])
            sub = self._convert_element(children[1])
            sup = self._convert_element(children[2])
            return f"{{{base}}}_{{{sub}}}^{{{sup}}}"
        return ""
    
    def _convert_under(self, element: ET.Element) -> str:
        """
        Convert munder (under) element
        """
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            under = self._convert_element(children[1])
            return f"\\underset{{{under}}}{{{base}}}"
        return ""
    
    def _convert_over(self, element: ET.Element) -> str:
        """
        Convert mover (over) element
        """
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            over = self._convert_element(children[1])
            return f"\\overset{{{over}}}{{{base}}}"
        return ""
    
    def _convert_underover(self, element: ET.Element) -> str:
        """
        Convert munderover element
        """
        children = list(element)
        if len(children) >= 3:
            base = self._convert_element(children[0])
            under = self._convert_element(children[1])
            over = self._convert_element(children[2])
            return f"\\overset{{{over}}}{{\\underset{{{under}}}{{{base}}}}}"
        return ""
    
    def _convert_fenced(self, element: ET.Element) -> str:
        """
        Convert mfenced (fenced) element
        """
        open_char = element.get('open', '(')
        close_char = element.get('close', ')')
        separators = element.get('separators', ',')
        
        # Convert special characters
        open_char = self._convert_delimiter(open_char)
        close_char = self._convert_delimiter(close_char)
        
        content = self._convert_children(element)
        
        return f"{open_char}{content}{close_char}"
    
    def _convert_delimiter(self, char: str) -> str:
        """
        Convert delimiter characters to LaTeX
        """
        delimiter_map = {
            '(': '\\left(',
            ')': '\\right)',
            '[': '\\left[',
            ']': '\\right]',
            '{': '\\left\\{',
            '}': '\\right\\}',
            '|': '\\left|',
            '‖': '\\left\\|',
            '⌊': '\\left\\lfloor',
            '⌋': '\\right\\rfloor',
            '⌈': '\\left\\lceil',
            '⌉': '\\right\\rceil',
        }
        return delimiter_map.get(char, char)
    
    def _convert_enclose(self, element: ET.Element) -> str:
        """
        Convert menclose element
        """
        notation = element.get('notation', '')
        content = self._convert_children(element)
        
        if notation == 'longdiv':
            return f"\\overline{{{content}}}"
        elif notation == 'actuarial':
            return f"\\overline{{{content}}}"
        elif notation == 'radical':
            return f"\\sqrt{{{content}}}"
        else:
            return content
    
    def _convert_table(self, element: ET.Element) -> str:
        """
        Convert mtable (table/matrix) element
        """
        rows = []
        for child in element:
            if child.tag.endswith('mtr'):
                row_content = []
                for cell in child:
                    if cell.tag.endswith('mtd'):
                        row_content.append(self._convert_children(cell))
                rows.append(' & '.join(row_content))
        
        if rows:
            return f"\\begin{{matrix}}\n" + " \\\\\n".join(rows) + "\n\\end{{matrix}}"
        return ""
    
    def _convert_table_row(self, element: ET.Element) -> str:
        """
        Convert mtr (table row) element
        """
        return self._convert_children(element)
    
    def _convert_table_cell(self, element: ET.Element) -> str:
        """
        Convert mtd (table cell) element
        """
        return self._convert_children(element)
    
    def _convert_row(self, element: ET.Element) -> str:
        """
        Convert mrow element
        """
        return self._convert_children(element)
    
    def _convert_style(self, element: ET.Element) -> str:
        """
        Convert mstyle element
        """
        return self._convert_children(element)
    
    def _convert_error(self, element: ET.Element) -> str:
        """
        Convert merror element
        """
        content = self._convert_children(element)
        return f"\\text{{Error: {content}}}"
    
    def _convert_padded(self, element: ET.Element) -> str:
        """
        Convert mpadded element
        """
        return self._convert_children(element)
    
    def _convert_phantom(self, element: ET.Element) -> str:
        """
        Convert mphantom element
        """
        return ""

def convert_mathml_in_text(text: str) -> str:
    """
    Convert all MathML expressions in a text to LaTeX
    """
    converter = MathMLToLaTeXConverter()
    
    # Find all MathML expressions
    mathml_pattern = r'<math[^>]*>.*?</math>'
    matches = re.finditer(mathml_pattern, text, re.DOTALL)
    
    result = text
    offset = 0
    
    for match in matches:
        mathml_expr = match.group(0)
        latex_expr = converter.convert(mathml_expr)
        
        # Replace in the result
        start = match.start() + offset
        end = match.end() + offset
        
        result = result[:start] + f"${latex_expr}$" + result[end:]
        offset += len(f"${latex_expr}$") - len(mathml_expr)
    
    return result

if __name__ == '__main__':
    # Test the converter
    converter = MathMLToLaTeXConverter()
    
    # Test cases
    test_cases = [
        '<math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>',
        '<math><msup><mi>x</mi><mn>2</mn></msup></math>',
        '<math><msqrt><mi>x</mi></msqrt></math>',
        '<math><munder><mi>lim</mi><mrow><mi>x</mi><mo>→</mo><mn>0</mn></mrow></munder></math>',
    ]
    
    print("MathML to LaTeX Converter Test")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        result = converter.convert(test)
        print(f"Test {i}:")
        print(f"  MathML: {test}")
        print(f"  LaTeX:  {result}")
        print()
