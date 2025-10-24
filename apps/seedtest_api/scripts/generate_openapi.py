#!/usr/bin/env python3
"""
Generate OpenAPI snapshot and ResultContract JSON Schema for the SeedTest API.

Outputs:
- apps/seedtest_api/openapi.json
- apps/seedtest_api/schemas/result.contract.schema.json

Usage (from repo root):
  PYTHONPATH=apps python3 apps/seedtest_api/scripts/generate_openapi.py
"""
from __future__ import annotations

import json
from pathlib import Path

# Import FastAPI app and schema model
from seedtest_api.app.main import app  # type: ignore
from seedtest_api.schemas.result import ResultContract  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
PKG_ROOT = ROOT / "apps" / "seedtest_api"
OUT_OPENAPI = PKG_ROOT / "openapi.json"
OUT_CONTRACT_SCHEMA = PKG_ROOT / "schemas" / "result.contract.schema.json"


def main() -> None:
    # OpenAPI snapshot
    openapi = app.openapi()
    OUT_OPENAPI.write_text(json.dumps(openapi, ensure_ascii=False, indent=2), encoding="utf-8")

    # JSON Schema for the contract
    contract_schema = ResultContract.model_json_schema()
    OUT_CONTRACT_SCHEMA.write_text(json.dumps(contract_schema, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote: {OUT_OPENAPI.relative_to(ROOT)}")
    print(f"Wrote: {OUT_CONTRACT_SCHEMA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
