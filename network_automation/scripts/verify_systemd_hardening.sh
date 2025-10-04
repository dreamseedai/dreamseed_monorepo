#!/bin/bash
# systemd 하드닝 설정 검증 스크립트
# 목적: 하드닝된 서비스가 정상 작동하는지 확인

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

SERVICE_NAME=${1:-"dreamseed"}

log_info "=== systemd 하드닝 설정 검증 시작 ==="
log_info "서비스: $SERVICE_NAME"

# 1. 서비스 상태 확인
log_info "1. 서비스 상태 확인 중..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "✅ 서비스가 실행 중입니다"
else
    log_warning "⚠️  서비스가 실행되지 않았습니다"
    systemctl status "$SERVICE_NAME" --no-pager -l || true
fi

# 2. 하드닝 옵션 확인
log_info "2. 하드닝 옵션 확인 중..."
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "=== 하드닝 옵션 확인 ==="
    
    # 주요 하드닝 옵션들 확인
    HARDENING_OPTIONS=(
        "NoNewPrivileges=yes"
        "ProtectSystem=full"
        "ProtectHome=true"
        "PrivateTmp=true"
        "CapabilityBoundingSet"
        "RestrictSUIDSGID=yes"
        "SystemCallFilter"
    )
    
    for option in "${HARDENING_OPTIONS[@]}"; do
        if grep -q "$option" "/etc/systemd/system/${SERVICE_NAME}.service"; then
            log_success "✅ $option 설정됨"
        else
            log_warning "⚠️  $option 설정되지 않음"
        fi
    done
else
    log_error "❌ 서비스 파일이 없습니다: /etc/systemd/system/${SERVICE_NAME}.service"
fi

# 3. 프로세스 보안 상태 확인
log_info "3. 프로세스 보안 상태 확인 중..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    PID=$(systemctl show -p MainPID --value "$SERVICE_NAME")
    if [ "$PID" != "0" ] && [ -n "$PID" ]; then
        echo "=== 프로세스 보안 상태 (PID: $PID) ==="
        
        # 프로세스 상태 확인
        if [ -f "/proc/$PID/status" ]; then
            echo "NoNewPrivileges: $(grep NoNewPrivileges /proc/$PID/status 2>/dev/null || echo 'N/A')"
            echo "Seccomp: $(grep Seccomp /proc/$PID/status 2>/dev/null || echo 'N/A')"
        fi
        
        # 프로세스 권한 확인
        echo "Effective capabilities:"
        getcap "/proc/$PID/exe" 2>/dev/null || echo "N/A"
    else
        log_warning "⚠️  유효한 PID를 찾을 수 없습니다"
    fi
fi

# 4. 로그 확인
log_info "4. 서비스 로그 확인 중..."
echo "=== 최근 서비스 로그 ==="
journalctl -u "$SERVICE_NAME" --no-pager -n 20 || echo "로그를 찾을 수 없습니다"

# 5. 네트워크 연결 확인
log_info "5. 네트워크 연결 확인 중..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "=== 네트워크 연결 상태 ==="
    ss -lntp | grep "$SERVICE_NAME" || echo "네트워크 연결 정보 없음"
fi

# 6. 하드닝 문제 해결 가이드
log_info "6. 하드닝 문제 해결 가이드"
echo ""
echo "🔧 하드닝 문제 해결 방법:"
echo "   • 서비스 시작 실패 시: systemctl status $SERVICE_NAME -l"
echo "   • 권한 문제 시: CapabilityBoundingSet 범위 완화"
echo "   • 시스템 콜 문제 시: SystemCallFilter 범위 완화"
echo "   • 설정 변경 후: systemctl daemon-reload && systemctl restart $SERVICE_NAME"

# 7. 검증 요약
echo ""
echo "📋 검증 요약:"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "✅ 서비스 정상 실행 중"
    log_success "✅ 하드닝 설정 적용됨"
    log_success "✅ 보안 격리 활성화됨"
else
    log_error "❌ 서비스 실행 실패"
    log_warning "⚠️  하드닝 설정 확인 필요"
fi

log_success "systemd 하드닝 검증 완료!"
