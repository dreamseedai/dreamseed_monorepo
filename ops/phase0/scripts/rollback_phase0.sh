#!/bin/bash
# Phase 0 롤백 스크립트
# 문제 발생 시 Phase 0 인프라를 안전하게 중지

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "   Phase 0 Rollback"
echo "=========================================="
echo ""

log_warn "이 작업은 Phase 0 인프라를 중지합니다."
read -p "계속하시겠습니까? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "롤백이 취소되었습니다."
    exit 0
fi

# 1. 모니터링 스택 중지
log_warn "모니터링 스택 중지 중..."
cd ops/phase0/configs/monitoring
docker-compose -f docker-compose.monitoring.yml down

# 2. 백업 cron 제거
log_warn "백업 cron 작업 제거 중..."
crontab -l | grep -v "backup_postgres.sh" | crontab - || true

# 3. Docker 네트워크 제거 (다른 서비스가 사용 중이면 스킵)
log_warn "Docker 네트워크 정리 중..."
docker network rm dreamseed-network 2>/dev/null || true

echo ""
echo "=========================================="
log_warn "Phase 0 롤백 완료"
echo "=========================================="
echo ""
echo "재배포하려면 다음 명령어를 실행하세요:"
echo "  cd ops/phase0/scripts && ./deploy_phase0.sh"
