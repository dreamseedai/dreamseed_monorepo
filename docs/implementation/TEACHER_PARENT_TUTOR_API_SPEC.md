# Teacher / Parent / Tutor API Specification

> **작성일**: 2025-11-19  
> **목적**: Teacher/Parent/Tutor 대시보드 MVP를 위한 백엔드 REST API 스펙  
> **버전**: 1.0  
> **상태**: 설계 완료, 구현 대기

---

## 📋 목차

1. [개요](#개요)
2. [설계 목표 & 범위](#설계-목표--범위)
3. [공통 데이터 모델 (Pydantic)](#공통-데이터-모델-pydantic)
4. [엔드포인트 스펙](#엔드포인트-스펙)
5. [RBAC 및 스코핑 규칙](#rbac-및-스코핑-규칙)
6. [구현 가이드](#구현-가이드)
7. [테스트 시나리오](#테스트-시나리오)

---

## 개요

### 배경

프론트엔드에서 이미 구현된 MVP 페이지들:
- `/teacher/students` - 학생 목록 (검색/필터)
- `/teacher/students/:id` - 학생 상세 (Ability Trend, Recent Tests)
- `/parent/children/:id` - 자녀 상세 (Strengths, Activity)
- `/tutor/sessions` - 세션 목록
- `/tutor/sessions/:id` - 세션 상세 (Notes, Tasks)

이를 뒷받침할 백엔드 REST API가 필요합니다.

### 핵심 원칙

1. **Role-based API 경로**: `/api/teachers/{teacher_id}/...`, `/api/parents/{parent_id}/...`
2. **RBAC 엄격 적용**: 자신의 데이터만 접근 (admin 제외)
3. **MVP 우선**: 복잡한 기능보다 핵심 CRUD에 집중
4. **프론트 호환**: 기존 mock 데이터 구조와 1:1 매칭

---

## 설계 목표 & 범위

### 필요한 엔드포인트 (MVP)

#### 1. Teacher API
- `GET /api/teachers/{teacher_id}/students` - 학생 목록 (필터/검색/페이지네이션)
- `GET /api/teachers/{teacher_id}/students/{student_id}` - 학생 상세

#### 2. Parent API
- `GET /api/parents/{parent_id}/children/{child_id}` - 자녀 상세

#### 3. Tutor API
- `GET /api/tutors/{tutor_id}/sessions` - 세션 목록
- `GET /api/tutors/{tutor_id}/sessions/{session_id}` - 세션 상세

### 제외 사항 (Phase 2)

- POST/PUT/DELETE (데이터 생성/수정은 나중)
- 실시간 업데이트 (WebSocket)
- 복잡한 분석/통계 (별도 analytics API)

---

## 공통 데이터 모델 (Pydantic)

### 파일 구조

```
backend/
├── app/
│   ├── schemas/
│   │   ├── common.py         # PageResponse, 공통 타입
│   │   ├── students.py       # StudentSummary, StudentDetail
│   │   └── tutors.py         # TutorSessionSummary, TutorSessionDetail
```

### 1. Common Schemas (`schemas/common.py`)

```python
from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PageResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 포맷"""
    total_count: int
    page: int
    page_size: int
    items: List[T]

    class Config:
        from_attributes = True
```

### 2. Student Schemas (`schemas/students.py`)

```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

StudentStatus = Literal["On Track", "At Risk", "Struggling"]

class StudentSummary(BaseModel):
    """학생 목록용 요약 데이터"""
    id: str
    name: str
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    current_ability_theta: Optional[float] = Field(None, description="IRT θ (ability)")
    recent_score: Optional[float] = Field(None, ge=0, le=100, description="최근 평균 점수 (%)")
    status: StudentStatus = "On Track"
    risk_flags: Optional[List[str]] = Field(default_factory=list, description="위험 신호 목록")

    class Config:
        from_attributes = True

class AbilityPoint(BaseModel):
    """Ability Trend 차트 포인트"""
    label: str = Field(..., example="4w ago")
    value: float = Field(..., description="θ 값")

class RecentTest(BaseModel):
    """최근 시험 기록"""
    date: str = Field(..., description="ISO8601 or YYYY-MM-DD")
    name: str = Field(..., example="미분·적분 퀴즈")
    score: float = Field(..., ge=0, le=100)

class StudentDetail(StudentSummary):
    """학생 상세 데이터"""
    ability_trend: List[AbilityPoint] = Field(default_factory=list)
    recent_tests: List[RecentTest] = Field(default_factory=list)
    # risk_flags는 StudentSummary에서 상속됨

class ChildDetail(StudentDetail):
    """학부모용 자녀 상세 (StudentDetail + α)"""
    study_time_month: Optional[str] = Field(None, example="12h / month")
    strengths: List[str] = Field(default_factory=list, example=["도형", "함수 응용"])
    areas_to_improve: List[str] = Field(default_factory=list, example=["확률", "통계"])
    recent_activity: List[dict] = Field(default_factory=list)
    # recent_activity 구조: [{"date": "2025-11-10", "description": "..."}]
```

### 3. Tutor Schemas (`schemas/tutors.py`)

```python
from typing import List, Literal
from pydantic import BaseModel, Field

SessionStatus = Literal["Completed", "Upcoming"]

class TutorSessionSummary(BaseModel):
    """세션 목록용 요약 데이터"""
    id: str
    date: str = Field(..., description="ISO8601 or YYYY-MM-DD")
    student_id: str
    student_name: str
    subject: str = Field(..., example="수학")
    topic: str = Field(..., example="미분·적분")
    status: SessionStatus

    class Config:
        from_attributes = True

class TutorSessionTask(BaseModel):
    """세션 내 할 일"""
    label: str = Field(..., example="교과서 예제 5개 풀이")
    done: bool

class TutorSessionDetail(TutorSessionSummary):
    """세션 상세 데이터"""
    duration_minutes: int = Field(..., example=90)
    notes: str = Field(..., description="세션 노트")
    tasks: List[TutorSessionTask] = Field(default_factory=list)
```

---

## 엔드포인트 스펙

### 1. Teacher API

#### 1.1. GET /api/teachers/{teacher_id}/students

**목적**: 선생님의 관할 학생 목록 조회 (검색/필터/페이지네이션)

**Request**:
```http
GET /api/teachers/{teacher_id}/students?q=홍길동&status=At%20Risk&page=1&page_size=20
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `q` | `string` | ❌ | - | 학생 이름 검색 |
| `class_id` | `string` | ❌ | - | 클래스 ID 필터 |
| `status` | `string` | ❌ | `all` | `"On Track"` / `"At Risk"` / `"Struggling"` / `"all"` |
| `page` | `int` | ❌ | `1` | 페이지 번호 |
| `page_size` | `int` | ❌ | `20` | 페이지 크기 |

**Response** (`200 OK`):
```json
{
  "total_count": 42,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "s1",
      "name": "홍길동",
      "class_id": "c1",
      "class_name": "수학 1반",
      "current_ability_theta": 0.12,
      "recent_score": 87.0,
      "status": "On Track",
      "risk_flags": ["최근 결석 없음", "추세 안정적"]
    }
  ]
}
```

**Error Responses**:
- `403 Forbidden`: 권한 없음 (다른 teacher의 데이터 접근 시도)
- `404 Not Found`: teacher_id가 존재하지 않음

---

#### 1.2. GET /api/teachers/{teacher_id}/students/{student_id}

**목적**: 학생 상세 정보 (Ability Trend, 최근 시험, 위험 신호)

**Request**:
```http
GET /api/teachers/{teacher_id}/students/s1
Authorization: Bearer <JWT_TOKEN>
```

**Response** (`200 OK`):
```json
{
  "id": "s1",
  "name": "홍길동",
  "class_id": "c1",
  "class_name": "수학 1반",
  "current_ability_theta": 0.12,
  "recent_score": 87.0,
  "status": "On Track",
  "risk_flags": ["최근 결석 없음", "추세 안정적"],
  "ability_trend": [
    { "label": "4w ago", "value": -0.2 },
    { "label": "3w ago", "value": -0.05 },
    { "label": "2w ago", "value": 0.0 },
    { "label": "1w ago", "value": 0.08 },
    { "label": "now", "value": 0.12 }
  ],
  "recent_tests": [
    { "date": "2025-11-10", "name": "미분·적분 퀴즈", "score": 90.0 },
    { "date": "2025-11-05", "name": "극한 개념 테스트", "score": 85.0 },
    { "date": "2025-10-30", "name": "수열 단원평가", "score": 88.0 }
  ]
}
```

**Error Responses**:
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 학생이 존재하지 않거나 teacher의 관할이 아님

---

### 2. Parent API

#### 2.1. GET /api/parents/{parent_id}/children/{child_id}

**목적**: 학부모의 특정 자녀 상세 정보

**Request**:
```http
GET /api/parents/p1/children/c1
Authorization: Bearer <JWT_TOKEN>
```

**Response** (`200 OK`):
```json
{
  "id": "c1",
  "name": "홍길동",
  "class_id": "c1",
  "class_name": "수학 심화반",
  "current_ability_theta": 0.25,
  "recent_score": 89.0,
  "status": "On Track",
  "risk_flags": ["추세 안정적"],
  "ability_trend": [
    { "label": "4w ago", "value": 0.0 },
    { "label": "3w ago", "value": 0.05 },
    { "label": "2w ago", "value": 0.12 },
    { "label": "1w ago", "value": 0.2 },
    { "label": "now", "value": 0.25 }
  ],
  "recent_tests": [
    { "date": "2025-11-10", "name": "중간고사", "score": 92.0 }
  ],
  "study_time_month": "12h / month",
  "strengths": ["도형", "함수 응용", "논리적 사고력"],
  "areas_to_improve": ["확률", "통계"],
  "recent_activity": [
    { "date": "2025-11-10", "description": "미분·적분 퀴즈 풀이 완료 (90%)" },
    { "date": "2025-11-05", "description": "극한 개념 복습 학습 완료" }
  ]
}
```

**Error Responses**:
- `403 Forbidden`: parent가 해당 child의 부모가 아님
- `404 Not Found`: child_id가 존재하지 않음

---

### 3. Tutor API

#### 3.1. GET /api/tutors/{tutor_id}/sessions

**목적**: 튜터의 세션 목록

**Request**:
```http
GET /api/tutors/t1/sessions?status=Completed&page=1&page_size=20
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `status` | `string` | ❌ | `all` | `"Upcoming"` / `"Completed"` / `"all"` |
| `page` | `int` | ❌ | `1` | 페이지 번호 |
| `page_size` | `int` | ❌ | `20` | 페이지 크기 |

**Response** (`200 OK`):
```json
{
  "total_count": 3,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "sess1",
      "date": "2025-11-10",
      "student_id": "s1",
      "student_name": "홍길동",
      "subject": "수학",
      "topic": "미분·적분",
      "status": "Completed"
    },
    {
      "id": "sess2",
      "date": "2025-11-08",
      "student_id": "s2",
      "student_name": "이영희",
      "subject": "수학",
      "topic": "함수 개념",
      "status": "Upcoming"
    }
  ]
}
```

---

#### 3.2. GET /api/tutors/{tutor_id}/sessions/{session_id}

**목적**: 세션 상세 (노트, 할 일, 상태)

**Request**:
```http
GET /api/tutors/t1/sessions/sess1
Authorization: Bearer <JWT_TOKEN>
```

**Response** (`200 OK`):
```json
{
  "id": "sess1",
  "date": "2025-11-10",
  "student_id": "s1",
  "student_name": "홍길동",
  "subject": "수학",
  "topic": "미분·적분",
  "status": "Completed",
  "duration_minutes": 90,
  "notes": "개념 이해는 양호, 문제 풀이 속도를 조금 더 올릴 필요 있음.",
  "tasks": [
    { "label": "교과서 예제 5개 풀이", "done": true },
    { "label": "심화 문제 3개 풀이", "done": true },
    { "label": "개념 요약 정리 복습", "done": false }
  ]
}
```

**Error Responses**:
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 세션이 존재하지 않거나 tutor의 세션이 아님

---

## RBAC 및 스코핑 규칙

### 공통 전제

1. **JWT 기반 인증**: 모든 엔드포인트는 `Authorization: Bearer <token>` 필요
2. **`get_current_user()` 의존성**: FastAPI에서 현재 유저 정보 추출
3. **User 모델**: `role` 필드 (`"teacher"` / `"parent"` / `"tutor"` / `"student"` / `"admin"`)

### Role별 접근 규칙

#### 1. Teacher API (`/api/teachers/{teacher_id}/...`)

| 조건 | 허용 여부 |
|------|----------|
| `current_user.role == "admin"` | ✅ 모든 teacher 데이터 접근 가능 |
| `current_user.role == "teacher"` AND `teacher_id == current_user.id` | ✅ 자신의 학생만 접근 |
| `current_user.role == "teacher"` AND `teacher_id != current_user.id` | ❌ 403 Forbidden |
| `current_user.role == "parent"` / `"student"` | ❌ 403 Forbidden |

**"me" alias 지원**:
- `GET /api/teachers/me/students` → `teacher_id`를 `current_user.id`로 자동 치환

#### 2. Parent API (`/api/parents/{parent_id}/children/{child_id}`)

| 조건 | 허용 여부 |
|------|----------|
| `current_user.role == "admin"` | ✅ 모든 데이터 접근 |
| `current_user.role == "parent"` AND `parent_id == current_user.id` AND `is_child_of(parent_id, child_id)` | ✅ 자신의 자녀만 접근 |
| `current_user.role == "parent"` AND 자녀 아님 | ❌ 403 Forbidden |
| 기타 | ❌ 403 Forbidden |

**검증 로직**:
```python
def is_child_of(parent_id: str, child_id: str) -> bool:
    """DB에서 parent-child 관계 확인"""
    # SELECT 1 FROM parent_child WHERE parent_id=? AND child_id=?
    return True  # 또는 False
```

#### 3. Tutor API (`/api/tutors/{tutor_id}/sessions/...`)

| 조건 | 허용 여부 |
|------|----------|
| `current_user.role == "admin"` | ✅ 모든 데이터 접근 |
| `current_user.role == "tutor"` AND `tutor_id == current_user.id` | ✅ 자신의 세션만 접근 |
| `current_user.role == "tutor"` AND `tutor_id != current_user.id` | ❌ 403 Forbidden |
| 기타 | ❌ 403 Forbidden |

### 구현 예시 (의존성 함수)

```python
# backend/app/api/dependencies.py

from fastapi import Depends, HTTPException
from app.core.security import get_current_user
from app.models.user import User

def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teacher role required")
    return current_user

def require_parent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("parent", "admin"):
        raise HTTPException(status_code=403, detail="Parent role required")
    return current_user

def require_tutor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("tutor", "admin"):
        raise HTTPException(status_code=403, detail="Tutor role required")
    return current_user

def verify_teacher_access(teacher_id: str, current_user: User) -> str:
    """teacher_id 검증 및 'me' 치환"""
    effective_id = teacher_id if teacher_id != "me" else current_user.id
    if current_user.role == "teacher" and effective_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access other teachers' data")
    return effective_id
```

---

## 구현 가이드

### Phase 1: Schema & Router 스켈레톤 (즉시)

1. **파일 생성**:
   ```bash
   backend/app/schemas/common.py
   backend/app/schemas/students.py
   backend/app/schemas/tutors.py
   backend/app/api/teachers.py
   backend/app/api/parents.py
   backend/app/api/tutors.py
   ```

2. **초기 응답**: Mock 데이터 또는 빈 리스트 반환
   ```python
   @router.get("/api/teachers/{teacher_id}/students")
   async def list_students(...):
       return PageResponse(total_count=0, page=1, page_size=20, items=[])
   ```

3. **RBAC만 먼저 구현**: 403 에러가 제대로 나는지 확인

### Phase 2: DB 연동 (1-2주 후)

1. **Student 테이블 쿼리**:
   ```python
   # SQLAlchemy example
   students = db.query(Student)\
       .filter(Student.teacher_id == effective_teacher_id)\
       .filter(Student.name.contains(q))\
       .all()
   ```

2. **Ability Trend 계산**: 최근 5주 θ 값 집계
3. **Recent Tests 조회**: 최근 3개 시험 결과

### Phase 3: 최적화 (나중에)

- Caching (Redis)
- N+1 쿼리 방지 (eager loading)
- 실시간 업데이트 (WebSocket)

---

## 테스트 시나리오

### 1. Teacher API 테스트

#### 성공 케이스
```bash
# 1. 자신의 학생 목록 조회
curl -H "Authorization: Bearer $TEACHER_TOKEN" \
  http://localhost:8000/api/teachers/me/students

# 2. 특정 학생 상세 조회
curl -H "Authorization: Bearer $TEACHER_TOKEN" \
  http://localhost:8000/api/teachers/me/students/s1

# 3. 필터링 (At Risk 학생만)
curl -H "Authorization: Bearer $TEACHER_TOKEN" \
  "http://localhost:8000/api/teachers/me/students?status=At%20Risk"
```

#### 실패 케이스
```bash
# 1. 다른 teacher 데이터 접근 시도 → 403
curl -H "Authorization: Bearer $TEACHER_TOKEN" \
  http://localhost:8000/api/teachers/other_teacher_id/students

# 2. Parent가 teacher API 호출 → 403
curl -H "Authorization: Bearer $PARENT_TOKEN" \
  http://localhost:8000/api/teachers/me/students
```

### 2. Parent API 테스트

#### 성공 케이스
```bash
# 자신의 자녀 상세 조회
curl -H "Authorization: Bearer $PARENT_TOKEN" \
  http://localhost:8000/api/parents/me/children/c1
```

#### 실패 케이스
```bash
# 다른 parent의 자녀 조회 시도 → 403
curl -H "Authorization: Bearer $PARENT_TOKEN" \
  http://localhost:8000/api/parents/me/children/other_child_id
```

### 3. Tutor API 테스트

#### 성공 케이스
```bash
# 1. 세션 목록 조회
curl -H "Authorization: Bearer $TUTOR_TOKEN" \
  http://localhost:8000/api/tutors/me/sessions

# 2. 특정 세션 상세 조회
curl -H "Authorization: Bearer $TUTOR_TOKEN" \
  http://localhost:8000/api/tutors/me/sessions/sess1
```

---

## 프론트엔드 연동

### API Client Helper 위치

```
portal_front/
├── src/
│   ├── lib/
│   │   ├── api.ts              # 기존 공통 API 헬퍼
│   │   ├── apiTeacher.ts       # Teacher API 전용
│   │   ├── apiParent.ts        # Parent API 전용
│   │   └── apiTutor.ts         # Tutor API 전용
```

### 사용 예시

```tsx
// portal_front/src/pages/teacher/StudentList.tsx

import { useEffect, useState } from 'react';
import { teacherApi } from '@/lib/apiTeacher';

export default function TeacherStudentsPage() {
  const [students, setStudents] = useState([]);

  useEffect(() => {
    async function loadStudents() {
      const response = await teacherApi.listStudents({
        q: '',
        status: 'all',
        page: 1,
        page_size: 20,
      });
      setStudents(response.items);
    }
    loadStudents();
  }, []);

  // ...
}
```

---

## 마이그레이션 체크리스트

- [x] Pydantic schemas 생성 (`schemas/common.py`, `students.py`, `tutors.py`) ✅
- [x] FastAPI routers 생성 (`api/teachers.py`, `parents.py`, `tutors.py`) ✅
- [x] RBAC 의존성 함수 구현 (각 router에 내장) ✅
- [x] Backend main.py에 라우터 등록 ✅
- [x] Frontend API helpers 작성 (`lib/apiTeacher.ts` 등) ✅
- [ ] Mock 데이터로 응답 확인 (Postman/curl)
- [ ] Frontend mock 데이터 → 실제 API 호출로 교체
- [ ] DB 쿼리 구현 (Student, Session 테이블)
- [ ] Ability Trend 계산 로직 구현
- [ ] E2E 테스트 작성
- [ ] Production 배포

---

## 참고 자료

### 내부 문서
- `docs/DASHBOARD_IMPLEMENTATION.md` - 프론트엔드 대시보드 구현
- `backend/API_GUIDE.md` - 기존 API 가이드
- `docs/implementation/13-ux-teacher-admin-console.md` - UX 설계

### 외부 리소스
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Guide](https://docs.pydantic.dev/latest/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|-----------|--------|
| 2025-11-19 | 초안 작성, 전체 엔드포인트 정의 | GitHub Copilot |
| 2025-11-19 | Backend schemas, routers, frontend helpers 구현 완료 | GitHub Copilot |
| 2025-11-19 | **플랫폼 레벨 통합 완료**: DB 스키마, ORM, 서비스 레이어, Redis 캐싱, Ability History API | GitHub Copilot |

---

**문서 작성**: GitHub Copilot  
**최종 업데이트**: 2025-11-19  
**버전**: 1.0
