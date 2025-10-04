#!/bin/bash

# DreamSeed Editor Server Monitor
# 서버 상태 모니터링 및 자동 재시작

set -e

# 설정
PROJECT_DIR="/home/won/projects/dreamseed_monorepo"
PORT=9000
HOST="0.0.0.0"
CHECK_INTERVAL=30  # 30초마다 체크
MAX_RETRIES=3      # 최대 재시도 횟수
LOG_FILE="$PROJECT_DIR/monitor.log"
START_SCRIPT="$PROJECT_DIR/start_server.sh"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 서버 상태 확인
check_server_health() {
    # HTTP 응답 확인
    if curl -s -I "http://$HOST:$PORT/dreamseed_editor.html" > /dev/null 2>&1; then
        # 응답 시간 측정
        RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "http://$HOST:$PORT/dreamseed_editor.html" 2>/dev/null || echo "999")
        if (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
            return 0  # 정상
        else
            warning "서버 응답 시간이 느림: ${RESPONSE_TIME}초"
            return 1  # 느림
        fi
    else
        return 2  # 연결 실패
    fi
}

# 서버 재시작
restart_server() {
    log "서버 재시작 시도 중..."
    
    if [ -f "$START_SCRIPT" ]; then
        "$START_SCRIPT" restart
        if [ $? -eq 0 ]; then
            success "서버 재시작 성공"
            return 0
        else
            error "서버 재시작 실패"
            return 1
        fi
    else
        error "시작 스크립트를 찾을 수 없습니다: $START_SCRIPT"
        return 1
    fi
}

# 모니터링 루프
monitor_loop() {
    log "DreamSeed Editor 서버 모니터링 시작"
    log "체크 간격: ${CHECK_INTERVAL}초"
    log "에디터 URL: http://$HOST:$PORT/dreamseed_editor.html"
    
    RETRY_COUNT=0
    LAST_SUCCESS=$(date +%s)
    
    while true; do
        CURRENT_TIME=$(date +%s)
        UPTIME=$((CURRENT_TIME - LAST_SUCCESS))
        
        log "서버 상태 확인 중... (가동시간: ${UPTIME}초)"
        
        check_server_health
        HEALTH_STATUS=$?
        
        case $HEALTH_STATUS in
            0)  # 정상
                if [ $RETRY_COUNT -gt 0 ]; then
                    success "서버가 정상 상태로 복구되었습니다"
                    RETRY_COUNT=0
                fi
                LAST_SUCCESS=$CURRENT_TIME
                ;;
            1)  # 느림
                warning "서버 응답이 느립니다. 모니터링 계속..."
                ;;
            2)  # 연결 실패
                error "서버 연결 실패"
                RETRY_COUNT=$((RETRY_COUNT + 1))
                
                if [ $RETRY_COUNT -le $MAX_RETRIES ]; then
                    log "재시도 $RETRY_COUNT/$MAX_RETRIES"
                    restart_server
                    if [ $? -eq 0 ]; then
                        RETRY_COUNT=0
                        LAST_SUCCESS=$CURRENT_TIME
                    fi
                else
                    error "최대 재시도 횟수 초과. 모니터링 중단"
                    exit 1
                fi
                ;;
        esac
        
        sleep $CHECK_INTERVAL
    done
}

# 시스템 리소스 모니터링
monitor_resources() {
    while true; do
        # CPU 사용률
        CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
        
        # 메모리 사용률
        MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
        
        # 디스크 사용률
        DISK_USAGE=$(df -h "$PROJECT_DIR" | awk 'NR==2{print $5}' | sed 's/%//')
        
        log "시스템 리소스 - CPU: ${CPU_USAGE}%, 메모리: ${MEMORY_USAGE}%, 디스크: ${DISK_USAGE}%"
        
        # 리소스 사용률이 높으면 경고
        if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
            warning "CPU 사용률이 높습니다: ${CPU_USAGE}%"
        fi
        
        if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
            warning "메모리 사용률이 높습니다: ${MEMORY_USAGE}%"
        fi
        
        if [ "$DISK_USAGE" -gt 80 ]; then
            warning "디스크 사용률이 높습니다: ${DISK_USAGE}%"
        fi
        
        sleep 300  # 5분마다 체크
    done
}

# 메인 실행
main() {
    case "${1:-monitor}" in
        "monitor")
            # 백그라운드에서 리소스 모니터링 시작
            monitor_resources &
            RESOURCE_PID=$!
            
            # 메인 모니터링 루프
            monitor_loop
            ;;
        "check")
            check_server_health
            case $? in
                0) success "서버가 정상 상태입니다" ;;
                1) warning "서버 응답이 느립니다" ;;
                2) error "서버 연결 실패" ;;
            esac
            ;;
        "restart")
            restart_server
            ;;
        *)
            echo "사용법: $0 {monitor|check|restart}"
            echo ""
            echo "명령어:"
            echo "  monitor - 지속적인 서버 모니터링 (기본값)"
            echo "  check   - 한 번만 서버 상태 확인"
            echo "  restart - 서버 재시작"
            exit 1
            ;;
    esac
}

# 시그널 핸들러
cleanup() {
    log "모니터링 중단됨"
    if [ ! -z "$RESOURCE_PID" ]; then
        kill "$RESOURCE_PID" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# 스크립트 실행
main "$@"
