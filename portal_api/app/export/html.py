from __future__ import annotations

from typing import Any, Optional

from markupsafe import escape


def tiptap_to_html(doc: dict[str, Any]) -> str:
    def render(node):
        t = node.get("type")
        if t == "doc":
            return "".join(render(n) for n in node.get("content", []))
        if t == "paragraph":
            return f"<p>{''.join(render(n) for n in node.get('content', []))}</p>"
        if t == "text":
            return escape(node.get("text", ""))
        if t == "math":
            latex = node.get("attrs", {}).get("latex", "")
            return f"<span class='math'>\\({escape(latex)}\\)</span>"
        return ""

    return render(doc or {"type": "doc"})


def build_html(
    doc: dict[str, Any],
    *,
    title: str,
    author: Optional[str],
    created_at_iso: Optional[str],
    logo_url: Optional[str] = None,
    size: str = "A4",
    brand: str = "DreamSeed",
) -> str:
    body = tiptap_to_html(doc)
    author = author or "-"
    date_label = created_at_iso or "-"
    logo = (
        f"<img src='{escape(logo_url)}' alt='logo' style='height:18px;vertical-align:middle;margin-right:8px'/>"
        if logo_url
        else ""
    )
    return f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\"/>
<title>{escape(title)}</title>
<style>
@page {{
  size: {escape(size)};
  margin: 18mm 16mm 18mm 16mm;
  @top-left    {{ content: "{escape(brand)}";  font-size: 10px; color:#666; }}
  @top-right   {{ content: "{escape(author)}"; font-size: 10px; color:#666; }}
  @bottom-center {{ content: "Page " counter(page) " / " counter(pages); font-size: 10px; color: #666; }}
}}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", "Apple SD Gothic Neo", "Malgun Gothic", "Nanum Gothic", sans-serif; line-height: 1.5; }}
h1.title {{ font-size: 26px; margin: 0 0 6px; }}
.meta {{ color:#666; font-size: 12px; margin: 0 0 16px; }}
p {{ margin: 0 0 8px; }}
.math {{ padding: 2px 4px; background: #f6f6f6; border-radius: 4px; }}
.coverbox {{
  background: linear-gradient(135deg,#f5f7fb 0%,#eef2f9 100%);
  border: 1px solid #e5e8ef; border-radius: 10px; padding: 16px;
}}
</style>
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\\\(','\\\\)'], ['$', '$']] }},
  svg: {{ fontCache: 'global' }}
}};
</script>
<script src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js\" defer></script>
</head>
<body>
  <section class=\"cover\">
    <div class=\"coverbox\">
      <h1 class=\"title\">{logo}{escape(title)}</h1>
      <div class=\"meta\">Author: {escape(author)} · Created: {escape(date_label)}</div>
    </div>
  </section>
  <section class=\"content\">
    {body}
  </section>
</body>
</html>"""
