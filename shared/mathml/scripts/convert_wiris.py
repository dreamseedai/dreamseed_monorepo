"""Wiris MathML → TeX 변환 스켈레톤"""
from xml.etree import ElementTree as ET
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from normalize_tex import normalize_tex

def mathml_to_tex(mathml: str) -> str:
    """MathML → TeX 변환 (스켈레톤)"""
    if not mathml:
        return ""
    root = ET.fromstring(mathml)
    
    def walk(node):
        tag = node.tag.split('}')[-1]
        if tag in ("math", "mrow"):
            return "".join(walk(c) for c in node)
        if tag == "msqrt":
            inner = "".join(walk(c) for c in node)
            return f"\\sqrt{{{inner}}}"
        if tag == "mroot":
            base = walk(node[0])
            idx = walk(node[1]) if len(node) > 1 else "2"
            return f"\\sqrt[{idx}]{{{base}}}"
        if tag == "mi":
            return node.text or ""
        if tag == "mn":
            return node.text or ""
        if tag == "mo":
            return node.text or ""
        return "".join(walk(c) for c in node)
    
    tex = walk(root)
    return normalize_tex(tex)
