package dreamseedai.ai_behavior_policy

# AI 행동 정책: AI 응답 행동 제한
default allow = false

# 응답 길이 제한 (예: 1000자 이하)
response_too_long {
    input.response_length != null
    input.response_length > 1000
}

# 외부 링크 포함 감지
external_link_detected {
    contains(lower(input.content), "http://")
}

external_link_detected {
    contains(lower(input.content), "https://")
}

# 학생의 과제 대행 요청 감지 (assignment_help 플래그로 전달되는 경우)
assignment_request {
    input.user.role == "student"
    input.request_type == "assignment_help"
}

# 모든 위반 조건이 없을 경우만 허용
allow {
    not response_too_long
    not external_link_detected
    not assignment_request
}
