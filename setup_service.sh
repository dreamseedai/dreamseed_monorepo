#!/bin/bash

# DreamSeed Editor Service Setup Script
# systemd 서비스 설정을 위한 스크립트

set -e

# 설정
SERVICE_NAME="dreamseed-editor"
SERVICE_FILE="/home/won/projects/dreamseed_monorepo/dreamseed-editor.service"
SYSTEMD_DIR="/etc/systemd/system"
PROJECT_DIR="/home/won/projects/dreamseed_monorepo"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로그 함수
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 서비스 설치
install_service() {
    log "DreamSeed Editor 서비스 설치 중..."
    
    # sudo 권한 확인
    if [ "$EUID" -ne 0 ]; then
        error "이 스크립트는 sudo 권한이 필요합니다"
        echo "사용법: sudo $0 install"
        exit 1
    fi
    
    # 서비스 파일 복사
    if [ -f "$SERVICE_FILE" ]; then
        cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
        success "서비스 파일 복사 완료"
    else
        error "서비스 파일을 찾을 수 없습니다: $SERVICE_FILE"
        exit 1
    fi
    
    # systemd 데몬 리로드
    systemctl daemon-reload
    success "systemd 데몬 리로드 완료"
    
    # 서비스 활성화
    systemctl enable "$SERVICE_NAME"
    success "서비스 활성화 완료"
    
    log "서비스 설치가 완료되었습니다"
    log "서비스 시작: sudo systemctl start $SERVICE_NAME"
    log "서비스 상태: sudo systemctl status $SERVICE_NAME"
    log "서비스 로그: sudo journalctl -u $SERVICE_NAME -f"
}

# 서비스 제거
uninstall_service() {
    log "DreamSeed Editor 서비스 제거 중..."
    
    # sudo 권한 확인
    if [ "$EUID" -ne 0 ]; then
        error "이 스크립트는 sudo 권한이 필요합니다"
        echo "사용법: sudo $0 uninstall"
        exit 1
    fi
    
    # 서비스 중지
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    
    # 서비스 비활성화
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    
    # 서비스 파일 제거
    rm -f "$SYSTEMD_DIR/$SERVICE_NAME.service"
    
    # systemd 데몬 리로드
    systemctl daemon-reload
    
    success "서비스 제거 완료"
}

# 서비스 상태 확인
check_service() {
    log "서비스 상태 확인 중..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        success "서비스가 실행 중입니다"
        systemctl status "$SERVICE_NAME" --no-pager -l
    else
        warning "서비스가 중지되어 있습니다"
        systemctl status "$SERVICE_NAME" --no-pager -l
    fi
}

# 서비스 시작
start_service() {
    log "서비스 시작 중..."
    
    if [ "$EUID" -ne 0 ]; then
        error "이 스크립트는 sudo 권한이 필요합니다"
        echo "사용법: sudo $0 start"
        exit 1
    fi
    
    systemctl start "$SERVICE_NAME"
    success "서비스 시작 완료"
    check_service
}

# 서비스 중지
stop_service() {
    log "서비스 중지 중..."
    
    if [ "$EUID" -ne 0 ]; then
        error "이 스크립트는 sudo 권한이 필요합니다"
        echo "사용법: sudo $0 stop"
        exit 1
    fi
    
    systemctl stop "$SERVICE_NAME"
    success "서비스 중지 완료"
}

# 서비스 재시작
restart_service() {
    log "서비스 재시작 중..."
    
    if [ "$EUID" -ne 0 ]; then
        error "이 스크립트는 sudo 권한이 필요합니다"
        echo "사용법: sudo $0 restart"
        exit 1
    fi
    
    systemctl restart "$SERVICE_NAME"
    success "서비스 재시작 완료"
    check_service
}

# 서비스 로그 보기
show_logs() {
    log "서비스 로그 표시 중..."
    sudo journalctl -u "$SERVICE_NAME" -f --no-pager
}

# 메인 실행
main() {
    case "${1:-help}" in
        "install")
            install_service
            ;;
        "uninstall")
            uninstall_service
            ;;
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "status")
            check_service
            ;;
        "logs")
            show_logs
            ;;
        "help"|*)
            echo "DreamSeed Editor Service Setup"
            echo ""
            echo "사용법: $0 {install|uninstall|start|stop|restart|status|logs}"
            echo ""
            echo "명령어:"
            echo "  install   - systemd 서비스 설치 (sudo 필요)"
            echo "  uninstall - systemd 서비스 제거 (sudo 필요)"
            echo "  start     - 서비스 시작 (sudo 필요)"
            echo "  stop      - 서비스 중지 (sudo 필요)"
            echo "  restart   - 서비스 재시작 (sudo 필요)"
            echo "  status    - 서비스 상태 확인"
            echo "  logs      - 서비스 로그 실시간 보기"
            echo ""
            echo "예시:"
            echo "  sudo $0 install    # 서비스 설치"
            echo "  sudo $0 start      # 서비스 시작"
            echo "  $0 status          # 상태 확인"
            echo "  $0 logs            # 로그 보기"
            ;;
    esac
}

# 스크립트 실행
main "$@"
