#!/usr/bin/env python3
"""
Policy Bundle Validator

Validates YAML policy bundles against JSON Schema.
"""

import sys
import json
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError


def load_schema(schema_path: Path) -> dict:
    """Load JSON Schema"""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_policy_bundle(bundle_path: Path) -> dict:
    """Load YAML policy bundle"""
    with open(bundle_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_bundle(bundle: dict, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate policy bundle against schema
    
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    try:
        validate(instance=bundle, schema=schema)
        return True, []
    except ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
        errors.append(f"  at path: {'.'.join(str(p) for p in e.absolute_path)}")
        return False, errors


def additional_validations(bundle: dict) -> tuple[bool, list[str]]:
    """
    Additional business logic validations
    """
    warnings = []
    errors = []
    
    # 1. Phase에 맞는 기능 플래그 검증
    phase = bundle.get('phase', 0)
    feature_flags = bundle.get('feature_flags', {})
    
    if phase == 0:
        # Phase 0: 거버넌스 비활성
        if feature_flags.get('rbac_enforcement'):
            warnings.append("Phase 0 should not have rbac_enforcement enabled")
    
    elif phase == 1:
        # Phase 1: 핵심 기능 필수
        required_flags = ['rbac_enforcement', 'content_safety_filter', 'audit_logging']
        for flag in required_flags:
            if not feature_flags.get(flag):
                errors.append(f"Phase 1 requires '{flag}' to be enabled")
    
    # 2. RBAC 역할 검증
    rbac = bundle.get('rbac', {})
    if rbac.get('enabled'):
        roles = rbac.get('roles', [])
        role_names = [r['name'] for r in roles]
        
        # 필수 역할 확인
        required_roles = ['platform_admin', 'teacher', 'student']
        for role in required_roles:
            if role not in role_names:
                warnings.append(f"Missing recommended role: {role}")
        
        # 중복 역할 확인
        if len(role_names) != len(set(role_names)):
            errors.append("Duplicate role names found")
    
    # 3. 승인 워크플로우 검증
    approvals = bundle.get('approvals', {})
    if approvals.get('enabled'):
        rules = approvals.get('rules', [])
        
        for rule in rules:
            # SLA 시간이 합리적인지 확인
            sla_hours = rule.get('sla_hours', 0)
            if sla_hours > 720:  # 30일
                warnings.append(f"Rule '{rule['id']}' has very long SLA: {sla_hours} hours")
            
            # approver_role이 RBAC에 존재하는지 확인
            approver_role = rule.get('approver_role')
            if rbac.get('enabled') and approver_role:
                if approver_role not in role_names:
                    errors.append(f"Rule '{rule['id']}' references unknown role: {approver_role}")
    
    # 4. 안전성 정책 검증
    safety = bundle.get('safety', {})
    if safety.get('enabled'):
        tutor = safety.get('tutor', {})
        
        # 시험 중 튜터 정책 검증
        if tutor.get('allow_during_exam') and tutor.get('response_mode_during_exam') == 'full':
            warnings.append("Allowing full tutor access during exam may compromise academic integrity")
    
    # 5. 개인정보 보호 정책 검증
    privacy = bundle.get('privacy', {})
    if privacy.get('enabled'):
        data_protection = privacy.get('data_protection', {})
        encryption = data_protection.get('encryption', {})
        
        # 암호화 표준 검증
        at_rest = encryption.get('at_rest', '')
        if at_rest and 'AES-256' not in at_rest:
            warnings.append(f"Weak encryption at rest: {at_rest}. Recommend AES-256-GCM")
        
        in_transit = encryption.get('in_transit', '')
        if in_transit and 'TLS-1.3' not in in_transit:
            warnings.append(f"Weak encryption in transit: {in_transit}. Recommend TLS-1.3")
    
    return len(errors) == 0, errors + warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate.py <policy_bundle.yaml>")
        sys.exit(1)
    
    bundle_path = Path(sys.argv[1])
    
    if not bundle_path.exists():
        print(f"Error: File not found: {bundle_path}")
        sys.exit(1)
    
    # Determine schema path
    governance_root = Path(__file__).parent.parent
    schema_path = governance_root / "schemas" / "policy-bundle.schema.json"
    
    if not schema_path.exists():
        print(f"Error: Schema not found: {schema_path}")
        sys.exit(1)
    
    print(f"Validating: {bundle_path}")
    print(f"Schema: {schema_path}")
    print()
    
    # Load files
    try:
        schema = load_schema(schema_path)
        bundle = load_policy_bundle(bundle_path)
    except Exception as e:
        print(f"Error loading files: {e}")
        sys.exit(1)
    
    # Validate against schema
    print("1. Schema validation...")
    is_valid_schema, schema_errors = validate_bundle(bundle, schema)
    
    if not is_valid_schema:
        print("❌ Schema validation FAILED")
        for error in schema_errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ Schema validation passed")
    
    # Additional validations
    print("\n2. Business logic validation...")
    is_valid_logic, logic_messages = additional_validations(bundle)
    
    if logic_messages:
        for msg in logic_messages:
            if "Error:" in msg or msg.startswith("Phase") or msg.startswith("Rule") or msg.startswith("Duplicate"):
                print(f"  ❌ {msg}")
            else:
                print(f"  ⚠️  {msg}")
    
    if not is_valid_logic:
        print("\n❌ Validation FAILED")
        sys.exit(1)
    else:
        print("\n✅ All validations passed")
        
        # Print summary
        print("\n" + "="*60)
        print("Policy Bundle Summary:")
        print("="*60)
        print(f"Bundle ID: {bundle.get('bundle_id')}")
        print(f"Version: {bundle.get('version')}")
        print(f"Phase: {bundle.get('phase')}")
        print(f"Description: {bundle.get('description', 'N/A')}")
        print(f"RBAC Enabled: {bundle.get('rbac', {}).get('enabled')}")
        print(f"Safety Enabled: {bundle.get('safety', {}).get('enabled')}")
        print(f"Privacy Enabled: {bundle.get('privacy', {}).get('enabled')}")
        print(f"Approvals Enabled: {bundle.get('approvals', {}).get('enabled')}")
        print(f"Enforcement Mode: {bundle.get('enforcement', {}).get('mode', 'N/A')}")
        
        # Feature flags summary
        feature_flags = bundle.get('feature_flags', {})
        enabled_features = [k for k, v in feature_flags.items() if v]
        print(f"\nEnabled Features ({len(enabled_features)}):")
        for feature in enabled_features:
            print(f"  - {feature}")
        
        print("="*60)
        sys.exit(0)


if __name__ == "__main__":
    main()
