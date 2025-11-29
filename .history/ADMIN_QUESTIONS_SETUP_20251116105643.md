# Admin Questions System - Technical Reference

## 개요
PostgreSQL 18,894개 문항을 관리하는 Admin Frontend + Backend API 시스템

레거시 PHP 코드를 참조하여 Next.js 관리자 페이지의 주요 특징을 정리했습니다:

주요 기능:

question_list.php: 검색, 페이징, 삭제 버튼, 생성/수정일 표시
question_info.php: TinyMCE 4.9.11 에디터, 카테고리 3단계, 상태/난이도/등급 선택
question_process.php: Create/Update/Delete 처리, 이미지 경로 자동 변환
현재 복구된 Next.js 코드에는 이미 대부분의 기능이 구현되어 있습니다:

ls -la /var/www/mpcstudy.com/public_html/admin/doc/question*.php 2>&1 | head -20
cat /var/www/mpcstudy.com/public_html/admin/doc/question_list.php
cat /var/www/mpcstudy.com/public_html/admin/doc/question_info.php | head -200
cat /var/www/mpcstudy.com/public_html/admin/doc/question_process.php

✅ QuestionsClient.tsx: 검색, 정렬, 삭제, 페이징
✅ QuestionForm.tsx: TinyMCE 4 + Wiris, 카테고리(topic), 상태/난이도
✅ RichTextEditor.tsx: TinyMCE 4.9.11 통합
✅ API: /api/admin/questions (CRUD)
레거시 PHP의 특별한 부분 중 현재 구현에 추가가 필요한 것이 있다면 말씀해 주세요. (예: 3단계 카테고리, 특정 필드, 이미지 업로드 경로 변환 등)
---

## 시스템 구성

### Frontend - Admin Questions UI
- **경로**: `/home/won/projects/dreamseed_monorepo/admin_front`
- **포트**: `3030`
- **URL**: http://localhost:3030/questions
- **프레임워크**: Next.js 14.2.5, React 18, TypeScript 5.5.4
- **에디터**: TinyMCE 4.9.11 (로컬 `/admin_front/public/tinymce/`)
- **수식**: MathLive 0.95.5 + KaTeX 0.16.11 (CDN)

#### 환경 변수 (.env.local)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8002
NEXT_PUBLIC_API_PREFIX=/api/admin
```

#### 실행 명령
```bash
cd /home/won/projects/dreamseed_monorepo/admin_front
npm run dev  # Port 3030에서 실행
```

#### 주요 컴포넌트
- `app/questions/page.tsx` - 문항 목록 페이지
- `app/questions/QuestionsClient.tsx` - 테이블 UI (ID, Title, Class, Grade, 난이도, Created, Modified, 상태, 작업)
- `app/questions/[id]/edit/page.tsx` - 문항 편집 페이지
- `components/QuestionForm.tsx` - 문항 폼 (TinyMCE 통합)
- `components/RichTextEditor.tsx` - TinyMCE 4.9.11 + Wiris 래퍼
- `lib/questions.ts` - API 클라이언트 (listQuestions, getQuestion, createQuestion, updateQuestion, deleteQuestion)

---

### Backend - Development API Server
- **경로**: `/home/won/projects/dreamseed_monorepo/backend`
- **포트**: `8002` (개발용, production은 8000)
- **URL**: http://localhost:8002/api/admin/questions
- **프레임워크**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy (raw SQL with text())
- **DB 드라이버**: psycopg 3.2.12 + psycopg-binary
- **가상환경**: `/home/won/projects/dreamseed_monorepo/venv`

#### 실행 명령
```bash
# 가상환경 활성화 후 실행
source /home/won/projects/dreamseed_monorepo/venv/bin/activate
cd /home/won/projects/dreamseed_monorepo/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8002 > /tmp/backend_dev_8002.log 2>&1 &

# 백그라운드 실행 확인
lsof -ti:8002
```

#### 로그 확인
```bash
tail -f /tmp/backend_dev_8002.log
```

#### 주요 파일
- `app/api/questions.py` - Questions CRUD API (PostgreSQL 연동)
- `app/core/database.py` - SQLAlchemy 연결 설정
- `main.py` - FastAPI 앱 엔트리포인트, CORS 설정

---

### Production Backend (참고용)
- **경로**: `/opt/dreamseed/current/backend`
- **포트**: `8000`
- **PID**: 1959 (www-data 사용자)
- **상태**: 이전 Mock 데이터 코드 사용 중 (PostgreSQL 미연동)
- **CORS**: http://localhost:3030 추가됨

---

## 데이터베이스 정보

### PostgreSQL - 메인 데이터베이스
- **호스트**: `127.0.0.1:5432`
- **데이터베이스**: `dreamseed`
- **사용자**: `postgres`
- **비밀번호**: `DreamSeedAi0908` (주의: `0908`이 아님!)
- **연결 URL**: `postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed`

#### 테이블: `problems`
```sql
-- 18,894개 문항 (mpcstudy 마이그레이션)
CREATE TABLE problems (
    uuid_legacy     uuid        NOT NULL,                    -- UUID (gen_random_uuid())
    title           text        NOT NULL,                    -- 문항 제목
    description     text        NOT NULL,                    -- 문항 내용 (stem)
    difficulty      varchar(20),                             -- 난이도 (1-5 또는 easy/medium/hard)
    category        varchar(50),                             -- 카테고리 (수학, 물리 등)
    created_by      uuid        REFERENCES users(id),        -- 작성자
    created_at      timestamptz DEFAULT NOW(),               -- 생성일
    updated_at      timestamptz DEFAULT NOW(),               -- 수정일
    mysql_metadata  jsonb       DEFAULT '{}',                -- MySQL 마이그레이션 메타데이터
    id              integer     NOT NULL GENERATED ALWAYS AS ((mysql_metadata->>'mysql_id')::integer) STORED,
    PRIMARY KEY (uuid_legacy)
);

-- 인덱스
CREATE INDEX idx_problems_id ON problems(id);
CREATE INDEX idx_problems_category ON problems(category);
CREATE INDEX idx_problems_difficulty ON problems(difficulty);
```

#### mysql_metadata JSONB 구조
```json
{
    "mysql_id": "1",           // 원본 MySQL que_id
    "que_class": "M",          // 과목 (M=수학, P=물리, C=화학 등)
    "que_grade": "G11"         // 학년 (G10, G11, G12 등)
}
```

#### PostgreSQL 접속
```bash
PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed
```

#### 유용한 쿼리
```sql
-- 전체 문항 수
SELECT COUNT(*) FROM problems;

-- Class/Grade 데이터 확인
SELECT id, 
       mysql_metadata->>'que_class' as class, 
       mysql_metadata->>'que_grade' as grade,
       title 
FROM problems 
LIMIT 10;

-- Class/Grade 업데이트된 레코드 수
SELECT COUNT(*) 
FROM problems 
WHERE mysql_metadata->>'que_class' IS NOT NULL 
  AND mysql_metadata->>'que_class' != '';

-- 특정 ID 검색
SELECT * FROM problems WHERE id = 18899;
```

---

### MySQL - 원본 데이터베이스
- **데이터베이스**: `mpcstudy_db`
- **사용자**: `mpcstudy_root`
- **비밀번호 옵션**:
  - `2B3Z45J3DACT` (주 비밀번호)
  - `0908`
  - `SetA_Strong_Pass!2025`

#### 테이블: `tbl_question`
```sql
-- 18,898개 원본 문항
CREATE TABLE tbl_question (
    que_id           int PRIMARY KEY AUTO_INCREMENT,
    que_status       int DEFAULT 1,
    que_class        char(1),        -- M=수학, P=물리, C=화학
    que_category1    int,
    que_category2    int,
    que_category3    int,
    que_grade        char(3),        -- G10, G11, G12
    que_level        int DEFAULT 1,
    que_en_title     text,
    que_en_desc      mediumtext,
    que_en_hint      mediumtext,
    que_en_solution  mediumtext,
    que_en_answers   mediumtext,
    que_en_answerm   char(1),
    que_answertype   int,
    que_en_example   text,
    que_en_resource  text,
    que_createddate  varchar(14),
    que_modifieddate varchar(14)
);
```

#### MySQL 접속
```bash
mysql -u mpcstudy_root -p'2B3Z45J3DACT'
USE mpcstudy_db;
SHOW TABLES;
DESCRIBE tbl_question;
```

#### MySQL → PostgreSQL 동기화

**Class/Grade 데이터 동기화**:
```bash
# 전체 18,898개 동기화
mysql -u mpcstudy_root -p'2B3Z45J3DACT' mpcstudy_db -N -e \
  "SELECT que_id, COALESCE(que_class,''), COALESCE(que_grade,'') FROM tbl_question;" 2>/dev/null | \
while IFS=$'\t' read -r id class grade; do
  echo "UPDATE problems SET mysql_metadata = jsonb_set(jsonb_set(mysql_metadata, '{que_class}', '\"$class\"'), '{que_grade}', '\"$grade\"') WHERE (mysql_metadata->>'mysql_id')::int = $id;"
done | PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed -q
```

---

## API 엔드포인트

### Base URL
- Development: `http://localhost:8002/api/admin`
- Production: `http://localhost:8000/api/admin`

### GET /questions
문항 목록 조회 (페이지네이션, 필터링, 정렬)

**Parameters**:
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지 크기 (기본값: 50, 최대: 100)
- `q`: 검색어 (ID 숫자 또는 제목/카테고리 텍스트)
- `difficulty`: 난이도 필터
- `category`: 카테고리 필터
- `sort_by`: 정렬 기준 (id, created_at, updated_at, difficulty)
- `order`: 정렬 순서 (asc, desc)

**Response**:
```json
{
  "total": 18895,
  "page": 1,
  "page_size": 50,
  "results": [
    {
      "id": 18899,
      "title": "신규 테스트 문항",
      "difficulty": "medium",
      "category": "수학",
      "que_class": "M",
      "que_grade": "G11",
      "created_at": "2025-11-15T00:07:39.011568-05:00",
      "updated_at": "2025-11-15T00:07:39.011568-05:00"
    }
  ]
}
```

**예시**:
```bash
# 기본 조회
curl "http://localhost:8002/api/admin/questions?page=1&page_size=50"

# ID 검색 (숫자)
curl "http://localhost:8002/api/admin/questions?q=18899"

# 제목 검색 (텍스트)
curl "http://localhost:8002/api/admin/questions?q=미분"

# 필터링 + 정렬
curl "http://localhost:8002/api/admin/questions?difficulty=medium&category=수학&sort_by=created_at&order=desc"
```

---

### GET /questions/{id}
특정 문항 상세 조회

**Response**:
```json
{
  "id": 18899,
  "title": "신규 테스트 문항",
  "stem": "문제 설명입니다",
  "difficulty": "medium",
  "topic": "수학",
  "que_class": "M",
  "que_grade": "G11",
  "created_at": "2025-11-15T00:07:39.011568-05:00",
  "updated_at": "2025-11-15T00:07:39.011568-05:00"
}
```

**예시**:
```bash
curl "http://localhost:8002/api/admin/questions/18899"
```

---

### POST /questions
새 문항 생성

**Request Body**:
```json
{
  "title": "신규 문항 제목",
  "stem": "문제 내용",
  "difficulty": "medium",
  "topic": "수학"
}
```

**Response**: GET /questions/{id}와 동일

**중요**: 
- `uuid_legacy`는 `gen_random_uuid()`로 자동 생성
- `mysql_metadata->>'mysql_id'`는 기존 최대값 + 1로 자동 할당
- `id`는 Generated Column으로 자동 생성

**예시**:
```bash
curl -X POST http://localhost:8002/api/admin/questions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 문항",
    "stem": "문제 설명",
    "difficulty": "medium",
    "topic": "수학"
  }'
```

---

### PUT /questions/{id}
문항 수정 (부분 업데이트 지원)

**Request Body** (모두 선택적):
```json
{
  "title": "수정된 제목",
  "stem": "수정된 내용",
  "difficulty": "hard",
  "topic": "물리"
}
```

**예시**:
```bash
curl -X PUT http://localhost:8002/api/admin/questions/18899 \
  -H "Content-Type: application/json" \
  -d '{"title": "수정된 제목"}'
```

---

### DELETE /questions/{id}
문항 삭제

**Response**:
```json
{
  "message": "Question deleted successfully",
  "id": 18899
}
```

**예시**:
```bash
curl -X DELETE http://localhost:8002/api/admin/questions/18899
```

---

## Backend 코드 구조

### app/core/database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

DATABASE_URL = "postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/api/questions.py - 주요 로직

**검색 쿼리 (ID 숫자 vs 텍스트)**:
```python
if q:
    try:
        q_int = int(q)
        where_clauses.append("(id = :q_int OR title ILIKE :q OR category ILIKE :q)")
        params["q_int"] = q_int
        params["q"] = f"%{q}%"
    except ValueError:
        where_clauses.append("(title ILIKE :q OR category ILIKE :q)")
        params["q"] = f"%{q}%"
```

**신규 문항 생성 (ID 자동 할당)**:
```python
# 다음 mysql_id 조회
max_id_query = text("""
    SELECT COALESCE(MAX((mysql_metadata->>'mysql_id')::int), 18898) + 1 AS next_id
    FROM problems
    WHERE mysql_metadata ? 'mysql_id'
""")
next_id = db.execute(max_id_query).scalar()

# INSERT with UUID + mysql_id
insert_query = text("""
    INSERT INTO problems (uuid_legacy, title, description, difficulty, category, mysql_metadata, created_at, updated_at)
    VALUES (gen_random_uuid(), :title, :description, :difficulty, :category, 
            jsonb_build_object('mysql_id', :mysql_id), NOW(), NOW())
    RETURNING id, title, description, difficulty, category, created_at, updated_at
""")
```

---

## 트러블슈팅

### 문제 1: TinyMCE 에디터가 사라짐
**원인**: Git에서 파일 손실  
**해결**: Git object에서 복구
```bash
git fsck --lost-found
git cat-file -p <hash> > components/QuestionForm.tsx
```

### 문제 2: Port 충돌
**증상**: Port 3000, 3001, 8000 이미 사용 중  
**해결**: 
- Admin Frontend: Port 3030
- Dev Backend: Port 8002
- Production Backend: Port 8000 (변경 안 함)

### 문제 3: CORS 에러
**증상**: localhost:3030에서 localhost:8000 API 호출 차단  
**해결**: Production backend CORS 설정 추가
```python
# /opt/dreamseed/current/backend/app/main.py
allow_origins=["http://localhost:3030", ...]
```

### 문제 4: PostgreSQL 연결 실패 - psycopg 없음
**증상**: `ModuleNotFoundError: No module named 'psycopg'`  
**해결**:
```bash
cd /home/won/projects/dreamseed_monorepo/backend
source .venv/bin/activate
pip install psycopg psycopg-binary
```

### 문제 5: POST 404 에러
**증상**: 신규 문항 추가 시 404  
**원인**: POST 엔드포인트 미구현  
**해결**: POST /api/admin/questions 엔드포인트 추가

### 문제 6: POST - uuid_legacy NOT NULL 에러
**증상**: `null value in column "uuid_legacy" violates not-null constraint`  
**해결**: `gen_random_uuid()` 사용
```sql
INSERT INTO problems (uuid_legacy, ...) 
VALUES (gen_random_uuid(), ...)
```

### 문제 7: POST - id NOT NULL 에러
**증상**: `null value in column "id" violates not-null constraint`  
**원인**: `id`는 Generated Column, `mysql_metadata->>'mysql_id'` 필요  
**해결**: mysql_id를 jsonb에 포함
```sql
INSERT INTO problems (..., mysql_metadata, ...)
VALUES (..., jsonb_build_object('mysql_id', :mysql_id), ...)
```

### 문제 8: ID 검색 안 됨
**증상**: 검색창에 숫자 입력해도 검색 안 됨  
**원인**: WHERE 절에 id 조건 없음  
**해결**: 숫자는 id 컬럼 검색, 텍스트는 title/category 검색
```python
try:
    q_int = int(q)
    where_clauses.append("(id = :q_int OR title ILIKE :q OR category ILIKE :q)")
except ValueError:
    where_clauses.append("(title ILIKE :q OR category ILIKE :q)")
```

### 문제 9: Class/Grade 표시 안 됨
**증상**: API는 que_class, que_grade 포함하지만 모두 null  
**원인**: PostgreSQL 마이그레이션 시 MySQL의 que_class, que_grade 누락  
**해결**: MySQL → PostgreSQL 동기화
```bash
mysql -u mpcstudy_root -p'2B3Z45J3DACT' mpcstudy_db -N -e \
  "SELECT que_id, COALESCE(que_class,''), COALESCE(que_grade,'') FROM tbl_question;" | \
while IFS=$'\t' read -r id class grade; do
  echo "UPDATE problems SET mysql_metadata = jsonb_set(jsonb_set(mysql_metadata, '{que_class}', '\"$class\"'), '{que_grade}', '\"$grade\"') WHERE (mysql_metadata->>'mysql_id')::int = $id;"
done | PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed -q
```

---

## 자주 사용하는 명령어

### 서비스 재시작
```bash
# Admin Frontend
cd /home/won/projects/dreamseed_monorepo/admin_front
pkill -f "next-server"
npm run dev > /tmp/admin_front.log 2>&1 &

# Dev Backend
cd /home/won/projects/dreamseed_monorepo/backend
pkill -f "uvicorn.*8002"
source .venv/bin/activate
uvicorn main:app --reload --port 8002 > /tmp/backend_dev.log 2>&1 &

# Production Backend (주의!)
sudo kill -HUP 1959  # Graceful reload
# 또는
sudo systemctl restart dreamseed-backend
```

### 로그 모니터링
```bash
# Frontend 로그
tail -f /tmp/admin_front.log

# Backend 로그
tail -f /tmp/backend_dev.log

# Production 로그
sudo journalctl -u dreamseed-backend -f
```

### 데이터베이스 상태 확인
```bash
# PostgreSQL 레코드 수
PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed -c "SELECT COUNT(*) FROM problems;"

# MySQL 레코드 수
mysql -u mpcstudy_root -p'2B3Z45J3DACT' mpcstudy_db -e "SELECT COUNT(*) FROM tbl_question;"

# Class/Grade 동기화 상태
PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed -c \
  "SELECT COUNT(*) as updated FROM problems WHERE mysql_metadata->>'que_class' IS NOT NULL AND mysql_metadata->>'que_class' != '';"
```

### API 테스트
```bash
# 목록 조회
curl "http://localhost:8002/api/admin/questions?page=1&page_size=5"

# ID 검색
curl "http://localhost:8002/api/admin/questions?q=18899"

# 상세 조회
curl "http://localhost:8002/api/admin/questions/18899"

# 생성
curl -X POST http://localhost:8002/api/admin/questions \
  -H "Content-Type: application/json" \
  -d '{"title":"테스트","stem":"내용","difficulty":"medium","topic":"수학"}'

# 수정
curl -X PUT http://localhost:8002/api/admin/questions/18899 \
  -H "Content-Type: application/json" \
  -d '{"title":"수정된 제목"}'

# 삭제
curl -X DELETE http://localhost:8002/api/admin/questions/18899
```

---

## 배포 체크리스트 (Production 반영 시)

### 1. 코드 복사
```bash
# Backend 코드
sudo cp -r /home/won/projects/dreamseed_monorepo/backend/app /opt/dreamseed/current/backend/
sudo chown -R www-data:www-data /opt/dreamseed/current/backend/app
```

### 2. 의존성 설치
```bash
cd /opt/dreamseed/current/backend
sudo -u www-data .venv/bin/pip install psycopg psycopg-binary
```

### 3. 환경 변수 확인
```bash
# Production .env 파일에 DATABASE_URL 추가
sudo vim /opt/dreamseed/current/backend/.env
# DATABASE_URL=postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed
```

### 4. 라우터 등록
```bash
# main.py에 questions router 포함 확인
sudo vim /opt/dreamseed/current/backend/main.py
# from app.api import questions
# app.include_router(questions.router)
```

### 5. 서비스 재시작
```bash
sudo systemctl restart dreamseed-backend
sudo systemctl status dreamseed-backend
```

### 6. Frontend 환경 변수 업데이트
```bash
# admin_front/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000  # Port 8002 → 8000
```

### 7. 테스트
```bash
# Production API 테스트
curl "http://localhost:8000/api/admin/questions?page=1&page_size=5"
```

---

## 참고 자료

### 관련 파일 위치
- **Frontend**: `/home/won/projects/dreamseed_monorepo/admin_front`
- **Backend Dev**: `/home/won/projects/dreamseed_monorepo/backend`
- **Backend Prod**: `/opt/dreamseed/current/backend`
- **MySQL 덤프**: `/home/won/projects/dreamseed_monorepo/mpcstudy_db.sql`
- **문서**: `/home/won/projects/dreamseed_monorepo/README_*.md`

### Git 브랜치
- Current: `hotfix/ci-remove-prepare-deployment`
- Repository: `dreamseedai/dreamseed_monorepo`

### 작업 이력
- 2025-11-15: TinyMCE 복구, PostgreSQL 연동, CRUD API 구현, Class/Grade 동기화

---

## 연락처 및 지원
- 문제 발생 시 이 문서의 "트러블슈팅" 섹션 참조
- 로그 파일: `/tmp/backend_dev.log`, `/tmp/admin_front.log`
- PostgreSQL 비밀번호 분실 시: `DreamSeedAi0908` (절대 잊지 말 것!)
