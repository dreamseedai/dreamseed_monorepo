# Rate Limiting 설계 문서 (P3)

**작성일**: 2025-11-29  
**브랜치**: `feature/rate-limiting-p3`  
**우선순위**: P3 (Week 5-6)

---

## 🎯 목표

API 엔드포인트를 브루트포스 공격, DDoS, 과도한 요청으로부터 보호하기 위한 Rate Limiting 구현.

### 핵심 요구사항

1. **로그인 엔드포인트**: 5회/분/IP
2. **토큰 갱신 엔드포인트**: 10회/시간/사용자
3. **일반 API**: 100회/분/사용자
4. **Redis 기반 카운터**: 기존 Redis 인프라 활용
5. **명확한 에러 메시지**: 429 Too Many Requests + Retry-After 헤더

---

## 🏗️ 아키텍처

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ Request
       ▼
┌─────────────────────┐
│  Rate Limiter       │ ◄── slowapi
│  Middleware         │     (FastAPI)
└──────┬──────────────┘
       │ Check Redis
       ▼
┌─────────────┐        ┌─────────────┐
│   Redis     │        │  Backend    │
│  (Counter)  │───────►│   Logic     │
└─────────────┘  Allow └─────────────┘
       │
       │ Deny
       ▼
┌─────────────┐
│ 429 Error   │
└─────────────┘
```

---

## 📊 Rate Limit 정책

| 엔드포인트 | 제한 | 키 | TTL | 이유 |
|-----------|------|-----|-----|------|
| `POST /api/auth/login` | 5/분 | IP | 60초 | 브루트포스 방지 |
| `POST /api/auth/register` | 3/시간 | IP | 3600초 | 스팸 계정 방지 |
| `POST /api/auth/refresh` | 10/시간 | user_id | 3600초 | 토큰 남용 방지 |
| `GET /api/auth/me` | 60/분 | user_id | 60초 | 일반 보호 |
| `GET /api/*` (기타) | 100/분 | user_id | 60초 | 기본 보호 |

### 429 응답 예시

```json
{
  "detail": "Rate limit exceeded: 5 requests per 1 minute",
  "retry_after": 45
}
```

**헤더**:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1701234567
Retry-After: 45
```

---

## 🛠️ 기술 스택

### slowapi
- FastAPI용 rate limiting 라이브러리
- Redis backend 지원
- 유연한 키 전략 (IP, user, custom)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

### Redis Counter
- 기존 Redis 인스턴스 활용 (DB 2)
- `INCR` + `EXPIRE` 조합
- Atomic 연산 보장

---

## 📁 파일 구조

```
backend/
├── app/
│   ├── core/
│   │   ├── rate_limiter.py         # NEW: Rate limiter 설정
│   │   └── settings.py             # UPDATE: Rate limit 설정 추가
│   ├── api/
│   │   └── auth.py                 # UPDATE: Rate limit 데코레이터 추가
│   └── main.py                     # UPDATE: Rate limiter 미들웨어 등록
└── tests/
    ├── test_rate_limiter.py        # NEW: 단위 테스트
    └── test_rate_limiting_integration.py  # NEW: 통합 테스트
```

---

## 🔧 구현 계획

### 1단계: slowapi 설치 및 설정 (30분)

```bash
# pyproject.toml에 추가
poetry add slowapi redis
```

**backend/app/core/rate_limiter.py**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import Redis
from .settings import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"{settings.redis_url}/2",  # DB 2 for rate limiting
    default_limits=["100/minute"]
)
```

### 2단계: 엔드포인트별 Rate Limit 적용 (1시간)

**backend/app/api/auth.py**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..core.rate_limiter import limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
):
    # ... 로그인 로직
    pass

@router.post("/register")
@limiter.limit("3/hour")
async def register(
    request: Request,
    user_create: UserCreate,
):
    # ... 회원가입 로직
    pass
```

### 3단계: 사용자 기반 Rate Limiting (1시간)

```python
from typing import Optional
from fastapi import Depends
from ..core.users import current_active_user

def get_user_id_or_ip(request: Request, user: Optional[User] = Depends(current_active_user)):
    """인증된 사용자는 user_id, 아니면 IP 사용"""
    if user:
        return f"user:{user.id}"
    return get_remote_address(request)

@router.post("/refresh")
@limiter.limit("10/hour", key_func=get_user_id_or_ip)
async def refresh_token(request: Request, user: User = Depends(current_active_user)):
    # ... 토큰 갱신 로직
    pass
```

### 4단계: 전역 미들웨어 등록 (30분)

**backend/app/main.py**:
```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.rate_limiter import limiter

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 5단계: 테스트 작성 (2시간)

**test_rate_limiter.py** (단위):
- Redis counter 증가 확인
- TTL 설정 확인
- 키 생성 로직 테스트

**test_rate_limiting_integration.py** (E2E):
- 로그인 5회 연속 시도 → 6번째 429
- 토큰 갱신 10회 후 429
- Retry-After 헤더 확인
- IP vs User 키 전략 테스트

---

## 🧪 테스트 시나리오

### 시나리오 1: 로그인 브루트포스
```python
def test_login_rate_limit():
    # 5회 로그인 시도 (성공)
    for i in range(5):
        response = client.post("/api/auth/login", data={...})
        assert response.status_code in [200, 401]
    
    # 6번째 시도 (차단)
    response = client.post("/api/auth/login", data={...})
    assert response.status_code == 429
    assert "retry_after" in response.json()
```

### 시나리오 2: 토큰 갱신 남용
```python
def test_refresh_token_rate_limit():
    user = create_test_user()
    token = login(user)
    
    # 10회 갱신 (성공)
    for i in range(10):
        response = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    # 11번째 시도 (차단)
    response = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 429
```

### 시나리오 3: IP vs User 키
```python
def test_rate_limit_key_strategy():
    # 익명 사용자 (IP 기반)
    for i in range(5):
        client.post("/api/auth/login")
    response = client.post("/api/auth/login")
    assert response.status_code == 429
    
    # 다른 IP에서는 정상 (IP 기반 격리)
    client2 = TestClient(app, base_url="http://testserver", headers={"X-Forwarded-For": "1.2.3.4"})
    response = client2.post("/api/auth/login")
    assert response.status_code != 429
```

---

## 📈 성능 고려사항

### Redis 부하
- 예상 QPS: 1000 req/sec
- Redis 작업: 2 ops/req (INCR + EXPIRE)
- 총 Redis ops: 2000 ops/sec (여유 있음)

### 메모리 사용
- 키당 메모리: ~50 bytes
- 1시간 TTL, 10000 users: 500 KB
- 충분히 가벼움

### 응답 시간
- Redis INCR: <1ms
- 전체 오버헤드: <2ms
- 사용자 체감 영향 없음

---

## 🔒 보안 개선사항

1. **브루트포스 방지**: 로그인 시도 제한
2. **DDoS 완화**: IP 기반 전역 제한
3. **토큰 남용 방지**: 사용자별 토큰 갱신 제한
4. **스팸 계정 방지**: 회원가입 IP 제한
5. **명확한 피드백**: Retry-After로 사용자 경험 개선

---

## 📝 환경 변수

```bash
# .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_DB=2
RATE_LIMIT_LOGIN_PER_MINUTE=5
RATE_LIMIT_REFRESH_PER_HOUR=10
RATE_LIMIT_DEFAULT_PER_MINUTE=100
```

---

## 🚀 배포 체크리스트

- [ ] slowapi 패키지 설치
- [ ] Redis DB 2 할당 (rate limiting 전용)
- [ ] rate_limiter.py 구현
- [ ] 엔드포인트별 데코레이터 추가
- [ ] 전역 미들웨어 등록
- [ ] 단위 테스트 (10+ cases)
- [ ] 통합 테스트 (5+ E2E)
- [ ] README 업데이트
- [ ] 환경 변수 문서화
- [ ] PR 생성

---

## 📚 참고 자료

- [slowapi GitHub](https://github.com/laurents/slowapi)
- [FastAPI Rate Limiting](https://fastapi.tiangolo.com/advanced/middleware/)
- [Redis INCR](https://redis.io/commands/incr/)
- [RFC 6585 - 429 Status Code](https://datatracker.ietf.org/doc/html/rfc6585#section-4)

---

**다음 단계**: `rate_limiter.py` 구현 시작
