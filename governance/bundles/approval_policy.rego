package dreamseedai.approval_policy

# 승인 워크플로우 정책: 고위험 액션에 대한 승인 요구
default allow = false

# 고위험 액션 목록
high_risk_actions = {"delete_user", "modify_permissions", "access_confidential_data"}

high_risk_action {
    input.action != null
    high_risk_actions[input.action]
}

# 승인 유효성 검사: 승인자가 관리자이며 승인 플래그 확인
approval_valid {
    input.approval.approved == true
    input.approval.approver.role == "admin"
}

# 고위험 액션이 아닌 경우 허용
allow {
    not high_risk_action
}

# 고위험 액션인 경우, 승인 있으면 허용
allow {
    high_risk_action
    approval_valid
}
