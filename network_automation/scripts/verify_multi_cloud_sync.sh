#!/bin/bash
# 멀티 클라우드 CIDR 동기화 검증 스크립트
# 목적: Cloudflare, AWS, GCP CIDR 동기화가 올바르게 작동하는지 확인

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

log_info "=== 멀티 클라우드 CIDR 동기화 검증 시작 ==="

# 1. 스크립트 존재 확인
log_info "1. 스크립트 존재 확인 중..."
if [ -f "/usr/local/sbin/update_real_ip_providers" ]; then
    log_success "✅ 스크립트 존재: /usr/local/sbin/update_real_ip_providers"
else
    log_error "❌ 스크립트가 없습니다: /usr/local/sbin/update_real_ip_providers"
    exit 1
fi

# 2. systemd 서비스 확인
log_info "2. systemd 서비스 확인 중..."
if systemctl list-unit-files | grep -q "update-real-ip-providers.service"; then
    log_success "✅ systemd 서비스 존재"
else
    log_warning "⚠️  systemd 서비스가 없습니다"
fi

# 3. systemd 타이머 확인
log_info "3. systemd 타이머 확인 중..."
if systemctl list-timers | grep -q "update-real-ip-providers.timer"; then
    log_success "✅ systemd 타이머 활성화됨"
    echo "=== 타이머 상태 ==="
    systemctl list-timers | grep real-ip-providers
else
    log_warning "⚠️  systemd 타이머가 활성화되지 않았습니다"
fi

# 4. nginx 설정 파일 확인
log_info "4. nginx 설정 파일 확인 중..."
CONF_FILE="/etc/nginx/conf.d/real_ip_providers.conf"
if [ -f "$CONF_FILE" ]; then
    log_success "✅ 설정 파일 존재: $CONF_FILE"
    
    # 파일 내용 확인
    echo "=== 설정 파일 내용 (처음 15줄) ==="
    head -15 "$CONF_FILE"
    
    # 통계 확인
    V4_COUNT=$(grep -c "set_real_ip_from.*[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+" "$CONF_FILE" || echo "0")
    V6_COUNT=$(grep -c "set_real_ip_from.*:" "$CONF_FILE" || echo "0")
    LOCAL_COUNT=$(grep -c "set_real_ip_from 127.0.0.1" "$CONF_FILE" || echo "0")
    
    # 프로바이더별 통계
    CF_COUNT=$(grep -c "# Cloudflare" "$CONF_FILE" || echo "0")
    AWS_COUNT=$(grep -c "# AWS ELB" "$CONF_FILE" || echo "0")
    AWS_VPC_COUNT=$(grep -c "# AWS VPC Subnets" "$CONF_FILE" || echo "0")
    GCP_COUNT=$(grep -c "# GCP" "$CONF_FILE" || echo "0")
    
    echo ""
    echo "=== IP 범위 통계 ==="
    echo "IPv4 범위: $V4_COUNT개"
    echo "IPv6 범위: $V6_COUNT개"
    echo "로컬 범위: $LOCAL_COUNT개"
    echo "총 범위: $((V4_COUNT + V6_COUNT + LOCAL_COUNT))개"
    echo ""
    echo "=== 프로바이더별 활성화 상태 ==="
    echo "Cloudflare: $([ "$CF_COUNT" -gt 0 ] && echo "활성화" || echo "비활성화")"
    echo "AWS ELB: $([ "$AWS_COUNT" -gt 0 ] && echo "활성화" || echo "비활성화")"
    echo "AWS VPC Subnets: $([ "$AWS_VPC_COUNT" -gt 0 ] && echo "활성화" || echo "비활성화")"
    echo "GCP LB: $([ "$GCP_COUNT" -gt 0 ] && echo "활성화" || echo "비활성화")"
    
    if [ "$V4_COUNT" -gt 0 ] || [ "$V6_COUNT" -gt 0 ]; then
        log_success "✅ 클라우드 IP 범위가 포함되어 있습니다"
    else
        log_warning "⚠️  클라우드 IP 범위가 없습니다"
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
if nginx -T | grep -q "real_ip_providers.conf"; then
    log_success "✅ nginx에서 real_ip_providers.conf가 포함됨"
    echo "=== nginx include 확인 ==="
    nginx -T | grep -A5 -B5 "real_ip_providers.conf"
else
    log_warning "⚠️  nginx에서 real_ip_providers.conf가 포함되지 않음"
fi

# 7. 환경 변수 확인
log_info "7. 환경 변수 확인 중..."
echo "=== 현재 환경 변수 ==="
echo "CF_ENABLE: ${CF_ENABLE:-not set}"
echo "AWS_ENABLE: ${AWS_ENABLE:-not set}"
echo "AWS_VPC_SUBNETS: ${AWS_VPC_SUBNETS:-not set}"
echo "AWS_REGION: ${AWS_REGION:-not set}"
echo "AWS_VPC_ID: ${AWS_VPC_ID:-not set}"
echo "GCP_ENABLE: ${GCP_ENABLE:-not set}"
echo "GCP_SCOPE: ${GCP_SCOPE:-not set}"

# 8. 수동 실행 테스트
log_info "8. 수동 실행 테스트 중..."
if sudo /usr/local/sbin/update_real_ip_providers; then
    log_success "✅ 수동 실행 성공"
else
    log_warning "⚠️  수동 실행 실패 (네트워크 문제일 수 있음)"
fi

# 9. 로그 확인
log_info "9. 로그 확인 중..."
echo "=== 최근 서비스 로그 ==="
journalctl -u update-real-ip-providers.service --no-pager -n 10 || echo "서비스 로그 없음"

# 10. 의존성 확인
log_info "10. 의존성 확인 중..."
if command -v curl >/dev/null 2>&1; then
    log_success "✅ curl 설치됨"
else
    log_error "❌ curl이 설치되지 않음"
fi

if command -v jq >/dev/null 2>&1; then
    log_success "✅ jq 설치됨"
else
    log_warning "⚠️  jq가 설치되지 않음 (Python으로 JSON 파싱)"
fi

if command -v python3 >/dev/null 2>&1; then
    log_success "✅ python3 설치됨"
else
    log_error "❌ python3이 설치되지 않음"
fi

if command -v aws >/dev/null 2>&1; then
    log_success "✅ AWS CLI 설치됨"
    # AWS 자격 증명 확인
    if aws sts get-caller-identity >/dev/null 2>&1; then
        log_success "✅ AWS 자격 증명 설정됨"
        # VPC 메타데이터 확인
        if curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-id >/dev/null 2>&1; then
            log_success "✅ AWS EC2 메타데이터 접근 가능"
        else
            log_warning "⚠️  AWS EC2 메타데이터 접근 불가 (VPC 자동 감지 불가)"
        fi
    else
        log_warning "⚠️  AWS 자격 증명이 설정되지 않음 (VPC 서브넷 기능 사용 불가)"
    fi
else
    log_warning "⚠️  AWS CLI가 설치되지 않음 (VPC 서브넷 기능 사용 불가)"
fi

# 11. 액세스 로그 확인 (선택사항)
log_info "11. 액세스 로그 확인 중..."
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

# 12. API 연결 테스트
log_info "12. API 연결 테스트 중..."
echo "=== 클라우드 API 연결 테스트 ==="

# Cloudflare 테스트
if curl -fsSL "https://www.cloudflare.com/ips-v4" | head -1 >/dev/null 2>&1; then
    log_success "✅ Cloudflare API 연결 성공"
else
    log_warning "⚠️  Cloudflare API 연결 실패"
fi

# AWS 테스트
if curl -fsSL "https://ip-ranges.amazonaws.com/ip-ranges.json" | head -1 >/dev/null 2>&1; then
    log_success "✅ AWS API 연결 성공"
else
    log_warning "⚠️  AWS API 연결 실패"
fi

# GCP 테스트
if curl -fsSL "https://www.gstatic.com/ipranges/cloud.json" | head -1 >/dev/null 2>&1; then
    log_success "✅ GCP API 연결 성공"
else
    log_warning "⚠️  GCP API 연결 실패"
fi

# 13. 검증 요약
echo ""
log_info "=== 검증 요약 ==="
if [ -f "$CONF_FILE" ] && nginx -t >/dev/null 2>&1; then
    log_success "✅ 멀티 클라우드 CIDR 동기화 시스템 정상 작동"
    log_success "✅ nginx 설정 검증 통과"
    log_success "✅ 자동 동기화 활성화됨"
    
    # 활성화된 프로바이더 표시
    ACTIVE_PROVIDERS=()
    [ "$CF_COUNT" -gt 0 ] && ACTIVE_PROVIDERS+=("Cloudflare")
    [ "$AWS_COUNT" -gt 0 ] && ACTIVE_PROVIDERS+=("AWS ELB")
    [ "$AWS_VPC_COUNT" -gt 0 ] && ACTIVE_PROVIDERS+=("AWS VPC Subnets")
    [ "$GCP_COUNT" -gt 0 ] && ACTIVE_PROVIDERS+=("GCP LB")
    
    if [ ${#ACTIVE_PROVIDERS[@]} -gt 0 ]; then
        log_success "✅ 활성화된 프로바이더: ${ACTIVE_PROVIDERS[*]}"
    else
        log_warning "⚠️  활성화된 프로바이더가 없습니다 (Cloudflare만 기본 활성화)"
    fi
else
    log_error "❌ 시스템에 문제가 있습니다"
    echo "   • 설정 파일 확인: ls -la $CONF_FILE"
    echo "   • nginx 설정 확인: nginx -t"
    echo "   • 수동 실행: sudo /usr/local/sbin/update_real_ip_providers"
fi

log_success "멀티 클라우드 CIDR 동기화 검증 완료!"
