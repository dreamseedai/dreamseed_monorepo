package dreamseedai.access_control

# 역할 기반 접근 제어 (RBAC) 정책
default allow = false

# 관리자 - 모든 액션 허용
allow {
    input.user.role == "admin"
}

# 교사 - 레슨 읽기 허용
allow {
    input.user.role == "teacher"
    input.resource.type == "lesson"
    input.action == "read"
}

# 교사 - 레슨 삭제 허용
allow {
    input.user.role == "teacher"
    input.resource.type == "lesson"
    input.action == "delete"
}

# 학생 - 자기 학년에 맞는 레슨 읽기 허용
allow {
    input.user.role == "student"
    input.resource.type == "lesson"
    input.action == "read"
    is_grade_appropriate(input.user, input.resource)
}

# Helper: 학생 학년과 레슨 학년 범위 검사
is_grade_appropriate(user, resource) {
    user.grade >= resource.min_grade
    user.grade <= resource.max_grade
}
