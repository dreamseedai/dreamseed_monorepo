package dreamseedai.ai_content_policy

# AI 콘텐츠 정책: 부적절한 콘텐츠 필터링
default allow = false

# 금지어 목록
forbidden_words = {"badword1", "badword2", "badword3"}

# 민감 주제 목록
sensitive_topics = {"politics", "religion", "sex", "violence"}

# 금지어 감지
forbidden_word_detected {
    forbidden_word := forbidden_words[_]
    contains(lower(input.content), forbidden_word)
}

# 민감 주제 감지
sensitive_topic_detected {
    topic := sensitive_topics[_]
    contains(lower(input.content), topic)
}

# 학년 적합성 위반 (사용자 학년보다 높은 콘텐츠 등급)
age_inappropriate {
    input.user.grade < input.content.min_grade
}

# 모든 위반 조건이 없을 경우만 허용
allow {
    not forbidden_word_detected
    not sensitive_topic_detected
    not age_inappropriate
}
