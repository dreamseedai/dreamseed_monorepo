package dreamseedai.data_protection

# 데이터 보호 정책: 개인정보 접근 제어 및 데이터 보존 확인
default allow = false

# 민감 데이터 접근 - 교사 또는 관리자만 허용
sensitive_data_access {
    input.resource.type == "personal_info"
    not (input.user.role == "teacher" or input.user.role == "admin")
}

# 학부모 동의 필요한 경우 - 학생에게 동의 없으면 거부
no_parental_consent {
    input.resource.requires_parent_consent == true
    input.user.role == "student"
    not input.user.parent_consent
}

# 데이터 보존 기간 초과 - 만료된 데이터 접근 시 거부
data_expired {
    input.resource.age_days != null
    input.resource.age_days > 365
}

# 모든 위반 조건이 없을 경우만 허용
allow {
    not sensitive_data_access
    not no_parental_consent
    not data_expired
}
