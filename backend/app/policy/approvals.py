"""
Approval Workflow
승인 워크플로우 관리
"""
from typing import Dict, List, Any, Optional
from datetime import datetime


def get_approval_rule(policy: Dict[str, Any], rule_id: str) -> Optional[Dict[str, Any]]:
    """
    승인 규칙 조회
    
    Args:
        policy: 정책 번들 딕셔너리
        rule_id: 규칙 ID
        
    Returns:
        승인 규칙 딕셔너리 또는 None
    """
    rules = policy.get("approvals", {}).get("rules", [])
    for rule in rules:
        if rule.get("id") == rule_id:
            return rule
    return None


def create_approval_if_needed(
    policy: Dict[str, Any],
    rule_id: str,
    payload: Dict[str, Any],
    user_roles: List[str]
) -> bool:
    """
    승인이 필요한지 체크하고 필요하면 승인 요청 생성
    
    Args:
        policy: 정책 번들 딕셔너리
        rule_id: 규칙 ID
        payload: 요청 데이터
        user_roles: 사용자 역할
        
    Returns:
        승인이 필요하면 True, 아니면 False
        
    Note:
        실제로는 DB에 approval_request 레코드를 insert해야 함
        여기서는 간단히 필요 여부만 반환
    """
    rule = get_approval_rule(policy, rule_id)
    
    if not rule:
        # 규칙이 없으면 승인 불필요
        return False
    
    # 자동 승인 조건 체크
    auto_approve_conditions = rule.get("auto_approve_if", [])
    for condition in auto_approve_conditions:
        cond_expr = condition.get("condition", "")
        # 간단 예시: safety_score > 0.95
        if "safety_score" in cond_expr:
            threshold = float(cond_expr.split(">")[1].strip())
            if payload.get("safety_score", 0) > threshold:
                return False  # 자동 승인
    
    # 승인 필요
    # TODO: DB에 approval_request 레코드 생성
    # INSERT INTO approval_request (rule_id, requester, approver_role, payload_json, created_at)
    return True


def check_sla_breach(created_at: datetime, sla_hours: int) -> bool:
    """
    SLA 위반 여부 체크
    
    Args:
        created_at: 승인 요청 생성 시각
        sla_hours: SLA 시간
        
    Returns:
        SLA 위반이면 True
    """
    from datetime import timedelta
    now = datetime.now()
    deadline = created_at + timedelta(hours=sla_hours)
    return now > deadline
