# DreamSeedAI Shared Modules

완전 패키지화된 공용 모듈 (타이핑, 배럴 익스포트, Zod 검증, Jest/PyTest)

## 📁 모듈 구조

```
shared/
├── editor/                    # TipTap Math 노드 (TypeScript)
│   ├── src/
│   │   ├── types.ts          # MathAttrs, MathLang 타입
│   │   ├── mathNodes.ts      # MathInline, MathBlock 노드
│   │   ├── mathPasteRules.ts # 붙여넣기 규칙
│   │   └── index.ts          # Barrel exports
│   ├── package.json          # @dreamseed/shared-editor
│   ├── tsconfig.json
│   └── jest.config.ts
│
├── schemas/                   # Zod 스키마 (TypeScript)
│   ├── src/
│   │   ├── tiptap.ts         # TipTap JSON 스키마
│   │   ├── goldenset.ts      # GoldenSet 스키마
│   │   ├── goldenset.test.ts # Jest 테스트
│   │   └── index.ts          # Barrel exports
│   ├── package.json          # @dreamseed/shared-schemas
│   ├── tsconfig.json
│   └── jest.config.ts
│
├── etl/                       # MySQL→Postgres ETL (Python)
│   ├── shared_etl/
│   │   ├── __init__.py
│   │   ├── types.py          # TypedDict, dataclass
│   │   ├── normalize_adapter.py
│   │   └── mysql_to_postgres_hooks.py
│   ├── tests/
│   │   └── test_schemas.py   # PyTest
│   └── pyproject.toml        # dreamseed-shared-etl
│
└── mathml/                    # MathML 변환 시스템
    ├── goldenset/
    ├── scripts/
    ├── node/
    └── tests/
```

---

## 🚀 빠른 시작

### 1. TypeScript 모듈 설치

```bash
# shared/editor
cd shared/editor
npm ci
npm run build
npm test

# shared/schemas
cd shared/schemas
npm ci
npm run build
npm test
```

### 2. Python 모듈 설치

```bash
cd shared/etl
pip install -e .
pytest
```

---

## 📦 패키지 사용법

### @dreamseed/shared-editor

```typescript
import { MathInline, MathBlock, MathPaste } from '@dreamseed/shared-editor'
import type { MathAttrs } from '@dreamseed/shared-editor'

// TipTap 에디터에 등록
const editor = new Editor({
  extensions: [
    StarterKit,
    MathInline,
    MathBlock,
    MathPaste,
  ]
})

// 수식 삽입
editor.commands.setMathInline({ tex: 'x^2', lang: 'math' })
editor.commands.setMathBlock({ tex: '\\int_0^1 x^2\\,dx', lang: 'math' })
```

### @dreamseed/shared-schemas

```typescript
import { TipTapDoc, GoldenSetItem } from '@dreamseed/shared-schemas'

// 런타임 검증
const doc = TipTapDoc.parse(jsonData)

// 타입 추론
const item: GoldenSetItem = {
  id: 'm_nested_sqrt_01',
  domain: 'math',
  locale: 'ko',
  source_format: 'latex-tex',
  payload: { tex: '\\sqrt{x}' },
  expected: { tex: '\\sqrt{x}' },
  tags: ['sqrt']
}
```

### dreamseed-shared-etl

```python
from shared_etl import run_etl, build_plain_text

# ETL 실행
run_etl(
    mysql_url="mysql+pymysql://user:pass@localhost:3306/legacy",
    pg_url="postgresql+psycopg://user:pass@localhost:5432/dreamseed",
    limit=1000,
    default_locale="ko"
)

# 플레인 텍스트 추출
plain = build_plain_text(tiptap_doc)
```

---

## 🎯 주요 기능

### shared/editor
- ✅ **MathInline**: 인라인 수식 노드 (`$x^2$`)
- ✅ **MathBlock**: 블록 수식 노드 (`$$\int_0^1 x^2\,dx$$`)
- ✅ **MathPaste**: 붙여넣기 규칙 (`$...$`, Wiris, MathML)
- ✅ **lang 속성**: `'math'` | `'chem'` 자동 감지

### shared/schemas
- ✅ **TipTapDoc**: TipTap JSON 스키마 (Zod)
- ✅ **GoldenSetItem**: 골든셋 스키마 (Zod)
- ✅ **런타임 검증**: `.parse()`, `.safeParse()`
- ✅ **타입 추론**: `z.infer<typeof Schema>`

### shared/etl
- ✅ **HTML → TipTap JSON**: Wiris/MathML 자동 변환
- ✅ **화학식 감지**: `H2SO4` → `\ce{H2SO4}`
- ✅ **플레인 텍스트**: 검색용 텍스트 추출
- ✅ **배치 처리**: MySQL → Postgres 일괄 변환

---

## 🔧 개발 가이드

### TypeScript 빌드

```bash
# shared/editor
cd shared/editor
npm run build  # dist/ 생성

# shared/schemas
cd shared/schemas
npm run build  # dist/ 생성
```

### Python 개발 모드

```bash
cd shared/etl
pip install -e .  # 개발 모드 설치
```

### 테스트 실행

```bash
# TypeScript (Jest)
npm test

# Python (PyTest)
pytest -v
```

---

## �� CI/CD 통합

### GitHub Actions

`.github/workflows/monorepo-ci.yml`:

```yaml
jobs:
  ts-schemas-editor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci && npm run build && npm test

  py-shared-etl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e . && pytest
```

---

## 📚 문서

### 모듈별 README
- **shared/editor**: TipTap Math 노드 사용법
- **shared/schemas**: Zod 스키마 검증
- **shared/etl**: MySQL→Postgres ETL 가이드
- **shared/mathml**: MathML 변환 시스템

### 통합 가이드
- **ETL_QUICKSTART.md**: ETL + 에디터 통합
- **INTEGRATION_GUIDE.md**: 전체 시스템 통합

---

## ✅ 체크리스트

### TypeScript 모듈
- [ ] `npm ci` 실행
- [ ] `npm run build` 성공
- [ ] `npm test` 통과
- [ ] `dist/` 디렉토리 생성 확인

### Python 모듈
- [ ] `pip install -e .` 실행
- [ ] `pytest` 통과
- [ ] Import 테스트 (`from shared_etl import run_etl`)

### CI/CD
- [ ] GitHub Actions 워크플로우 확인
- [ ] PR 자동 테스트 확인

---

**완성도 높은 shared/ 모듈 패키지화 완료\!** 🎉

**즉시 실행**:
```bash
# TypeScript
cd shared/editor && npm ci && npm run build && npm test
cd shared/schemas && npm ci && npm run build && npm test

# Python
cd shared/etl && pip install -e . && pytest
```
