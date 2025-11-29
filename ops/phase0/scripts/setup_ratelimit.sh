#!/bin/bash
# Rate Limiting 시스템 설정
# 실행: ./setup_ratelimit.sh

set -e

GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_info "Rate Limiting 시스템 설정 시작..."

# 1. Rate Limit 설정 디렉토리 생성
RATELIMIT_DIR="../configs/ratelimit"
mkdir -p $RATELIMIT_DIR

# 2. Redis 기반 Rate Limiter Python 모듈 생성
cat > $RATELIMIT_DIR/rate_limiter.py <<'PYTHON_CODE'
"""
Redis 기반 Rate Limiter
사용법:
    from rate_limiter import RateLimiter
    
    limiter = RateLimiter(redis_url="redis://localhost:6379")
    
    @limiter.limit("100/minute")
    async def my_endpoint(user_id: str):
        ...
"""

import time
from functools import wraps
from typing import Callable, Optional
import redis.asyncio as redis
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class RateLimiter:
    """Redis 기반 Rate Limiter"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    def limit(self, rate: str, key_func: Optional[Callable] = None):
        """
        Rate limiting 데코레이터
        
        Args:
            rate: "100/minute", "1000/hour", "10000/day" 형식
            key_func: 사용자 식별 함수 (기본: IP 주소)
        """
        # rate 파싱
        count, period = rate.split("/")
        count = int(count)
        
        period_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }[period]
        
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                # 사용자 식별
                if key_func:
                    user_key = key_func(request)
                else:
                    user_key = request.client.host
                
                # Redis 키 생성
                redis_key = f"ratelimit:{func.__name__}:{user_key}"
                
                # 현재 요청 수 확인
                current = await self.redis_client.get(redis_key)
                
                if current is None:
                    # 첫 요청
                    await self.redis_client.setex(redis_key, period_seconds, 1)
                    remaining = count - 1
                elif int(current) >= count:
                    # 제한 초과
                    ttl = await self.redis_client.ttl(redis_key)
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                        headers={"Retry-After": str(ttl)}
                    )
                else:
                    # 요청 수 증가
                    await self.redis_client.incr(redis_key)
                    remaining = count - int(current) - 1
                
                # 응답 헤더에 Rate Limit 정보 추가
                response = await func(request, *args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers["X-RateLimit-Limit"] = str(count)
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + period_seconds)
                
                return response
            
            return wrapper
        return decorator


# FastAPI 미들웨어 버전
class RateLimitMiddleware:
    """전역 Rate Limiting 미들웨어"""
    
    def __init__(self, app, redis_url: str, default_limit: str = "100/minute"):
        self.app = app
        self.limiter = RateLimiter(redis_url)
        self.default_limit = default_limit
    
    async def __call__(self, request: Request, call_next):
        # Rate limit 체크
        user_key = request.client.host
        count, period = self.default_limit.split("/")
        count = int(count)
        
        period_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }[period]
        
        redis_key = f"ratelimit:global:{user_key}"
        current = await self.limiter.redis_client.get(redis_key)
        
        if current is None:
            await self.limiter.redis_client.setex(redis_key, period_seconds, 1)
        elif int(current) >= count:
            ttl = await self.limiter.redis_client.ttl(redis_key)
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Try again in {ttl} seconds."},
                headers={"Retry-After": str(ttl)}
            )
        else:
            await self.limiter.redis_client.incr(redis_key)
        
        # 다음 미들웨어/핸들러 실행
        response = await call_next(request)
        return response
PYTHON_CODE

# 3. FastAPI 통합 예제 생성
cat > $RATELIMIT_DIR/fastapi_example.py <<'FASTAPI_EXAMPLE'
"""
FastAPI Rate Limiting 통합 예제
"""

from fastapi import FastAPI, Request
from rate_limiter import RateLimiter, RateLimitMiddleware
import os

app = FastAPI()

# Redis URL 환경 변수에서 로드
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# 전역 Rate Limiting 미들웨어 추가 (100 req/min per IP)
app.add_middleware(RateLimitMiddleware, redis_url=REDIS_URL, default_limit="100/minute")

# Rate Limiter 인스턴스
limiter = RateLimiter(redis_url=REDIS_URL)


# 사용자별 Rate Limit 적용
def get_user_id(request: Request) -> str:
    """Authorization 헤더에서 사용자 ID 추출"""
    auth_header = request.headers.get("Authorization", "")
    # JWT 토큰에서 user_id 추출 (간단한 예제)
    if auth_header.startswith("Bearer "):
        # 실제로는 JWT 디코딩 필요
        return auth_header.split(" ")[1][:10]  # 임시로 토큰 앞 10자리 사용
    return request.client.host


@app.get("/")
async def root():
    return {"message": "DreamSeed API - Rate Limited"}


@app.get("/api/problems")
@limiter.limit("50/minute", key_func=get_user_id)
async def get_problems(request: Request):
    """문제 목록 조회 (50 req/min per user)"""
    return {"problems": []}


@app.post("/api/ai/generate")
@limiter.limit("10/minute", key_func=get_user_id)
async def generate_ai_content(request: Request):
    """AI 생성 엔드포인트 (10 req/min per user)"""
    return {"generated": "content"}


@app.get("/health")
async def health_check():
    """헬스체크 (Rate Limit 제외)"""
    return {"status": "ok"}
FASTAPI_EXAMPLE

# 4. Rate Limit 테스트 스크립트 생성
cat > $RATELIMIT_DIR/test_ratelimit.sh <<'TEST_SCRIPT'
#!/bin/bash
# Rate Limit 테스트 스크립트
# 사용법: ./test_ratelimit.sh

echo "Rate Limit 테스트 시작..."
echo ""

API_URL="http://localhost:8000/api/problems"

# 100번 요청 (limit이 100/minute이므로 100번까지는 성공)
echo "1. 100번 요청 테스트 (모두 성공해야 함)..."
for i in {1..100}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
    if [ $response -ne 200 ]; then
        echo "✗ 요청 $i 실패 (HTTP $response)"
        exit 1
    fi
    echo -n "."
done
echo ""
echo "✓ 100번 요청 성공"

# 101번째 요청 (429 에러 예상)
echo ""
echo "2. 101번째 요청 테스트 (429 에러 예상)..."
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
if [ $response -eq 429 ]; then
    echo "✓ Rate Limit 정상 작동 (HTTP 429)"
else
    echo "✗ Rate Limit 실패 (HTTP $response, 예상: 429)"
    exit 1
fi

echo ""
echo "=========================================="
echo "Rate Limit 테스트 완료! ✅"
echo "=========================================="
TEST_SCRIPT

chmod +x $RATELIMIT_DIR/test_ratelimit.sh

# 5. Prometheus 메트릭 수집 설정 (선택 사항)
cat > $RATELIMIT_DIR/metrics.py <<'METRICS_CODE'
"""
Rate Limiting Prometheus 메트릭
"""

from prometheus_client import Counter, Histogram

# Rate Limit 카운터
rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total number of rate limit exceeded errors',
    ['endpoint', 'user']
)

# 요청 처리 시간
request_duration = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method']
)

# 총 요청 수
total_requests = Counter(
    'total_requests',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)
METRICS_CODE

log_info "✓ Rate Limiting 시스템 설정 완료"
log_info "  - Rate Limiter 모듈: $RATELIMIT_DIR/rate_limiter.py"
log_info "  - FastAPI 예제: $RATELIMIT_DIR/fastapi_example.py"
log_info "  - 테스트 스크립트: $RATELIMIT_DIR/test_ratelimit.sh"
log_info ""
log_info "다음 명령어로 테스트하세요:"
log_info "  cd $RATELIMIT_DIR && ./test_ratelimit.sh"
