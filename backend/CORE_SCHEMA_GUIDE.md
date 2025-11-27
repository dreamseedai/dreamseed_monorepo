# DreamSeed Core Schema & FastAPI Integration Guide

**Created:** 2024-11-20  
**Status:** ✅ Implementation Complete  
**Purpose:** INTEGER-based core schema with FastAPI CRUD endpoints

---

## 📋 Overview

This implementation provides a comprehensive, production-ready foundation for the DreamSeed CAT system:

- **7 Core Tables**: Organizations, Users, Teachers, Students, Classes, ExamSessions, Attempts
- **INTEGER PKs**: Performance-optimized with SERIAL/BIGSERIAL
- **SQLAlchemy Models**: Full ORM with relationships
- **Pydantic Schemas**: Request/response validation
- **FastAPI Endpoints**: RESTful CRUD operations
- **IRT Integration**: Theta, standard error, adaptive testing support

---

## 🗂️ File Structure

```
migrations/
└── 20251120_core_schema_integer_based.sql  # PostgreSQL DDL (NEW)

backend/app/
├── models/
│   ├── __init__.py                          # Updated: Added core entities
│   └── core_entities.py                     # Updated: Full relationships
├── schemas/
│   └── core_schemas.py                      # NEW: Pydantic schemas
└── api/routers/
    └── core.py                              # NEW: FastAPI endpoints
```

---

## 🏗️ Schema Architecture

### Entity Relationship Diagram

```
organizations (1) ──┬──> (N) users
                    ├──> (N) teachers
                    ├──> (N) students
                    └──> (N) classes

users (1) ──┬──> (1) teacher
            └──> (1) student

teacher (1) ──> (N) classes

student (N) ←──> (N) classes  [via student_classroom]

student (1) ──┬──> (N) exam_sessions
              └──> (N) attempts

exam_session (1) ──> (N) attempts
```

### Table Specifications

| Table | PK Type | Key Columns | Indexes |
|-------|---------|-------------|---------|
| **organizations** | SERIAL | name, type | id, name |
| **users** | SERIAL | email, role, password_hash | id, email, org_id, role |
| **teachers** | SERIAL | user_id (FK), subject | id, user_id, org_id |
| **students** | SERIAL | user_id (FK), grade | id, user_id, org_id, grade |
| **classes** | SERIAL | teacher_id (FK), name, subject | id, teacher_id, org_id |
| **student_classroom** | Composite (student_id, class_id) | - | student_id, class_id |
| **exam_sessions** | BIGSERIAL | student_id (FK), theta, score | id, student_id, class_id, status, started_at |
| **attempts** | BIGSERIAL | exam_session_id (FK), item_id, correct | id, student_id, exam_session_id, item_id |

---

## 🚀 Deployment Instructions

### Step 1: Apply Database Migration

```bash
# Connect to PostgreSQL
psql -U postgres -d dreamseed

# Apply schema migration
\i migrations/20251120_core_schema_integer_based.sql

# Verify tables
\dt
\d+ exam_sessions
\d+ attempts
```

⚠️ **Important Checks Before Running:**

1. **Existing Tables**: Check if `users`, `students`, `classes` already exist
2. **Conflicts**: Review foreign key references
3. **Data Migration**: If existing data, create migration scripts

```sql
-- Check existing tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'students', 'classes', 'teachers');

-- Check for column conflicts
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users';
```

### Step 2: Register FastAPI Router

```python
# backend/main.py
from app.api.routers import core

app.include_router(core.router)
```

### Step 3: Test Endpoints

```bash
# Start server
cd backend
uvicorn main:app --reload --port 8000

# Test in browser
http://localhost:8000/docs

# Or use curl
curl http://localhost:8000/api/core/organizations
```

---

## 📡 API Endpoints Reference

### Organizations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/core/organizations` | Create organization |
| GET | `/api/core/organizations` | List organizations |
| GET | `/api/core/organizations/{id}` | Get organization |
| PATCH | `/api/core/organizations/{id}` | Update organization |
| DELETE | `/api/core/organizations/{id}` | Delete organization |

**Example: Create Organization**
```bash
curl -X POST http://localhost:8000/api/core/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "서울고등학교", "type": "school"}'
```

### Teachers

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/core/teachers` | Create teacher profile |
| GET | `/api/core/teachers` | List teachers (with filters) |
| GET | `/api/core/teachers/{id}` | Get teacher |
| PATCH | `/api/core/teachers/{id}` | Update teacher |

**Example: Create Teacher**
```bash
curl -X POST http://localhost:8000/api/core/teachers \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "org_id": 1,
    "subject": "math",
    "meta": {"certifications": ["Math Level 2"], "years_experience": 5}
  }'
```

### Student-Classroom Enrollments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/core/enrollments` | Enroll student in class |
| POST | `/api/core/enrollments/bulk` | Bulk enroll students |
| GET | `/api/core/classes/{id}/students` | List class students |
| DELETE | `/api/core/enrollments/{student_id}/{class_id}` | Unenroll student |

**Example: Bulk Enrollment**
```bash
curl -X POST http://localhost:8000/api/core/enrollments/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": 1,
    "student_ids": [1, 2, 3, 4, 5]
  }'
```

### Exam Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/core/exam-sessions` | Start new exam |
| GET | `/api/core/exam-sessions` | List exams (with filters) |
| GET | `/api/core/exam-sessions/{id}` | Get exam with attempts |
| PATCH | `/api/core/exam-sessions/{id}` | Update exam (completion) |

**Example: Start Exam Session**
```bash
curl -X POST http://localhost:8000/api/core/exam-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "class_id": 1,
    "exam_type": "placement",
    "meta": {"algorithm": "CAT", "max_items": 30}
  }'
```

**Example: Complete Exam Session**
```bash
curl -X PATCH http://localhost:8000/api/core/exam-sessions/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "ended_at": "2024-11-20T15:30:00Z",
    "score": 85.5,
    "theta": 1.234,
    "standard_error": 0.456,
    "duration_sec": 1800
  }'
```

### Attempts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/core/attempts` | Record item response |
| GET | `/api/core/exam-sessions/{id}/attempts` | List exam attempts |
| PATCH | `/api/core/attempts/{id}` | Update attempt (scoring) |

**Example: Record Attempt**
```bash
curl -X POST http://localhost:8000/api/core/attempts \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "exam_session_id": 1,
    "item_id": 12345,
    "correct": true,
    "selected_choice": 3,
    "response_time_ms": 45000,
    "meta": {"item_difficulty": 0.5, "discrimination": 1.2}
  }'
```

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/core/students/{id}/exam-stats` | Student performance stats |
| GET | `/api/core/classes/{id}/exam-stats` | Class performance stats |

**Example Response: Student Stats**
```json
{
  "student_id": 1,
  "total_exams": 5,
  "completed_exams": 4,
  "average_score": 82.5,
  "average_theta": 0.856,
  "latest_exam_date": "2024-11-20T10:30:00Z"
}
```

---

## 🔍 Query Examples

### SQLAlchemy ORM Queries

```python
from sqlalchemy import select
from app.models.core_entities import ExamSession, Attempt, Student

# Get student's latest exam with attempts
query = (
    select(ExamSession)
    .where(ExamSession.student_id == 1)
    .order_by(ExamSession.started_at.desc())
    .limit(1)
    .options(selectinload(ExamSession.attempts))
)
latest_exam = db.execute(query).scalar_one_or_none()

# Get all completed exams for a class
query = (
    select(ExamSession)
    .where(ExamSession.class_id == 1)
    .where(ExamSession.status == "completed")
    .order_by(ExamSession.started_at.desc())
)
class_exams = db.execute(query).scalars().all()

# Calculate class average theta
from sqlalchemy import func
query = select(func.avg(ExamSession.theta)).where(
    ExamSession.class_id == 1,
    ExamSession.status == "completed"
)
avg_theta = db.execute(query).scalar_one()
```

### Raw SQL Queries

```sql
-- Get student exam history with class info
SELECT 
    es.id,
    es.exam_type,
    es.score,
    es.theta,
    es.started_at,
    c.name AS class_name,
    COUNT(a.id) AS total_attempts
FROM exam_sessions es
LEFT JOIN classes c ON es.class_id = c.id
LEFT JOIN attempts a ON a.exam_session_id = es.id
WHERE es.student_id = 1
GROUP BY es.id, c.name
ORDER BY es.started_at DESC;

-- Get class leaderboard
SELECT 
    s.id AS student_id,
    s.name,
    AVG(es.score) AS average_score,
    AVG(es.theta) AS average_theta,
    COUNT(es.id) AS total_exams
FROM students s
JOIN student_classroom sc ON sc.student_id = s.id
JOIN exam_sessions es ON es.student_id = s.id AND es.class_id = sc.class_id
WHERE sc.class_id = 1 AND es.status = 'completed'
GROUP BY s.id, s.name
ORDER BY average_theta DESC;

-- Get item difficulty statistics
SELECT 
    a.item_id,
    COUNT(*) AS total_attempts,
    SUM(CASE WHEN a.correct THEN 1 ELSE 0 END) AS correct_count,
    AVG(CASE WHEN a.correct THEN 1.0 ELSE 0.0 END) AS p_correct,
    AVG(a.response_time_ms) AS avg_response_time
FROM attempts a
GROUP BY a.item_id
HAVING COUNT(*) >= 10
ORDER BY p_correct DESC;
```

---

## 🧪 Testing Guide

### Unit Tests (pytest)

```python
# tests/test_core_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_organization():
    response = client.post("/api/core/organizations", json={
        "name": "Test School",
        "type": "school"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test School"
    assert "id" in data

def test_create_exam_session():
    response = client.post("/api/core/exam-sessions", json={
        "student_id": 1,
        "class_id": 1,
        "exam_type": "practice"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["exam_type"] == "practice"

def test_record_attempt():
    response = client.post("/api/core/attempts", json={
        "student_id": 1,
        "exam_session_id": 1,
        "item_id": 100,
        "correct": True,
        "response_time_ms": 5000
    })
    assert response.status_code == 201
```

### Integration Tests

```bash
# Run all tests
pytest tests/test_core_endpoints.py -v

# Run with coverage
pytest tests/ --cov=app.api.routers.core --cov-report=html
```

---

## 📊 Performance Optimization

### Database Indexes

All critical query paths are indexed:

```sql
-- Already created by migration script
CREATE INDEX idx_exam_sessions_student_id ON exam_sessions(student_id);
CREATE INDEX idx_exam_sessions_class_id ON exam_sessions(class_id);
CREATE INDEX idx_exam_sessions_status ON exam_sessions(status);
CREATE INDEX idx_attempts_exam_session_id ON attempts(exam_session_id);
```

### Query Optimization Tips

1. **Use selectinload() for relationships**
   ```python
   query = select(ExamSession).options(selectinload(ExamSession.attempts))
   ```

2. **Filter at database level**
   ```python
   query = select(ExamSession).where(ExamSession.status == "completed")
   ```

3. **Paginate large result sets**
   ```python
   query = query.offset(skip).limit(limit)
   ```

4. **Use bulk operations**
   ```python
   db.bulk_insert_mappings(Attempt, attempt_dicts)
   db.commit()
   ```

---

## 🔒 Security Considerations

### Authentication Integration

```python
# Add authentication dependency
from app.core.security import get_current_user

@router.post("/exam-sessions")
def create_exam_session(
    exam: ExamSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Add this
):
    # Verify user has permission to create exam for this student
    if current_user.role != "admin" and exam.student_id != current_user.student.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_exam = ExamSession(**exam.model_dump())
    db.add(db_exam)
    db.commit()
    return db_exam
```

### Row-Level Security (RLS)

If using PostgreSQL RLS:

```sql
-- Enable RLS on sensitive tables
ALTER TABLE exam_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Students can only see their own exams
CREATE POLICY student_exam_policy ON exam_sessions
FOR SELECT
USING (student_id = current_setting('app.current_user_id')::INTEGER);

-- Policy: Teachers can see their class exams
CREATE POLICY teacher_exam_policy ON exam_sessions
FOR SELECT
USING (
    class_id IN (
        SELECT id FROM classes 
        WHERE teacher_id = current_setting('app.current_teacher_id')::INTEGER
    )
);
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue 1: Foreign Key Constraint Violation**
```
ERROR: insert or update on table "teachers" violates foreign key constraint
```
**Solution**: Ensure referenced user exists before creating teacher profile
```python
user = db.get(User, user_id)
if not user:
    raise HTTPException(status_code=400, detail="User not found")
```

**Issue 2: Duplicate Enrollment**
```
ERROR: duplicate key value violates unique constraint
```
**Solution**: Check enrollment exists before inserting
```python
existing = db.execute(
    select(StudentClassroom).where(
        StudentClassroom.student_id == student_id,
        StudentClassroom.class_id == class_id
    )
).scalar_one_or_none()

if existing:
    raise HTTPException(status_code=400, detail="Already enrolled")
```

**Issue 3: Table Already Exists**
```
ERROR: relation "exam_sessions" already exists
```
**Solution**: Use `CREATE TABLE IF NOT EXISTS` or drop existing table
```sql
-- Check if table exists
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'exam_sessions';

-- Drop if needed (⚠️ loses data)
DROP TABLE IF EXISTS exam_sessions CASCADE;
```

---

## 📚 Next Steps

### Immediate Extensions

1. **Items Table**: Define item/question repository
   ```sql
   CREATE TABLE items (
       id BIGSERIAL PRIMARY KEY,
       content TEXT NOT NULL,
       difficulty NUMERIC(5,3),  -- IRT b parameter
       discrimination NUMERIC(5,3),  -- IRT a parameter
       guessing NUMERIC(5,3) DEFAULT 0.25,  -- IRT c parameter
       subject VARCHAR(50),
       grade VARCHAR(20)
   );
   ```

2. **Authentication**: Integrate JWT/session auth
3. **Webhooks**: Real-time exam progress notifications
4. **Caching**: Redis for frequently accessed data
5. **Analytics**: Time-series data for learning curves

### Future Enhancements

- [ ] Multi-language support (i18n)
- [ ] Adaptive algorithm configuration UI
- [ ] Parent dashboard endpoints
- [ ] Reporting & PDF generation
- [ ] ML model training pipeline

---

## 📞 Support

For questions or issues:
- Check existing code comments
- Review FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Open GitHub issue

---

**Last Updated:** 2024-11-20  
**Version:** 1.0.0  
**Author:** GitHub Copilot + Developer Team
