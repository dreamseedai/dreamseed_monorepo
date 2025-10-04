#!/bin/bash
# Cloudflare CIDR 자동 동기화 시스템 설치 스크립트
# 목적: 스크립트, 서비스, 타이머를 시스템에 설치하고 활성화

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

SCRIPT_DIR=$(dirname "$0")

log_info "=== Cloudflare CIDR 자동 동기화 시스템 설치 시작 ==="

# 1. 스크립트 설치
log_info "1. 스크립트 설치 중..."
if [ -f "$SCRIPT_DIR/update_cloudflare_real_ip.sh" ]; then
    sudo install -m 0755 "$SCRIPT_DIR/update_cloudflare_real_ip.sh" /usr/local/sbin/update_cloudflare_real_ip
    log_success "✅ 스크립트 설치 완료: /usr/local/sbin/update_cloudflare_real_ip"
else
    log_error "❌ 스크립트 파일을 찾을 수 없습니다: $SCRIPT_DIR/update_cloudflare_real_ip.sh"
    exit 1
fi

# 2. systemd 서비스 설치
log_info "2. systemd 서비스 설치 중..."
if [ -f "$SCRIPT_DIR/update-cloudflare-real-ip.service" ]; then
    sudo cp "$SCRIPT_DIR/update-cloudflare-real-ip.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    log_success "✅ systemd 서비스 설치 완료"
else
    log_error "❌ 서비스 파일을 찾을 수 없습니다: $SCRIPT_DIR/update-cloudflare-real-ip.service"
    exit 1
fi

# 3. systemd 타이머 설치
log_info "3. systemd 타이머 설치 중..."
if [ -f "$SCRIPT_DIR/update-cloudflare-real-ip.timer" ]; then
    sudo cp "$SCRIPT_DIR/update-cloudflare-real-ip.timer" /etc/systemd/system/
    sudo systemctl daemon-reload
    log_success "✅ systemd 타이머 설치 완료"
else
    log_error "❌ 타이머 파일을 찾을 수 없습니다: $SCRIPT_DIR/update-cloudflare-real-ip.timer"
    exit 1
fi

# 4. nginx conf.d 디렉토리 생성
log_info "4. nginx 설정 디렉토리 생성 중..."
sudo mkdir -p /etc/nginx/conf.d
log_success "✅ nginx 설정 디렉토리 생성 완료"

# 5. 초기 실행
log_info "5. 초기 CIDR 동기화 실행 중..."
if sudo /usr/local/sbin/update_cloudflare_real_ip; then
    log_success "✅ 초기 CIDR 동기화 완료"
else
    log_warning "⚠️  초기 동기화 실패 (네트워크 문제일 수 있음)"
fi

# 6. systemd 타이머 활성화
log_info "6. systemd 타이머 활성화 중..."
if sudo systemctl enable --now update-cloudflare-real-ip.timer; then
    log_success "✅ systemd 타이머 활성화 완료"
else
    log_error "❌ systemd 타이머 활성화 실패"
    exit 1
fi

# 7. 타이머 상태 확인
log_info "7. 타이머 상태 확인 중..."
echo "=== 타이머 상태 ==="
sudo systemctl list-timers | grep cloudflare || log_warning "타이머가 표시되지 않습니다"

# 8. cron 대안 설정 (선택사항)
log_info "8. cron 대안 설정 (선택사항)..."
read -p "cron으로도 설정하시겠습니까? (y/N): " use_cron
if [[ "$use_cron" =~ ^[Yy]$ ]]; then
    echo '17 3 * * * root /usr/local/sbin/update_cloudflare_real_ip >/var/log/update_cloudflare_real_ip.log 2>&1' | sudo tee /etc/cron.d/update-cloudflare-real-ip
    log_success "✅ cron 설정 완료 (매일 03:17 실행)"
else
    log_info "cron 설정을 건너뜁니다"
fi

# 9. nginx 설정 검증
log_info "9. nginx 설정 검증 중..."
if sudo nginx -t; then
    log_success "✅ nginx 설정 검증 통과"
else
    log_error "❌ nginx 설정 검증 실패"
    exit 1
fi

# 10. 설치 완료 요약
echo ""
log_success "🎉 Cloudflare CIDR 자동 동기화 시스템 설치 완료!"
echo ""
echo "📋 설치된 구성요소:"
echo "   • 스크립트: /usr/local/sbin/update_cloudflare_real_ip"
echo "   • 서비스: /etc/systemd/system/update-cloudflare-real-ip.service"
echo "   • 타이머: /etc/systemd/system/update-cloudflare-real-ip.timer"
echo "   • 설정 파일: /etc/nginx/conf.d/real_ip_cloudflare.conf"
echo ""
echo "🔧 관리 명령어:"
echo "   • 수동 실행: sudo /usr/local/sbin/update_cloudflare_real_ip"
echo "   • 타이머 상태: sudo systemctl list-timers | grep cloudflare"
echo "   • 서비스 로그: sudo journalctl -u update-cloudflare-real-ip.service"
echo "   • 설정 확인: sudo nginx -T | grep real_ip_cloudflare"
echo ""
echo "⚠️  보안 주의사항:"
echo "   • Cloudflare 뒤에 놓인 서버에서만 사용하세요"
echo "   • 직접 접속이 가능한 환경이면 방화벽으로 원 서버 접근을 차단하세요"
echo "   • real_ip_recursive on과 함께 신뢰 범위를 최소화하세요"
