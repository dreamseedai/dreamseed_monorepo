# Platform Database & API Integration Guide

**작성일**: 2025-11-19  
**버전**: 1.0  
**상태**: 구현 완료 (DB 미적용)

---

## 개요

DreamSeed 플랫폼의 Teacher/Parent/Tutor 대시보드를 위한 데이터베이스 스키마, ORM 모델, 서비스 레이어, API 통합을 완료했습니다.

### 구현 범위

1. ✅ **DB 스키마 설계** - 5개 테이블 (students, classes, student_classes, tutor_sessions, student_ability_history)
2. ✅ **SQLAlchemy ORM 모델** - 6개 모델 파일
3. ✅ **서비스 레이어** - CRUD 로직 캡슐화
4. ✅ **API 라우터 통합** - Mock 데이터 → 실제 DB 쿼리
5. ✅ **Redis 캐싱 + ETag** - 인프라 구현 (적용 준비 완료)
6. ✅ **Ability History API** - 차트 데이터 엔드포인트

---

## 파일 구조

```
backend/
├── alembic/
│   └── versions/
│       └── 001_create_platform_tables.py  # ✨ NEW: Migration 스크립트
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                        # ✨ NEW
│   │   ├── student.py                     # ✨ NEW
│   │   ├── tutor.py                       # ✨ NEW
│   │   └── ability_history.py             # ✨ NEW
│   ├── services/
│   │   ├── students.py                    # ✨ NEW
│   │   └── tutors.py                      # ✨ NEW
│   ├── api/
│   │   ├── teachers.py                    # ✅ UPDATED (DB 통합)
│   │   ├── parents.py                     # ✅ UPDATED (DB 통합)
│   │   └── tutors.py                      # ✅ UPDATED (DB 통합)
│   ├── core/
│   │   ├── database.py                    # ✅ UPDATED (Base 추가)
│   │   ├── security.py                    # ✨ NEW
│   │   └── cache.py                       # ✨ NEW (Redis + ETag)
│   └── schemas/
│       ├── common.py                      # ✅ EXISTS
│       ├── students.py                    # ✅ EXISTS
│       └── tutors.py                      # ✅ EXISTS
```

---

## 1. Database Schema

### 1.1 Core Tables

#### `students` - 학생 정보
```sql
CREATE TABLE students (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    external_id     TEXT,                       -- 학교 학번 등
    name            TEXT NOT NULL,
    grade           TEXT,                       -- e.g., "G10", "중3"
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Indexes**:
- `ix_students_id` (PRIMARY)
- `ix_students_user_id`
- `ix_students_name`
- `ix_students_external_id`

---

#### `classes` - 수업/반 정보
```sql
CREATE TABLE classes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,              -- e.g., "수학 1반"
    subject         TEXT,                       -- e.g., "Math"
    grade           TEXT,                       -- e.g., "Grade 10"
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Indexes**:
- `ix_classes_id` (PRIMARY)
- `ix_classes_teacher_id`

---

#### `student_classes` - Many-to-many 관계
```sql
CREATE TABLE student_classes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id        UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (student_id, class_id)
);
```

**Indexes**:
- `ix_student_classes_student_id`
- `ix_student_classes_class_id`

---

#### `tutor_sessions` - 과외 세션
```sql
CREATE TABLE tutor_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutor_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id          UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    date                DATE NOT NULL,
    subject             TEXT,
    topic               TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'Upcoming',  -- 'Upcoming' | 'Completed'
    duration_minutes    INT,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Indexes**:
- `ix_tutor_sessions_tutor_id`
- `ix_tutor_sessions_student_id`
- `ix_tutor_sessions_date`
- `ix_tutor_sessions_status`

---

#### `tutor_session_tasks` - 세션 내 작업 항목
```sql
CREATE TABLE tutor_session_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES tutor_sessions(id) ON DELETE CASCADE,
    label           TEXT NOT NULL,
    done            BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order      INT DEFAULT 0
);
```

---

#### `student_ability_history` - IRT theta 이력
```sql
CREATE TABLE student_ability_history (
    id              SERIAL PRIMARY KEY,
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    as_of_date      DATE NOT NULL,
    theta           DOUBLE PRECISION NOT NULL,
    source          TEXT,                 -- e.g., "IRT_3PL", "estimation_job_2025Q1"
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (student_id, as_of_date)
);
```

**Indexes**:
- `idx_student_ability_history_student_date` (student_id, as_of_date DESC)

---

## 2. ORM Models

### 2.1 Student Models (`app/models/student.py`)

```python
class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    grade = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    classes = relationship("StudentClass", back_populates="student")
    tutor_sessions = relationship("TutorSession", back_populates="student")
    ability_history = relationship("StudentAbilityHistory", back_populates="student")


class Class(Base):
    __tablename__ = "classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    subject = Column(Text, nullable=True)
    grade = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    students = relationship("StudentClass", back_populates="clazz")


class StudentClass(Base):
    __tablename__ = "student_classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    student = relationship("Student", back_populates="classes")
    clazz = relationship("Class", back_populates="students")
```

---

## 3. Service Layer

### 3.1 Student Services (`app/services/students.py`)

**Functions**:
- `list_students_for_teacher()` - 학생 목록 (필터링, 페이지네이션)
- `get_student_detail_for_teacher()` - 학생 상세 + ability_trend
- `get_child_detail_for_parent()` - 자녀 상세 (parent용)
- `get_student_ability_history()` - 차트 데이터

**예시**:
```python
def list_students_for_teacher(
    db: Session,
    teacher_id: UUID,
    q: Optional[str] = None,
    class_id: Optional[UUID] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[StudentSummary], int]:
    """
    Teacher의 학생 목록 조회 (필터링 + 페이지네이션)
    """
    stmt = (
        select(Student, Class.id, Class.name)
        .join(StudentClass, StudentClass.student_id == Student.id)
        .join(Class, Class.id == StudentClass.class_id)
        .where(Class.teacher_id == teacher_id)
    )
    
    if q:
        stmt = stmt.where(Student.name.ilike(f"%{q}%"))
    if class_id:
        stmt = stmt.where(Class.id == class_id)
    
    # ... pagination, ability calculation, status filtering
    
    return summaries, total
```

---

## 4. API Router Updates

### 4.1 Teachers API (`app/api/teachers.py`)

**엔드포인트**:
- ✅ `GET /api/teachers/{teacher_id}/students` - 학생 목록
- ✅ `GET /api/teachers/{teacher_id}/students/{student_id}` - 학생 상세
- ✨ `GET /api/teachers/{teacher_id}/students/{student_id}/ability-history` - 차트 데이터

**변경사항**:
- Mock 데이터 제거
- `svc_list_students()`, `svc_get_student_detail()` 서비스 호출
- UUID 검증 추가
- 404 처리

---

### 4.2 Parents API (`app/api/parents.py`)

**엔드포인트**:
- ✅ `GET /api/parents/{parent_id}/children/{child_id}` - 자녀 상세

**변경사항**:
- `svc_get_child_detail()` 서비스 호출
- TODO: parent-child 관계 검증 로직 필요

---

### 4.3 Tutors API (`app/api/tutors.py`)

**엔드포인트**:
- ✅ `GET /api/tutors/{tutor_id}/sessions` - 세션 목록
- ✅ `GET /api/tutors/{tutor_id}/sessions/{session_id}` - 세션 상세

**변경사항**:
- `svc_list_sessions()`, `svc_get_session_detail()` 서비스 호출
- Tasks 자동 로드

---

## 5. Redis Caching + ETag

### 5.1 Cache Infrastructure (`app/core/cache.py`)

**Features**:
- `RedisCache` 클래스 - get/set/delete/invalidate_pattern
- `compute_etag()` - MD5 해시 생성
- `with_cache_and_etag()` - 데코레이터 (구현 준비 완료)

**사용 예시**:
```python
from app.core.cache import RedisCache, compute_etag

cache = RedisCache("redis://localhost:6379/0")

# Set cache with TTL
cache.set("student_detail:teacher1:student1", data_dict, ttl=300)

# Get cache
cached = cache.get("student_detail:teacher1:student1")

# Invalidate pattern
cache.invalidate_pattern("student_detail:teacher1:*")
```

### 5.2 ETag 처리 패턴

```python
@router.get("/{teacher_id}/students/{student_id}")
async def get_student_detail(
    request: Request,
    response: Response,
    ...
):
    cache_key = f"student_detail:{teacher_id}:{student_id}"
    cached = redis.get(cache_key)
    
    if cached:
        etag = compute_etag(cached)
        if request.headers.get("if-none-match") == etag:
            response.status_code = 304
            return None
        response.headers["ETag"] = etag
        return cached
    
    # DB query
    detail = svc_get_student_detail(...)
    etag = compute_etag(detail)
    redis.setex(cache_key, 60, json.dumps(detail))
    response.headers["ETag"] = etag
    return detail
```

---

## 6. Migration & Deployment

### 6.1 Apply Migration

```bash
cd backend

# Review migration
alembic history

# Apply migration
alembic upgrade head

# Verify tables
psql $DATABASE_URL -c "\\dt"
```

**Expected Tables**:
- students
- classes
- student_classes
- tutor_sessions
- tutor_session_tasks
- student_ability_history

---

### 6.2 Seed Data (Optional)

```python
# backend/scripts/seed_data.py
from app.models.student import Student, Class, StudentClass
from app.models.ability_history import StudentAbilityHistory
from app.core.database import SessionLocal

db = SessionLocal()

# Create test teacher user (if not exists)
teacher_id = "uuid-of-teacher-user"

# Create class
math_class = Class(
    id="uuid-class-1",
    teacher_id=teacher_id,
    name="수학 1반",
    subject="Math",
    grade="Grade 10",
)
db.add(math_class)

# Create student
student = Student(
    id="uuid-student-1",
    user_id="uuid-of-student-user",
    name="홍길동",
    grade="G10",
)
db.add(student)

# Link student to class
link = StudentClass(
    student_id=student.id,
    class_id=math_class.id,
)
db.add(link)

# Add ability history
history = StudentAbilityHistory(
    student_id=student.id,
    as_of_date=date(2025, 11, 1),
    theta=0.12,
    source="seed_data",
)
db.add(history)

db.commit()
```

---

## 7. Testing Guide

### 7.1 API Testing (Swagger UI)

```bash
# Start backend
cd backend
uvicorn main:app --reload --port 8000

# Open Swagger UI
# http://localhost:8000/docs
```

**Test Endpoints**:
1. `GET /api/teachers/me/students` - Should return empty list (no data yet)
2. `GET /api/teachers/me/students/{uuid}` - Should return 404 or 400
3. After seeding data, verify pagination, filters work

---

### 7.2 Cache Testing (Redis)

```bash
# Start Redis
redis-server

# Monitor cache keys
redis-cli MONITOR

# In another terminal, make API requests
curl http://localhost:8000/api/teachers/me/students/uuid-student-1

# Check Redis keys
redis-cli KEYS "*"
# Output: student_detail:uuid-teacher:uuid-student

# Check ETag header
curl -I http://localhost:8000/api/teachers/me/students/uuid-student-1
# Should see: ETag: "abc123...", X-Cache: MISS

# Repeat request
curl -I http://localhost:8000/api/teachers/me/students/uuid-student-1
# Should see: X-Cache: HIT
```

---

### 7.3 Database Query Performance

```sql
-- Check query plan for student list
EXPLAIN ANALYZE
SELECT s.*, c.id, c.name
FROM students s
JOIN student_classes sc ON sc.student_id = s.id
JOIN classes c ON c.id = sc.class_id
WHERE c.teacher_id = 'uuid-teacher'
LIMIT 20;

-- Check ability history index usage
EXPLAIN ANALYZE
SELECT * FROM student_ability_history
WHERE student_id = 'uuid-student'
ORDER BY as_of_date DESC
LIMIT 10;
```

---

## 8. TODO & Next Steps

### 8.1 Immediate (Phase 2)

- [ ] **Apply Alembic migration** - `alembic upgrade head`
- [ ] **Seed test data** - Create script or manual INSERT
- [ ] **Test all endpoints** - Verify pagination, filters, RBAC
- [ ] **Implement JWT authentication** - `app/core/security.py`
- [ ] **Parent-child relationship table** - Add `parent_children` table
- [ ] **Test results table** - For `recent_tests` field
- [ ] **Activity logging table** - For `recent_activity` field

### 8.2 Optimization (Phase 3)

- [ ] **Apply Redis caching** - Add to hot endpoints
- [ ] **ETag response handling** - Frontend integration
- [ ] **Database connection pooling** - Tune `pool_size`, `max_overflow`
- [ ] **Add database indexes** - Based on slow query log
- [ ] **Ability calculation optimization** - Materialized view or cron job
- [ ] **API rate limiting** - Prevent abuse

### 8.3 Features (Phase 4)

- [ ] **Real-time updates** - WebSocket for live data
- [ ] **Bulk operations** - Import students from CSV
- [ ] **Advanced filtering** - Date ranges, multiple statuses
- [ ] **Export functionality** - PDF reports, Excel exports
- [ ] **Analytics dashboard** - Aggregated metrics

---

## 9. Reference

### 9.1 Documentation

- `docs/DASHBOARD_IMPLEMENTATION.md` - Frontend 대시보드 가이드
- `docs/implementation/TEACHER_PARENT_TUTOR_API_SPEC.md` - API 스펙
- `backend/alembic/versions/001_create_platform_tables.py` - Migration 스크립트

### 9.2 Dependencies

**Required**:
- `sqlalchemy>=2.0.0` - ORM
- `alembic>=1.12.0` - Migrations
- `psycopg>=3.0.0` or `psycopg2-binary` - PostgreSQL driver
- `redis>=5.0.0` - Caching (optional)

**Install**:
```bash
cd backend
pip install sqlalchemy alembic psycopg redis
```

---

## 10. Change Log

| Date | Description | Author |
|------|-------------|--------|
| 2025-11-19 | 초안 작성: DB 스키마, ORM, 서비스, API 통합, Redis 캐싱 | GitHub Copilot |

---

**문서 작성**: GitHub Copilot  
**최종 업데이트**: 2025-11-19  
**버전**: 1.0  
**상태**: ✅ 구현 완료 (DB 미적용)
