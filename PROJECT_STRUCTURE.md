# DreamSeed 모노레포 구조

## 활성 프로젝트 구조

```
dreamseed_monorepo/
├── backend/                    # 통합 백엔드 (FastAPI)
│   ├── app/
│   │   ├── main.py            # 메인 FastAPI 앱
│   │   ├── api/               # API 엔드포인트들
│   │   ├── services/          # 비즈니스 로직 (AI 서비스)
│   │   ├── models/            # 데이터 모델
│   │   ├── core/              # 설정 및 공통 코드
│   │   └── utils/             # 유틸리티
│   └── README.md
│
├── adaptive_engine/            # 적응형 학습 엔진
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── services/
│   └── utils/
│
├── frontend/                   # 학생용 프론트엔드 (Next.js)
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
│
├── portal_front/              # 교사/관리자 포털 (Next.js)
│   ├── app/
│   ├── components/
│   ├── ops/                   # K8s 배포 설정
│   └── src/
│
├── admin_front/               # 어드민 대시보드 (Next.js)
│   ├── app/
│   ├── components/
│   └── lib/
│
├── shared/                    # 공유 라이브러리
│   ├── mathml/               # MathML 변환
│   ├── etl/                  # 데이터 처리
│   ├── editor/               # 문제 에디터
│   ├── analytics/            # 분석 도구
│   └── schemas/              # 공통 스키마
│
├── ops/                       # 운영 및 배포
│   ├── k8s/                  # Kubernetes 설정
│   └── scripts/              # 배포 스크립트
│
├── docs/                      # 프로젝트 문서
│   ├── AUTH_IMPLEMENTATION_GUIDE.md
│   ├── DEV_SYNC_GUARD.md
│   └── DATA_MODEL_API_INTEGRATION.md
│
├── tests/                     # 통합 테스트
├── tools/                     # 개발 도구
├── packages/                  # NPM 패키지
├── migrations/                # 데이터베이스 마이그레이션
├── alembic/                   # Alembic 마이그레이션
│   └── env.py
│
├── docker-compose.yml         # Docker 설정
├── package.json               # NPM 설정
├── pnpm-workspace.yaml        # PNPM 워크스페이스
├── pyproject.toml             # Python 프로젝트 설정
└── README.md                  # 메인 README
```

## 비활성/아카이브 디렉토리

```
archive/                       # 정리된 구버전 파일들
├── config/                   # 구버전 설정 파일
├── docs/                     # 구버전 문서
├── scripts/                  # 구버전 스크립트
├── reports/                  # 분석 리포트
└── deprecated/               # 사용 중단된 코드

examples/                     # 예제 코드 (참고용)
webtests/                     # 웹 테스트 (구버전)
translator.py/                # 변환 도구 (독립 실행)
```

## 백엔드 API 구조

### 메인 API (backend/)
- **포트**: 8000
- **위치**: `backend/app/main.py`
- **실행**: `cd backend && uvicorn app.main:app --reload --port 8000`
- **API 문서**: http://localhost:8000/docs

### 적응형 엔진 (adaptive_engine/)
- **포트**: 8001
- **위치**: `adaptive_engine/main.py`
- **실행**: `cd adaptive_engine && python main.py`

## 프론트엔드 구조

### 학생용 (frontend/)
- **포트**: 3000
- **기술**: Next.js 14, React, TypeScript
- **실행**: `cd frontend && npm run dev`

### 교사 포털 (portal_front/)
- **포트**: 3001
- **기술**: Next.js, Dashboard
- **실행**: `cd portal_front && npm run dev`

### 어드민 (admin_front/)
- **포트**: 3002
- **기술**: Next.js, Admin UI
- **실행**: `cd admin_front && npm run dev`

## 공유 라이브러리 (shared/)

### MathML (shared/mathml/)
- MathML 변환 및 파싱
- KaTeX 통합

### ETL (shared/etl/)
- 데이터 추출/변환/로드
- CSV/JSON 처리

### Editor (shared/editor/)
- 문제 에디터 컴포넌트
- Quill 통합

### Analytics (shared/analytics/)
- Grafana 대시보드
- SQL 쿼리
- 학습 분석

## 개발 환경 설정

### Python 환경
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r backend/requirements.txt
```

### Node.js 환경
```bash
pnpm install
```

### Docker 환경
```bash
docker-compose up -d
```

## 주요 설정 파일

- `docker-compose.yml` - Docker 서비스 정의
- `pnpm-workspace.yaml` - PNPM 워크스페이스 설정
- `package.json` - 루트 NPM 설정
- `pyproject.toml` - Python 프로젝트 설정
- `.vscode/settings.json` - VSCode 검색 제외 설정

## Git 브랜치 전략

- **main**: 프로덕션 브랜치
- **feat/***: 기능 개발 브랜치
- **fix/***: 버그 수정 브랜치
- **현재**: feat/governance-production-ready

## 검색 최적화

`.vscode/settings.json`에서 다음 디렉토리를 검색에서 제외:
- `node_modules/`, `.venv/`, `venv/`
- `archive/`, `examples/`, `webtests/`
- `htmlcov/`, `test-results/`
- `.history/`, `.git/`, `.mamba/`
- 각종 캐시 디렉토리 (`__pycache__`, `.pytest_cache` 등)

이를 통해 Copilot과 검색 성능이 크게 향상됩니다.
