# Phase 1: MVP Launch (최소 기능 제품 출시)

**기간**: Week 3-8 (6주)  
**목표**: 첫 1,000명 사용자  
**예산**: $100-150/month

---

## 🎯 Phase 1 목표

### 비즈니스 목표
- ✅ **첫 유료 고객 10명** 확보
- ✅ **베타 테스터 100명** 모집
- ✅ **핵심 기능 검증** (문제 풀이, AI 피드백)
- ✅ **제품-시장 적합성(PMF)** 초기 검증

### 기술 목표
- ✅ FastAPI 백엔드 구축
- ✅ Next.js 프론트엔드 (admin_front 활용)
- ✅ 인증/RBAC 통합
- ✅ PostgreSQL 데이터베이스 스키마
- ✅ 기본 AI 피드백 기능

---

## 📋 MVP 기능 범위

### 필수 기능 (Must Have)
1. **사용자 관리**
   - 회원가입 / 로그인
   - 4가지 역할: student, parent, teacher, admin
   - 프로필 관리

2. **문제 관리**
   - 문제 목록 조회
   - 문제 상세 보기
   - 문제 풀이 제출
   - (선생님/관리자만) 문제 생성/수정/삭제

3. **AI 피드백**
   - 문제 풀이 후 AI 평가
   - 힌트 제공
   - 오답 분석

4. **진도 추적**
   - 학생: 내 진도 확인
   - 부모: 자녀 진도 확인
   - 선생님: 학생별 진도 확인

### 제외 기능 (Out of Scope)
- ❌ 실시간 채팅
- ❌ 화상 수업
- ❌ 복잡한 분석 대시보드
- ❌ 결제 시스템 (Phase 2에서 추가)

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                     사용자                               │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Next.js (admin_front)                      │
│  - 로그인/회원가입                                        │
│  - 문제 목록/상세                                         │
│  - 진도 대시보드                                          │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP/REST API
                    ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend                            │
│  - JWT 인증 미들웨어                                      │
│  - Rate Limiting                                        │
│  - CRUD API                                             │
│  - AI 피드백 서비스                                       │
└───────────┬─────────────────┬───────────────────────────┘
            │                 │
            ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│   PostgreSQL     │  │   Redis Cache    │
│  - users         │  │  - sessions      │
│  - problems      │  │  - rate limits   │
│  - submissions   │  │                  │
└──────────────────┘  └──────────────────┘
```

---

## 📊 데이터베이스 스키마 (v1.0)

### 1. users (사용자)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'parent', 'teacher', 'admin')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### 2. problems (문제)
```sql
CREATE TABLE problems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    category VARCHAR(50),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_problems_difficulty ON problems(difficulty);
CREATE INDEX idx_problems_category ON problems(category);
```

### 3. submissions (제출)
```sql
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    is_correct BOOLEAN,
    ai_feedback TEXT,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    submitted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_submissions_user ON submissions(user_id);
CREATE INDEX idx_submissions_problem ON submissions(problem_id);
```

### 4. progress (진도)
```sql
CREATE TABLE progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('not_started', 'in_progress', 'completed')),
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(user_id, problem_id)
);

CREATE INDEX idx_progress_user ON progress(user_id);
CREATE INDEX idx_progress_status ON progress(status);
```

---

## 📁 프로젝트 구조

```
dreamseed_monorepo/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 앱
│   │   ├── config.py               # 환경 설정
│   │   ├── database.py             # DB 연결
│   │   ├── models/                 # SQLAlchemy 모델
│   │   │   ├── user.py
│   │   │   ├── problem.py
│   │   │   ├── submission.py
│   │   │   └── progress.py
│   │   ├── schemas/                # Pydantic 스키마
│   │   │   ├── user.py
│   │   │   ├── problem.py
│   │   │   └── submission.py
│   │   ├── api/                    # API 라우터
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── problems.py
│   │   │   └── submissions.py
│   │   ├── services/               # 비즈니스 로직
│   │   │   ├── auth_service.py
│   │   │   ├── ai_service.py
│   │   │   └── progress_service.py
│   │   └── middleware/             # 미들웨어
│   │       ├── auth.py             # Phase 0에서 만든 것 통합
│   │       └── rate_limit.py       # Phase 0에서 만든 것 통합
│   ├── alembic/                    # DB 마이그레이션
│   │   └── versions/
│   ├── tests/                      # 테스트
│   │   ├── test_auth.py
│   │   ├── test_problems.py
│   │   └── test_submissions.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── admin_front/                    # 기존 Next.js 프로젝트 활용
│   ├── app/
│   │   ├── auth/
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── dashboard/
│   │   ├── problems/
│   │   └── progress/
│   └── components/
│
└── ops/
    └── phase1/
        ├── README.md               # 이 파일
        ├── scripts/
        │   ├── setup_backend.sh    # 백엔드 설정
        │   ├── setup_db.sh         # DB 마이그레이션
        │   └── deploy_phase1.sh    # Phase 1 배포
        └── configs/
            └── docker-compose.phase1.yml
```

---

## 🚀 Phase 1 실행 계획

### Week 3-4: 백엔드 개발
- [ ] FastAPI 프로젝트 구조 생성
- [ ] SQLAlchemy 모델 작성
- [ ] Alembic 마이그레이션 설정
- [ ] 인증 API (로그인/회원가입)
- [ ] 문제 CRUD API
- [ ] 제출 API
- [ ] AI 피드백 서비스 (간단한 버전)

### Week 5-6: 프론트엔드 개발
- [ ] Next.js 페이지 구조
- [ ] 로그인/회원가입 UI
- [ ] 문제 목록/상세 페이지
- [ ] 문제 풀이 제출 폼
- [ ] 진도 대시보드

### Week 7: 통합 테스트
- [ ] E2E 테스트
- [ ] 부하 테스트 (100 concurrent users)
- [ ] 버그 수정

### Week 8: 베타 출시
- [ ] 베타 테스터 모집
- [ ] 피드백 수집
- [ ] 개선 사항 적용

---

## 📊 API 엔드포인트

### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `POST /api/auth/refresh` - 토큰 갱신
- `GET /api/auth/me` - 내 정보

### 사용자
- `GET /api/users` - 사용자 목록 (admin/teacher만)
- `GET /api/users/{user_id}` - 사용자 상세
- `PUT /api/users/{user_id}` - 사용자 수정
- `DELETE /api/users/{user_id}` - 사용자 삭제 (admin만)

### 문제
- `GET /api/problems` - 문제 목록
- `GET /api/problems/{problem_id}` - 문제 상세
- `POST /api/problems` - 문제 생성 (teacher/admin만)
- `PUT /api/problems/{problem_id}` - 문제 수정
- `DELETE /api/problems/{problem_id}` - 문제 삭제

### 제출
- `POST /api/submissions` - 답안 제출
- `GET /api/submissions` - 내 제출 목록
- `GET /api/submissions/{submission_id}` - 제출 상세

### 진도
- `GET /api/progress` - 내 진도
- `GET /api/progress/{user_id}` - 특정 사용자 진도 (부모/선생님)

---

## 💰 Phase 1 예상 비용

| 항목 | 월 비용 | 설명 |
|------|---------|------|
| Phase 0 인프라 | $100 | 기본 인프라 유지 |
| 개발 서버 전력 | $30 | 추가 서버 (API) |
| 예비 | $20 | 기타 |
| **합계** | **$150/month** | Phase 1 |

---

## ✅ Phase 1 완료 조건

1. ✅ 회원가입/로그인 동작
2. ✅ 문제 10개 이상 등록
3. ✅ 문제 풀이 제출 및 AI 피드백 정상 작동
4. ✅ 진도 대시보드 표시
5. ✅ 베타 테스터 10명 이상 확보
6. ✅ 부하 테스트 100 concurrent users 통과

---

## 🔗 관련 문서

- [Phase 0: Infrastructure Foundation](../phase0/README.md)
- [ARCHITECTURE_MASTERPLAN.md](../maintenance/ARCHITECTURE_MASTERPLAN.md)
- [SCALING_STRATEGY.md](../maintenance/SCALING_STRATEGY.md)

---

**다음 단계**: Phase 1 완료 후 → [Phase 2: Growth (1K → 10K users)](../phase2/README.md)
