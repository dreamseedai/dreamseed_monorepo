# DreamSeedAI Core Schema & Architecture Integration Guide

**문서 목적**: DreamSeedAI의 코어 엔티티를 기반으로 실제 구현 가능한 실행 스키마(INTEGER 기반)와 FastAPI 구조를 정리  
**작성일**: 2025년 11월 19일  
**버전**: 1.0  
**대상**: 개발팀, Copilot/Continue AI 참조용

---

## 🔥 1. 목적

이 문서는 다음을 한 번에 정리합니다:

* **실행 가능한 PostgreSQL 스키마 (INTEGER PK/FK 버전)**
* **일관된 SQLAlchemy 모델 구조**
* **FastAPI 코어 라우터 스켈레톤**
* **Phase 0 → Phase 1 전환에 필요한 핵심 구조 정의**

DreamSeedAI 전체 아키텍처(데이터 모델 · API · 정책 계층)의 바탕을 이루는 "코어 오브젝트 모델"을 가장 최소하고 안정적인 형태로 정의합니다.

---

## 📦 2. PostgreSQL 실행 스키마 (INTEGER 기반)

DreamSeedAI의 핵심 엔티티는 다음 여섯 가지입니다:

* **organizations** (멀티테넌시용)
* **users** (공통 계정)
* **students**
* **teachers**
* **classes** (학급)
* **student_classroom** (N:N 관계)
* **exam_sessions** (시험)
* **attempts** (문항 단위 답안)

각 엔티티는 실제 FastAPI + SQLAlchemy + PostgreSQL 환경에서 바로 사용할 수 있도록 설계되었습니다.

### 2.1 스키마 설계 원칙

```yaml
ID 타입:
  - 모든 PK: INTEGER with SERIAL (autoincrement)
  - 모든 FK: INTEGER (참조하는 테이블의 PK 타입과 일치)
  
타임스탬프:
  - created_at: TIMESTAMP WITH TIME ZONE (서버 기본값 now())
  - updated_at: TIMESTAMP WITH TIME ZONE (자동 업데이트)
  
인덱스:
  - PK는 자동 인덱스
  - FK는 명시적 인덱스 추가
  - 자주 조회되는 컬럼 인덱스
  
제약조건:
  - ON DELETE CASCADE (참조 무결성)
  - UNIQUE 제약 (중복 방지)
  - NOT NULL (필수 필드)
```

### 2.2 코어 테이블 정의

```sql
-- 1. Organizations (멀티테넌시)
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) UNIQUE,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_organizations_domain ON organizations(domain);
CREATE INDEX idx_organizations_is_active ON organizations(is_active);

-- 2. Users (공통 계정)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    role VARCHAR(50) NOT NULL, -- 'student', 'teacher', 'parent', 'admin'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_organization ON users(organization_id);

-- 3. Students
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    external_id VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    grade VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_external_id ON students(external_id);
CREATE INDEX idx_students_name ON students(name);

-- 4. Teachers
CREATE TABLE teachers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_teachers_user_id ON teachers(user_id);
CREATE INDEX idx_teachers_name ON teachers(name);

-- 5. Classes (학급)
CREATE TABLE classes (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100),
    grade VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_classes_teacher_id ON classes(teacher_id);
CREATE INDEX idx_classes_name ON classes(name);

-- 6. Student-Classroom (N:N)
CREATE TABLE student_classroom (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(student_id, class_id)
);

CREATE INDEX idx_student_classroom_student ON student_classroom(student_id);
CREATE INDEX idx_student_classroom_class ON student_classroom(class_id);

-- 7. ExamSessions (시험)
CREATE TABLE exam_sessions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    exam_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'abandoned'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE,
    final_theta FLOAT,
    final_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_exam_sessions_student ON exam_sessions(student_id);
CREATE INDEX idx_exam_sessions_status ON exam_sessions(status);
CREATE INDEX idx_exam_sessions_started_at ON exam_sessions(started_at);

-- 8. Attempts (문항 단위 답안)
CREATE TABLE attempts (
    id SERIAL PRIMARY KEY,
    exam_session_id INTEGER REFERENCES exam_sessions(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL,
    student_answer TEXT,
    is_correct BOOLEAN,
    response_time_sec INTEGER,
    theta_before FLOAT,
    theta_after FLOAT,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_attempts_exam_session ON attempts(exam_session_id);
CREATE INDEX idx_attempts_problem ON attempts(problem_id);
CREATE INDEX idx_attempts_attempted_at ON attempts(attempted_at);
```

---

## 🧱 3. SQLAlchemy ORM 모델 (core/models.py)

아래 모델들은 위 스키마를 ORM으로 구성한 것입니다. DreamSeedAI의 모든 앱(학생/교사/학부모/관리자)이 공유할 수 있는 공통 모델 레이어입니다.

### 3.1 관계 설계

```yaml
User ↔ Student/Teacher:
  - 1:1 관계
  - User는 role에 따라 Student 또는 Teacher와 연결
  
Student ↔ Class:
  - N:N 관계 (student_classroom 중간 테이블)
  - 한 학생이 여러 반에 소속 가능
  
ExamSession ↔ Attempt:
  - 1:N 관계
  - 한 시험에 여러 문항 답안
```

### 3.2 모델 코드

```python
# backend/app/core/models.py
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text, 
    DateTime, ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(100), unique=True, index=True)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), nullable=False, index=True)  # 'student', 'teacher', 'parent', 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    external_id = Column(String(100), index=True)
    name = Column(String(255), nullable=False, index=True)
    grade = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="student")
    classrooms = relationship("StudentClassroom", back_populates="student")
    exam_sessions = relationship("ExamSession", back_populates="student")


class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    department = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="teacher")
    classes = relationship("Class", back_populates="teacher")


class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    name = Column(String(255), nullable=False, index=True)
    subject = Column(String(100))
    grade = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    teacher = relationship("Teacher", back_populates="classes")
    students = relationship("StudentClassroom", back_populates="class_obj")


class StudentClassroom(Base):
    __tablename__ = "student_classroom"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("student_id", "class_id", name="uq_student_class"),
    )
    
    # Relationships
    student = relationship("Student", back_populates="classrooms")
    class_obj = relationship("Class", back_populates="students")


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_name = Column(String(255), nullable=False)
    status = Column(String(50), default="active", index=True)  # 'active', 'completed', 'abandoned'
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))
    final_theta = Column(Float)
    final_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="exam_sessions")
    attempts = relationship("Attempt", back_populates="exam_session")


class Attempt(Base):
    __tablename__ = "attempts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exam_session_id = Column(Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(Integer, nullable=False, index=True)
    student_answer = Column(Text)
    is_correct = Column(Boolean)
    response_time_sec = Column(Integer)
    theta_before = Column(Float)
    theta_after = Column(Float)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    exam_session = relationship("ExamSession", back_populates="attempts")
```

---

## 🚦 4. FastAPI Router 스켈레톤

핵심 기능 3가지만 기본 라우터를 제공합니다:

1. **시험 시작** - `/api/exams/start`
2. **답안 제출** - `/api/exams/answer`
3. **교사용 클래스 요약** - `/api/classes/{id}/summary`

CAT/IRT 로직은 별도 서비스 레이어로 확장할 수 있으며, 여기서는 최소 API 골격만 제시합니다.

### 4.1 시험 라우터

```python
# backend/app/api/exams.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import ExamSession, Attempt, Student
from app.schemas.exams import (
    ExamStartRequest, ExamStartResponse,
    AnswerSubmitRequest, AnswerSubmitResponse
)

router = APIRouter(prefix="/api/exams", tags=["exams"])


@router.post("/start", response_model=ExamStartResponse)
def start_exam(
    request: ExamStartRequest,
    db: Session = Depends(get_db)
):
    """
    시험 시작
    
    - student_id로 학생 확인
    - ExamSession 생성 (status='active')
    - 초기 theta 설정 (default 0.0)
    """
    student = db.query(Student).filter(Student.id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    exam_session = ExamSession(
        student_id=request.student_id,
        exam_name=request.exam_name,
        status="active"
    )
    db.add(exam_session)
    db.commit()
    db.refresh(exam_session)
    
    return ExamStartResponse(
        exam_session_id=exam_session.id,
        status="started",
        initial_theta=0.0
    )


@router.post("/answer", response_model=AnswerSubmitResponse)
def submit_answer(
    request: AnswerSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    답안 제출
    
    - Attempt 레코드 생성
    - CAT/IRT 로직 호출 (별도 서비스)
    - theta 업데이트
    - 다음 문제 추천
    """
    exam_session = db.query(ExamSession).filter(
        ExamSession.id == request.exam_session_id
    ).first()
    
    if not exam_session or exam_session.status != "active":
        raise HTTPException(status_code=400, detail="Invalid exam session")
    
    # Attempt 생성
    attempt = Attempt(
        exam_session_id=request.exam_session_id,
        problem_id=request.problem_id,
        student_answer=request.answer,
        is_correct=request.is_correct,  # TODO: 자동 채점 로직
        response_time_sec=request.response_time_sec,
        theta_before=exam_session.final_theta or 0.0
    )
    
    # TODO: CAT/IRT 로직으로 theta_after 계산
    attempt.theta_after = attempt.theta_before + (0.1 if request.is_correct else -0.1)
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    # ExamSession theta 업데이트
    exam_session.final_theta = attempt.theta_after
    db.commit()
    
    return AnswerSubmitResponse(
        attempt_id=attempt.id,
        is_correct=attempt.is_correct,
        updated_theta=attempt.theta_after,
        next_problem_id=None  # TODO: CAT 로직으로 다음 문제 선택
    )
```

### 4.2 클래스 라우터

```python
# backend/app/api/classes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import Class, StudentClassroom, Student
from app.schemas.classes import ClassSummaryResponse, StudentInClass

router = APIRouter(prefix="/api/classes", tags=["classes"])


@router.get("/{class_id}/summary", response_model=ClassSummaryResponse)
def get_class_summary(
    class_id: int,
    db: Session = Depends(get_db)
):
    """
    교사용 클래스 요약
    
    - 클래스 정보
    - 소속 학생 목록
    - 학생별 최근 시험 결과 요약
    """
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # 소속 학생 조회
    student_classrooms = db.query(StudentClassroom).filter(
        StudentClassroom.class_id == class_id
    ).all()
    
    students = []
    for sc in student_classrooms:
        student = db.query(Student).filter(Student.id == sc.student_id).first()
        if student:
            # TODO: 최근 시험 결과 조회
            students.append(StudentInClass(
                student_id=student.id,
                name=student.name,
                grade=student.grade,
                recent_exam_count=0,  # TODO
                average_theta=0.0  # TODO
            ))
    
    return ClassSummaryResponse(
        class_id=class_obj.id,
        class_name=class_obj.name,
        subject=class_obj.subject,
        teacher_id=class_obj.teacher_id,
        student_count=len(students),
        students=students
    )
```

---

## 🧩 5. 어떻게 활용하면 좋은가?

이 문서의 목적은:

* **개발자들이 레포에서 바로 실행 가능하도록**
* **Copilot/Continue가 맥락을 이해하도록**
* **FastAPI + PostgreSQL 구조를 표준화하도록**

입니다.

### 5.1 Copilot/Continue 활용법

특히 Copilot/Continue에게:

```
"이 문서(Dreamseed_Core_Schema_Alignment.md)를 기준으로 
core/models.py · core/schemas.py · api/routers/...을 자동 완성해줘"
```

라고 지시하면 정확도가 매우 높아집니다.

### 5.2 개발 워크플로우

```yaml
Step 1: 스키마 생성
  - PostgreSQL에 위 SQL 실행
  - 또는 Alembic migration 생성

Step 2: 모델 동기화
  - core/models.py에 ORM 모델 복사
  - Relationship 확인

Step 3: 스키마 정의
  - core/schemas.py에 Pydantic 모델 생성
  - Request/Response 타입 정의

Step 4: 라우터 구현
  - api/routers/에 엔드포인트 추가
  - 서비스 로직 분리

Step 5: 테스트
  - pytest로 API 테스트
  - DB 마이그레이션 검증
```

---

## 🚀 6. 다음 단계 제안

### Phase 0.5: 코어 백엔드 완성

```bash
1. core_backend/ 프로젝트 생성
   - 이 문서 기반 모델/스키마/라우터 배치

2. Phase 0 인프라에 연결
   - PostgreSQL dreamseed DB 사용
   - 로컬 완전 실행 (Phase 0.5 완성)

3. 시드 데이터 생성
   - Organizations → Users → Students/Teachers
   - Classes → Student-Classroom
   - 테스트용 ExamSession

4. API 테스트
   - /api/exams/start
   - /api/exams/answer
   - /api/classes/{id}/summary
```

### Phase 1: Cloud 배포

```yaml
Infrastructure:
  - GCP Cloud Run 배포
  - Cloud SQL (PostgreSQL)
  - Secret Manager (환경변수)

Features:
  - CAT/IRT 엔진 통합
  - AI 피드백 생성
  - 학부모 대시보드

Monitoring:
  - Prometheus + Grafana
  - Error tracking
  - Performance metrics
```

이 문서가 전체 구현의 **기준선(Base Artifact)**이 됩니다.

---

## 📘 7. 부록: Pydantic 스키마 예시

### 7.1 시험 스키마

```python
# backend/app/schemas/exams.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExamStartRequest(BaseModel):
    student_id: int
    exam_name: str


class ExamStartResponse(BaseModel):
    exam_session_id: int
    status: str
    initial_theta: float


class AnswerSubmitRequest(BaseModel):
    exam_session_id: int
    problem_id: int
    answer: str
    is_correct: bool
    response_time_sec: int


class AnswerSubmitResponse(BaseModel):
    attempt_id: int
    is_correct: bool
    updated_theta: float
    next_problem_id: Optional[int]
```

### 7.2 클래스 스키마

```python
# backend/app/schemas/classes.py
from pydantic import BaseModel
from typing import List, Optional


class StudentInClass(BaseModel):
    student_id: int
    name: str
    grade: Optional[str]
    recent_exam_count: int
    average_theta: float


class ClassSummaryResponse(BaseModel):
    class_id: int
    class_name: str
    subject: Optional[str]
    teacher_id: int
    student_count: int
    students: List[StudentInClass]
```

---

## 📊 8. 관계 다이어그램

```
Organization (멀티테넌시)
    ↓
   User (공통 계정)
    ↓
   ├─→ Student ←→ StudentClassroom ←→ Class ←─ Teacher
   │      ↓
   │   ExamSession
   │      ↓
   │   Attempt
   │
   └─→ Teacher → Class
```

---

## ✅ 9. 체크리스트

### Phase 0.5 완료 기준

- [ ] PostgreSQL 스키마 생성 완료
- [ ] SQLAlchemy 모델 정의 완료
- [ ] Pydantic 스키마 정의 완료
- [ ] 3개 라우터 구현 완료
  - [ ] POST /api/exams/start
  - [ ] POST /api/exams/answer
  - [ ] GET /api/classes/{id}/summary
- [ ] 시드 데이터 생성 완료
- [ ] API 테스트 통과
- [ ] 로컬 환경 완전 실행

### Phase 1 준비

- [ ] Cloud Run 배포 스크립트
- [ ] Cloud SQL 연결 설정
- [ ] Secret Manager 통합
- [ ] CI/CD 파이프라인
- [ ] 모니터링 설정

---

## 📞 10. 참고 문서

- **데이터 모델 전체 아키텍처**: `docs/implementation/DATA_MODEL_API_INTEGRATION.md`
- **DB 통합 가이드**: `docs/implementation/DB_INTEGRATION_REQUEST.md`
- **Phase 0 인프라**: `ops/phase0/CONSTRUCTION_COMPLETE.md`
- **인프라 청사진**: `docs/architecture/INFRASTRUCTURE_BLUEPRINT.md`

---

---

## 🧠 11. IRT/CAT Engine Integration (Future)

### 11.1 IRT Engine Template

```python
# backend/app/services/irt_engine.py
"""
IRT (Item Response Theory) Engine
- 2PL/3PL 모델 지원
- Maximum Likelihood Estimation
- Bayesian Estimation (MAP/EAP)
"""

class IRTEngine:
    def estimate_theta(
        self,
        responses: List[Tuple[int, bool]],  # [(problem_id, is_correct), ...]
        prior_theta: float = 0.0
    ) -> float:
        """학생의 능력치 theta 추정"""
        # TODO: 실제 IRT 알고리즘 구현
        pass
    
    def calculate_probability(
        self,
        theta: float,
        difficulty: float,
        discrimination: float = 1.0,
        guessing: float = 0.0
    ) -> float:
        """문항 정답 확률 계산 (3PL)"""
        # TODO: 3PL 모델 구현
        pass
```

### 11.2 CAT Engine Template

```python
# backend/app/services/cat_engine.py
"""
CAT (Computerized Adaptive Testing) Engine
- Maximum Information Selection
- Content Balancing
- Exposure Control
"""

class CATEngine:
    def select_next_item(
        self,
        current_theta: float,
        previous_items: List[int],
        item_bank: List[dict]
    ) -> int:
        """다음 문항 선택 (Maximum Information)"""
        # TODO: 최대 정보량 기준 문항 선택
        pass
    
    def check_termination(
        self,
        theta: float,
        se_theta: float,
        num_items: int
    ) -> bool:
        """시험 종료 조건 확인"""
        # TODO: 종료 조건 체크 (SE < 0.3 or N >= 30)
        pass
```

**Note**: IRT/CAT 엔진은 Phase 1에서 통합 예정입니다. 현재는 간단한 theta 업데이트 로직만 사용합니다.

---

**🎯 DreamSeedAI Core Schema Alignment Guide 완료!**

**"코드는 한 번, 활용은 Phase별로!"** 🚀
