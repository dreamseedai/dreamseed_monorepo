# Dashboard API Response Structures

CAT 대시보드 API의 응답 구조 명세서

## Overview

모든 API는 JSON 형식으로 응답하며, 역할(Teacher/Tutor/Parent)에 따라 다른 수준의 정보를 제공합니다.

---

## 1. Teacher API Responses

### 1.1 반 단위 요약

**Endpoint:** `GET /api/dashboard/teacher/classes/{class_id}/exams`

**Request Parameters:**
- `class_id` (path, required): 반 ID
- `limit` (query, optional): 최대 시험 수 (기본값: 50)

**Response:**

```json
{
  "class_id": 1,
  "name": "고2-1반",
  "subject": "수학",
  "grade": "고2",
  "student_count": 25,
  "exam_sessions": [
    {
      "exam_session_id": 101,
      "exam_type": "mock",
      "status": "completed",
      "started_at": "2025-11-20T10:00:00+00:00",
      "ended_at": "2025-11-20T12:00:00+00:00",
      "duration_sec": 7200,
      "theta": 0.45,
      "standard_error": 0.28,
      "score": 88.5,
      "grade_numeric": 2,
      "grade_letter": "A",
      "percentile": 82.3,
      "t_score": 54.5
    },
    {
      "exam_session_id": 102,
      "exam_type": "practice",
      "status": "completed",
      "started_at": "2025-11-19T14:00:00+00:00",
      "ended_at": "2025-11-19T15:30:00+00:00",
      "duration_sec": 5400,
      "theta": 0.32,
      "standard_error": 0.31,
      "score": 82.7,
      "grade_numeric": 2,
      "grade_letter": "B",
      "percentile": 75.6,
      "t_score": 53.2
    }
  ],
  "students": [
    {
      "student_id": 10,
      "name": "김철수",
      "grade": "고2",
      "exam_count": 3,
      "latest_exam": {
        "exam_session_id": 101,
        "exam_type": "mock",
        "status": "completed",
        "started_at": "2025-11-20T10:00:00+00:00",
        "ended_at": "2025-11-20T12:00:00+00:00",
        "duration_sec": 7200,
        "theta": 0.45,
        "standard_error": 0.28,
        "score": 88.5,
        "grade_numeric": 2,
        "grade_letter": "A",
        "percentile": 82.3,
        "t_score": 54.5
      }
    },
    {
      "student_id": 11,
      "name": "이영희",
      "grade": "고2",
      "exam_count": 5,
      "latest_exam": {
        "exam_session_id": 105,
        "exam_type": "mock",
        "status": "completed",
        "started_at": "2025-11-20T10:00:00+00:00",
        "ended_at": "2025-11-20T12:15:00+00:00",
        "duration_sec": 8100,
        "theta": 0.68,
        "standard_error": 0.25,
        "score": 92.3,
        "grade_numeric": 1,
        "grade_letter": "A",
        "percentile": 89.5,
        "t_score": 56.8
      }
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `class_id` | int | 반 ID |
| `name` | string | 반 이름 |
| `subject` | string | 과목 (math, english, etc.) |
| `grade` | string | 학년 (고1, 고2, etc.) |
| `student_count` | int | 학생 수 |
| `exam_sessions` | array | 최근 시험 세션 목록 |
| `students` | array | 학생별 요약 |

---

### 1.2 학생별 시험 히스토리

**Endpoint:** `GET /api/dashboard/teacher/students/{student_id}/exams`

**Request Parameters:**
- `student_id` (path, required): 학생 ID
- `limit` (query, optional): 최대 시험 수 (기본값: 50)

**Response:**

```json
{
  "student_id": 10,
  "student_name": "김철수",
  "student_grade": "고2",
  "exams": [
    {
      "exam_session_id": 101,
      "exam_type": "mock",
      "status": "completed",
      "started_at": "2025-11-20T10:00:00+00:00",
      "ended_at": "2025-11-20T12:00:00+00:00",
      "duration_sec": 7200,
      "theta": 0.45,
      "standard_error": 0.28,
      "score": 88.5,
      "grade_numeric": 2,
      "grade_letter": "A",
      "percentile": 82.3,
      "t_score": 54.5
    },
    {
      "exam_session_id": 98,
      "exam_type": "practice",
      "status": "completed",
      "started_at": "2025-11-18T14:00:00+00:00",
      "ended_at": "2025-11-18T15:45:00+00:00",
      "duration_sec": 6300,
      "theta": 0.38,
      "standard_error": 0.30,
      "score": 85.2,
      "grade_numeric": 2,
      "grade_letter": "B",
      "percentile": 78.9,
      "t_score": 53.8
    },
    {
      "exam_session_id": 92,
      "exam_type": "placement",
      "status": "completed",
      "started_at": "2025-11-15T10:00:00+00:00",
      "ended_at": "2025-11-15T11:30:00+00:00",
      "duration_sec": 5400,
      "theta": 0.25,
      "standard_error": 0.35,
      "score": 79.2,
      "grade_numeric": 3,
      "grade_letter": "B",
      "percentile": 72.1,
      "t_score": 52.5
    }
  ],
  "statistics": {
    "total_exams": 3,
    "avg_score": 84.3,
    "max_score": 88.5,
    "min_score": 79.2,
    "latest_score": 88.5
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | int | 학생 ID |
| `student_name` | string | 학생 이름 |
| `student_grade` | string | 학년 |
| `exams` | array | 시험 히스토리 (최신순) |
| `statistics` | object | 통계 정보 |

---

## 2. Tutor API Responses

### 2.1 전체 학생 요약

**Endpoint:** `GET /api/dashboard/tutor/students/exams`

**Request Parameters:**
- `limit` (query, optional): 최대 학생 수 (기본값: 50)

**Response:**

```json
{
  "tutor_id": 1,
  "students": [
    {
      "student_id": 10,
      "name": "김철수",
      "grade": "고2",
      "exam_count": 3,
      "latest_exam": {
        "exam_session_id": 101,
        "exam_type": "mock",
        "status": "completed",
        "started_at": "2025-11-20T10:00:00+00:00",
        "ended_at": "2025-11-20T12:00:00+00:00",
        "duration_sec": 7200,
        "theta": 0.45,
        "standard_error": 0.28,
        "score": 88.5,
        "grade_numeric": 2,
        "grade_letter": "A",
        "percentile": 82.3,
        "t_score": 54.5
      }
    },
    {
      "student_id": 11,
      "name": "이영희",
      "grade": "고2",
      "exam_count": 5,
      "latest_exam": {
        "exam_session_id": 105,
        "exam_type": "mock",
        "status": "completed",
        "started_at": "2025-11-20T10:00:00+00:00",
        "ended_at": "2025-11-20T12:15:00+00:00",
        "duration_sec": 8100,
        "theta": 0.68,
        "standard_error": 0.25,
        "score": 92.3,
        "grade_numeric": 1,
        "grade_letter": "A",
        "percentile": 89.5,
        "t_score": 56.8
      }
    },
    {
      "student_id": 12,
      "name": "박지훈",
      "grade": "고1",
      "exam_count": 2,
      "latest_exam": {
        "exam_session_id": 103,
        "exam_type": "practice",
        "status": "completed",
        "started_at": "2025-11-19T15:00:00+00:00",
        "ended_at": "2025-11-19T16:30:00+00:00",
        "duration_sec": 5400,
        "theta": 0.12,
        "standard_error": 0.38,
        "score": 72.4,
        "grade_numeric": 3,
        "grade_letter": "C",
        "percentile": 65.2,
        "t_score": 51.2
      }
    }
  ],
  "statistics": {
    "total_students": 3,
    "students_with_exams": 3,
    "avg_score": 84.4,
    "max_score": 92.3,
    "min_score": 72.4
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `tutor_id` | int | 튜터 ID |
| `students` | array | 담당 학생 목록 (최근 시험 날짜순) |
| `statistics` | object | 전체 통계 |

**Note:** 튜터는 개별 학생 히스토리 및 반 요약을 조회할 때 교사 API를 재사용합니다:
- `GET /api/dashboard/teacher/students/{student_id}/exams`
- `GET /api/dashboard/teacher/classes/{class_id}/exams`

---

## 3. Parent API Responses

### 3.1 자녀 시험 히스토리

**Endpoint:** `GET /api/dashboard/parent/children/{student_id}/exams`

**Request Parameters:**
- `student_id` (path, required): 자녀(학생) ID
- `limit` (query, optional): 최대 시험 수 (기본값: 50)

**Response:**

```json
{
  "student_id": 10,
  "student_name": "김철수",
  "student_grade": "고2",
  "exams": [
    {
      "exam_session_id": 101,
      "exam_type": "mock",
      "date": "2025-11-20T12:00:00+00:00",
      "duration_sec": 7200,
      "score": 88.5,
      "grade_numeric": 2,
      "grade_letter": "A",
      "percentile": 82.3
    },
    {
      "exam_session_id": 98,
      "exam_type": "practice",
      "date": "2025-11-18T15:45:00+00:00",
      "duration_sec": 6300,
      "score": 85.2,
      "grade_numeric": 2,
      "grade_letter": "B",
      "percentile": 78.9
    },
    {
      "exam_session_id": 92,
      "exam_type": "placement",
      "date": "2025-11-15T11:30:00+00:00",
      "duration_sec": 5400,
      "score": 79.2,
      "grade_numeric": 3,
      "grade_letter": "B",
      "percentile": 72.1
    }
  ],
  "statistics": {
    "total_exams": 3,
    "avg_score": 84.3,
    "max_score": 88.5,
    "min_score": 79.2,
    "recent_trend": "improving"
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | int | 자녀 ID |
| `student_name` | string | 자녀 이름 |
| `student_grade` | string | 학년 |
| `exams` | array | 시험 히스토리 (최신순) |
| `statistics` | object | 통계 정보 |

**Note:** 학부모는 `theta`, `standard_error`, `t_score` 등의 기술적 정보를 볼 수 없습니다.

---

## 4. Common API Responses

### 4.1 시험 세션 상세

**Endpoint:** `GET /api/dashboard/exams/{exam_session_id}`

**Request Parameters:**
- `exam_session_id` (path, required): 시험 세션 ID

**Response:**

```json
{
  "exam_session": {
    "exam_session_id": 101,
    "exam_type": "mock",
    "status": "completed",
    "started_at": "2025-11-20T10:00:00+00:00",
    "ended_at": "2025-11-20T12:00:00+00:00",
    "duration_sec": 7200,
    "theta": 0.45,
    "standard_error": 0.28,
    "score": 88.5,
    "grade_numeric": 2,
    "grade_letter": "A",
    "percentile": 82.3,
    "t_score": 54.5
  },
  "student": {
    "id": 10,
    "name": "김철수",
    "grade": "고2"
  },
  "attempts": [
    {
      "attempt_id": 501,
      "item_id": 25,
      "correct": true,
      "response_time_ms": 45000,
      "selected_choice_id": 102,
      "theta_before": 0.0,
      "theta_after": 0.25,
      "created_at": "2025-11-20T10:05:00+00:00"
    },
    {
      "attempt_id": 502,
      "item_id": 28,
      "correct": false,
      "response_time_ms": 52000,
      "selected_choice_id": 115,
      "theta_before": 0.25,
      "theta_after": 0.18,
      "created_at": "2025-11-20T10:12:00+00:00"
    },
    {
      "attempt_id": 503,
      "item_id": 31,
      "correct": true,
      "response_time_ms": 38000,
      "selected_choice_id": 128,
      "theta_before": 0.18,
      "theta_after": 0.35,
      "created_at": "2025-11-20T10:18:00+00:00"
    }
  ],
  "attempt_count": 10
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `exam_session` | object | 시험 세션 정보 |
| `student` | object | 학생 정보 |
| `attempts` | array | 문항별 응답 기록 |
| `attempt_count` | int | 전체 문항 수 |

---

## Field Reference

### Exam Session Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `exam_session_id` | int | 시험 세션 ID | 101 |
| `exam_type` | string | 시험 유형 | "mock", "practice", "placement" |
| `status` | string | 시험 상태 | "completed", "in_progress" |
| `started_at` | string (ISO 8601) | 시험 시작 시간 | "2025-11-20T10:00:00+00:00" |
| `ended_at` | string (ISO 8601) | 시험 종료 시간 | "2025-11-20T12:00:00+00:00" |
| `duration_sec` | int | 소요 시간 (초) | 7200 |
| `theta` | float | IRT 능력치 | 0.45 |
| `standard_error` | float | 표준 오차 | 0.28 |
| `score` | float | 0-100 점수 | 88.5 |
| `grade_numeric` | int | 수치 등급 (1-9) | 2 |
| `grade_letter` | string | 문자 등급 (A-F) | "A" |
| `percentile` | float | 백분위 (0-100) | 82.3 |
| `t_score` | float | T-점수 | 54.5 |

### Score Field Ranges

| Field | Min | Max | Description |
|-------|-----|-----|-------------|
| `theta` | -3.0 | 3.0 | IRT 능력치 (표준정규분포) |
| `standard_error` | 0.0 | 2.0 | 추정 오차 (낮을수록 정확) |
| `score` | 0.0 | 100.0 | 0-100 변환 점수 |
| `grade_numeric` | 1 | 9 | 9등급제 (1=최상위) |
| `grade_letter` | A | F | A, B, C, D, F |
| `percentile` | 0.0 | 100.0 | 백분위 (상위 %) |
| `t_score` | 20.0 | 80.0 | T-점수 (평균 50, 표준편차 10) |

---

## Response by Role

### Data Visibility Matrix

| Field | Teacher | Tutor | Parent | Student |
|-------|---------|-------|--------|---------|
| `theta` | ✅ | ✅ | ❌ | ✅ |
| `standard_error` | ✅ | ✅ | ❌ | ✅ |
| `score` | ✅ | ✅ | ✅ | ✅ |
| `grade_numeric` | ✅ | ✅ | ✅ | ✅ |
| `grade_letter` | ✅ | ✅ | ✅ | ✅ |
| `percentile` | ✅ | ✅ | ✅ | ✅ |
| `t_score` | ✅ | ✅ | ❌ | ✅ |
| `attempts` (문항별) | ✅ | ✅ | ❌ | ✅ |

**Notes:**
- 학부모는 기술적 세부사항(`theta`, `standard_error`, `t_score`) 제외
- 학부모는 문항별 응답 기록(`attempts`) 제외
- 모든 역할은 `score`, `grade`, `percentile` 확인 가능

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid student_id parameter"
}
```

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

### 500 Internal Server Error

```json
{
  "detail": "Internal server error. Please try again later."
}
```

---

## API Comparison

### Teacher vs Tutor vs Parent

| Aspect | Teacher | Tutor | Parent |
|--------|---------|-------|--------|
| **반 단위 조회** | ✅ 자신의 반 | ✅ 자신의 반 | ❌ |
| **학생 히스토리** | ✅ 자신의 학생 | ✅ 자신의 학생 | ✅ 자신의 자녀 |
| **전체 학생 요약** | ❌ | ✅ (전용 API) | ❌ |
| **기술 정보 (θ/SE)** | ✅ | ✅ | ❌ |
| **문항별 응답** | ✅ | ✅ | ❌ |
| **통계 정보** | ✅ 상세 | ✅ 상세 | ✅ 간소화 |

---

## Usage Examples

### JavaScript/TypeScript

```typescript
// Teacher: Get class exam summary
const getClassExams = async (classId: number) => {
  const response = await fetch(
    `/api/dashboard/teacher/classes/${classId}/exams?limit=50`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return response.json();
};

// Tutor: Get all students
const getTutorStudents = async () => {
  const response = await fetch(
    '/api/dashboard/tutor/students/exams',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return response.json();
};

// Parent: Get child exams
const getChildExams = async (studentId: number) => {
  const response = await fetch(
    `/api/dashboard/parent/children/${studentId}/exams`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return response.json();
};
```

### Python

```python
import requests

# Teacher: Get student exam history
def get_student_exams(student_id: int, token: str):
    response = requests.get(
        f"/api/dashboard/teacher/students/{student_id}/exams",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

# Tutor: Get all students
def get_tutor_students(token: str):
    response = requests.get(
        "/api/dashboard/tutor/students/exams",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()
```

### cURL

```bash
# Teacher: Class exams
curl -X GET "http://localhost:8000/api/dashboard/teacher/classes/1/exams" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Tutor: All students
curl -X GET "http://localhost:8000/api/dashboard/tutor/students/exams" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Parent: Child exams
curl -X GET "http://localhost:8000/api/dashboard/parent/children/10/exams" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Common: Exam detail
curl -X GET "http://localhost:8000/api/dashboard/exams/101" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Related Documentation

- [Dashboard API Documentation](./DASHBOARD_API.md)
- [Dashboard Routes Structure](./DASHBOARD_ROUTES.md)
- [Score Conversion Utilities](./SCORE_UTILS.md)

---

**Last Updated:** 2024-11-20
**Version:** 1.0.0
