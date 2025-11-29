#!/bin/bash
# Phase 0 전체 배포 스크립트
# 실행: ./deploy_phase0.sh

set -e  # 에러 발생 시 즉시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 배너
echo "=========================================="
echo "   Phase 0: Infrastructure Foundation    "
echo "=========================================="
echo ""

# 1. 환경 변수 확인
log_info "Step 1/7: 환경 변수 확인 중..."
if [ ! -f "../../../.env" ]; then
    log_error ".env 파일이 없습니다. .env.example을 복사하여 .env를 생성하세요."
    exit 1
fi

# 필수 환경 변수 체크
required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET"
    "B2_APPLICATION_KEY_ID"
    "B2_APPLICATION_KEY"
    "B2_BUCKET_NAME"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" ../../../.env; then
        log_error "필수 환경 변수 누락: ${var}"
        exit 1
    fi
done

log_info "✓ 모든 환경 변수 확인 완료"

# 2. Docker 및 Docker Compose 확인
log_info "Step 2/7: Docker 설치 확인 중..."
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_warn "docker-compose가 설치되지 않았습니다. docker compose 플러그인을 사용합니다."
fi

log_info "✓ Docker 확인 완료"

# 3. 모니터링 스택 배포
log_info "Step 3/7: 모니터링 스택 배포 중 (Prometheus + Grafana)..."
chmod +x ./setup_monitoring.sh
./setup_monitoring.sh

# 4. 백업 자동화 설정
log_info "Step 4/7: 백업 자동화 설정 중..."
chmod +x ./setup_backup.sh
./setup_backup.sh

# 5. Rate Limiting 설정
log_info "Step 5/7: Rate Limiting 설정 중..."
chmod +x ./setup_ratelimit.sh
./setup_ratelimit.sh

# 6. 인증 시스템 설정
log_info "Step 6/7: 인증/RBAC 시스템 설정 중..."
chmod +x ./setup_auth.sh
./setup_auth.sh

# 7. 헬스체크
log_info "Step 7/7: 헬스체크 실행 중..."
sleep 10  # 서비스 시작 대기

# PostgreSQL 헬스체크
if docker exec dreamseed-postgres pg_isready -U postgres > /dev/null 2>&1; then
    log_info "✓ PostgreSQL 정상"
else
    log_error "✗ PostgreSQL 비정상"
    exit 1
fi

# Redis 헬스체크
if docker exec dreamseed-redis redis-cli ping | grep -q PONG; then
    log_info "✓ Redis 정상"
else
    log_error "✗ Redis 비정상"
    exit 1
fi

# Prometheus 헬스체크
if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus"; then
    log_info "✓ Prometheus 정상"
else
    log_error "✗ Prometheus 비정상"
    exit 1
fi

# Grafana 헬스체크
if curl -s http://localhost:3000/api/health | grep -q "ok"; then
    log_info "✓ Grafana 정상"
else
    log_error "✗ Grafana 비정상"
    exit 1
fi

echo ""
echo "=========================================="
log_info "Phase 0 배포 완료! 🎉"
echo "=========================================="
echo ""
echo "다음 URL에서 확인하세요:"
echo "  - Grafana:    http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "다음 단계:"
echo "  1. Grafana에 로그인하여 대시보드 확인"
echo "  2. 백업이 B2에 업로드되었는지 확인"
echo "  3. Rate Limiter 테스트 실행"
echo "  4. CI/CD 파이프라인 설정"
echo ""
