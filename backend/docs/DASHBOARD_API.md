# Dashboard API Documentation

CAT 시험 결과 조회를 위한 대시보드 API

## Overview

교사/학부모/튜터가 학생들의 적응형 시험(CAT) 결과를 조회할 수 있는 API입니다.
`ExamSession.score`와 `meta.grade_*` 정보를 활용하여 점수, 등급, 백분위 등을 제공합니다.

## Authentication

모든 엔드포인트는 인증이 필요합니다.
- HTTP Bearer 토큰 사용
- 역할 기반 접근 제어 (RBAC)

## API Endpoints

### 1. 교사/튜터용: 반 시험 요약

```http
GET /api/dashboard/teacher/classes/{class_id}/exams
```

특정 반의 최근 시험 결과 요약을 조회합니다.

**Parameters:**
- `class_id` (path, required): 반 ID
- `limit` (query, optional): 최대 시험 수 (기본값: 50, 최대: 200)

**Response:**
```json
{
  "class_id": 1,
  "name": "수학 1반",
  "subject": "math",
  "grade": "고1",
  "student_count": 25,
  "exam_sessions": [
    {
      "exam_session_id": 123,
      "exam_type": "mock",
      "status": "completed",
      "started_at": "2024-11-20T10:00:00+00:00",
      "ended_at": "2024-11-20T10:30:00+00:00",
      "duration_sec": 1800,
      "theta": 0.5,
      "standard_error": 0.3,
      "score": 58.3,
      "grade_numeric": 2,
      "grade_letter": "B",
      "percentile": 69.1,
      "t_score": 55.0
    }
  ],
  "students": [
    {
      "student_id": 1,
      "name": "김철수",
      "grade": "고1",
      "exam_count": 3,
      "latest_exam": { /* 위와 동일한 형식 */ }
    }
  ]
}
```

**Permissions:**
- 교사: 자신이 담당하는 반만
- 튜터: 자신이 담당하는 반만

---

### 2. 교사/튜터용: 학생 시험 히스토리

```http
GET /api/dashboard/teacher/students/{student_id}/exams
```

특정 학생의 시험 히스토리를 조회합니다.

**Parameters:**
- `student_id` (path, required): 학생 ID
- `limit` (query, optional): 최대 시험 수 (기본값: 50, 최대: 200)

**Response:**
```json
{
  "student_id": 1,
  "student_name": "김철수",
  "student_grade": "고1",
  "exams": [
    {
      "exam_session_id": 123,
      "exam_type": "mock",
      "status": "completed",
      "started_at": "2024-11-20T10:00:00+00:00",
      "ended_at": "2024-11-20T10:30:00+00:00",
      "duration_sec": 1800,
      "theta": 0.5,
      "standard_error": 0.3,
      "score": 58.3,
      "grade_numeric": 2,
      "grade_letter": "B",
      "percentile": 69.1,
      "t_score": 55.0
    }
  ],
  "statistics": {
    "total_exams": 3,
    "avg_score": 62.5,
    "max_score": 75.2,
    "min_score": 58.3,
    "latest_score": 58.3
  }
}
```

**Permissions:**
- 교사: 자신의 학생만
- 튜터: 자신의 학생만

---

### 3. 튜터용: 전체 학생 요약

```http
GET /api/dashboard/tutor/students/exams
```

튜터가 담당하는 모든 학생의 최근 시험 요약을 조회합니다.

**Parameters:**
- `limit` (query, optional): 최대 학생 수 (기본값: 50, 최대: 200)

**Response:**
```json
{
  "tutor_id": 1,
  "students": [
    {
      "student_id": 1,
      "name": "김철수",
      "grade": "고1",
      "exam_count": 3,
      "latest_exam": {
        "exam_session_id": 123,
        "score": 58.3,
        "grade_numeric": 2,
        "grade_letter": "B"
      }
    }
  ],
  "statistics": {
    "total_students": 15,
    "students_with_exams": 12,
    "avg_score": 65.5,
    "max_score": 85.2,
    "min_score": 45.3
  }
}
```

**Permissions:**
- 튜터만 접근 가능

---

### 4. 학부모용: 자녀 시험 히스토리

```http
GET /api/dashboard/parent/children/{student_id}/exams
```

자녀의 시험 히스토리를 조회합니다.

**Parameters:**
- `student_id` (path, required): 학생 ID
- `limit` (query, optional): 최대 시험 수 (기본값: 50, 최대: 200)

**Response:**
```json
{
  "student_id": 1,
  "student_name": "김철수",
  "student_grade": "고1",
  "exams": [
    {
      "exam_session_id": 123,
      "exam_type": "mock",
      "date": "2024-11-20T10:30:00+00:00",
      "duration_sec": 1800,
      "score": 58.3,
      "grade_numeric": 2,
      "grade_letter": "B",
      "percentile": 69.1
    }
  ],
  "statistics": {
    "total_exams": 3,
    "avg_score": 62.5,
    "max_score": 75.2,
    "min_score": 58.3,
    "recent_trend": "improving"
  }
}
```

**Note:** 학부모는 theta, standard_error 등의 기술적 세부사항을 볼 수 없습니다.

**Permissions:**
- 학부모: 자신의 자녀만

---

### 5. 공통: 시험 세션 상세

```http
GET /api/dashboard/exams/{exam_session_id}
```

특정 시험 세션의 상세 정보를 조회합니다.

**Parameters:**
- `exam_session_id` (path, required): 시험 세션 ID

**Response:**
```json
{
  "exam_session": {
    "exam_session_id": 123,
    "exam_type": "mock",
    "status": "completed",
    "started_at": "2024-11-20T10:00:00+00:00",
    "ended_at": "2024-11-20T10:30:00+00:00",
    "duration_sec": 1800,
    "theta": 0.5,
    "standard_error": 0.3,
    "score": 58.3,
    "grade_numeric": 2,
    "grade_letter": "B",
    "percentile": 69.1,
    "t_score": 55.0
  },
  "student": {
    "id": 1,
    "name": "김철수",
    "grade": "고1"
  },
  "attempts": [
    {
      "attempt_id": 1,
      "item_id": 5,
      "correct": true,
      "response_time_ms": 15000,
      "selected_choice_id": 12,
      "theta_before": 0.0,
      "theta_after": 0.5,
      "created_at": "2024-11-20T10:05:00+00:00"
    }
  ],
  "attempt_count": 10
}
```

**Permissions:**
- 교사/튜터: 자신의 학생만
- 학부모: 자신의 자녀만
- 학생: 자신의 시험만

---

## Score/Grade Fields

### Score Fields

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `score` | float | 0-100 점수 | 0.0 ~ 100.0 |
| `t_score` | float | T-점수 (표준화) | 일반적으로 20 ~ 80 |
| `percentile` | float | 백분위 | 0.0 ~ 100.0 |
| `grade_numeric` | int | 수치 등급 (9등급제) | 1 ~ 9 |
| `grade_letter` | str | 문자 등급 | A, B, C, D, F |

### Grade Conversion

- **9등급제**: 1등급(최상위) ~ 9등급(최하위)
  - 1등급: θ ≥ 1.0
  - 2등급: 0.5 ≤ θ < 1.0
  - 3등급: 0.0 ≤ θ < 0.5
  - ...

- **A-F 등급**:
  - A: 90-100 percentile
  - B: 75-90 percentile
  - C: 50-75 percentile
  - D: 25-50 percentile
  - F: 0-25 percentile

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "교사 또는 튜터만 접근할 수 있습니다."
}
```

### 404 Not Found
```json
{
  "detail": "Student not found"
}
```

---

## Integration with score_utils

모든 점수/등급 변환은 `app.core.services.score_utils` 모듈을 사용합니다:

```python
from app.core.services.score_utils import summarize_theta

# Theta를 모든 점수 형식으로 변환
summary = summarize_theta(theta=0.5)
# Returns:
# {
#     "theta": 0.5,
#     "score_0_100": 58.3,
#     "t_score": 55.0,
#     "percentile": 69.1,
#     "grade_numeric": 2,
#     "grade_letter": "B"
# }
```

---

## Testing

테스트 실행:
```bash
pytest tests/test_dashboard.py -v
```

테스트 커버리지:
- ✅ 교사 반 시험 요약
- ✅ 교사 학생 시험 히스토리
- ✅ 튜터 전체 학생 요약
- ✅ 학부모 자녀 시험 히스토리
- ✅ 시험 세션 상세 조회

---

## Production Notes

### TODO Items

1. **Parent-Student 관계 검증**
   - 현재: 간단한 존재 여부만 체크
   - 필요: ParentApproval 테이블 또는 parent_student 관계 테이블 검증

2. **인증 구현**
   - 현재: `get_current_user`가 501 Not Implemented 반환
   - 필요: JWT 검증 로직 구현

3. **캐싱**
   - 통계 데이터 Redis 캐싱
   - TTL: 5분 권장

4. **페이지네이션**
   - 현재: limit 파라미터로 제한
   - 고려: cursor-based pagination

5. **권한 최적화**
   - 현재: 매 요청마다 DB 조회
   - 고려: 권한 정보 캐싱

---

## Examples

### cURL Examples

**교사: 반 시험 요약 조회**
```bash
curl -X GET "http://localhost:8000/api/dashboard/teacher/classes/1/exams" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**학부모: 자녀 시험 히스토리**
```bash
curl -X GET "http://localhost:8000/api/dashboard/parent/children/1/exams?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**튜터: 전체 학생 요약**
```bash
curl -X GET "http://localhost:8000/api/dashboard/tutor/students/exams" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Change Log

### 2024-11-20
- ✅ 초기 구현 완료
- ✅ 교사/튜터/학부모 API 구현
- ✅ score_utils 통합
- ✅ 5개 테스트 통과
