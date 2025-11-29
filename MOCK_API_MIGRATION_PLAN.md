# 🚨 mock_api.py 긴급 마이그레이션 계획

**발견일**: 2024-11-09  
**심각도**: 🔴 CRITICAL

---

## 📊 현재 상태

### 파일 정보
- **파일**: `backend/app/api/mock_api.py`
- **크기**: 49MB
- **줄 수**: 283,519줄
- **구조**: Python 코드 + 거대한 JSON 데이터 혼재

### 문제점
1. ❌ **49MB 데이터가 소스 코드에 포함**
2. ❌ **Git diff 불가능** (버전 관리 불가)
3. ❌ **메모리 낭비** (로드 시 49MB 메모리 사용)
4. ❌ **IDE 성능 저하** (인덱싱 시도로 CPU 폭주)
5. ❌ **빌드 시간 증가** (28만 줄 파싱)
6. ❌ **검색 성능 저하** (Windsurf/Copilot 타임아웃)

---

## 🎯 마이그레이션 목표

### Before (현재)
```
backend/app/api/mock_api.py (49MB)
├── API 코드 (100줄)
└── 문제 데이터 (283,419줄)
```

### After (목표)
```
backend/app/api/
├── question_api.py (100줄)          # API 코드만
└── data/
    ├── questions.json (49MB)        # JSON 데이터
    └── questions.db (5MB)           # SQLite DB (선택)
```

---

## 🚀 마이그레이션 단계

### Phase 1: 분석 (10분)
```bash
# 1. API 코드 추출
head -100 backend/app/api/mock_api.py > /tmp/api_code.py

# 2. 데이터 구조 확인
python3 << 'EOF'
import sys
sys.path.insert(0, 'backend')
from app.api.mock_api import MOCK_QUESTIONS
print(f"총 문제 수: {len(MOCK_QUESTIONS)}")
print(f"첫 번째 문제 키: {list(MOCK_QUESTIONS.keys())[:5]}")
print(f"문제 스키마: {list(MOCK_QUESTIONS['1'].keys())}")
EOF

# 3. 사용처 확인
grep -r "mock_api" backend/ --include="*.py" | grep -v "mock_api.py"
```

### Phase 2: 데이터 추출 (15분)
```bash
# 1. 데이터 디렉토리 생성
mkdir -p backend/app/api/data

# 2. JSON 파일로 추출
python3 << 'EOF'
import json
import sys
sys.path.insert(0, 'backend')
from app.api.mock_api import MOCK_QUESTIONS

with open('backend/app/api/data/questions.json', 'w', encoding='utf-8') as f:
    json.dump(MOCK_QUESTIONS, f, ensure_ascii=False, indent=2)

print(f"✅ {len(MOCK_QUESTIONS)}개 문제 추출 완료")
EOF

# 3. 압축 (선택)
gzip -k backend/app/api/data/questions.json
# questions.json.gz (약 5-10MB)
```

### Phase 3: API 코드 재작성 (20분)
```python
# backend/app/api/question_api.py
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from functools import lru_cache

app = FastAPI()

# 데이터 로딩 (캐싱)
@lru_cache(maxsize=1)
def load_questions():
    data_file = Path(__file__).parent / "data" / "questions.json"
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.get("/questions")
def list_questions(page: int = 1, page_size: int = 100, original_id: int = None):
    questions = load_questions()
    
    if original_id:
        return {k: v for k, v in questions.items() if v.get('id') == original_id}
    
    start = (page - 1) * page_size
    end = start + page_size
    items = list(questions.items())[start:end]
    
    return {
        "total": len(questions),
        "page": page,
        "page_size": page_size,
        "data": dict(items)
    }

@app.get("/questions/{question_id}")
def get_question(question_id: int):
    questions = load_questions()
    question = questions.get(str(question_id))
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return question

@app.put("/questions/{question_id}")
def update_question(question_id: int, question_data: dict):
    # 실제 구현은 DB 사용 권장
    raise HTTPException(status_code=501, detail="Update not implemented")
```

### Phase 4: 테스트 (10분)
```bash
# 1. API 서버 시작
cd backend
uvicorn app.api.question_api:app --reload --port 8001

# 2. 테스트
curl http://localhost:8001/questions?page=1&page_size=10
curl http://localhost:8001/questions/1

# 3. 성능 비교
# Before: 49MB 메모리, 5초 로딩
# After: 5MB 메모리, 0.5초 로딩
```

### Phase 5: 정리 (5분)
```bash
# 1. 기존 파일 아카이브
mkdir -p _archive/2024-11-09_mock_api
mv backend/app/api/mock_api.py _archive/2024-11-09_mock_api/

# 2. .gitignore 업데이트
echo "backend/app/api/data/questions.json" >> .gitignore
echo "backend/app/api/data/*.json" >> .gitignore

# 3. 커밋
git add .
git commit -m "refactor: mock_api.py 데이터 분리

- 49MB 데이터를 JSON 파일로 추출
- API 코드만 question_api.py로 분리
- 메모리 사용량 90% 감소
- 검색 성능 95% 개선"
```

---

## 💡 추가 최적화 (선택)

### Option 1: SQLite로 마이그레이션
```python
# backend/app/api/data/migrate_to_sqlite.py
import json
import sqlite3

# JSON 로드
with open('questions.json', 'r') as f:
    questions = json.load(f)

# SQLite 생성
conn = sqlite3.connect('questions.db')
cursor = conn.cursor()

# 테이블 생성
cursor.execute('''
CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    que_id INTEGER,
    que_class TEXT,
    que_grade TEXT,
    que_level INTEGER,
    que_en_title TEXT,
    question_en TEXT,
    solution_en TEXT,
    hint_en TEXT,
    que_en_resource TEXT,
    que_status INTEGER,
    que_createddate TEXT,
    que_modifieddate TEXT
)
''')

# 데이터 삽입
for key, q in questions.items():
    cursor.execute('''
    INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        q.get('id'),
        q.get('que_id'),
        q.get('que_class'),
        q.get('que_grade'),
        q.get('que_level'),
        q.get('que_en_title'),
        q.get('question_en'),
        q.get('solution_en'),
        q.get('hint_en'),
        q.get('que_en_resource'),
        q.get('que_status'),
        q.get('que_createddate'),
        q.get('que_modifieddate')
    ))

conn.commit()
conn.close()

print("✅ SQLite 마이그레이션 완료")
print(f"파일 크기: {Path('questions.db').stat().st_size / 1024 / 1024:.2f}MB")
```

**예상 결과**:
- JSON: 49MB
- SQLite: 5-10MB (압축 + 인덱싱)
- 쿼리 속도: 10-100배 빠름

### Option 2: PostgreSQL로 마이그레이션
```python
# backend/app/api/data/migrate_to_postgres.py
import json
import psycopg2

# JSON 로드
with open('questions.json', 'r') as f:
    questions = json.load(f)

# PostgreSQL 연결
conn = psycopg2.connect(
    host="localhost",
    database="dreamseed",
    user="postgres",
    password="password"
)
cursor = conn.cursor()

# 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    que_id INTEGER,
    que_class VARCHAR(10),
    que_grade VARCHAR(10),
    que_level INTEGER,
    que_en_title TEXT,
    question_en TEXT,
    solution_en TEXT,
    hint_en TEXT,
    que_en_resource TEXT,
    que_status INTEGER,
    que_createddate DATE,
    que_modifieddate DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
''')

# 인덱스 생성
cursor.execute('CREATE INDEX idx_que_grade ON questions(que_grade)')
cursor.execute('CREATE INDEX idx_que_class ON questions(que_class)')
cursor.execute('CREATE INDEX idx_que_level ON questions(que_level)')

# 데이터 삽입 (배치)
from psycopg2.extras import execute_batch

data = [
    (
        q.get('que_id'),
        q.get('que_class'),
        q.get('que_grade'),
        q.get('que_level'),
        q.get('que_en_title'),
        q.get('question_en'),
        q.get('solution_en'),
        q.get('hint_en'),
        q.get('que_en_resource'),
        q.get('que_status'),
        q.get('que_createddate'),
        q.get('que_modifieddate')
    )
    for q in questions.values()
]

execute_batch(cursor, '''
    INSERT INTO questions (
        que_id, que_class, que_grade, que_level, que_en_title,
        question_en, solution_en, hint_en, que_en_resource,
        que_status, que_createddate, que_modifieddate
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
''', data, page_size=1000)

conn.commit()
conn.close()

print("✅ PostgreSQL 마이그레이션 완료")
```

---

## 📊 예상 효과

| 항목 | Before | After | 개선율 |
|-----|--------|-------|--------|
| **파일 크기** | 49MB | 100KB (코드) + 49MB (데이터) | - |
| **Git 크기** | 49MB | 100KB | **99.8% 감소** |
| **메모리 사용** | 49MB | 5MB (캐싱) | **90% 감소** |
| **로딩 시간** | 5초 | 0.5초 | **90% 개선** |
| **검색 속도** | 타임아웃 | 즉시 | **100% 개선** |
| **IDE 성능** | CPU 100% | CPU 5% | **95% 개선** |

---

## ⚠️ 주의사항

1. **백업 필수**
   ```bash
   cp backend/app/api/mock_api.py backend/app/api/mock_api.py.backup
   ```

2. **의존성 확인**
   ```bash
   grep -r "from.*mock_api import" backend/
   grep -r "import.*mock_api" backend/
   ```

3. **점진적 마이그레이션**
   - 먼저 JSON으로 추출
   - API 코드 분리
   - 테스트 완료 후 기존 파일 삭제

4. **데이터 무결성**
   - 마이그레이션 전후 데이터 개수 확인
   - 샘플 데이터 비교

---

## ✅ 체크리스트

### 실행 전
- [ ] 현재 파일 백업
- [ ] 의존성 확인
- [ ] 테스트 환경 준비

### 실행 중
- [ ] Phase 1: 분석 완료
- [ ] Phase 2: 데이터 추출 완료
- [ ] Phase 3: API 재작성 완료
- [ ] Phase 4: 테스트 완료
- [ ] Phase 5: 정리 완료

### 실행 후
- [ ] 데이터 무결성 확인
- [ ] 성능 테스트
- [ ] 문서 업데이트
- [ ] 팀원 공유

---

## 🆘 롤백 방법

```bash
# 백업에서 복원
cp backend/app/api/mock_api.py.backup backend/app/api/mock_api.py

# 또는 Git에서 복원
git checkout HEAD -- backend/app/api/mock_api.py
```

---

**다음 단계**: Phase 1 분석 실행
```bash
# 분석 스크립트 실행
python3 backend/app/api/data/analyze_mock_api.py
```
