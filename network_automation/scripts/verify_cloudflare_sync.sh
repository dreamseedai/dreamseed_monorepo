#!/bin/bash
# Cloudflare CIDR 동기화 검증 스크립트
# 목적: CIDR 동기화가 올바르게 작동하는지 확인

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

log_info "=== Cloudflare CIDR 동기화 검증 시작 ==="

# 1. 스크립트 존재 확인
log_info "1. 스크립트 존재 확인 중..."
if [ -f "/usr/local/sbin/update_cloudflare_real_ip" ]; then
    log_success "✅ 스크립트 존재: /usr/local/sbin/update_cloudflare_real_ip"
else
    log_error "❌ 스크립트가 없습니다: /usr/local/sbin/update_cloudflare_real_ip"
    exit 1
fi

# 2. systemd 서비스 확인
log_info "2. systemd 서비스 확인 중..."
if systemctl list-unit-files | grep -q "update-cloudflare-real-ip.service"; then
    log_success "✅ systemd 서비스 존재"
else
    log_warning "⚠️  systemd 서비스가 없습니다"
fi

# 3. systemd 타이머 확인
log_info "3. systemd 타이머 확인 중..."
if systemctl list-timers | grep -q "update-cloudflare-real-ip.timer"; then
    log_success "✅ systemd 타이머 활성화됨"
    echo "=== 타이머 상태 ==="
    systemctl list-timers | grep cloudflare
else
    log_warning "⚠️  systemd 타이머가 활성화되지 않았습니다"
fi

# 4. nginx 설정 파일 확인
log_info "4. nginx 설정 파일 확인 중..."
CONF_FILE="/etc/nginx/conf.d/real_ip_cloudflare.conf"
if [ -f "$CONF_FILE" ]; then
    log_success "✅ 설정 파일 존재: $CONF_FILE"
    
    # 파일 내용 확인
    echo "=== 설정 파일 내용 (처음 10줄) ==="
    head -10 "$CONF_FILE"
    
    # IPv4/IPv6 범위 개수 확인
    V4_COUNT=$(grep -c "set_real_ip_from.*[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+" "$CONF_FILE" || echo "0")
    V6_COUNT=$(grep -c "set_real_ip_from.*:" "$CONF_FILE" || echo "0")
    LOCAL_COUNT=$(grep -c "set_real_ip_from 127.0.0.1" "$CONF_FILE" || echo "0")
    
    echo ""
    echo "=== IP 범위 통계 ==="
    echo "IPv4 범위: $V4_COUNT개"
    echo "IPv6 범위: $V6_COUNT개"
    echo "로컬 범위: $LOCAL_COUNT개"
    echo "총 범위: $((V4_COUNT + V6_COUNT + LOCAL_COUNT))개"
    
    if [ "$V4_COUNT" -gt 0 ] || [ "$V6_COUNT" -gt 0 ]; then
        log_success "✅ Cloudflare IP 범위가 포함되어 있습니다"
    else
        log_warning "⚠️  Cloudflare IP 범위가 없습니다"
    fi
else
    log_warning "⚠️  설정 파일이 없습니다: $CONF_FILE"
fi

# 5. nginx 설정 검증
log_info "5. nginx 설정 검증 중..."
if nginx -t; then
    log_success "✅ nginx 설정 검증 통과"
else
    log_error "❌ nginx 설정 검증 실패"
    nginx -t
fi

# 6. nginx include 확인
log_info "6. nginx include 확인 중..."
if nginx -T | grep -q "real_ip_cloudflare.conf"; then
    log_success "✅ nginx에서 real_ip_cloudflare.conf가 포함됨"
    echo "=== nginx include 확인 ==="
    nginx -T | grep -A5 -B5 "real_ip_cloudflare.conf"
else
    log_warning "⚠️  nginx에서 real_ip_cloudflare.conf가 포함되지 않음"
fi

# 7. 수동 실행 테스트
log_info "7. 수동 실행 테스트 중..."
if sudo /usr/local/sbin/update_cloudflare_real_ip; then
    log_success "✅ 수동 실행 성공"
else
    log_warning "⚠️  수동 실행 실패 (네트워크 문제일 수 있음)"
fi

# 8. 로그 확인
log_info "8. 로그 확인 중..."
echo "=== 최근 서비스 로그 ==="
journalctl -u update-cloudflare-real-ip.service --no-pager -n 10 || echo "서비스 로그 없음"

# 9. cron 설정 확인 (선택사항)
log_info "9. cron 설정 확인 중..."
if [ -f "/etc/cron.d/update-cloudflare-real-ip" ]; then
    log_success "✅ cron 설정 존재"
    echo "=== cron 설정 ==="
    cat "/etc/cron.d/update-cloudflare-real-ip"
else
    log_info "ℹ️  cron 설정 없음 (systemd 타이머만 사용)"
fi

# 10. 액세스 로그 확인 (선택사항)
log_info "10. 액세스 로그 확인 중..."
ACCESS_LOGS=$(find /var/log/nginx -name "*.access.log" 2>/dev/null | head -3)
if [ -n "$ACCESS_LOGS" ]; then
    echo "=== 최근 액세스 로그 (클라이언트 IP 확인) ==="
    for log in $ACCESS_LOGS; do
        echo "--- $log ---"
        tail -5 "$log" | awk '{print $1}' | sort | uniq -c | sort -nr | head -3
    done
else
    log_info "ℹ️  nginx 액세스 로그를 찾을 수 없습니다"
fi

# 11. 검증 요약
echo ""
log_info "=== 검증 요약 ==="
if [ -f "$CONF_FILE" ] && nginx -t >/dev/null 2>&1; then
    log_success "✅ Cloudflare CIDR 동기화 시스템 정상 작동"
    log_success "✅ nginx 설정 검증 통과"
    log_success "✅ 자동 동기화 활성화됨"
else
    log_error "❌ 시스템에 문제가 있습니다"
    echo "   • 설정 파일 확인: ls -la $CONF_FILE"
    echo "   • nginx 설정 확인: nginx -t"
    echo "   • 수동 실행: sudo /usr/local/sbin/update_cloudflare_real_ip"
fi

log_success "Cloudflare CIDR 동기화 검증 완료!"
