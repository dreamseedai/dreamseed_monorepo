# DreamSeed AI Platform

<div align="center">

![DreamSeed Logo](https://via.placeholder.com/200x80/4F46E5/FFFFFF?text=DreamSeed)

**AI 기반 교육 플랫폼**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.0-green.svg)](https://flask.palletsprojects.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)

[🚀 빠른 시작](#-빠른-시작) • [📚 문서](#-문서) • [🛠️ 개발](#️-개발) • [🚀 배포](#-배포) • [🤝 기여](#-기여)

</div>

---

## 🔔 모노레포 구조화 안내 (2024-11-09)

> **검색 성능 개선 및 고립된 파일 제거를 위한 구조화가 준비되었습니다.**

### 빠른 실행
```bash
# 1. 백업
git checkout -b restructure-monorepo
git add . && git commit -m "chore: 구조화 전 스냅샷"

# 2. 실행 (5분)
./RESTRUCTURE_EXECUTE.sh

# 3. 커밋
git add . && git commit -m "refactor: 모노레포 구조화"
```

### 상세 가이드
- **빠른 시작**: [`QUICK_START.md`](./QUICK_START.md)
- **상세 계획**: [`MONOREPO_RESTRUCTURE_PLAN.md`](./MONOREPO_RESTRUCTURE_PLAN.md)
- **실행 요약**: [`RESTRUCTURE_SUMMARY.md`](./RESTRUCTURE_SUMMARY.md)

### 예상 효과
- ✅ 검색 속도 **95% 개선**
- ✅ 스캔 디렉토리 **87% 감소** (30+ → 4개)
- ✅ 고립된 파일 **100% 제거** (17개 디렉토리)

---

## 🤖 AI Endpoint Switching (Local ↔ Cloud)

DreamSeed modules now share a single, consistent way to switch between a local OpenAI-compatible endpoint (e.g., llama.cpp or vLLM) and OpenAI Cloud.

### Env toggles

Set these environment variables once and all AI-enabled scripts will follow:

```bash
# Local (llama.cpp default)
export USE_LOCAL_LLM=1
# or pin explicitly
# export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
# Optional model override for local compat servers
# export OPENAI_MODEL=gpt-4o-mini-compat

# Cloud OpenAI
# export OPENAI_BASE_URL=https://api.openai.com/v1
# export OPENAI_API_KEY=sk-...
# export OPENAI_MODEL=gpt-4o-mini
```

Tip: You can quickly verify connectivity from the admin app:
- Probe: `GET /dsadmin/ai_probe`
- Echo: `GET /dsadmin/ai_echo?q=Hello&temperature=0.0`

### Shared helper: `ai_client.py`

Use this helper in your Python modules to avoid duplicating config logic:

```python
from ai_client import get_openai_client, get_model

client = get_openai_client()          # builds with OPENAI_BASE_URL / USE_LOCAL_LLM
model = get_model()                   # uses OPENAI_MODEL or sensible defaults

resp = client.chat.completions.create(
	model=model,
	messages=[
		{"role": "system", "content": "You are concise."},
		{"role": "user", "content": "Reply with pong"},
	],
	temperature=0.0,
)
print(resp.choices[0].message.content)
```

Defaults without env:
- Base URL: local `http://127.0.0.1:11434/v1` if `USE_LOCAL_LLM=1`, else cloud
- Model: `gpt-4o-mini-compat` (local) or `gpt-4o-mini` (cloud)

---

## 📖 프로젝트 소개

DreamSeed AI Platform은 AI 기술을 활용한 교육 플랫폼입니다. 수학, 과학, 언어 등 다양한 과목의 문제를 AI가 자동으로 생성하고, 사용자의 학습 패턴을 분석하여 개인화된 학습 경험을 제공합니다.

### ✨ 주요 기능

- 🤖 **AI 문제 생성**: GPT 기반 문제 자동 생성
- 📊 **실시간 대시보드**: 사용자 활동 및 통계 모니터링
- 🗺️ **지역별 분석**: 세계 지도 기반 사용자 분포 시각화
- 🔄 **MathML 변환**: 수학 공식을 다양한 형식으로 변환
- 💾 **캐싱 시스템**: Redis 기반 고성능 캐싱
- 📈 **모니터링**: Prometheus + Grafana 기반 모니터링
- 🐳 **컨테이너화**: Docker 기반 배포
- 🔄 **CI/CD**: GitHub Actions 기반 자동화

### 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│                 │    │                 │    │                 │
│ • HTML/CSS/JS   │◄──►│ • Flask API     │◄──►│ • SQLite        │
│ • Bootstrap 5   │    │ • Gunicorn      │    │ • Redis Cache   │
│ • Chart.js      │    │ • Prometheus    │    │                 │
│ • Leaflet.js    │    │ • Nginx         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🚀 빠른 시작

### 필수 요구사항

- **Python**: 3.11+
- **Node.js**: 20+ (선택사항)
- **Redis**: 7+
- **SQLite**: 3.35+
- **Docker**: 20.10+ (선택사항)

### 로컬 개발 환경 설정

#### 1. 저장소 클론
```bash
git clone https://github.com/dreamseed/platform.git
cd platform
```

#### 2. 가상환경 설정
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

#### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 4. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# 환경 변수 편집
nano .env
```

```env
# .env 파일 내용
PORT=8002
ENVIRONMENT=development
DEBUG=True
REDIS_URL=redis://localhost:6379
DB_PATH=./dreamseed_analytics.db
LOG_LEVEL=DEBUG

# Authentication (JWT + Token Blacklist)
JWT_SECRET=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440  # 24 hours
REDIS_TOKEN_BLACKLIST_DB=1  # Separate Redis DB for token blacklist
```

#### 5. Redis 설치 및 실행
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server

# macOS (Homebrew)
brew install redis
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### 6. 개발 서버 실행
```bash
# API 서버 실행
python api/dashboard_data.py

# 프론트엔드 서버 실행 (별도 터미널)
python -m http.server 9000
```

#### 7. 접속 확인
- **API 서버**: http://localhost:8002/healthz
- **관리자 패널**: http://localhost:9000/admin/
- **API 문서**: http://localhost:8002/docs

---

## 🔐 Authentication & Security

### Rate Limiting (slowapi + Redis)

**NEW (P3)**: DreamSeed는 slowapi를 사용하여 Redis 기반 rate limiting을 구현합니다.

#### Rate Limit 정책

| 엔드포인트 | 제한 | 키 | 목적 |
|-----------|------|-----|------|
| `POST /api/auth/login` | 5/분 | IP | 브루트포스 방지 |
| `POST /api/auth/register` | 3/시간 | IP | 스팸 계정 방지 |
| `GET /api/*` (기타) | 100/분 | User/IP | 일반 보호 |

#### 설정

```bash
# Rate Limiting 설정
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_LOGIN_PER_MINUTE=5
export RATE_LIMIT_REGISTER_PER_HOUR=3
export RATE_LIMIT_DEFAULT_PER_MINUTE=100
```

#### 429 응답 예시

```json
{
  "detail": "Rate limit exceeded: 5 requests per 1 minute"
}
```

**헤더**:
- `X-RateLimit-Limit`: 제한 횟수
- `X-RateLimit-Remaining`: 남은 횟수
- `X-RateLimit-Reset`: 리셋 시간
- `Retry-After`: 재시도까지 대기 시간 (초)

---

### Token Blacklist (Redis)

DreamSeed는 JWT 기반 인증과 함께 Redis를 사용한 토큰 블랙리스트를 구현하여 안전한 로그아웃 및 세션 관리를 제공합니다.

#### 주요 기능

- **JWT 토큰 무효화**: 로그아웃 시 토큰을 블랙리스트에 추가하여 즉시 무효화
- **자동 만료**: Redis TTL을 사용하여 토큰 만료 시간에 맞춰 자동 정리
- **사용자 레벨 블랙리스트**: 비밀번호 변경 시 모든 사용자 토큰 일괄 무효화
- **고성능**: Redis의 빠른 조회 속도로 인증 성능 저하 없음

#### 설정

환경 변수를 통해 Redis 및 JWT 설정:

```bash
# Redis 연결 (토큰 블랙리스트용)
export REDIS_URL=redis://localhost:6379
export REDIS_TOKEN_BLACKLIST_DB=1  # Token blacklist (별도 DB)
export REDIS_RATE_LIMIT_DB=2       # Rate limiting (별도 DB)

# JWT 설정
export JWT_SECRET=your-secret-key-here
export JWT_ALGORITHM=HS256
export JWT_EXPIRE_MINUTES=1440  # 24시간
```

#### 사용법

**로그아웃 API:**

```bash
# 로그아웃 (토큰 블랙리스트 등록)
curl -X POST http://localhost:8001/api/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Python SDK:**

```python
from app.services.token_blacklist import TokenBlacklistService
from app.core.redis_config import get_redis

# 토큰 블랙리스트 서비스 사용
redis = await get_redis()
blacklist_service = TokenBlacklistService(redis)

# 특정 토큰 무효화
await blacklist_service.blacklist_token(
    jti="token-unique-id",
    expires_at=datetime.now() + timedelta(hours=24)
)

# 사용자 모든 토큰 무효화 (비밀번호 변경 등)
await blacklist_service.blacklist_user_tokens(
    user_id=123,
    expires_at=datetime.now() + timedelta(hours=24)
)
```

#### 아키텍처

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │      │  FastAPI    │      │   Redis     │
│             │─────►│  Backend    │─────►│  (DB 1)     │
│             │ JWT  │             │ Check │ Blacklist   │
│             │◄─────│  JWT        │◄─────│             │
└─────────────┘      │  Strategy   │      └─────────────┘
                     └─────────────┘
                            │
                            │ Verify JTI
                            ▼
                     ┌─────────────┐
                     │ PostgreSQL  │
                     │ (Users DB)  │
                     └─────────────┘
```

#### 성능

- **토큰 검증**: < 5ms (Redis 조회)
- **로그아웃**: < 100ms (Redis 저장 + TTL 설정)
- **메모리 효율**: 토큰당 ~100 bytes (JTI + TTL)

#### 보안 고려사항

1. **JWT Secret 관리**: 프로덕션에서는 반드시 강력한 시크릿 사용
2. **Redis 보안**: Redis AUTH 설정 및 네트워크 격리 권장
3. **토큰 만료 시간**: 짧은 만료 시간 + Refresh Token 패턴 권장
4. **DB 분리**: 블랙리스트는 별도 Redis DB 사용 (기본: DB 1)

---

## 📚 문서

### 📖 사용자 문서
- [사용자 매뉴얼](docs/user/user_manual.md) - 일반 사용자를 위한 가이드
- [API 문서](docs/api/README.md) - API 사용법 및 예제
- [문제 해결 가이드](docs/troubleshooting/troubleshooting_guide.md) - 일반적인 문제 해결

### 🛠️ 개발자 문서
- [개발자 가이드](docs/developer/developer_guide.md) - 개발 환경 설정 및 개발 가이드
- [배포 가이드](docs/deployment/deployment_guide.md) - 프로덕션 배포 가이드
- [API 스펙](api/openapi.yaml) - OpenAPI 3.0 스펙

### 📊 모니터링
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **메트릭**: http://localhost:8002/metrics

---

## 🛠️ 개발

### 프로젝트 구조

```
dreamseed_monorepo/
├── api/                    # 백엔드 API
│   ├── dashboard_data.py   # 메인 API 서버
│   ├── auth_middleware.py  # 인증 미들웨어
│   └── openapi.yaml        # API 문서
├── admin/                  # 관리자 패널
│   ├── index.html         # 메인 관리자 페이지
│   ├── css/               # 스타일시트
│   └── js/                # JavaScript 파일
├── tests/                  # 테스트 파일
│   ├── test_api.py        # API 테스트
│   ├── test_security.py   # 보안 테스트
│   ├── smoke_tests.py     # 스모크 테스트
│   └── locustfile.py      # 부하 테스트
├── docs/                   # 문서
│   ├── api/               # API 문서
│   ├── user/              # 사용자 매뉴얼
│   ├── developer/         # 개발자 가이드
│   ├── deployment/        # 배포 가이드
│   └── troubleshooting/   # 문제 해결
├── .github/               # GitHub Actions
│   └── workflows/         # CI/CD 워크플로우
├── docker-compose.yml     # Docker Compose 설정
├── Dockerfile            # Docker 이미지 설정
├── requirements.txt      # Python 의존성
├── pyproject.toml        # 프로젝트 설정
└── README.md            # 프로젝트 설명
```

### 개발 워크플로우

#### 1. 브랜치 생성
```bash
git checkout main
git pull origin main
git checkout -b feature/new-feature
```

#### 2. 개발 및 테스트
```bash
# 코드 작성
# ...

# 테스트 실행
pytest

# 코드 포맷팅
black .
isort .

# 린팅
flake8 .
```

#### 3. 커밋 및 푸시
```bash
git add .
git commit -m "feat: add new dashboard feature"
git push origin feature/new-feature
```

#### 4. Pull Request 생성
- PR 템플릿에 따라 작성
- 리뷰어 지정
- 관련 이슈 연결

### 테스트

#### 단위 테스트
```bash
# 모든 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_api.py

# 커버리지 포함
pytest --cov=api --cov-report=html
```

#### 로컬 빠른 테스트 (권장)
커버리지/리포트 없이 빠르게 실행하여 로컬 개발 시 느린/중단 이슈를 방지합니다.

```bash
# 전체 테스트를 빠르게 실행
make test-fast

# ai_client 단위 테스트만 빠르게 실행
make test-ai-client

# 린트/타입체크(설치된 경우) + 빠른 테스트를 한 번에
make verify
```

VS Code 작업(Tasks):
- backend:verify → `make verify` 실행 (ruff/mypy가 있으면 수행 후 fast pytest)
- verify:fast → `pytest.fast.ini`로 빠른 테스트만 실행

#### CI에서 fast/full 프로필 사용
- 기본 CI(`DreamSeed CI Pipeline`)은 `workflow_dispatch` 입력값(profile) 또는 트리거에 따라 자동으로 fast/full을 선택합니다.
	- 스케줄 실행 또는 main 브랜치 push: full (커버리지 포함)
	- 그 외: fast (빠른 런)
- 별도 워크플로:
	- `ci-fast.yml`: feature/chore/fix 브랜치에서 빠른 테스트 전용
	- `ci-full.yml`: main/develop에서 커버리지 포함 전체 테스트

GitHub Actions 수동 실행 시 profile을 fast/full로 선택하여 `DreamSeed CI Pipeline`을 트리거할 수 있습니다.

#### Codecov/브랜치 보호 팁
- Codecov 업로드는 기본적으로 main/develop 또는 내부 PR에서만 수행되며, 포크 PR에서는 업로드를 생략합니다.
- 필요한 경우 `Settings → Secrets and variables → Actions`에 `CODECOV_TOKEN`을 저장하세요.
- `codecov.yml`에서 최소 커버리지(`project: 70%`, `patch: 75%`)와 허용 편차(`threshold: 1%`)를 정의했습니다.
- GitHub Branch Protection Rule에서 Required status checks에 Codecov의 project/patch 상태를 추가해 실패 시 머지를 막을 수 있습니다.

#### 통합 테스트
```bash
# API 서버 시작
python api/dashboard_data.py &

# 통합 테스트 실행
python tests/smoke_tests.py
```

#### 성능 테스트
```bash
# Locust 부하 테스트
locust -f tests/locustfile.py --host=http://localhost:8002
```

---

## 🚀 배포

### Docker 배포

#### 1. Docker 이미지 빌드
```bash
docker build -t dreamseed:latest .
```

#### 2. Docker Compose 실행
```bash
# 개발 환경
docker-compose up -d

# 프로덕션 환경
docker-compose -f docker-compose.prod.yml up -d
```

### 수동 배포

#### 1. 스테이징 배포
```bash
chmod +x deploy_staging.sh
./deploy_staging.sh
```

#### 2. 프로덕션 배포
```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

### CI/CD

GitHub Actions를 통한 자동 배포:
- **Push to main**: 자동으로 스테이징 환경에 배포
- **Create tag**: 자동으로 프로덕션 환경에 배포
- **Pull Request**: 자동으로 테스트 실행

---

## 🔧 설정

### 환경 변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `PORT` | API 서버 포트 | 8002 | ✅ |
| `ENVIRONMENT` | 실행 환경 | development | ✅ |
| `DEBUG` | 디버그 모드 | False | ❌ |
| `REDIS_URL` | Redis 연결 URL | redis://localhost:6379 | ✅ |
| `DB_PATH` | SQLite 데이터베이스 경로 | ./dreamseed_analytics.db | ✅ |
| `LOG_LEVEL` | 로그 레벨 | INFO | ❌ |

### 데이터베이스 설정

#### SQLite
- **파일**: `dreamseed_analytics.db`
- **백업**: 자동 백업 (매일 오전 2시)
- **복구**: `./rollback.sh` 스크립트 사용

#### Redis
- **포트**: 6379
- **메모리**: 자동 관리
- **지속성**: AOF (Append Only File)

---

## 📊 모니터링

### 메트릭 수집

- **Prometheus**: 메트릭 수집 및 저장
- **Grafana**: 대시보드 및 시각화
- **Node Exporter**: 시스템 메트릭

### 주요 메트릭

- **요청 수**: `dreamseed_requests_total`
- **응답 시간**: `dreamseed_request_duration_seconds`
- **활성 사용자**: `dreamseed_active_users`
- **캐시 히트율**: `dreamseed_cache_hits`

### 알림 설정

- **이메일**: 시스템 오류 시 알림
- **Slack**: 배포 완료 시 알림
- **SMS**: 긴급 상황 시 알림

---

## 🤝 기여

### 기여 방법

1. **Fork** 저장소
2. **브랜치 생성** (`git checkout -b feature/amazing-feature`)
3. **커밋** (`git commit -m 'Add amazing feature'`)
4. **푸시** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 코딩 컨벤션

- **Python**: PEP 8, Black, isort
- **JavaScript**: ES6+, Prettier
- **커밋 메시지**: Conventional Commits
- **문서**: Markdown, JSDoc, docstring

### 이슈 보고

버그 리포트나 기능 요청은 [GitHub Issues](https://github.com/dreamseed/platform/issues)를 사용해주세요.

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 📞 지원 및 문의

- **이메일**: support@dreamseed.com
- **문서**: https://docs.dreamseed.com
- **GitHub**: https://github.com/dreamseed/platform
- **Slack**: #dreamseed-community

---

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들의 도움을 받았습니다:

- [Flask](https://flask.palletsprojects.com/) - 웹 프레임워크
- [Redis](https://redis.io/) - 캐시 시스템
- [Chart.js](https://www.chartjs.org/) - 차트 라이브러리
- [Leaflet](https://leafletjs.com/) - 지도 라이브러리
- [Bootstrap](https://getbootstrap.com/) - CSS 프레임워크
- [Prometheus](https://prometheus.io/) - 모니터링 시스템
- [Grafana](https://grafana.com/) - 시각화 플랫폼

---

<div align="center">

**DreamSeed AI Platform** - AI로 만드는 교육의 미래

[⭐ Star](https://github.com/dreamseed/platform) • [🐛 Issues](https://github.com/dreamseed/platform/issues) • [💬 Discussions](https://github.com/dreamseed/platform/discussions) • [📖 Wiki](https://github.com/dreamseed/platform/wiki)

</div>
---


---


---


---

## 프런트엔드 실행/배포 (요약)

### 환경 변수 (.env.example)

```env
NEXT_PUBLIC_API_BASE=/ # client fetch base (reverse proxy assumed)
FLASK_BASE_URL=http://127.0.0.1:5000
```

### 설치

```bash
pnpm i
```

### 실행

```bash
pnpm dev
```

### 빌드/실행

```bash
pnpm build && pnpm start
```

### 체크리스트

- **CTA 링크 이동 확인**: /pricing#pro, /guides
- **반응형 레이아웃**: 모바일/태블릿/PC
- **언어 토글**: ?lang=en
- **Lighthouse**: ≥ 90 스냅샷
