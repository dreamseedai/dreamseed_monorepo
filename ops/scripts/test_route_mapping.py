#!/usr/bin/env python3
"""
governance route_to_action 테스트
policy_routes.py 매핑 검증
"""
import sys
from pathlib import Path

# Monorepo 루트를 기준으로 backend 경로 추가
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_PATH = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))

# backend 경로 추가 후 import (sys.path 수정 필요)
from app.middleware.policy_routes import route_to_action, get_all_actions, get_routes_for_action  # noqa: E402  # type: ignore

def test_classes():
    """클래스 엔드포인트 테스트"""
    cases = [
        ("GET", "/api/v1/classes/123/snapshot", "class:read", None, None),
        ("GET", "/api/v1/classes/456/students", "class:read", None, None),
        ("GET", "/api/v1/classes/789/risk/summary", "risk:read", "risk_engine", None),
        ("POST", "/api/v1/classes", "class:write", None, None),
        ("PUT", "/api/v1/classes/123", "class:update", None, None),
        ("PATCH", "/api/v1/classes/123", "class:update", None, None),
        ("DELETE", "/api/v1/classes/123", "class:delete", None, None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
        assert flag == expected_flag, f"❌ {method} {path}: flag mismatch"
        assert approval == expected_approval, f"❌ {method} {path}: approval mismatch"
    
    print("✅ Classes: 7 tests passed")

def test_students():
    """학생 엔드포인트 테스트"""
    cases = [
        ("GET", "/api/v1/students/123/timeline", "student:read", None, None),
        ("GET", "/api/v1/students/123", "student:read", None, None),
        ("POST", "/api/v1/students", "student:write", None, None),
        ("PUT", "/api/v1/students/123", "student:update", None, None),
        ("DELETE", "/api/v1/students/123", "student:delete", None, None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
    
    print("✅ Students: 5 tests passed")

def test_assignments():
    """과제 엔드포인트 테스트"""
    cases = [
        ("POST", "/api/v1/assignments", "assignment:create", None, "content.newitem"),
        ("GET", "/api/v1/assignments/123", "assignment:read", None, None),
        ("PUT", "/api/v1/assignments/123", "assignment:update", None, None),
        ("DELETE", "/api/v1/assignments/123", "assignment:delete", None, None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
        assert approval == expected_approval, f"❌ {method} {path}: approval mismatch"
    
    print("✅ Assignments: 4 tests passed")

def test_tutor():
    """튜터 엔드포인트 테스트"""
    cases = [
        ("POST", "/api/v1/tutor/query", "tutor:ask", None, None),
        ("GET", "/api/v1/tutor/sessions/123", "tutor:read", None, None),
        ("GET", "/api/v1/tutor/sessions", "tutor:read", None, None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
    
    print("✅ Tutor: 3 tests passed")

def test_risk():
    """위험도 엔드포인트 테스트"""
    cases = [
        ("GET", "/api/v1/risk/students/123", "risk:read", "risk_engine", None),
        ("POST", "/api/v1/risk/analyze", "risk:write", "risk_engine", None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
        assert flag == expected_flag, f"❌ {method} {path}: flag mismatch"
    
    print("✅ Risk: 2 tests passed")

def test_content():
    """콘텐츠 엔드포인트 테스트"""
    cases = [
        ("POST", "/api/v1/content/propose", "content:propose", None, "ai_content_recommendation"),
        ("POST", "/api/v1/content/approve", "content:approve", None, None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
        assert approval == expected_approval, f"❌ {method} {path}: approval mismatch"
    
    print("✅ Content: 2 tests passed")

def test_parent():
    """학부모 포털 엔드포인트 테스트"""
    cases = [
        ("GET", "/api/v1/parent/children", "own_children:read", "parent_portal", None),
        ("GET", "/api/v1/parent/children/123", "own_children:read", "parent_portal", None),
        ("POST", "/api/v1/parent/consent", "consent:manage", "parent_portal", None),
        ("POST", "/api/v1/parent/data-deletion", "data_deletion:request", "parent_portal", "data_deletion_request"),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
        assert flag == expected_flag, f"❌ {method} {path}: flag mismatch"
        assert approval == expected_approval, f"❌ {method} {path}: approval mismatch"
    
    print("✅ Parent: 4 tests passed")

def test_internal():
    """내부 API 엔드포인트 테스트"""
    cases = [
        ("POST", "/internal/policy/reload", "policy:write", None, None),
        ("GET", "/internal/policy/status", "policy:read", None, None),
        ("GET", "/internal/audit/logs", "audit:read", None, None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
    
    print("✅ Internal: 3 tests passed")

def test_health():
    """헬스체크 엔드포인트 테스트"""
    cases = [
        ("GET", "/healthz", "meta:read", None, None),
        ("GET", "/readyz", "meta:read", None, None),
        ("GET", "/__ok", "meta:read", None, None),
    ]
    
    for method, path, expected_action, expected_flag, expected_approval in cases:
        action, flag, approval = route_to_action(method, path)
        assert action == expected_action, f"❌ {method} {path}: {action} != {expected_action}"
    
    print("✅ Health: 3 tests passed")

def test_unknown():
    """알 수 없는 경로 테스트"""
    action, flag, approval = route_to_action("GET", "/api/v1/unknown/path")
    assert action == "unknown", f"❌ Unknown path: {action} != unknown"
    print("✅ Unknown: 1 test passed")

def test_helpers():
    """헬퍼 함수 테스트"""
    all_actions = get_all_actions()
    assert "class:read" in all_actions
    assert "student:write" in all_actions
    assert "assignment:create" in all_actions
    print(f"✅ Helpers: {len(all_actions)} unique actions found")
    
    routes = get_routes_for_action("class:read")
    assert len(routes) >= 2, f"❌ class:read routes: {len(routes)} < 2"
    print(f"✅ Helpers: class:read has {len(routes)} routes")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing policy_routes.py route_to_action mappings")
    print("=" * 60)
    
    try:
        test_classes()
        test_students()
        test_assignments()
        test_tutor()
        test_risk()
        test_content()
        test_parent()
        test_internal()
        test_health()
        test_unknown()
        test_helpers()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n{e}")
        print("=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
