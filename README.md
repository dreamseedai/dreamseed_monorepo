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