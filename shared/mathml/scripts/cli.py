"""일괄 변환 파이프라인 CLI"""

import json
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from convert_wiris import mathml_to_tex
from normalize_tex import normalize_tex


def process_item(item):
    """골든셋 항목 처리"""
    src = item["source_format"]
    pld = item["payload"]

    if src == "wiris-mathml":
        tex = mathml_to_tex(pld.get("mathml"))
    elif src == "latex-tex":
        tex = normalize_tex(pld.get("tex", ""))
    elif src == "image-ocr":
        tex = normalize_tex(pld.get("tex", ""))
    else:
        tex = ""

    item.setdefault("expected", {})["tex"] = tex
    return item


def main():
    ap = argparse.ArgumentParser(description="Wiris MathML → TeX 일괄 변환")
    ap.add_argument("--infile", required=True, help="입력 JSONL 파일")
    ap.add_argument("--outfile", required=True, help="출력 JSONL 파일")
    args = ap.parse_args()

    with (
        open(args.infile, "r", encoding="utf-8") as f,
        open(args.outfile, "w", encoding="utf-8") as out,
    ):
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            item = process_item(item)
            out.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ 변환 완료: {args.outfile}")


if __name__ == "__main__":
    sys.exit(main())
