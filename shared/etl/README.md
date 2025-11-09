# MySQL → Postgres ETL 시스템

TinyMCE + Wiris → TipTap JSON + TeX 정규화

## 🎯 핵심 기능

### 1. HTML → TipTap JSON 변환
- **Wiris 이미지**: `<img class="Wirisformula" data-mathml="...">` → `math-inline` 노드
- **MathML 태그**: `<math>...</math>` → `math-inline` 노드
- **블록 수식**: 단독 수식 → `math-block` 노드
- **텍스트**: `paragraph` 노드

### 2. 화학식 자동 감지
- `\ce{...}` 패턴 감지
- 연속된 원소 기호 패턴 감지 (예: `H2SO4`)
- `lang: 'chem'` 자동 설정

### 3. TeX 정규화
- 함수 토큰화 (`sin`, `cos`, `log` 등)
- 연속 밑첨자 보호 (`a_n` → `a_{n}`)
- 루트 괄호 보강 (`\sqrt x` → `\sqrt{x}`)

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install beautifulsoup4 sqlalchemy pymysql psycopg
```

### 2. ETL 실행

```python
from shared.etl import run_etl

run_etl(
    mysql_url="mysql+pymysql://user:pass@localhost:3306/mpc_legacy",
    pg_url="postgresql+psycopg://user:pass@localhost:5432/dreamseed",
    limit=2000,
    default_locale="ko"
)
```

### 3. 결과 확인

```sql
-- Postgres에서 확인
SELECT id, title, body_json, body_plain, locale
FROM problems
LIMIT 10;
```

## 📊 변환 예시

### 입력 (MySQL TinyMCE HTML)

```html
<p>다음을 계산하라.</p>
<p><img class="Wirisformula" data-mathml="<math><msqrt><mi>x</mi></msqrt></math>" /></p>
<p>반응식: <math><mi>H</mi><mn>2</mn><mi>O</mi></math></p>
```

### 출력 (Postgres TipTap JSON)

```json
{
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "다음을 계산하라."}]
    },
    {
      "type": "math-block",
      "attrs": {"tex": "\\sqrt{x}", "lang": "math"}
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "반응식: "},
        {"type": "math-inline", "attrs": {"tex": "\\ce{H2O}", "lang": "chem"}}
      ]
    }
  ]
}
```

### 플레인 텍스트 (검색용)

```
다음을 계산하라.
\sqrt{x}
반응식: \ce{H2O}
```

## 🔧 고급 사용법

### 커스텀 변환 규칙

```python
from shared.etl.mysql_to_postgres_hooks import _html_to_tiptap_doc

# HTML → TipTap JSON
html = "<p>이차방정식: <math>...</math></p>"
doc = _html_to_tiptap_doc(html, default_locale="ko")

print(doc)
# {'type': 'doc', 'content': [...]}
```

### 플레인 텍스트 추출

```python
from shared.etl import build_plain_text

plain = build_plain_text(tiptap_doc)
print(plain)
# "이차방정식: x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}"
```

### 배치 처리

```python
from shared.etl import fetch_mysql_rows, upsert_postgres_rows

# MySQL에서 조회
rows = fetch_mysql_rows(mysql_url, limit=1000)

# 변환
items = []
for row in rows:
    doc = _html_to_tiptap_doc(row.content_html)
    items.append({
        "id": row.id,
        "title": row.title,
        "body_json": json.dumps(doc),
        "body_plain": build_plain_text(doc),
        "locale": "ko"
    })

# Postgres에 저장
upsert_postgres_rows(pg_url, items)
```

## 📋 Postgres 스키마

```sql
CREATE TABLE problems (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body_json JSONB NOT NULL,
    body_plain TEXT,
    locale VARCHAR(10) DEFAULT 'ko',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 전문 검색 인덱스
CREATE INDEX idx_problems_body_plain ON problems USING gin(to_tsvector('korean', body_plain));

-- JSON 인덱스
CREATE INDEX idx_problems_body_json ON problems USING gin(body_json);
```

## 🎨 TipTap 노드 구조

### math-inline (인라인 수식)

```json
{
  "type": "math-inline",
  "attrs": {
    "tex": "x^2 + y^2 = r^2",
    "lang": "math"
  }
}
```

### math-block (블록 수식)

```json
{
  "type": "math-block",
  "attrs": {
    "tex": "\\int_0^1 x^2\\,dx = \\frac{1}{3}",
    "lang": "math"
  }
}
```

### 화학식 (lang: 'chem')

```json
{
  "type": "math-inline",
  "attrs": {
    "tex": "\\ce{H2SO4 + 2NaOH -> Na2SO4 + 2H2O}",
    "lang": "chem"
  }
}
```

## 🔍 문제 해결

### 문제 1: BeautifulSoup 파싱 오류

**원인**: 잘못된 HTML 구조

**해결**:
```python
from bs4 import BeautifulSoup

# lxml 파서 사용
soup = BeautifulSoup(html, 'lxml')
```

### 문제 2: MathML 변환 실패

**원인**: 복잡한 MathML 구조

**해결**:
```python
# 서버 API 사용
import requests

response = requests.post('/api/mathml/convert', json={'mathml': mathml})
tex = response.json()['tex']
```

### 문제 3: 화학식 감지 실패

**원인**: 패턴 불일치

**해결**:
```python
# 수동으로 lang 설정
doc = _html_to_tiptap_doc(html)
for block in doc['content']:
    if block['type'] == 'math-inline':
        if 'H2SO4' in block['attrs']['tex']:
            block['attrs']['lang'] = 'chem'
```

## 📚 참고 자료

- [TipTap Documentation](https://tiptap.dev/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [MathML Spec](https://www.w3.org/TR/MathML3/)

## ✅ 체크리스트

- [ ] MySQL 연결 문자열 확인
- [ ] Postgres 스키마 생성
- [ ] Python 의존성 설치
- [ ] ETL 실행
- [ ] 결과 검증
- [ ] 전문 검색 인덱스 생성
