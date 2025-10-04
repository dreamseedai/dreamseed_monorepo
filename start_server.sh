#!/bin/bash

# DreamSeed Editor Server Startup Script
# 안정적인 서버 실행을 위한 스크립트

set -e  # 에러 발생 시 스크립트 종료

# 설정
PROJECT_DIR="/home/won/projects/dreamseed_monorepo"
PORT=9000
HOST="0.0.0.0"
LOG_FILE="$PROJECT_DIR/server.log"
PID_FILE="$PROJECT_DIR/server.pid"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# 기존 서버 프로세스 정리
cleanup_existing_servers() {
    log "기존 서버 프로세스 정리 중..."
    
    # PID 파일이 있으면 해당 프로세스 종료
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            log "기존 서버 프로세스 ($OLD_PID) 종료 중..."
            kill "$OLD_PID" 2>/dev/null || true
            sleep 2
        fi
        rm -f "$PID_FILE"
    fi
    
    # 포트 사용 중인 프로세스 찾아서 종료
    PORT_PID=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ ! -z "$PORT_PID" ]; then
        log "포트 $PORT 사용 중인 프로세스 ($PORT_PID) 종료 중..."
        kill "$PORT_PID" 2>/dev/null || true
        sleep 2
    fi
    
    # Python HTTP 서버 프로세스들 정리
    PIDS=$(ps aux | grep "python3 -m http.server" | grep -v grep | awk '{print $2}' || true)
    if [ ! -z "$PIDS" ]; then
        log "기존 Python HTTP 서버 프로세스들 종료 중..."
        echo "$PIDS" | xargs kill 2>/dev/null || true
        sleep 2
    fi
    
    success "기존 서버 프로세스 정리 완료"
}

# 서버 상태 확인
check_server_status() {
    if curl -s -I "http://$HOST:$PORT/dreamseed_editor.html" > /dev/null 2>&1; then
        return 0  # 서버 실행 중
    else
        return 1  # 서버 중지
    fi
}

# 서버 시작
start_server() {
    log "DreamSeed Editor 서버 시작 중..."
    log "포트: $PORT"
    log "호스트: $HOST"
    log "프로젝트 디렉토리: $PROJECT_DIR"
    
    cd "$PROJECT_DIR"
    
    # 서버 시작 (백그라운드)
    nohup python3 -m http.server "$PORT" --bind "$HOST" > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # PID 저장
    echo "$SERVER_PID" > "$PID_FILE"
    
    # 서버 시작 대기
    log "서버 시작 대기 중... (최대 10초)"
    for i in {1..10}; do
        if check_server_status; then
            success "서버가 성공적으로 시작되었습니다!"
            log "서버 PID: $SERVER_PID"
            log "에디터 URL: http://$HOST:$PORT/dreamseed_editor.html"
            return 0
        fi
        sleep 1
    done
    
    error "서버 시작 실패"
    return 1
}

# 서버 중지
stop_server() {
    log "서버 중지 중..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            log "서버 프로세스 ($PID) 종료됨"
        fi
        rm -f "$PID_FILE"
    fi
    
    success "서버 중지 완료"
}

# 서버 재시작
restart_server() {
    log "서버 재시작 중..."
    stop_server
    sleep 2
    start_server
}

# 메인 실행
main() {
    case "${1:-start}" in
        "start")
            cleanup_existing_servers
            start_server
            ;;
        "stop")
            stop_server
            ;;
        "restart")
            restart_server
            ;;
        "status")
            if check_server_status; then
                success "서버가 실행 중입니다"
                log "에디터 URL: http://$HOST:$PORT/dreamseed_editor.html"
            else
                warning "서버가 중지되어 있습니다"
            fi
            ;;
        "logs")
            if [ -f "$LOG_FILE" ]; then
                tail -f "$LOG_FILE"
            else
                error "로그 파일이 없습니다: $LOG_FILE"
            fi
            ;;
        *)
            echo "사용법: $0 {start|stop|restart|status|logs}"
            echo ""
            echo "명령어:"
            echo "  start   - 서버 시작 (기본값)"
            echo "  stop    - 서버 중지"
            echo "  restart - 서버 재시작"
            echo "  status  - 서버 상태 확인"
            echo "  logs    - 로그 실시간 보기"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"
