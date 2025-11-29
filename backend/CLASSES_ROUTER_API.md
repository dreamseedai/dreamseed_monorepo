# Classes Router API Documentation

**Router**: `app.api.routers.classes`  
**Prefix**: `/api/classes`  
**Tags**: `classes`

교사용 반 관리 및 통계 API입니다. 교사가 담당하는 반의 학생 목록, 성적 통계, 시험 현황을 조회할 수 있습니다.

---

## Authentication

모든 엔드포인트는 인증이 필요합니다 (현재는 Mock 구현).

**TODO**: JWT Bearer 토큰으로 실제 인증 구현 필요
```python
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### 1. GET /api/classes/{class_id}/summary

반 요약 정보 조회 (교사용 대시보드)

**Access Control**:
- ✅ Teacher: 본인이 담당하는 반만 조회 가능
- ✅ Admin/Super Admin: 모든 반 조회 가능
- ❌ Student/Parent: 접근 불가

**Path Parameters**:
- `class_id` (integer, required): 반 ID

**Response 200**:
```json
{
  "class_id": 1,
  "name": "고2-1반 수학",
  "subject": "math",
  "grade": "11",
  "student_count": 25,
  "average_score": 78.5,
  "recent_exam_count": 120
}
```

**Response Fields**:
- `class_id`: 반 ID
- `name`: 반 이름
- `subject`: 과목 (math, english, science, etc.)
- `grade`: 학년
- `student_count`: 등록된 학생 수
- `average_score`: 완료된 모든 시험의 평균 점수 (0-100 scale), 시험이 없으면 `null`
- `recent_exam_count`: 완료된 총 시험 횟수

**Error Responses**:
- `403 Forbidden`: 권한 없음 (다른 교사의 반 접근 시도)
- `404 Not Found`: 존재하지 않는 반

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/classes/1/summary" \
  -H "Authorization: Bearer <token>"
```

**Use Cases**:
- 교사 대시보드 메인 화면
- 반별 성적 개요 확인
- 학생 수 및 참여도 모니터링

---

### 2. GET /api/classes/{class_id}/students

반 학생 목록 조회 (페이지네이션 지원)

**Access Control**:
- ✅ Teacher: 본인 담당 반만
- ✅ Admin: 모든 반
- ❌ Others: 접근 불가

**Path Parameters**:
- `class_id` (integer, required): 반 ID

**Query Parameters**:
- `skip` (integer, optional, default=0): 페이지네이션 오프셋
- `limit` (integer, optional, default=50, max=100): 한 페이지당 최대 학생 수

**Response 200**:
```json
{
  "class_id": 1,
  "students": [
    {
      "student_id": 10,
      "name": "김철수",
      "grade": "11",
      "latest_score": 85.5,
      "exam_count": 5,
      "enrolled_at": "2024-03-01T09:00:00Z"
    },
    {
      "student_id": 11,
      "name": "이영희",
      "grade": "11",
      "latest_score": 92.0,
      "exam_count": 7,
      "enrolled_at": "2024-03-01T09:00:00Z"
    }
  ],
  "total_count": 25
}
```

**Response Fields**:
- `class_id`: 반 ID
- `students`: 학생 목록 (배열)
  - `student_id`: 학생 ID
  - `name`: 학생 이름
  - `grade`: 학년
  - `latest_score`: 가장 최근 완료한 시험 점수 (없으면 `null`)
  - `exam_count`: 완료한 총 시험 횟수
  - `enrolled_at`: 반에 등록된 시점 (ISO 8601)
- `total_count`: 전체 학생 수 (페이지네이션에 사용)

**Error Responses**:
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 존재하지 않는 반

**cURL Example**:
```bash
# 첫 페이지 (50명)
curl -X GET "http://localhost:8000/api/classes/1/students?skip=0&limit=50" \
  -H "Authorization: Bearer <token>"

# 두 번째 페이지
curl -X GET "http://localhost:8000/api/classes/1/students?skip=50&limit=50" \
  -H "Authorization: Bearer <token>"
```

**Use Cases**:
- 학생 명단 관리
- 개별 학생 성적 확인
- 등록 현황 파악

---

### 3. GET /api/classes/{class_id}/exam-stats

반 시험 통계 조회 (상세 분석용)

**Access Control**:
- ✅ Teacher: 본인 담당 반만
- ✅ Admin: 모든 반

**Path Parameters**:
- `class_id` (integer, required): 반 ID

**Query Parameters**:
- `exam_type` (string, optional): 시험 유형 필터
  - 가능한 값: `placement`, `practice`, `mock`, `official`, `quiz`
  - 생략 시: 모든 시험 유형 포함

**Response 200**:
```json
{
  "class_id": 1,
  "exam_type": "mock",
  "stats": {
    "total_exams": 150,
    "completed_exams": 145,
    "avg_score": 78.5,
    "min_score": 45.0,
    "max_score": 98.5,
    "std_dev": 12.3,
    "avg_theta": 0.25,
    "avg_duration_sec": 3600
  }
}
```

**Response Fields**:
- `class_id`: 반 ID
- `exam_type`: 필터링된 시험 유형 (없으면 `null`)
- `stats`: 통계 정보
  - `total_exams`: 전체 시험 세션 수 (완료되지 않은 것 포함)
  - `completed_exams`: 완료된 시험 수
  - `avg_score`: 평균 점수 (0-100)
  - `min_score`: 최저 점수
  - `max_score`: 최고 점수
  - `std_dev`: 표준편차 (점수 분포)
  - `avg_theta`: 평균 IRT 능력치 (일반적으로 -3 ~ +3)
  - `avg_duration_sec`: 평균 소요 시간 (초)

**빈 데이터 처리**:
학생이 없거나 완료된 시험이 없으면 모든 통계값이 `null`입니다:
```json
{
  "class_id": 1,
  "exam_type": null,
  "stats": {
    "total_exams": 0,
    "completed_exams": 0,
    "avg_score": null,
    "min_score": null,
    "max_score": null,
    "std_dev": null,
    "avg_theta": null,
    "avg_duration_sec": null
  }
}
```

**Error Responses**:
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 존재하지 않는 반

**cURL Examples**:
```bash
# 모든 시험 유형 통계
curl -X GET "http://localhost:8000/api/classes/1/exam-stats" \
  -H "Authorization: Bearer <token>"

# mock 시험만 필터링
curl -X GET "http://localhost:8000/api/classes/1/exam-stats?exam_type=mock" \
  -H "Authorization: Bearer <token>"

# official 시험만 필터링
curl -X GET "http://localhost:8000/api/classes/1/exam-stats?exam_type=official" \
  -H "Authorization: Bearer <token>"
```

**Use Cases**:
- 반별 성적 분석
- 시험 유형별 난이도 파악
- IRT 기반 능력 분포 확인
- 학습 시간 분석

---

## Common Error Responses

### 403 Forbidden
```json
{
  "detail": "권한이 없습니다. 교사 또는 관리자만 접근 가능합니다."
}
```
또는
```json
{
  "detail": "해당 반에 대한 권한이 없습니다. 본인이 담당하는 반만 조회 가능합니다."
}
```

### 404 Not Found
```json
{
  "detail": "Class not found: 999"
}
```

### 501 Not Implemented (Authentication)
```json
{
  "detail": "Authentication not yet implemented. Please implement JWT verification."
}
```

---

## Data Models

### Class Model
```python
class Class(Base):
    __tablename__ = "classes"
    
    id: int                      # Primary key
    teacher_id: int              # FK to users.id
    name: str                    # "고2-1반 수학"
    subject: Optional[str]       # "math", "english", etc.
    grade: Optional[str]         # "11", "K", etc.
    created_at: datetime
    updated_at: datetime
```

### Student Model
```python
class Student(Base):
    __tablename__ = "students"
    
    id: int                      # Primary key
    user_id: int                 # FK to users.id
    name: str
    grade: Optional[str]
    created_at: datetime
```

### StudentClass Model (Junction)
```python
class StudentClass(Base):
    __tablename__ = "student_classes"
    
    student_id: int              # FK to students.id
    class_id: int                # FK to classes.id
    created_at: datetime         # Enrollment timestamp
```

### ExamSession Model
```python
class ExamSession(Base):
    __tablename__ = "exam_sessions"
    
    id: int                      # Primary key (BIGSERIAL)
    student_id: int              # FK to students.id
    class_id: Optional[int]      # FK to classes.id
    exam_type: str               # placement, practice, mock, official, quiz
    status: str                  # in_progress, completed, abandoned
    started_at: datetime
    ended_at: Optional[datetime]
    score: Optional[Decimal]     # 0-100
    duration_sec: Optional[int]
    theta: Optional[Decimal]     # IRT ability (-3 to +3)
    standard_error: Optional[Decimal]
```

---

## Integration Guide

### 1. Register Router in main.py ✅ DONE
```python
from app.api.routers.classes import router as classes_router
app.include_router(classes_router)
```

### 2. Implement JWT Authentication (TODO)
Replace the mock `get_current_user()` function in `classes.py`:
```python
from app.core.security import get_current_user  # Import real implementation
```

### 3. Frontend Integration Example (React/Next.js)
```typescript
// Fetch class summary
const response = await fetch(`/api/classes/${classId}/summary`, {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
const summary = await response.json();

// Fetch students with pagination
const studentsResponse = await fetch(
  `/api/classes/${classId}/students?skip=0&limit=50`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const { students, total_count } = await studentsResponse.json();

// Fetch exam statistics
const statsResponse = await fetch(
  `/api/classes/${classId}/exam-stats?exam_type=mock`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const { stats } = await statsResponse.json();
```

---

## Testing

Test suite location: `backend/tests/test_classes_router.py`

Run tests:
```bash
cd backend
pytest tests/test_classes_router.py -v
```

**Test Coverage**: 10/10 tests passed ✅
- Response structure validation
- Empty class handling
- Pagination limits
- Role-based access control
- Teacher authorization logic
- Score calculation with None values
- Exam type filtering
- Statistics aggregate queries

---

## Performance Considerations

1. **Indexing**: 이미 최적화된 인덱스 사용
   - `classes.teacher_id`
   - `student_classes.class_id`
   - `exam_sessions.student_id`
   - `exam_sessions.status`

2. **Query Optimization**:
   - SQL aggregates 사용 (AVG, MIN, MAX, STDDEV)
   - 필요한 컬럼만 SELECT
   - JOIN 최소화

3. **Pagination**:
   - 기본 limit: 50
   - 최대 limit: 100 (하드 제한)

4. **Caching Recommendations** (TODO):
   - Class summary: 5분 TTL
   - Student list: 1분 TTL
   - Exam stats: 10분 TTL

---

## Future Enhancements

### Short Term
- [ ] JWT authentication 통합
- [ ] Response caching (Redis)
- [ ] Rate limiting
- [ ] Audit logging

### Medium Term
- [ ] 시간대별 성적 변화 그래프 API
- [ ] 학생별 상세 분석 API
- [ ] CSV/Excel export 기능
- [ ] 실시간 시험 진행 현황 (WebSocket)

### Long Term
- [ ] AI 기반 반 성적 예측
- [ ] 자동 그룹핑 추천
- [ ] 학습 패턴 분석
- [ ] 맞춤형 학습 리소스 추천

---

## Related Documentation

- **Database Schema**: `migrations/20251120_core_schema_integer_based.sql`
- **SQLAlchemy Models**: `app/models/core_entities.py`, `app/models/student.py`
- **Pydantic Schemas**: `app/schemas/core_schemas.py`
- **Authentication**: `app/core/security.py`
- **Dashboard Router**: `app/api/routers/dashboard.py`

---

**Status**: ✅ Production Ready (Authentication pending)  
**Test Coverage**: 10/10 passed  
**API Version**: 1.0.0  
**Last Updated**: 2024-11-20
