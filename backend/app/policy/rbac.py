"""
RBAC (Role-Based Access Control)
역할 기반 접근 제어
"""

from typing import Dict, List, Set, Any


def check_permission(policy: Dict[str, Any], roles: List[str], action: str) -> bool:
    """
    RBAC 권한 체크

    Args:
        policy: 정책 번들 딕셔너리
        roles: 사용자 역할 리스트
        action: 수행하려는 액션 (예: "class:read", "student:write")

    Returns:
        권한이 있으면 True, 없으면 False

    Logic:
        1. Deny 우선 (하나라도 deny면 거부)
        2. Allow 체크 (역할 중 하나라도 allow면 허용)
        3. 기본: Deny
    """
    # RBAC 비활성화 시 모두 허용
    if not policy.get("rbac", {}).get("enabled", True):
        return True

    # 역할별 권한 맵 구성
    role_map: Dict[str, Dict[str, Set[str]]] = {}
    for role_def in policy.get("rbac", {}).get("roles", []):
        role_name = role_def.get("name")
        if not role_name:
            continue

        role_map[role_name] = {
            "allows": set(role_def.get("allows", [])),
            "denies": set(role_def.get("denies", [])),
        }

    # 1. Deny 체크 (우선순위 높음)
    for role in roles:
        if role not in role_map:
            continue
        denies = role_map[role].get("denies", set())
        if action in denies or "*" in denies:
            return False

    # 2. Allow 체크
    for role in roles:
        if role not in role_map:
            continue
        allows = role_map[role].get("allows", set())
        if "*" in allows or action in allows:
            return True

    # 3. 기본: Deny
    return False


def get_user_roles(user_context: Dict[str, Any]) -> List[str]:
    """
    사용자 컨텍스트에서 역할 추출

    Args:
        user_context: 사용자 정보 딕셔너리

    Returns:
        역할 리스트
    """
    # 헤더, 토큰, DB 등에서 역할 추출
    # 간단 예시: user_context에 roles 키가 있다고 가정
    return user_context.get("roles", [])
