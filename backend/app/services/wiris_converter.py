"""
MPCStudy to DreamSeedAI Migration - Wiris to MathLive Conversion

This module handles the conversion of MPCStudy question bank (MySQL)
to DreamSeedAI IRT-ready format (PostgreSQL).

Key transformations:
1. TinyMCE + Wiris HTML → TipTap + MathLive format
2. MathML → LaTeX conversion
3. Difficulty levels (1-5) → IRT b parameters (-2 to +2)
4. Multiple choice → ItemOption with correctness flags

Dependencies:
- BeautifulSoup4 for HTML parsing
- lxml for MathML processing
- latex2mathml / mathml2latex for format conversion
"""

from bs4 import BeautifulSoup
import re
from typing import Dict
from lxml import etree  # type: ignore[import]


def mathml_to_latex(mathml_str: str) -> str:
    """
    Convert MathML to LaTeX using lxml parsing.
    
    This is a simplified converter. For production, consider using:
    - WIRIS official MathML-to-LaTeX API
    - mathml2latex library
    - Node.js mathml-to-latex package
    
    Args:
        mathml_str: MathML string (e.g., <math>...</math>)
    
    Returns:
        LaTeX string
    
    Example:
        >>> mathml = '<math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>'
        >>> latex = mathml_to_latex(mathml)
        >>> print(latex)
        \\frac{1}{2}
    """
    try:
        # Parse MathML
        root = etree.fromstring(mathml_str.encode('utf-8'))
        
        # Recursive conversion
        latex = _mathml_node_to_latex(root)
        return latex.strip()
    
    except Exception as e:
        print(f"⚠️  MathML conversion failed: {e}")
        # Fallback: return as-is or placeholder
        return "[MATH_ERROR]"


def _mathml_node_to_latex(node: etree._Element) -> str:
    """
    Recursively convert MathML node to LaTeX.
    
    Handles common MathML elements:
    - <mn> → numbers
    - <mi> → variables
    - <mo> → operators
    - <mfrac> → \\frac{}{}
    - <msup> → ^{}
    - <msub> → _{}
    - <msqrt> → \\sqrt{}
    - <mrow> → group
    
    This is a MINIMAL implementation. For production, use a full library.
    """
    tag = node.tag
    
    # Strip namespace if present
    if '}' in tag:
        tag = tag.split('}')[1]
    
    # Text nodes (numbers, variables, operators)
    if tag in ('mn', 'mi', 'mo'):
        return node.text or ''
    
    # Fractions: <mfrac><numerator/><denominator/></mfrac>
    elif tag == 'mfrac':
        children = list(node)
        if len(children) >= 2:
            num = _mathml_node_to_latex(children[0])
            den = _mathml_node_to_latex(children[1])
            return f"\\frac{{{num}}}{{{den}}}"
        return ''
    
    # Superscript: <msup><base/><exponent/></msup>
    elif tag == 'msup':
        children = list(node)
        if len(children) >= 2:
            base = _mathml_node_to_latex(children[0])
            exp = _mathml_node_to_latex(children[1])
            return f"{base}^{{{exp}}}"
        return ''
    
    # Subscript: <msub><base/><index/></msub>
    elif tag == 'msub':
        children = list(node)
        if len(children) >= 2:
            base = _mathml_node_to_latex(children[0])
            idx = _mathml_node_to_latex(children[1])
            return f"{base}_{{{idx}}}"
        return ''
    
    # Square root: <msqrt><content/></msqrt>
    elif tag == 'msqrt':
        children = list(node)
        if children:
            content = _mathml_node_to_latex(children[0])
            return f"\\sqrt{{{content}}}"
        return ''
    
    # Row (grouping): <mrow>...</mrow>
    elif tag == 'mrow':
        parts = [_mathml_node_to_latex(child) for child in node]
        return ''.join(parts)
    
    # Math root: <math>...</math>
    elif tag == 'math':
        parts = [_mathml_node_to_latex(child) for child in node]
        return ''.join(parts)
    
    # Unknown tag: recurse on children
    else:
        parts = [_mathml_node_to_latex(child) for child in node]
        return ''.join(parts)


def convert_wiris_html_to_mathlive(html: str) -> str:
    """
    Convert TinyMCE + Wiris HTML to TipTap + MathLive format.
    
    Steps:
    1. Parse HTML with BeautifulSoup
    2. Find all <math> (MathML) tags
    3. Convert MathML to LaTeX
    4. Replace with <span data-math="...">$...$</span>
    5. Find Wiris-specific spans (class="math-tex")
    6. Extract LaTeX and wrap in $...$
    7. Clean up unnecessary inline styles
    
    Args:
        html: Original HTML from MPCStudy (TinyMCE + Wiris)
    
    Returns:
        Clean HTML with MathLive-ready LaTeX
    
    Example:
        >>> html = '<p>Solve <math><mfrac><mn>1</mn><mn>2</mn></mfrac></math></p>'
        >>> clean_html = convert_wiris_html_to_mathlive(html)
        >>> print(clean_html)
        <p>Solve <span data-math="\\frac{1}{2}">$\\frac{1}{2}$</span></p>
    """
    if not html:
        return ''
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # (1) Convert all <math> tags (MathML) to LaTeX spans
    for math_tag in soup.find_all('math'):
        mathml_str = str(math_tag)
        latex = mathml_to_latex(mathml_str)
        
        # Create new span with data-math attribute
        span = soup.new_tag('span')
        span['data-math'] = latex
        span.string = f"${latex}$"
        
        # Replace <math> with <span>
        math_tag.replace_with(span)
    
    # (2) Convert Wiris-specific spans (class="math-tex")
    for span in soup.find_all('span', class_='math-tex'):
        # Usually contains LaTeX already
        latex = span.get_text().strip()
        
        # Remove existing content
        span.clear()
        
        # Add data-math attribute
        span['data-math'] = latex
        span.string = f"${latex}$"
        
        # Remove Wiris class
        if 'class' in span.attrs:
            class_attr = span.get('class')
            if class_attr:
                classes = [c for c in class_attr if c != 'math-tex']
                if classes:
                    span['class'] = ' '.join(classes)
                else:
                    del span['class']
    
    # (3) Remove unnecessary inline styles (optional cleanup)
    for tag in soup.find_all(style=True):
        # Keep only essential styles, remove Wiris artifacts
        style = str(tag.get('style', ''))
        # Example: remove "cursor: pointer;" added by Wiris editor
        style = re.sub(r'cursor:\s*pointer;?', '', style)
        
        if style.strip():
            tag['style'] = style
        else:
            del tag['style']
    
    # (4) Convert back to HTML
    clean_html = str(soup)
    
    return clean_html


def map_difficulty_to_irt_b(difficulty_level: int) -> float:
    """
    Map MPCStudy difficulty level (1-5) to IRT b parameter.
    
    Mapping:
        1 (easiest)  → b = -2.0
        2            → b = -1.0
        3 (medium)   → b =  0.0
        4            → b = +1.0
        5 (hardest)  → b = +2.0
    
    Args:
        difficulty_level: Integer 1-5
    
    Returns:
        IRT difficulty parameter b (float)
    """
    mapping = {
        1: -2.0,
        2: -1.0,
        3: 0.0,
        4: 1.0,
        5: 2.0,
    }
    return mapping.get(difficulty_level, 0.0)


def estimate_initial_irt_params(
    difficulty_level: int,
    num_choices: int = 4,
) -> Dict[str, float]:
    """
    Estimate initial IRT 3PL parameters before calibration.
    
    These are expert estimates that will be refined later using mirt R package
    with actual student response data.
    
    Args:
        difficulty_level: MPCStudy difficulty (1-5)
        num_choices: Number of multiple choice options (default: 4)
    
    Returns:
        Dictionary with keys: a, b, c
    
    Example:
        >>> params = estimate_initial_irt_params(difficulty_level=3, num_choices=4)
        >>> print(params)
        {'a': 1.0, 'b': 0.0, 'c': 0.25}
    """
    # Discrimination: Start with 1.0 (will be calibrated)
    a = 1.0
    
    # Difficulty: Map from 1-5 scale
    b = map_difficulty_to_irt_b(difficulty_level)
    
    # Guessing: Based on number of choices
    # 2 choices → c = 0.5
    # 4 choices → c = 0.25
    # 5 choices → c = 0.2
    c = 1.0 / num_choices if num_choices > 0 else 0.2
    
    return {'a': a, 'b': b, 'c': c}


def sanitize_html(html: str) -> str:
    """
    Clean HTML for security (XSS prevention).
    
    Remove:
    - <script> tags
    - javascript: URLs
    - onclick/onerror handlers
    
    Args:
        html: Raw HTML
    
    Returns:
        Sanitized HTML
    """
    if not html:
        return ''
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script tags
    for script in soup.find_all('script'):
        script.decompose()
    
    # Remove event handlers
    for tag in soup.find_all():
        for attr in list(tag.attrs.keys()):
            if attr.startswith('on'):  # onclick, onerror, etc.
                del tag[attr]
    
    # Remove javascript: URLs
    for tag in soup.find_all(href=True):
        href = str(tag.get('href', ''))
        if href.strip().lower().startswith('javascript:'):
            del tag['href']
    
    return str(soup)


if __name__ == "__main__":
    # Test conversions
    print("MPCStudy → DreamSeedAI Converter - Tests")
    print("=" * 60)
    
    # Test 1: MathML to LaTeX
    print("\n1. MathML to LaTeX:")
    mathml = '<math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>'
    latex = mathml_to_latex(mathml)
    print(f"   Input:  {mathml}")
    print(f"   Output: {latex}")
    
    # Test 2: Full HTML conversion
    print("\n2. Wiris HTML to MathLive:")
    html = '<p>Solve <math><mfrac><mn>x</mn><mn>2</mn></mfrac></math> = 10</p>'
    clean = convert_wiris_html_to_mathlive(html)
    print(f"   Input:  {html}")
    print(f"   Output: {clean}")
    
    # Test 3: Difficulty mapping
    print("\n3. Difficulty → IRT b parameter:")
    for level in range(1, 6):
        params = estimate_initial_irt_params(level, num_choices=4)
        print(f"   Level {level}: a={params['a']:.1f}, b={params['b']:+.1f}, c={params['c']:.2f}")
    
    print("\n✓ All tests complete")
