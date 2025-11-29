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
- **포트**: `3030` (기본), `3031` (충돌 시 대체)
- **URL**: 
  - http://localhost:3030/questions
  - http://localhost:3031/questions (대체)
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

# Port 충돌 시
npm run dev -- -p 3031 > /tmp/admin_front_3031.log 2>&1 &
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
    mysql_metadata  jsonb       DEFAULT '{}',                -- MySQL 마이그레이션 메타데이터 + 확장 필드
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
    "mysql_id": "1",                  // 원본 MySQL que_id
    "que_class": "M",                 // 과목 (M=수학, P=물리, C=화학 등)
    "que_grade": "G11",               // 학년 (G10, G11, G12 등)
    
    // 확장 필드 (PostgreSQL에 컬럼 없음)
    "explanation": "해설 내용",        // 문제 해설
    "hint": "힌트 내용",               // 힌트
    "resource": "참고 자료",           // 참고 자료
    "answer_text": "정답 서술",        // 정답 설명
    "options": ["보기1", "보기2", "보기3", "보기4"],  // 선택지 배열
    "answer": 0,                       // 정답 인덱스 (0-based)
    "tags": ["태그1", "태그2"]          // 태그 배열
}
```

**중요**: `mysql_metadata`는 PostgreSQL 스키마를 변경하지 않고 추가 필드를 저장하는 유연한 방법입니다. 새로운 필드가 필요하면 JSONB에 추가하세요.

#### PostgreSQL 접속 정보
- **호스트**: `127.0.0.1:5432`
- **데이터베이스**: `dreamseed`
- **사용자**: `postgres`
- **비밀번호**: `DreamSeedAi0908`

#### PostgreSQL 접속 명령어
```bash
# 비밀번호를 환경변수로 전달
PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed

# 또는 비밀번호 프롬프트 방식
psql -h 127.0.0.1 -U postgres -d dreamseed
# Password: DreamSeedAi0908 입력
```

#### SQLAlchemy 연결 URL
```
postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed
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
- **호스트**: `localhost` (unix socket 사용)
- **데이터베이스**: `mpcstudy_db`
- **사용자**: `mpcstudy_root`
- **비밀번호**: `2B3Z45J3DACT` ✅ (검증됨)
- **비밀번호 옵션** (하나가 안 되면 다른 것 시도):
  - `2B3Z45J3DACT` ← 실제 작동하는 비밀번호
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
# 비밀번호와 함께 접속 (검증된 방법)
mysql -u mpcstudy_root -p'2B3Z45J3DACT'

# 데이터베이스 선택
USE mpcstudy_db;

# 테이블 목록 확인
SHOW TABLES;

# tbl_question 구조 확인
DESCRIBE tbl_question;

# 데이터 확인
SELECT que_id, que_en_title, LENGTH(que_en_solution) as solution_length 
FROM tbl_question 
LIMIT 5;
```

#### Python에서 MySQL 접속
```python
import pymysql

# Unix socket으로 접속 (권장)
connection = pymysql.connect(
    unix_socket='/var/run/mysqld/mysqld.sock',  # 또는 /tmp/mysql.sock
    user='mpcstudy_root',
    password='2B3Z45J3DACT',
    database='mpcstudy_db',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 또는 TCP/IP로 접속
connection = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='mpcstudy_root',
    password='2B3Z45J3DACT',
    database='mpcstudy_db',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
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
  "explanation": "해설 내용입니다",
  "hint": "힌트 내용",
  "resource": "참고 자료",
  "answer_text": "정답 서술",
  "options": ["보기1", "보기2", "보기3", "보기4"],
  "answer": 1,
  "tags": ["태그1", "태그2"],
  "created_at": "2025-11-16T10:37:32.541073-05:00",
  "updated_at": "2025-11-16T10:51:44.101824-05:00"
}
```

**예시**:
```bash
curl "http://localhost:8002/api/admin/questions/18899"
```

---

### POST /questions
새 문항 생성

**Request Body** (필수 필드):
```json
{
  "title": "신규 문항 제목",
  "stem": "문제 내용",
  "difficulty": "medium",
  "topic": "수학",
  "explanation": "해설 내용",
  "hint": "힌트",
  "resource": "참고 자료",
  "answer_text": "정답 서술",
  "options": ["보기1", "보기2", "보기3", "보기4"],
  "answer": 0,
  "tags": ["태그1"]
}
```

**Response**: GET /questions/{id}와 동일

**중요**: 
- `uuid_legacy`는 `gen_random_uuid()`로 자동 생성
- `mysql_metadata->>'mysql_id'`는 기존 최대값 + 1로 자동 할당
- `id`는 Generated Column으로 자동 생성
- `explanation`, `hint`, `resource`, `answer_text`, `options`, `answer`, `tags`는 `mysql_metadata` JSONB에 저장

**예시**:
```bash
curl -X POST http://localhost:8002/api/admin/questions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 문항",
    "stem": "문제 설명",
    "difficulty": "medium",
    "topic": "수학",
    "explanation": "해설",
    "options": ["A", "B", "C", "D"],
    "answer": 0
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
  "topic": "물리",
  "explanation": "수정된 해설",
  "hint": "수정된 힌트",
  "resource": "새 자료",
  "answer_text": "새 정답 서술",
  "options": ["새 보기1", "새 보기2"],
  "answer": 1,
  "tags": ["새 태그"]
}
```

**중요**:
- 기본 필드(title, stem, difficulty, topic)는 `problems` 테이블 컬럼에 저장
- 확장 필드(explanation, hint, options, answer 등)는 `mysql_metadata` JSONB에 병합 저장
- `mysql_metadata || CAST(:metadata AS jsonb)` 사용하여 기존 데이터 유지하면서 업데이트

**예시**:
```bash
# 제목만 수정
curl -X PUT http://localhost:8002/api/admin/questions/18899 \
  -H "Content-Type: application/json" \
  -d '{"title": "수정된 제목"}'

# 여러 필드 동시 수정
curl -X PUT http://localhost:8002/api/admin/questions/18899 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "수정된 제목",
    "explanation": "수정된 해설",
    "options": ["A", "B", "C", "D"],
    "answer": 2
  }'
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
**증상**: localhost:3030 또는 localhost:3031에서 localhost:8002 API 호출 차단  
**해결**: Backend CORS 설정에 모든 개발 포트 추가
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5172",
        "http://localhost:3030", 
        "http://localhost:3031"  # Port 충돌 시 대체 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**검증**:
```bash
curl -I -H "Origin: http://localhost:3031" http://localhost:8002/api/admin/questions/18899 | grep access-control
# access-control-allow-origin: http://localhost:3031 출력 확인
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

### 문제 10: DELETE 버튼 작동 안 함 (Port 3031)
**증상**: 삭제 버튼 클릭해도 반응 없음, CORS 에러  
**원인**: localhost:3031이 CORS allow_origins에 없음  
**해결**: 문제 3 참조 - CORS 설정에 3031 추가

### 문제 11: 삭제 후 Undo UI 크래시
**증상**: `Cannot read properties of undefined (reading 'slice')`  
**원인**: Backend가 `stem` 필드를 반환하지 않아 `undo.prev.stem.slice()` 실패  
**해결**: QuestionsClient.tsx 수정
```tsx
// Before
<span>삭제됨: {undo.prev.stem.slice(0, 30)}...</span>

// After
<span>삭제됨: {(undo.prev.stem || undo.prev.title || '제목 없음').slice(0, 30)}...</span>
```

### 문제 12: 편집 페이지에서 해설/보기/힌트 저장 안 됨
**증상**: http://localhost:3031/questions/18899/edit 에서 explanation, options, hint, resource, answer_text 저장하면 사라짐  
**원인**: 
- Backend `QuestionUpdate` Pydantic 모델에 확장 필드 없음
- PUT 엔드포인트가 title, stem, difficulty, topic만 처리
- PostgreSQL `problems` 테이블에 확장 필드 컬럼 없음

**해결** (2025-11-16):
1. `QuestionCreate`와 `QuestionUpdate` 모델에 모든 필드 추가
```python
class QuestionCreate(BaseModel):
    title: str
    stem: str = ""
    difficulty: str = "1"
    topic: str = "수학"
    explanation: str = ""
    hint: str = ""
    resource: str = ""
    answer_text: str = ""
    options: List[str] = []
    answer: int = 0
    tags: List[str] = []

class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    stem: Optional[str] = None
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    resource: Optional[str] = None
    answer_text: Optional[str] = None
    options: Optional[List[str]] = None
    answer: Optional[int] = None
    tags: Optional[List[str]] = None
```

2. POST 엔드포인트 - mysql_metadata에 확장 필드 저장
```python
metadata = {
    'mysql_id': next_id,
    'explanation': data.explanation or '',
    'hint': data.hint or '',
    'resource': data.resource or '',
    'answer_text': data.answer_text or '',
    'options': data.options or [],
    'answer': data.answer if data.answer is not None else 0,
    'tags': data.tags or []
}

insert_query = text("""
    INSERT INTO problems (..., mysql_metadata, ...)
    VALUES (..., :metadata::jsonb, ...)
    RETURNING id, title, description, difficulty, category, mysql_metadata, created_at, updated_at
""")
```

3. PUT 엔드포인트 - JSONB 병합 업데이트
```python
metadata_fields = {}
if data.explanation is not None:
    metadata_fields['explanation'] = data.explanation
# ... 다른 필드들

if metadata_fields:
    import json
    updates.append("mysql_metadata = mysql_metadata || CAST(:metadata AS jsonb)")
    params["metadata"] = json.dumps(metadata_fields)
```

4. GET 엔드포인트 - mysql_metadata에서 필드 추출
```python
metadata = result[5] or {}

return {
    "id": result[0],
    "title": result[1],
    "stem": result[2] or "",
    "difficulty": result[3],
    "topic": result[4],
    "explanation": metadata.get('explanation', ''),
    "hint": metadata.get('hint', ''),
    "resource": metadata.get('resource', ''),
    "answer_text": metadata.get('answer_text', ''),
    "options": metadata.get('options', []),
    "answer": metadata.get('answer', 0),
    "tags": metadata.get('tags', []),
    "created_at": result[6].isoformat() if result[6] else None,
    "updated_at": result[7].isoformat() if result[7] else None
}
```

**검증**:
```bash
# 모든 필드 포함하여 업데이트
curl -X PUT http://localhost:8002/api/admin/questions/18899 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 제목",
    "stem": "본문",
    "explanation": "해설 내용",
    "hint": "힌트",
    "options": ["보기1", "보기2", "보기3", "보기4"],
    "answer": 1
  }'

# 저장 확인
curl http://localhost:8002/api/admin/questions/18899 | python3 -m json.tool
```

### 문제 13: 편집 페이지에서 해설(explanation) 로드 안 됨
**증상**: http://localhost:3031/questions/13164/edit 에서 해설(Solution)이 비어있음  
**원인**: 
- PostgreSQL 마이그레이션 시 MySQL의 `que_en_solution` 필드가 `mysql_metadata->>'explanation'`으로 복사되지 않음
- MySQL `tbl_question.que_en_solution`에는 데이터가 있지만 PostgreSQL `problems.mysql_metadata->>'explanation'`은 비어있음
- 18,855개 레코드가 동일한 문제

**해결** (2025-11-17):

**1단계: 백필 스크립트 생성**
```bash
# scripts/backfill_explanation.py 생성
# MySQL tbl_question.que_en_solution → PostgreSQL problems.mysql_metadata->>'explanation'
```

**2단계: 필요한 패키지 설치**
```bash
cd /home/won/projects/dreamseed_monorepo
source .venv/bin/activate
pip install pymysql psycopg psycopg-binary
```

**3단계: Dry-run으로 확인**
```bash
# 전체 대상 확인
python scripts/backfill_explanation.py

# 10개만 확인
python scripts/backfill_explanation.py --limit 10
```

**4단계: 실제 백필 실행**
```bash
# 전체 실행 (자동 백업 포함)
python scripts/backfill_explanation.py --execute

# 결과:
# ✓ 18,855개 레코드 성공적으로 업데이트
# ✓ 백업: /tmp/problems_backup_20251117_212845.sql
# ✓ 트랜잭션으로 안전하게 실행 (실패 시 자동 rollback)
```

**백필 스크립트 주요 기능**:
- MySQL과 PostgreSQL 간 `mysql_id` 기준으로 조인
- `explanation`이 비어있고 `que_en_solution`에 데이터가 있는 레코드만 처리
- `pg_dump`로 자동 백업 생성
- 트랜잭션으로 안전하게 실행
- 100개마다 진행률 표시
- 완료 후 랜덤 샘플 검증

**검증**:
```bash
# 특정 ID 확인
curl -s "http://localhost:8002/api/admin/questions/13164" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); \
  print(f'ID: {d[\"id\"]}\nExplanation length: {len(d[\"explanation\"])} chars')"

# 결과: Explanation length: 8892 chars (성공!)
```

**스크립트 사용법**:
```bash
# Dry-run (어떤 변경이 일어날지만 확인)
python scripts/backfill_explanation.py

# 실제 실행
python scripts/backfill_explanation.py --execute

# 제한된 개수만 실행
python scripts/backfill_explanation.py --execute --limit 1000

# 백업 없이 실행 (권장하지 않음)
python scripts/backfill_explanation.py --execute --skip-backup

# 도움말
python scripts/backfill_explanation.py --help
```

**백업 복원 방법** (문제 발생 시):
```bash
# 백업 파일 확인
ls -lh /tmp/problems_backup_*.sql

# 복원
PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed < /tmp/problems_backup_20251117_212845.sql
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
- **2025-11-15**: 
  - TinyMCE 복구 (Git object에서)
  - PostgreSQL 연동 (psycopg 3.2.12)
  - CRUD API 구현
  - Class/Grade 동기화 (18,898개)
  
- **2025-11-16**: 
  - Port 3031 CORS 추가
  - DELETE 기능 검증 및 Undo UI 수정
  - 확장 필드 저장 구현 (explanation, hint, options, answer, resource, answer_text, tags)
  - mysql_metadata JSONB를 활용한 스키마리스 필드 저장
  - QuestionCreate/QuestionUpdate Pydantic 모델 확장
  - POST/PUT/GET 엔드포인트에서 모든 필드 처리
  
- **2025-11-17**:
  - MySQL `que_en_solution` → PostgreSQL `explanation` 백필 (18,855개)
  - `scripts/backfill_explanation.py` 생성
  - pymysql + psycopg 통합 스크립트
  - 자동 백업 + 트랜잭션 + 검증 로직 구현
  - 모든 문항의 해설(Solution) 데이터 복구 완료

---

## 핵심 정보 요약 (빠른 복구용)

### 데이터베이스 접속 정보
```bash
# PostgreSQL
PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed

# MySQL
mysql -u mpcstudy_root -p'2B3Z45J3DACT' mpcstudy_db
```

### 서비스 시작
```bash
# Admin Frontend (Port 3031)
cd /home/won/projects/dreamseed_monorepo/admin_front
npm run dev -- -p 3031 > /tmp/admin_front_3031.log 2>&1 &

# Backend Dev (Port 8002)
cd /home/won/projects/dreamseed_monorepo/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8002 > /tmp/backend_dev_8002.log 2>&1 &

# 확인
lsof -ti:3031  # Frontend
lsof -ti:8002  # Backend
```

### 주요 URL
- **Admin Frontend**: http://localhost:3031/questions
- **Backend API**: http://localhost:8002/api/admin/questions
- **API Docs**: http://localhost:8002/docs

### 필수 스크립트
```bash
# MySQL → PostgreSQL 해설 백필 (한 번만 실행)
python scripts/backfill_explanation.py --execute

# Class/Grade 동기화
mysql -u mpcstudy_root -p'2B3Z45J3DACT' mpcstudy_db -N -e \
  "SELECT que_id, COALESCE(que_class,''), COALESCE(que_grade,'') FROM tbl_question;" | \
while IFS=$'\t' read -r id class grade; do
  echo "UPDATE problems SET mysql_metadata = jsonb_set(jsonb_set(mysql_metadata, '{que_class}', '\"$class\"'), '{que_grade}', '\"$grade\"') WHERE (mysql_metadata->>'mysql_id')::int = $id;"
done | PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed -q
```

### 백업 및 복원
```bash
# PostgreSQL 백업
pg_dump -h 127.0.0.1 -U postgres -d dreamseed -t problems -f /tmp/problems_backup_$(date +%Y%m%d_%H%M%S).sql

# PostgreSQL 복원
PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed < /tmp/problems_backup_YYYYMMDD_HHMMSS.sql

# MySQL 백업
mysqldump -u mpcstudy_root -p'2B3Z45J3DACT' mpcstudy_db tbl_question > /tmp/tbl_question_backup_$(date +%Y%m%d_%H%M%S).sql
```

## 연락처 및 지원
- 문제 발생 시 이 문서의 "트러블슈팅" 섹션 참조
- 로그 파일: `/tmp/backend_dev_8002.log`, `/tmp/admin_front_3031.log`
- PostgreSQL 비밀번호: `DreamSeedAi0908`
- MySQL 비밀번호: `2B3Z45J3DACT`
_______________________________________________________________________

## Appendix: Editor Data Pipeline & Root Cause Analysis (v1.0)

아래는 DreamSeedAI Editor 시스템에서 explanation / hint / resource / answer_text가 DB → API → Pydantic → FastAPI Response → Frontend → Editor로 흐르는 파이프라인을 파일 경로와 정확한 필드명 중심으로 재구성한 것입니다. 이어서 “Editor에서 explanation이 로드되지 않는” 문제를 가장 가능성 높은 순서로 5가지 후보와 검증 절차를 제시합니다. 수정은 하지 않고 분석만 제공합니다.

1) End-to-end 파이프라인 구조(필드: explanation, hint, resource, answer_text)

- DB (PostgreSQL)
  - 테이블/컬럼:
    - problems.title (문자열)
    - problems.description (= stem)
    - problems.category (= topic)
    - problems.mysql_metadata JSONB
      - keys: explanation, hint, resource(단수), answer_text, options, answer, tags, que_class, que_grade, mysql_id 등
  - 주의:
    - explanation은 MySQL의 que_en_solution이 매핑된 필드
    - resource는 복수형(resources)이 아님

- API/Backend (FastAPI + SQLAlchemy)
  - 파일: /home/won/projects/dreamseed_monorepo/backend/app/api/questions.py
  - GET /api/admin/questions/{id}
    - DB에서 title/description/category/mysql_metadata 등을 SELECT
    - mysql_metadata를 dict로 파싱 후 아래 필드를 꺼내 응답에 포함
      - "explanation": metadata.get("explanation", "")
      - "hint": metadata.get("hint", "")
      - "resource": metadata.get("resource", "")
      - "answer_text": metadata.get("answer_text", "")
    - 목록(GET /questions) 응답에는 위 4개 필드가 포함되지 않음
  - POST /api/admin/questions
    - Request Body에 포함된 explanation/hint/resource/answer_text를 mysql_metadata에 저장
  - PUT /api/admin/questions/{id}
    - Request Body에서 전달된 필드만 반영
    - 확장 필드(explanation/hint/resource/answer_text)는 mysql_metadata = mysql_metadata || :metadata 병합 업데이트

- Pydantic 모델 (Request Body 스키마)
  - 파일: /home/won/projects/dreamseed_monorepo/backend/app/api/questions.py
  - QuestionCreate
    - explanation: str = ""
    - hint: str = ""
    - resource: str = ""
    - answer_text: str = ""
  - QuestionUpdate
    - explanation: Optional[str] = None
    - hint: Optional[str] = None
    - resource: Optional[str] = None
    - answer_text: Optional[str] = None
  - 동작 규칙:
    - POST는 기본값이 빈 문자열("")로 저장될 수 있음
    - PUT은 None이 아닌 항목만 업데이트(키 생략 시 변경 없음)

- FastAPI Response (상세 조회에 한정)
  - 파일: /home/won/projects/dreamseed_monorepo/backend/app/api/questions.py
  - GET /questions/{id} 응답 JSON
    - explanation, hint, resource, answer_text 포함
  - GET /questions (목록)
    - 포함 안 됨

- Frontend (Next.js)
  - API 클라이언트: /home/won/projects/dreamseed_monorepo/admin_front/lib/questions.ts
    - getQuestion(id): /api/admin/questions/{id} 호출, 응답을 그대로 반환(여기에 explanation/hint/resource/answer_text 포함)
  - 편집 페이지: /home/won/projects/dreamseed_monorepo/admin_front/app/questions/[id]/edit/page.tsx
    - getQuestion 결과를 받아 QuestionForm 컴포넌트에 props로 전달
  - 폼 컴포넌트: /home/won/projects/dreamseed_monorepo/admin_front/components/QuestionForm.tsx
    - props.question.explanation 등으로 폼 상태를 초기화
    - 각 필드를 Editor에 바인딩
  - Editor 래퍼: /home/won/projects/dreamseed_monorepo/admin_front/components/RichTextEditor.tsx
    - TinyMCE 4.9.11
    - value 또는 initialValue 형태로 문자열을 받아 표시
    - 비동기 로딩 시 value 변화가 setContent로 반영되도록 구현되어 있어야 함

- 환경 변수/엔드포인트
  - 파일: /home/won/projects/dreamseed_monorepo/admin_front/.env.local
    - NEXT_PUBLIC_API_BASE_URL=http://localhost:8002
    - NEXT_PUBLIC_API_PREFIX=/api/admin
  - 잘못된 BASE_URL/포트(예: 8000) 또는 목록 API를 상세로 오인 호출 시 상세 필드 미포함

2) Editor에서 explanation이 로드되지 않는 원인 후보 Top 5(검증 절차 포함)

1. Backend 상세 조회 응답에 explanation이 포함되지 않음(컬럼/인덱스/파싱 문제)
- 개연성:
  - questions.py에서 SELECT 결과 컬럼 순서가 바뀌었거나 mysql_metadata 인덱싱(result[5] 등)이 틀어지면 metadata 파싱 실패로 explanation 누락 가능
  - 문제 12 해결 전/후 코드 혼재 시 응답에 확장 필드를 넣지 않는 경로가 남아있을 수 있음
- 검증:
  - 브라우저 DevTools Network → GET /api/admin/questions/{id} 응답 JSON에 "explanation" 키 존재/값 확인
  - curl로 재현: curl http://localhost:8002/api/admin/questions/18899 | python3 -m json.tool
  - backend 로그 확인: /tmp/backend_dev_8002.log에서 해당 요청 처리 시 mysql_metadata dict 파싱이 정상인지 점검

2. Frontend 바인딩/명칭 불일치(“solution” vs “explanation”) 또는 prop 전달 누락
- 개연성:
  - UI 레이블이 “Solution”이라 내부 변수명을 solution으로 사용했다면 실제 API 키 explanation과 불일치
  - QuestionForm.tsx에서 RichTextEditor로 전달하는 prop 이름(value/initialValue)이 다른 필드에 연결되었을 수 있음
- 검증:
  - /admin_front/components/QuestionForm.tsx에서 Editor에 전달하는 prop가 question.explanation인지 확인(읽기 흐름만 점검)
  - /admin_front/components/RichTextEditor.tsx가 받는 prop 인터페이스와 사용하는 값이 동일한지 확인
  - 렌더 직전 콘솔 로깅으로 props.question.explanation 값이 존재하는지 확인

3. TinyMCE 래퍼 비동기 반영 불가(initialValue만 사용, value 변화 미반영)
- 개연성:
  - getQuestion가 비동기로 데이터를 받아온 뒤 폼 상태가 갱신되지만, RichTextEditor가 initialValue만 사용하고 value 변경 시 setContent를 호출하지 않으면 빈 상태 유지
  - TinyMCE 초기화 타이밍과 상태 업데이트 타이밍 경합으로 표시 실패
- 검증:
  - /admin_front/components/RichTextEditor.tsx에서 value 변경(useEffect 등) 시 editor.setContent(...)가 호출되는지 시나리오 확인
  - 편집 페이지 최초 렌더 때는 빈값 → fetch 완료 후 상태가 채워져도 에디터 내용이 갱신되는지 관찰
  - 동일 폼에서 stem(=description) 등 다른 에디터 필드는 정상 반영되는지 비교

4. 잘못된 API 호출/환경 구성(상세 대신 목록 호출, BASE_URL/포트 오설정, 구 프로덕션으로 호출)
- 개연성:
  - 목록 API(GET /questions)는 explanation을 포함하지 않으므로 이를 상세로 오인 사용하면 빈값
  - .env.local에서 NEXT_PUBLIC_API_BASE_URL이 8000(구 프로덕션 Mock)으로 설정되어 상세 필드가 누락된 응답을 수신할 수 있음
- 검증:
  - DevTools Network에서 실제 호출 URL이 정확히 http://localhost:8002/api/admin/questions/{id}인지 확인
  - 응답 JSON에 explanation 키 유무 확인
  - CORS/포트 매칭(3030/3031 ↔ 8002) 확인

5. DB에 실제 값이 없음(마이그레이션 누락 또는 해당 문항의 공백 데이터)
- 개연성:
  - 해당 문제 ID의 mysql_metadata.explanation 값이 NULL 또는 ""이면 UI에서는 “로딩 안 됨”으로 인지될 수 있음
- 검증:
  - psql로 직접 조회:
    - SELECT mysql_metadata->>'explanation' FROM problems WHERE id = <문제ID>;
  - 값이 NULL/""인지 확인
  - 다른 필드(hint/resource/answer_text) 유무도 함께 확인하여 특정 필드만 공백인지 구분

권장 점검 순서(효율적 진단)
- 1단계: 네트워크 응답 확인 → GET /questions/{id} JSON에 "explanation" 존재/값 확인(후보 1, 4 식별)
- 2단계: 프론트 바인딩/명칭 확인 → QuestionForm.tsx ↔ RichTextEditor.tsx prop 연결과 키 이름(explanation) 일치 여부(후보 2)
- 3단계: TinyMCE 반영 시나리오 확인 → 비동기 상태 변경 시 setContent 적용 여부(후보 3)
- 4단계: DB 값 점검 → 실제 값 부재인지 최종 확인(후보 5)

참고 파일 경로 요약
- Backend
  - /home/won/projects/dreamseed_monorepo/backend/app/api/questions.py
  - /home/won/projects/dreamseed_monorepo/backend/app/core/database.py
  - /home/won/projects/dreamseed_monorepo/backend/main.py
- Frontend
  - /home/won/projects/dreamseed_monorepo/admin_front/lib/questions.ts
  - /home/won/projects/dreamseed_monorepo/admin_front/app/questions/[id]/edit/page.tsx
  - /home/won/projects/dreamseed_monorepo/admin_front/components/QuestionForm.tsx
  - /home/won/projects/dreamseed_monorepo/admin_front/components/RichTextEditor.tsx
  - /home/won/projects/dreamseed_monorepo/admin_front/.env.local

핵심 주의
- UI 라벨 “Solution”은 실제 키 explanation이다.
- resource는 단수. resources로 잘못 쓰면 저장/로드 모두 누락된다.
- 목록 API에는 확장 필드가 없다 → 편집 화면은 반드시 GET /questions/{id} 상세를 사용해야 한다.
_______________________________________________________________________________

  - name: "/editor-root-cause"
    prompt: |
      너는 DreamSeedAI Editor 시스템의 문제 원인을 추적하는 전문가다.
      특히 explanation / hint / resource / answer_text 필드가
      DB → API → Pydantic → FastAPI Response → Frontend → Editor(TinyMCE)
      로 흐르는 파이프라인에 대해 잘 알고 있다.

      참고 문서:
      - ADMIN_QUESTIONS_SETUP.md 맨 아래의 파이프라인/원인 분석 섹션
      - 해당 문서에 정리된 Top 5 원인 후보와 파일 경로

      현재 목표:
      - "Editor에서 explanation(=Solution)이 로드되지 않는" 문제의 root cause를 찾는 것이다.
      - 코드는 수정하지 말고, 분석만 수행하라.

      네가 할 일:
      1) ADMIN_QUESTIONS_SETUP.md 에 정리된 파이프라인을 기반으로,
         DB→API→Pydantic→Response→Frontend→Editor 전체 흐름을 다시 한 번 요약해라.
      2) 현재 레포의 실제 코드(backend/app/api/questions.py, 
         admin_front/lib/questions.ts, 
         admin_front/components/QuestionForm.tsx, 
         admin_front/components/RichTextEditor.tsx 등)를 살펴보고,
         Top 5 원인 후보 중 무엇이 가장 유력한지 우선순위를 매겨라.
      3) 각 원인 후보마다:
         - 확인해야 할 파일 경로
         - 확인해야 할 코드 위치(가능하면 함수/컴포넌트/라인 근처)
         - GitLens로 Line History/File History를 어떻게 확인해야 하는지
         를 구체적으로 적어라.
      4) 수정 코드는 절대 제안하지 말고,
         "여기를 고치면 될 것 같다" 수준의 설명만 제공하라.
      5) 최종적으로, 사람이 따라갈 수 있는
         "점검 순서 체크리스트(1→2→3→4)"를 만들어라.
______________________________________________________________________)

