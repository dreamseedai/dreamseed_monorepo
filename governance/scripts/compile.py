#!/usr/bin/env python3
"""
Policy Bundle Compiler

Compiles Rego policies to Base64-encoded JSON bundle for OPA.
"""

import base64
import json
import glob
import sys
import os


def compile_policies(bundle_dir=None, output_file=None, version="1.0.0"):
    if bundle_dir is None:
        # 기본 경로: 현재 디렉토리의 ../bundles
        bundle_dir = os.path.join(os.path.dirname(__file__), "..", "bundles")
    if output_file is None:
        output_file = os.path.join(bundle_dir, "policy.json")

    bundles = {}
    # .rego 정책 파일들 (테스트 파일 제외) 처리
    pattern = os.path.join(bundle_dir, "*.rego")
    for file_path in glob.glob(pattern):
        if file_path.endswith("_test.rego"):
            continue
        file_name = os.path.basename(file_path)
        bundle_name = file_name.replace(".rego", "").replace("_policy", "")
        with open(file_path, "r") as f:
            rego_content = f.read()
        encoded = base64.b64encode(rego_content.encode("utf-8")).decode("utf-8")
        bundles[bundle_name] = {"revision": version, "modules": {file_name: encoded}}
    bundle_obj = {"bundles": bundles}
    with open(output_file, "w") as f:
        json.dump(bundle_obj, f, indent=4)
    print(f"Policy bundle compiled to {output_file}")


if __name__ == "__main__":
    bundle_dir = None
    output_file = None
    version = "1.0.0"
    if len(sys.argv) > 1:
        bundle_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        version = sys.argv[3]
    compile_policies(bundle_dir, output_file, version)
