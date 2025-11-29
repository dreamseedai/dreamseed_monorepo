"""
Route-to-Action Mapping for DreamSeedAI
고도화된 route → action 매핑 (Regex 기반)
"""

import re
from typing import Optional, Tuple

# (method, regex, action, required_flag, approval_rule)
_ROUTE_RULES = [
    # ========================================================================
    # Classes (클래스/학급)
    # ========================================================================
    ("GET", re.compile(r"^/api/v1/classes/\d+/snapshot$"), "class:read", None, None),
    ("GET", re.compile(r"^/api/v1/classes/\d+/students$"), "class:read", None, None),
    (
        "GET",
        re.compile(r"^/api/v1/classes/\d+/risk/summary$"),
        "risk:read",
        "risk_engine",
        None,
    ),
    ("POST", re.compile(r"^/api/v1/classes$"), "class:write", None, None),
    ("PUT", re.compile(r"^/api/v1/classes/\d+$"), "class:update", None, None),
    ("PATCH", re.compile(r"^/api/v1/classes/\d+$"), "class:update", None, None),
    ("DELETE", re.compile(r"^/api/v1/classes/\d+$"), "class:delete", None, None),
    # ========================================================================
    # Students (학생)
    # ========================================================================
    ("GET", re.compile(r"^/api/v1/students/\d+/timeline$"), "student:read", None, None),
    ("GET", re.compile(r"^/api/v1/students/\d+$"), "student:read", None, None),
    ("POST", re.compile(r"^/api/v1/students$"), "student:write", None, None),
    ("PUT", re.compile(r"^/api/v1/students/\d+$"), "student:update", None, None),
    ("PATCH", re.compile(r"^/api/v1/students/\d+$"), "student:update", None, None),
    ("DELETE", re.compile(r"^/api/v1/students/\d+$"), "student:delete", None, None),
    # ========================================================================
    # Assignments (과제)
    # ========================================================================
    (
        "POST",
        re.compile(r"^/api/v1/assignments$"),
        "assignment:create",
        None,
        "content.newitem",
    ),
    ("GET", re.compile(r"^/api/v1/assignments/\d+$"), "assignment:read", None, None),
    ("PUT", re.compile(r"^/api/v1/assignments/\d+$"), "assignment:update", None, None),
    (
        "PATCH",
        re.compile(r"^/api/v1/assignments/\d+$"),
        "assignment:update",
        None,
        None,
    ),
    (
        "DELETE",
        re.compile(r"^/api/v1/assignments/\d+$"),
        "assignment:delete",
        None,
        None,
    ),
    # ========================================================================
    # Assignment Templates (과제 템플릿)
    # ========================================================================
    (
        "GET",
        re.compile(r"^/api/v1/assignment-templates$"),
        "assignment:template:read",
        None,
        None,
    ),
    (
        "GET",
        re.compile(r"^/api/v1/assignment-templates/\d+$"),
        "assignment:template:read",
        None,
        None,
    ),
    # ========================================================================
    # Tutor (AI 튜터)
    # ========================================================================
    ("POST", re.compile(r"^/api/v1/tutor/query$"), "tutor:ask", None, None),
    ("GET", re.compile(r"^/api/v1/tutor/sessions/\d+$"), "tutor:read", None, None),
    ("GET", re.compile(r"^/api/v1/tutor/sessions$"), "tutor:read", None, None),
    # ========================================================================
    # Risk Engine (위험도 분석)
    # ========================================================================
    (
        "GET",
        re.compile(r"^/api/v1/risk/students/\d+$"),
        "risk:read",
        "risk_engine",
        None,
    ),
    ("POST", re.compile(r"^/api/v1/risk/analyze$"), "risk:write", "risk_engine", None),
    # ========================================================================
    # Content (콘텐츠 제안/승인)
    # ========================================================================
    (
        "POST",
        re.compile(r"^/api/v1/content/propose$"),
        "content:propose",
        None,
        "ai_content_recommendation",
    ),
    ("POST", re.compile(r"^/api/v1/content/approve$"), "content:approve", None, None),
    # ========================================================================
    # Exams (시험)
    # ========================================================================
    ("GET", re.compile(r"^/api/v1/exams/\d+$"), "exam:read", "exam_pipeline", None),
    ("POST", re.compile(r"^/api/v1/exams$"), "exam:create", "exam_pipeline", None),
    # ========================================================================
    # Parent Portal (학부모 포털)
    # ========================================================================
    (
        "GET",
        re.compile(r"^/api/v1/parent/children$"),
        "own_children:read",
        "parent_portal",
        None,
    ),
    (
        "GET",
        re.compile(r"^/api/v1/parent/children/\d+$"),
        "own_children:read",
        "parent_portal",
        None,
    ),
    (
        "POST",
        re.compile(r"^/api/v1/parent/consent$"),
        "consent:manage",
        "parent_portal",
        None,
    ),
    (
        "POST",
        re.compile(r"^/api/v1/parent/data-deletion$"),
        "data_deletion:request",
        "parent_portal",
        "data_deletion_request",
    ),
    # ========================================================================
    # Internal (내부 관리 API)
    # ========================================================================
    ("POST", re.compile(r"^/internal/policy/reload$"), "policy:write", None, None),
    ("GET", re.compile(r"^/internal/policy/status$"), "policy:read", None, None),
    ("GET", re.compile(r"^/internal/audit/logs$"), "audit:read", None, None),
    # ========================================================================
    # Health Checks (Public)
    # ========================================================================
    ("GET", re.compile(r"^/healthz$"), "meta:read", None, None),
    ("GET", re.compile(r"^/readyz$"), "meta:read", None, None),
    ("GET", re.compile(r"^/__ok$"), "meta:read", None, None),
]


def route_to_action(method: str, path: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    HTTP 요청 → (action, required_flag, approval_rule) 매핑

    Args:
        method: HTTP 메서드 (GET, POST, PUT, PATCH, DELETE)
        path: 요청 경로

    Returns:
        (action, required_flag, approval_rule)
        - action: 권한 키 (예: "class:read")
        - required_flag: 필요한 feature flag (None이면 불필요)
        - approval_rule: 승인 규칙 ID (None이면 불필요)
    """
    method = method.upper()

    for rule_method, regex, action, flag, approval in _ROUTE_RULES:
        if rule_method == method and regex.match(path):
            return action, flag, approval

    return "unknown", None, None


def get_all_actions() -> set:
    """모든 정의된 action 키 반환 (문서/테스트용)"""
    actions = set()
    for _, _, action, _, _ in _ROUTE_RULES:
        actions.add(action)
    return actions


def get_routes_for_action(action: str) -> list:
    """특정 action에 매핑된 모든 route 반환 (문서/테스트용)"""
    routes = []
    for method, regex, act, flag, approval in _ROUTE_RULES:
        if act == action:
            routes.append(
                {
                    "method": method,
                    "pattern": regex.pattern,
                    "flag": flag,
                    "approval": approval,
                }
            )
    return routes
