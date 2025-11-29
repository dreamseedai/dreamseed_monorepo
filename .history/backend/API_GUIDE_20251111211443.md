# Phase 1 MVP - Authentication API Guide

## 🎯 완료된 기능

### ✅ 데이터베이스 마이그레이션
- 4개 테이블 생성: `users`, `problems`, `submissions`, `progress`
- Alembic을 통한 스키마 버전 관리

### ✅ 인증 API
- 회원가입 (POST /auth/register)
- 로그인 (POST /auth/login)
- 현재 사용자 정보 조회 (GET /auth/me)
- 토큰 갱신 (POST /auth/refresh)

---

## 📡 API 엔드포인트

### 1. 회원가입

**Endpoint:** `POST /auth/register`

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "secure_password_123",
  "full_name": "홍길동",
  "role": "student"
}
```

**역할 (role) 옵션:**
- `student` - 학생
- `parent` - 학부모
- `teacher` - 교사
- `admin` - 관리자

**Response (201 Created):**
```json
{
  "id": "uuid-here",
  "email": "student@example.com",
  "full_name": "홍길동",
  "role": "student",
  "is_active": true,
  "created_at": "2025-11-11T12:00:00Z",
  "updated_at": "2025-11-11T12:00:00Z"
}
```

---

### 2. 로그인

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "secure_password_123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**토큰 유효기간:** 30분 (환경변수로 설정 가능)

---

### 3. 현재 사용자 정보 조회

**Endpoint:** `GET /auth/me`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "uuid-here",
  "email": "student@example.com",
  "full_name": "홍길동",
  "role": "student",
  "is_active": true,
  "created_at": "2025-11-11T12:00:00Z",
  "updated_at": "2025-11-11T12:00:00Z"
}
```

---

### 4. 토큰 갱신

**Endpoint:** `POST /auth/refresh`

**Headers:**
```
Authorization: Bearer {old_access_token}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 🔐 보안 기능

### 비밀번호 해싱
- **알고리즘:** bcrypt
- **Salt:** 자동 생성 (랜덤)
- **검증:** 안전한 비교 함수 사용

### JWT 토큰
- **알고리즘:** HS256
- **페이로드:**
  - `sub`: 사용자 ID (UUID)
  - `email`: 사용자 이메일
  - `role`: 사용자 역할
  - `exp`: 만료 시간

### 권한 관리
- **의존성 주입을 통한 인증 확인**
  - `get_current_user`: 로그인 필수
  - `get_current_active_admin`: 관리자 권한 필요
  - `get_current_active_teacher`: 교사/관리자 권한 필요

---

## 🧪 테스트 결과

### 테스트 사용자
- **이메일:** test@dreamseed.ai
- **비밀번호:** test1234
- **역할:** student

### 검증 완료
✅ 회원가입 정상 작동  
✅ 중복 이메일 차단  
✅ 로그인 JWT 토큰 발급  
✅ 잘못된 비밀번호 차단  
✅ 토큰 디코딩 및 검증  
✅ 사용자 정보 조회  

---

## 🚀 다음 단계

### Phase 1 남은 작업
1. **문제(Problem) CRUD API** - `POST/GET/PUT/DELETE /problems`
2. **제출(Submission) API** - `POST /submissions`, `GET /submissions/{id}`
3. **진행도(Progress) API** - `GET /progress`, `GET /progress/{user_id}`
4. **API 테스트** - pytest 테스트 작성

### 환경 변수 설정
`.env` 파일에 다음 값 설정:
```
DATABASE_URL=postgresql+psycopg2://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed
JWT_SECRET=your-super-secret-key-here-64-chars-recommended
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## 📊 데이터베이스 스키마

### users 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | Primary Key |
| email | String(255) | Unique, Indexed |
| hashed_password | String | bcrypt 해시 |
| full_name | String(100) | 사용자 이름 |
| role | String(20) | student/parent/teacher/admin |
| is_active | Boolean | 계정 활성화 여부 |
| created_at | DateTime | 생성 시간 |
| updated_at | DateTime | 수정 시간 |

---

## 💡 사용 예제 (curl)

### 회원가입
```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "테스트",
    "role": "student"
  }'
```

### 로그인
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 사용자 정보 조회
```bash
TOKEN="your-jwt-token-here"
curl -X GET http://localhost:8001/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

**구현 완료일:** 2025-11-11  
**다음 업데이트:** 문제 CRUD API 구현
