#!/bin/bash
# 빠른 복구 스크립트
# 목적: nginx 롤백, HSTS 비활성화 등 긴급 상황 대응

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
OUT="/etc/nginx/sites-available/${DOMAIN}.conf"

echo "=== DreamSeed 빠른 복구 도구 ==="
echo "도메인: $DOMAIN"
echo ""

# 1. nginx 빠른 롤백
nginx_rollback() {
    log_info "1. nginx 빠른 롤백 중..."
    
    if [ ! -f "$OUT" ]; then
        log_error "nginx 설정 파일이 없습니다: $OUT"
        return 1
    fi
    
    # 가장 최신 백업 찾기
    LATEST=$(ls -1t "${OUT}.bak."* 2>/dev/null | head -n1 || echo "")
    
    if [ -z "$LATEST" ]; then
        log_error "백업 파일이 없습니다: ${OUT}.bak.*"
        return 1
    fi
    
    log_info "최신 백업으로 복원: $LATEST"
    cp -af "$LATEST" "$OUT"
    
    # nginx 설정 검증
    if nginx -t; then
        systemctl reload nginx
        log_success "✅ nginx 롤백 완료"
    else
        log_error "❌ nginx 설정 검증 실패"
        return 1
    fi
}

# 2. HSTS 임시 비활성화
hsts_disable() {
    log_info "2. HSTS 임시 비활성화 중..."
    
    if [ ! -f "$OUT" ]; then
        log_error "nginx 설정 파일이 없습니다: $OUT"
        return 1
    fi
    
    # HSTS 헤더 주석 처리
    sed -i 's/add_header Strict-Transport-Security/#add_header Strict-Transport-Security/g' "$OUT"
    
    # nginx 설정 검증
    if nginx -t; then
        systemctl reload nginx
        log_success "✅ HSTS 비활성화 완료"
        log_warning "⚠️  브라우저에 저장된 HSTS 정책은 여전히 유효할 수 있습니다"
    else
        log_error "❌ nginx 설정 검증 실패"
        return 1
    fi
}

# 3. 서비스 상태 확인
service_status() {
    log_info "3. 서비스 상태 확인 중..."
    
    echo "=== nginx 상태 ==="
    systemctl status nginx --no-pager -l || true
    echo ""
    
    echo "=== 포트 상태 ==="
    ss -lntp | grep -E ":(80|443|8080|8000)" || true
    echo ""
    
    echo "=== 최근 nginx 로그 ==="
    tail -20 /var/log/nginx/error.log 2>/dev/null || echo "nginx 로그 없음"
    echo ""
}

# 4. 헬스 체크
health_check() {
    log_info "4. 헬스 체크 중..."
    
    # HTTP 체크
    if curl -sI "http://${DOMAIN}" | head -n1; then
        log_success "✅ HTTP 응답 정상"
    else
        log_warning "⚠️  HTTP 응답 실패"
    fi
    
    # HTTPS 체크
    if curl -skI "https://${DOMAIN}" | head -n1; then
        log_success "✅ HTTPS 응답 정상"
    else
        log_warning "⚠️  HTTPS 응답 실패"
    fi
}

# 5. 메뉴 표시
show_menu() {
    echo ""
    echo "=== 복구 옵션 ==="
    echo "1) nginx 빠른 롤백"
    echo "2) HSTS 임시 비활성화"
    echo "3) 서비스 상태 확인"
    echo "4) 헬스 체크"
    echo "5) 모든 복구 작업 실행"
    echo "0) 종료"
    echo ""
}

# 메인 메뉴
if [ $# -eq 0 ]; then
    show_menu
    read -p "선택하세요 (0-5): " choice
    
    case $choice in
        1) nginx_rollback ;;
        2) hsts_disable ;;
        3) service_status ;;
        4) health_check ;;
        5) 
            nginx_rollback
            hsts_disable
            service_status
            health_check
            ;;
        0) echo "종료합니다."; exit 0 ;;
        *) echo "잘못된 선택입니다."; exit 1 ;;
    esac
else
    # 명령행 인수로 실행
    case "$1" in
        "rollback") nginx_rollback ;;
        "hsts-disable") hsts_disable ;;
        "status") service_status ;;
        "health") health_check ;;
        "all")
            nginx_rollback
            hsts_disable
            service_status
            health_check
            ;;
        *) 
            echo "사용법: $0 [rollback|hsts-disable|status|health|all]"
            exit 1
            ;;
    esac
fi

log_success "복구 작업 완료!"
