#!/usr/bin/env python3
"""
Policy Bundle Compiler

Compiles YAML policy bundles to JSON for runtime use.
Validates before compiling.
"""

import sys
import json
import yaml
import hashlib
from pathlib import Path
from datetime import datetime


def load_yaml(path: Path) -> dict:
    """Load YAML file"""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def calculate_hash(data: dict) -> str:
    """Calculate SHA256 hash of policy bundle"""
    # Convert to canonical JSON string
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def compile_bundle(bundle: dict, add_metadata: bool = True) -> dict:
    """
    Compile policy bundle
    
    Args:
        bundle: Policy bundle dict
        add_metadata: Add compilation metadata
    
    Returns:
        Compiled bundle with metadata
    """
    compiled = bundle.copy()
    
    if add_metadata:
        # Add compilation metadata
        if '_compiled' not in compiled:
            compiled['_compiled'] = {}
        
        compiled['_compiled']['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        compiled['_compiled']['compiler_version'] = '1.0.0'
        compiled['_compiled']['hash'] = calculate_hash(bundle)
    
    return compiled


def save_json(data: dict, path: Path, pretty: bool = True):
    """Save dict as JSON file"""
    with open(path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    
    print(f"✅ Saved: {path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python compile.py <policy_bundle.yaml> [-o output.json] [--no-pretty]")
        print("\nOptions:")
        print("  -o, --output    Output JSON file path (default: compiled/<bundle_id>.json)")
        print("  --no-pretty     Compact JSON output")
        sys.exit(1)
    
    # Parse arguments
    bundle_path = Path(sys.argv[1])
    output_path = None
    pretty = True
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] in ('-o', '--output'):
            output_path = Path(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == '--no-pretty':
            pretty = False
            i += 1
        else:
            print(f"Unknown option: {sys.argv[i]}")
            sys.exit(1)
    
    if not bundle_path.exists():
        print(f"Error: File not found: {bundle_path}")
        sys.exit(1)
    
    print(f"Compiling: {bundle_path}")
    
    # Load YAML
    try:
        bundle = load_yaml(bundle_path)
    except Exception as e:
        print(f"Error loading YAML: {e}")
        sys.exit(1)
    
    # Validate first (call validate.py)
    print("\nValidating before compilation...")
    import subprocess
    validate_script = Path(__file__).parent / "validate.py"
    
    result = subprocess.run(
        [sys.executable, str(validate_script), str(bundle_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ Validation failed. Fix errors before compiling.")
        print(result.stdout)
        sys.exit(1)
    
    print("✅ Validation passed")
    
    # Compile
    print("\nCompiling...")
    compiled = compile_bundle(bundle)
    
    # Determine output path
    if output_path is None:
        governance_root = Path(__file__).parent.parent
        compiled_dir = governance_root / "compiled"
        compiled_dir.mkdir(exist_ok=True)
        
        bundle_id = bundle.get('bundle_id', 'unknown')
        output_path = compiled_dir / f"{bundle_id}.json"
    
    # Save JSON
    save_json(compiled, output_path, pretty=pretty)
    
    # Print summary
    print("\n" + "="*60)
    print("Compilation Summary:")
    print("="*60)
    print(f"Input:  {bundle_path}")
    print(f"Output: {output_path}")
    print(f"Bundle ID: {bundle.get('bundle_id')}")
    print(f"Version: {bundle.get('version')}")
    print(f"Phase: {bundle.get('phase')}")
    print(f"Hash: {compiled['_compiled']['hash'][:16]}...")
    print(f"Compiled at: {compiled['_compiled']['timestamp']}")
    print(f"Size: {output_path.stat().st_size} bytes")
    print("="*60)
    
    print("\n✅ Compilation successful!")
    print("\nTo use this policy bundle, set:")
    print(f"  export POLICY_BUNDLE_ID={bundle.get('bundle_id')}")
    print(f"  export POLICY_BUNDLE_PATH={output_path}")
    

if __name__ == "__main__":
    main()
