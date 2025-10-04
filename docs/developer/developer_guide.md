# DreamSeed AI Platform 개발자 가이드

## 📖 목차

1. [개발 환경 설정](#개발-환경-설정)
2. [프로젝트 구조](#프로젝트-구조)
3. [API 개발](#api-개발)
4. [프론트엔드 개발](#프론트엔드-개발)
5. [데이터베이스](#데이터베이스)
6. [테스트](#테스트)
7. [배포](#배포)
8. [모니터링](#모니터링)
9. [기여 가이드](#기여-가이드)

---

## 🛠️ 개발 환경 설정

### 필수 요구사항
- **Python**: 3.11+
- **Node.js**: 20+
- **Redis**: 7+
- **SQLite**: 3.35+
- **Docker**: 20.10+ (선택사항)

### 로컬 개발 환경 설정

#### 1. 저장소 클론
```bash
git clone https://github.com/dreamseed/platform.git
cd platform
```

#### 2. Python 가상환경 설정
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

#### 3. 환경 변수 설정
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
REDIS_URL=redis://localhost:6379
DB_PATH=./dreamseed_analytics.db
DEBUG=True
LOG_LEVEL=DEBUG
```

#### 4. Redis 설치 및 실행
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

#### 5. 개발 서버 실행
```bash
# API 서버 실행
python api/dashboard_data.py

# 프론트엔드 서버 실행 (별도 터미널)
python -m http.server 9000
```

### IDE 설정

#### VS Code 설정
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### 추천 확장 프로그램
- Python
- Python Docstring Generator
- GitLens
- REST Client
- Thunder Client
- Docker

---

## 🏗️ 프로젝트 구조

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

### 핵심 파일 설명

#### API 서버 (`api/dashboard_data.py`)
- Flask 기반 RESTful API
- Redis 캐싱
- Prometheus 메트릭
- CORS 지원

#### 관리자 패널 (`admin/index.html`)
- Bootstrap 5 기반 반응형 UI
- Chart.js 차트
- Leaflet.js 지도
- 실시간 데이터 업데이트

#### 테스트 (`tests/`)
- 단위 테스트 (pytest)
- 통합 테스트
- 보안 테스트
- 성능 테스트 (Locust)

---

## 🔌 API 개발

### API 구조

#### 엔드포인트 설계 원칙
- **RESTful**: HTTP 메서드와 리소스 기반 설계
- **일관성**: 동일한 패턴의 URL 구조
- **버전 관리**: API 버전 명시
- **문서화**: OpenAPI 3.0 스펙 준수

#### 기본 URL 패턴
```
GET    /healthz                    # 헬스체크
GET    /api/dashboard/stats        # 통계 데이터
GET    /api/dashboard/user-growth  # 사용자 증가
POST   /api/cache/invalidate       # 캐시 무효화
GET    /metrics                    # Prometheus 메트릭
```

### 새 API 엔드포인트 추가

#### 1. 엔드포인트 정의
```python
@app.route('/api/dashboard/new-endpoint', methods=['GET'])
def get_new_data():
    """새 엔드포인트 설명"""
    try:
        # 비즈니스 로직
        data = fetch_data_from_database()
        
        # 캐싱 (선택사항)
        cache_key = f"dreamseed:new_data"
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # 데이터 처리
        result = process_data(data)
        
        # 캐시 저장 (선택사항)
        set_cached_data(cache_key, result, 300)  # 5분 캐시
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API 오류: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
```

#### 2. 데이터 모델 정의
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NewDataModel:
    id: int
    name: str
    value: float
    created_at: str
    metadata: Optional[dict] = None
```

#### 3. 유효성 검사
```python
from marshmallow import Schema, fields, validate

class NewDataSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    value = fields.Float(required=True, validate=validate.Range(min=0))
    metadata = fields.Dict(required=False)
```

#### 4. 테스트 작성
```python
def test_new_endpoint(client):
    """새 엔드포인트 테스트"""
    response = client.get('/api/dashboard/new-endpoint')
    assert response.status_code == 200
    
    data = response.json
    assert 'data' in data
    assert isinstance(data['data'], list)
```

### 캐싱 전략

#### Redis 캐싱
```python
import redis
import json
from functools import wraps

def cache_result(ttl=300):
    """결과 캐싱 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"dreamseed:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 캐시에서 조회
            cached_data = get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 결과 캐싱
            set_cached_data(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# 사용 예제
@cache_result(ttl=600)  # 10분 캐시
def get_expensive_data():
    # 비용이 큰 연산
    return expensive_calculation()
```

### 에러 처리

#### 커스텀 예외 클래스
```python
class DreamSeedAPIException(Exception):
    """DreamSeed API 기본 예외"""
    def __init__(self, message, status_code=500, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class ValidationError(DreamSeedAPIException):
    """유효성 검사 오류"""
    def __init__(self, message):
        super().__init__(message, 400, "VALIDATION_ERROR")

class NotFoundError(DreamSeedAPIException):
    """리소스 없음 오류"""
    def __init__(self, message):
        super().__init__(message, 404, "NOT_FOUND")
```

#### 전역 에러 핸들러
```python
@app.errorhandler(DreamSeedAPIException)
def handle_api_exception(e):
    """API 예외 처리"""
    return jsonify({
        "error": e.error_code or "API_ERROR",
        "message": e.message,
        "status_code": e.status_code
    }), e.status_code

@app.errorhandler(404)
def handle_not_found(e):
    """404 오류 처리"""
    return jsonify({
        "error": "NOT_FOUND",
        "message": "요청한 리소스를 찾을 수 없습니다."
    }), 404

@app.errorhandler(500)
def handle_internal_error(e):
    """500 오류 처리"""
    logger.error(f"Internal server error: {e}")
    return jsonify({
        "error": "INTERNAL_ERROR",
        "message": "서버 내부 오류가 발생했습니다."
    }), 500
```

---

## 🎨 프론트엔드 개발

### 기술 스택
- **HTML5**: 시맨틱 마크업
- **CSS3**: Flexbox, Grid, 애니메이션
- **JavaScript (ES6+)**: 모던 JavaScript
- **Bootstrap 5**: 반응형 UI 프레임워크
- **Chart.js**: 차트 라이브러리
- **Leaflet.js**: 지도 라이브러리

### 컴포넌트 구조

#### HTML 템플릿
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DreamSeed AI Platform</title>
    
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <!-- 네비게이션 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <!-- 네비게이션 내용 -->
    </nav>
    
    <!-- 메인 콘텐츠 -->
    <main class="container-fluid">
        <!-- 콘텐츠 영역 -->
    </main>
    
    <!-- JavaScript -->
    <script src="js/app.js"></script>
</body>
</html>
```

#### JavaScript 모듈 구조
```javascript
// js/app.js
class DreamSeedApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8002';
        this.charts = {};
        this.maps = {};
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // 이벤트 리스너 설정
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeCharts();
            this.initializeMaps();
        });
    }
    
    async loadInitialData() {
        try {
            const stats = await this.fetchData('/api/dashboard/stats');
            this.updateDashboard(stats);
        } catch (error) {
            console.error('데이터 로드 오류:', error);
        }
    }
    
    async fetchData(endpoint) {
        const response = await fetch(`${this.apiBaseUrl}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
}

// 앱 초기화
const app = new DreamSeedApp();
```

### 차트 개발

#### Chart.js 사용법
```javascript
class ChartManager {
    constructor(canvasId, type = 'line') {
        this.canvas = document.getElementById(canvasId);
        this.type = type;
        this.chart = null;
    }
    
    createChart(data, options = {}) {
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '차트 제목'
                }
            }
        };
        
        const config = {
            type: this.type,
            data: data,
            options: { ...defaultOptions, ...options }
        };
        
        this.chart = new Chart(this.canvas, config);
    }
    
    updateChart(newData) {
        if (this.chart) {
            this.chart.data = newData;
            this.chart.update();
        }
    }
    
    destroy() {
        if (this.chart) {
            this.chart.destroy();
        }
    }
}

// 사용 예제
const userGrowthChart = new ChartManager('userGrowthChart', 'line');
userGrowthChart.createChart({
    labels: ['1월', '2월', '3월'],
    datasets: [{
        label: '사용자 수',
        data: [100, 150, 200],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
    }]
});
```

### 지도 개발

#### Leaflet.js 사용법
```javascript
class MapManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.map = null;
        this.markers = [];
    }
    
    initializeMap() {
        this.map = L.map(this.container).setView([37.5665, 126.9780], 2);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
    }
    
    addMarker(lat, lng, data) {
        const marker = L.circleMarker([lat, lng], {
            radius: this.getRadius(data.users),
            fillColor: this.getColor(data.users),
            color: '#000',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        });
        
        marker.bindPopup(`
            <div>
                <h6>${data.country_name}</h6>
                <p>총 사용자: ${data.users}명</p>
                <p>오늘 활성: ${data.today_active}명</p>
            </div>
        `);
        
        marker.addTo(this.map);
        this.markers.push(marker);
    }
    
    getRadius(users) {
        return Math.max(5, Math.min(20, users / 10));
    }
    
    getColor(users) {
        return users > 100 ? '#ff0000' :
               users > 50 ? '#ffa500' :
               users > 10 ? '#ffff00' : '#00ff00';
    }
    
    clearMarkers() {
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];
    }
}
```

---

## 🗄️ 데이터베이스

### SQLite 스키마

#### 사용자 테이블
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    user_type TEXT DEFAULT 'free' CHECK (user_type IN ('free', 'paid', 'premium')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME,
    is_online BOOLEAN DEFAULT 0,
    country TEXT,
    metadata TEXT  -- JSON 문자열
);
```

#### 활동 로그 테이블
```sql
CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    description TEXT,
    metadata TEXT,  -- JSON 문자열
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### 문제 테이블
```sql
CREATE TABLE problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    answer TEXT,
    subject TEXT,
    difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'draft')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 데이터베이스 관리

#### 연결 관리
```python
import sqlite3
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
```

#### 마이그레이션
```python
class MigrationManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.migrations = []
    
    def add_migration(self, version, description, up_sql, down_sql):
        self.migrations.append({
            'version': version,
            'description': description,
            'up_sql': up_sql,
            'down_sql': down_sql
        })
    
    def migrate(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 마이그레이션 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migrations (
                    version TEXT PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 적용된 마이그레이션 조회
            cursor.execute('SELECT version FROM migrations')
            applied = {row[0] for row in cursor.fetchall()}
            
            # 미적용 마이그레이션 실행
            for migration in self.migrations:
                if migration['version'] not in applied:
                    print(f"마이그레이션 적용: {migration['description']}")
                    cursor.execute(migration['up_sql'])
                    cursor.execute(
                        'INSERT INTO migrations (version) VALUES (?)',
                        (migration['version'],)
                    )
                    conn.commit()
```

---

## 🧪 테스트

### 테스트 구조

#### 단위 테스트
```python
import pytest
from unittest.mock import patch, MagicMock
from api.dashboard_data import app, get_realtime_stats

class TestDashboardAPI:
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_healthz_endpoint(self, client):
        response = client.get('/healthz')
        assert response.status_code == 200
        data = response.json
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    @patch('api.dashboard_data.sqlite3.connect')
    def test_get_realtime_stats(self, mock_connect):
        # Mock 설정
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (100, 50, 10)
        
        # 테스트 실행
        stats = get_realtime_stats()
        
        # 검증
        assert 'total_users' in stats
        assert stats['total_users'] == 100
```

#### 통합 테스트
```python
import requests
import time

class TestIntegration:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url
    
    def test_api_integration(self):
        # 헬스체크
        response = requests.get(f"{self.base_url}/healthz")
        assert response.status_code == 200
        
        # 통계 조회
        response = requests.get(f"{self.base_url}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert 'total_users' in data
        
        # 캐시 상태
        response = requests.get(f"{self.base_url}/api/cache/status")
        assert response.status_code == 200
```

#### 성능 테스트 (Locust)
```python
from locust import HttpUser, task, between

class DreamSeedUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def check_health(self):
        self.client.get("/healthz")
    
    @task(5)
    def get_stats(self):
        self.client.get("/api/dashboard/stats")
    
    @task(2)
    def get_user_growth(self):
        self.client.get("/api/dashboard/user-growth")
```

### 테스트 실행

#### pytest 실행
```bash
# 모든 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_api.py

# 커버리지 포함
pytest --cov=api --cov-report=html

# 병렬 실행
pytest -n 4
```

#### Locust 실행
```bash
# 웹 UI로 실행
locust -f tests/locustfile.py --host=http://localhost:8002

# 헤드리스 모드
locust -f tests/locustfile.py --host=http://localhost:8002 --headless -u 10 -r 2 -t 30s
```

---

## 🚀 배포

### Docker 배포

#### Dockerfile 최적화
```dockerfile
# 멀티스테이지 빌드
FROM python:3.11-slim as builder

# 빌드 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 프로덕션 이미지
FROM python:3.11-slim

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 사용자 생성
RUN groupadd -r dreamseed && useradd -r -g dreamseed dreamseed

# 의존성 복사
COPY --from=builder /root/.local /home/dreamseed/.local
ENV PATH=/home/dreamseed/.local/bin:$PATH

# 애플리케이션 복사
COPY . /app
WORKDIR /app
RUN chown -R dreamseed:dreamseed /app

# 포트 노출
EXPOSE 8002

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/healthz || exit 1

# 사용자 전환
USER dreamseed

# 시작 명령
CMD ["gunicorn", "--config", "gunicorn.conf.py", "api.dashboard_data:app"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  dreamseed-api:
    build: .
    ports:
      - "8002:8002"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### CI/CD 파이프라인

#### GitHub Actions
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=api --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # 배포 스크립트 실행
          ./deploy_production.sh
```

---

## 📊 모니터링

### 로깅

#### 로그 설정
```python
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """로깅 설정"""
    if not app.debug:
        # 파일 핸들러
        file_handler = RotatingFileHandler(
            'logs/dreamseed.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        app.logger.addHandler(console_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('DreamSeed startup')
```

#### 구조화된 로깅
```python
import json
import logging

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_api_request(self, method, endpoint, status_code, duration):
        self.logger.info(json.dumps({
            'event': 'api_request',
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': duration
        }))
    
    def log_error(self, error, context=None):
        self.logger.error(json.dumps({
            'event': 'error',
            'error': str(error),
            'context': context or {}
        }))
```

### 메트릭 수집

#### Prometheus 메트릭
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# 메트릭 정의
REQUEST_COUNT = Counter('dreamseed_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('dreamseed_request_duration_seconds', 'Request duration')
ACTIVE_USERS = Gauge('dreamseed_active_users', 'Active users')

# 메트릭 수집
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint).inc()
    return response

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}
```

### 알림

#### 이메일 알림
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationManager:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_alert(self, subject, message, recipients):
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
```

---

## 🤝 기여 가이드

### 개발 워크플로우

#### 1. 이슈 생성
- 버그 리포트 또는 기능 요청 이슈 생성
- 라벨을 적절히 설정 (bug, enhancement, documentation)

#### 2. 브랜치 생성
```bash
# 메인 브랜치에서 최신 코드 가져오기
git checkout main
git pull origin main

# 새 기능 브랜치 생성
git checkout -b feature/new-feature
# 또는
git checkout -b fix/bug-fix
```

#### 3. 개발 및 테스트
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

#### 4. 커밋 및 푸시
```bash
# 변경사항 스테이징
git add .

# 커밋 (컨벤션 준수)
git commit -m "feat: add new dashboard feature"

# 브랜치 푸시
git push origin feature/new-feature
```

#### 5. Pull Request 생성
- PR 템플릿에 따라 작성
- 리뷰어 지정
- 관련 이슈 연결

### 코딩 컨벤션

#### Python
- **PEP 8** 스타일 가이드 준수
- **Black** 코드 포맷터 사용
- **isort** import 정렬
- **docstring** 작성 (Google 스타일)

```python
def calculate_user_stats(user_type: str, time_range: str) -> dict:
    """사용자 통계를 계산합니다.
    
    Args:
        user_type: 사용자 타입 ('free', 'paid', 'premium')
        time_range: 시간 범위 ('daily', 'weekly', 'monthly')
    
    Returns:
        dict: 사용자 통계 데이터
        
    Raises:
        ValueError: 잘못된 user_type 또는 time_range
    """
    if user_type not in ['free', 'paid', 'premium']:
        raise ValueError(f"Invalid user_type: {user_type}")
    
    # 구현...
    return stats
```

#### JavaScript
- **ES6+** 문법 사용
- **camelCase** 변수명
- **PascalCase** 클래스명
- **JSDoc** 주석 작성

```javascript
/**
 * 사용자 통계를 계산합니다.
 * @param {string} userType - 사용자 타입
 * @param {string} timeRange - 시간 범위
 * @returns {Promise<Object>} 사용자 통계 데이터
 */
async function calculateUserStats(userType, timeRange) {
    if (!['free', 'paid', 'premium'].includes(userType)) {
        throw new Error(`Invalid userType: ${userType}`);
    }
    
    // 구현...
    return stats;
}
```

### PR 템플릿

```markdown
## 변경사항
- [ ] 버그 수정
- [ ] 새 기능 추가
- [ ] 문서 업데이트
- [ ] 리팩토링
- [ ] 성능 개선

## 설명
변경사항에 대한 자세한 설명을 작성해주세요.

## 테스트
- [ ] 단위 테스트 추가/수정
- [ ] 통합 테스트 통과
- [ ] 수동 테스트 완료

## 체크리스트
- [ ] 코드 스타일 가이드 준수
- [ ] 문서 업데이트
- [ ] Breaking change 없음
- [ ] 기존 기능 영향 없음

## 관련 이슈
Closes #이슈번호
```

---

## 📞 지원 및 문의

- **개발팀 이메일**: dev@dreamseed.com
- **기술 문의**: tech@dreamseed.com
- **Slack**: #dreamseed-dev
- **GitHub Issues**: [이슈 트래커](https://github.com/dreamseed/platform/issues)

---

*이 개발자 가이드는 DreamSeed AI Platform v1.0.0 기준으로 작성되었습니다.*
*최신 업데이트: 2024년 1월 15일*

