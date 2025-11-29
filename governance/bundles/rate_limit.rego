package dreamseedai.rate_limit

# 사용량 제한 정책: API 호출 및 자원 사용 제한
default allow = false

# 하루 API 호출 횟수 제한 (예: 1000회)
over_rate_limit {
    input.user.api_calls_today != null
    input.user.api_calls_today > 1000
}

# AI 튜터 세션 시간 제한 (예: 60분)
session_time_exceeded {
    input.session.duration_minutes != null
    input.session.duration_minutes > 60
}

# 자원 사용량 쿼터 초과
quota_exceeded {
    input.user.quota != null
    input.user.usage != null
    input.user.usage > input.user.quota
}

# 모든 위반 조건이 없을 경우만 허용
allow {
    not over_rate_limit
    not session_time_exceeded
    not quota_exceeded
}
