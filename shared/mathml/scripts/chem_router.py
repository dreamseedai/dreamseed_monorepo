"""화학식 mhchem 강제 변환"""
import re

def ensure_mhchem(tex: str) -> str:
    """화학식을 \ce{...}로 강제 변환"""
    if tex is None:
        return tex
    if r"\ce{" in tex:
        return tex
    # 단순 치환: SO4^{2-} → \ce{SO4^2-}
    t = tex.replace("^{", "^").replace("}", "")
    return f"\\ce{{{t}}}"
