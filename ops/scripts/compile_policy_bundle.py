#!/usr/bin/env python3
"""
Policy Bundle Compiler
컴파일: YAML → JSON + 스키마 검증
"""
import sys
import json
import yaml
import pathlib
from jsonschema import validate, ValidationError

# 경로 설정
root = pathlib.Path(__file__).resolve().parents[2]
schema_path = root / "governance" / "schemas" / "policy-bundle.schema.json"
compiled_dir = root / "governance" / "compiled"
compiled_dir.mkdir(parents=True, exist_ok=True)

# 스키마 로드
if not schema_path.exists():
    print(f"❌ Schema not found: {schema_path}")
    sys.exit(1)

schema = json.loads(schema_path.read_text("utf-8"))


def compile_one(yaml_path: pathlib.Path):
    """단일 YAML 번들 컴파일"""
    try:
        # YAML 로드
        data = yaml.safe_load(yaml_path.read_text("utf-8"))
        
        # 스키마 검증
        validate(instance=data, schema=schema)
        
        # JSON 출력
        out = compiled_dir / (yaml_path.stem + ".json")
        out.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            "utf-8"
        )
        
        print(f"✔ compiled {yaml_path.name} -> {out.name}")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML parse error in {yaml_path.name}: {e}")
        return False
    except ValidationError as e:
        print(f"❌ Schema validation failed for {yaml_path.name}:")
        print(f"   {e.message}")
        return False
    except Exception as e:
        print(f"❌ Error compiling {yaml_path.name}: {e}")
        return False


def main():
    """모든 번들 컴파일"""
    bundles_dir = root / "governance" / "bundles"
    
    if not bundles_dir.exists():
        print(f"❌ Bundles directory not found: {bundles_dir}")
        sys.exit(1)
    
    yaml_files = list(bundles_dir.glob("*.yaml"))
    
    if not yaml_files:
        print(f"⚠️  No YAML files found in {bundles_dir}")
        sys.exit(0)
    
    print(f"📦 Compiling {len(yaml_files)} policy bundle(s)...")
    print()
    
    success_count = 0
    for yaml_file in yaml_files:
        if compile_one(yaml_file):
            success_count += 1
    
    print()
    print(f"✅ Successfully compiled {success_count}/{len(yaml_files)} bundle(s)")
    print(f"📁 Output directory: {compiled_dir}")
    
    if success_count < len(yaml_files):
        sys.exit(1)


if __name__ == "__main__":
    main()
