#!/usr/bin/env python3
"""
Rego Policy Validator

Validates Rego policies using OPA Docker image.
"""

import subprocess
import sys
import os


def validate_policies(bundle_dir: str):
    # Convert to absolute path
    abs_bundle_dir = os.path.abspath(bundle_dir)

    # Get list of .rego files only (excluding tests for check, including tests for test)
    policy_files = [f for f in os.listdir(abs_bundle_dir) if f.endswith(".rego")]

    if not policy_files:
        print(f"❌ No .rego files found in {bundle_dir}")
        sys.exit(1)

    print(f"Found {len(policy_files)} Rego files")

    # 정책 파일 구문 검증 (Docker) - 각 파일 개별적으로
    print("\nChecking Rego syntax...")
    for rego_file in policy_files:
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{abs_bundle_dir}:/policies",
                "openpolicyagent/opa:0.58.0",
                "check",
                f"/policies/{rego_file}",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(
                f"❌ Syntax check failed for {rego_file}:\n",
                result.stderr or result.stdout,
            )
            sys.exit(1)

    print("✅ All policy syntax checks passed.")

    # 정책 테스트 실행 (Docker) - .rego 파일들을 인자로 전달
    print("\nRunning Rego tests...")
    rego_paths = [f"/policies/{f}" for f in policy_files]

    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{abs_bundle_dir}:/policies",
            "openpolicyagent/opa:0.58.0",
            "test",
        ]
        + rego_paths
        + ["-v"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("❌ Policy tests failed:\n", result.stderr or result.stdout)
        sys.exit(1)
    print("✅ All policy tests passed.\n")
    print(result.stdout)


if __name__ == "__main__":
    bundle_dir = sys.argv[1] if len(sys.argv) > 1 else "governance/bundles"
    validate_policies(bundle_dir)
