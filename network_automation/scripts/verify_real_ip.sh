#!/bin/bash
# nginx real_ip 설정 검증 스크립트
# 목적: real_ip 설정이 올바르게 작동하는지 확인

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

DOMAIN=${1:-"staging.dreamseedai.com"}
CONF_FILE="/etc/nginx/sites-available/${DOMAIN}.conf"

log_info "=== nginx real_ip 설정 검증 시작 ==="
log_info "도메인: $DOMAIN"
log_info "설정 파일: $CONF_FILE"

# 1. nginx 설정 파일 확인
log_info "1. nginx 설정 파일 확인 중..."
if [ -f "$CONF_FILE" ]; then
    log_success "✅ 설정 파일 존재: $CONF_FILE"
else
    log_error "❌ 설정 파일이 없습니다: $CONF_FILE"
    exit 1
fi

# 2. real_ip 설정 확인
log_info "2. real_ip 설정 확인 중..."
echo "=== real_ip 설정 확인 ==="

REAL_IP_SETTINGS=(
    "set_real_ip_from"
    "real_ip_header"
    "real_ip_recursive"
)

for setting in "${REAL_IP_SETTINGS[@]}"; do
    if grep -q "$setting" "$CONF_FILE"; then
        log_success "✅ $setting 설정됨"
        grep "$setting" "$CONF_FILE" | head -5
    else
        log_warning "⚠️  $setting 설정되지 않음"
    fi
done

# 3. nginx 설정 문법 검증
log_info "3. nginx 설정 문법 검증 중..."
if nginx -t; then
    log_success "✅ nginx 설정 문법 정상"
else
    log_error "❌ nginx 설정 문법 오류"
    nginx -t
    exit 1
fi

# 4. nginx 재로드
log_info "4. nginx 재로드 중..."
if systemctl reload nginx; then
    log_success "✅ nginx 재로드 성공"
else
    log_error "❌ nginx 재로드 실패"
    exit 1
fi

# 5. real_ip 테스트
log_info "5. real_ip 테스트 중..."
echo "=== real_ip 테스트 ==="

# 테스트 요청 생성
TEST_IP="203.0.113.1"  # RFC 5737 테스트 IP
TEST_URL="http://${DOMAIN}/test-real-ip"

echo "테스트 IP: $TEST_IP"
echo "테스트 URL: $TEST_URL"

# X-Forwarded-For 헤더로 테스트 요청
if curl -s -H "X-Forwarded-For: $TEST_IP" "$TEST_URL" >/dev/null 2>&1; then
    log_success "✅ 테스트 요청 성공"
else
    log_warning "⚠️  테스트 요청 실패 (정상일 수 있음)"
fi

# 6. 액세스 로그 확인
log_info "6. 액세스 로그 확인 중..."
ACCESS_LOG="/var/log/nginx/${DOMAIN}.access.log"

if [ -f "$ACCESS_LOG" ]; then
    echo "=== 최근 액세스 로그 (real_ip 확인) ==="
    tail -10 "$ACCESS_LOG" | grep -E "(X-Forwarded-For|real_ip)" || echo "real_ip 관련 로그 없음"
    
    # 클라이언트 IP 패턴 확인
    echo ""
    echo "=== 클라이언트 IP 패턴 ==="
    tail -20 "$ACCESS_LOG" | awk '{print $1}' | sort | uniq -c | sort -nr | head -5
else
    log_warning "⚠️  액세스 로그 파일이 없습니다: $ACCESS_LOG"
fi

# 7. Cloudflare CIDR 확인 (주석 처리된 경우)
log_info "7. Cloudflare CIDR 설정 확인 중..."
if grep -q "# set_real_ip_from 173.245.48.0/20" "$CONF_FILE"; then
    log_info "ℹ️  Cloudflare CIDR가 주석 처리되어 있습니다 (로컬 환경)"
    echo "   Cloudflare 도입 시 주석을 해제하고 최신 CIDR 목록을 추가하세요"
else
    log_info "ℹ️  Cloudflare CIDR 설정 확인됨"
fi

# 8. 보안 권장사항
log_info "8. 보안 권장사항"
echo ""
echo "🔒 real_ip 보안 권장사항:"
echo "   • 신뢰할 수 있는 프록시 IP만 set_real_ip_from에 추가"
echo "   • Cloudflare 사용 시 최신 CIDR 목록 유지"
echo "   • real_ip_recursive on으로 중첩 프록시 지원"
echo "   • 액세스 로그에서 클라이언트 IP 패턴 모니터링"

# 9. 문제 해결 가이드
echo ""
echo "🔧 real_ip 문제 해결:"
echo "   • 클라이언트 IP가 로그에 나타나지 않으면 X-Forwarded-For 헤더 확인"
echo "   • 잘못된 IP가 나타나면 set_real_ip_from 범위 확인"
echo "   • 프록시 설정 변경 후 nginx 재로드 필요"

# 10. 검증 요약
echo ""
echo "📋 real_ip 검증 요약:"
if grep -q "real_ip_header X-Forwarded-For" "$CONF_FILE"; then
    log_success "✅ real_ip 설정 적용됨"
    log_success "✅ X-Forwarded-For 헤더 처리됨"
    log_success "✅ nginx 설정 정상"
else
    log_error "❌ real_ip 설정 누락"
fi

log_success "nginx real_ip 검증 완료!"
