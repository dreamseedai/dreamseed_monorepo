#!/usr/bin/env python3
"""
Validate a project config JSON against the bundled JSON Schema.

Usage:
    python portal_front/scripts/validate_project_config.py [--config PATH] [--schema PATH] [--project-url URL]

Defaults:
  --config reads from env PROJECT_CONFIG_JSON (if set), else portal_front/scripts/project_config.json if present;
  --schema defaults to portal_front/scripts/project_config.schema.json

Exit codes:
  0 - valid or config not found (no-op)
  1 - invalid (schema validation failed)
  2 - tool error (missing jsonschema or unreadable files)
"""
import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=os.getenv("PROJECT_CONFIG_JSON", ""))
    parser.add_argument(
        "--schema",
        default=str(
            Path("portal_front/scripts/project_config.schema.json").resolve()
        ),
    )
    parser.add_argument("--project-url", default=os.getenv("PROJECT_URL", ""))
    args = parser.parse_args()

    # Resolve config path
    cfg_path = args.config
    if not cfg_path:
        default_cfg = Path("portal_front/scripts/project_config.json")
        if default_cfg.exists():
            cfg_path = str(default_cfg)
    if not cfg_path:
        print("No config specified and no default found; skipping.")
        return 0

    try:
        import jsonschema  # type: ignore
    except Exception:
        print("jsonschema not installed. Install with: pip install jsonschema", file=sys.stderr)
        return 2

    try:
        with open(args.schema, "r", encoding="utf-8") as f:
            schema = json.load(f)
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        return 2

    try:
        jsonschema.validate(instance=cfg, schema=schema)
    except Exception as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        return 1

    # Optional: lint project URL either from --project-url/env or config.projectUrl
    url = args.project_url or (cfg.get("projectUrl") if isinstance(cfg, dict) else "")
    if url:
        import re
        pat = re.compile(r"^https://github.com/orgs/[^/]+/projects/[0-9]+$")
        if not pat.match(url):
            print(f"Validation failed: project URL not in expected format: {url}", file=sys.stderr)
            return 1

    print(f"Validation PASS for {cfg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
