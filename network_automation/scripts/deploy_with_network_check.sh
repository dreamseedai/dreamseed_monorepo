#!/bin/bash
# 네트워크 연결성 자동 검증이 포함된 배포 스크립트
# 목적: "서버는 정상인데 외부에서 접속 불가" 문제를 사전에 방지

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 매개변수
PORT=${1:-8080}
SERVICE_NAME=${2:-"web-service"}
BIND_ADDRESS=${3:-"0.0.0.0"}

log_info "=== 네트워크 연결성 자동 검증 배포 시작 ==="
log_info "포트: $PORT"
log_info "서비스: $SERVICE_NAME"
log_info "바인딩 주소: $BIND_ADDRESS"

# 1. 포트 정책 검사
log_info "1. 포트 정책 검사 중..."
if [[ "$PORT" =~ ^(6000|6665|6666|6667|6668|6669|10080)$ ]]; then
    log_error "브라우저가 차단하는 포트입니다: $PORT"
    log_error "안전한 포트를 사용하세요: 8000, 8080, 3000, 5173"
    exit 1
fi

# 안전한 포트 목록
SAFE_PORTS=(8000 8080 3000 5173 9000 4000)
if [[ ! " ${SAFE_PORTS[@]} " =~ " ${PORT} " ]]; then
    log_warning "권장하지 않는 포트입니다: $PORT"
    log_warning "권장 포트: ${SAFE_PORTS[*]}"
fi

# 2. UFW 방화벽 자동 설정
log_info "2. UFW 방화벽 설정 중..."
if command -v ufw >/dev/null 2>&1; then
    # UFW가 활성화되어 있는지 확인
    if ufw status | grep -q "Status: active"; then
        log_info "UFW가 활성화되어 있습니다. 포트 $PORT 허용 중..."
        sudo ufw allow ${PORT}/tcp || {
            log_warning "UFW 포트 허용 실패 (권한 부족일 수 있음)"
        }
        sudo ufw reload || {
            log_warning "UFW 재로드 실패"
        }
        log_success "UFW 설정 완료"
    else
        log_info "UFW가 비활성화되어 있습니다."
    fi
else
    log_warning "UFW가 설치되지 않았습니다."
fi

# 3. 서버 시작
log_info "3. 서버 시작 중..."
# 기존 프로세스 종료
pkill -f "python3 -m http.server.*${PORT}" || true
sleep 2

# 서버 시작 (백그라운드)
python3 -m http.server ${PORT} --bind ${BIND_ADDRESS} &
SERVER_PID=$!
sleep 3

# 서버 시작 확인
if ! kill -0 $SERVER_PID 2>/dev/null; then
    log_error "서버 시작 실패"
    exit 1
fi

log_success "서버 시작 완료 (PID: $SERVER_PID)"

# 4. 로컬 연결성 테스트
log_info "4. 로컬 연결성 테스트 중..."
LOCAL_TEST_URL="http://127.0.0.1:${PORT}"
if curl -s -o /dev/null -w "%{http_code}" "$LOCAL_TEST_URL" | grep -q "200"; then
    log_success "로컬 연결성 테스트 통과"
else
    log_error "로컬 연결성 테스트 실패"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# 5. 외부 IP 연결성 테스트
log_info "5. 외부 IP 연결성 테스트 중..."
EXTERNAL_IP=$(hostname -I | awk '{print $1}')
EXTERNAL_TEST_URL="http://${EXTERNAL_IP}:${PORT}"

log_info "외부 IP: $EXTERNAL_IP"
log_info "테스트 URL: $EXTERNAL_TEST_URL"

if curl -s -o /dev/null -w "%{http_code}" "$EXTERNAL_TEST_URL" | grep -q "200"; then
    log_success "외부 IP 연결성 테스트 통과"
    EXTERNAL_ACCESS=true
else
    log_warning "외부 IP 연결성 테스트 실패"
    log_warning "방화벽 또는 네트워크 설정을 확인하세요"
    EXTERNAL_ACCESS=false
fi

# 6. 네트워크 진단 정보 수집
log_info "6. 네트워크 진단 정보 수집 중..."
{
    echo "=== 네트워크 진단 정보 ==="
    echo "시간: $(date)"
    echo "포트: $PORT"
    echo "서버 PID: $SERVER_PID"
    echo "외부 IP: $EXTERNAL_IP"
    echo ""
    echo "=== 포트 상태 ==="
    ss -lntp | grep ":$PORT " || echo "포트 $PORT가 LISTEN 상태가 아닙니다"
    echo ""
    echo "=== UFW 상태 ==="
    ufw status || echo "UFW 상태 확인 실패"
    echo ""
    echo "=== 네트워크 인터페이스 ==="
    ip addr show | grep -E "(inet |UP)" || echo "네트워크 인터페이스 정보 없음"
} > "network_diagnostics_${PORT}_$(date +%Y%m%d_%H%M%S).log"

# 7. Windows 클라이언트 검증 가이드 출력
log_info "7. 클라이언트 검증 가이드 생성 중..."

cat << EOF

${GREEN}🎉 배포 완료!${NC}

${BLUE}=== 서버 정보 ===${NC}
- 서버 IP: $EXTERNAL_IP
- 포트: $PORT
- 서비스: $SERVICE_NAME
- PID: $SERVER_PID

${BLUE}=== Windows 클라이언트 검증 가이드 ===${NC}
다음 순서로 접속을 확인하세요:

1. ${YELLOW}네트워크 연결 확인${NC}:
   ping $EXTERNAL_IP

2. ${YELLOW}HTTP 연결 확인${NC}:
   curl http://$EXTERNAL_IP:$PORT

3. ${YELLOW}브라우저 접속${NC}:
   http://$EXTERNAL_IP:$PORT

${BLUE}=== 문제 해결 가이드 ===${NC}
${RED}접속이 안 될 경우:${NC}
- Windows 방화벽 확인
- 브라우저 캐시 삭제 (Ctrl+Shift+Delete)
- 시크릿 모드로 테스트 (Ctrl+Shift+N)
- 프록시 설정 확인

${RED}서버 로그 확인:${NC}
- 네트워크 진단: network_diagnostics_${PORT}_*.log
- 서버 로그: tail -f /var/log/syslog

${BLUE}=== 서버 중지 방법 ===${NC}
kill $SERVER_PID

EOF

if [ "$EXTERNAL_ACCESS" = false ]; then
    log_warning "⚠️  외부 접속이 불가능합니다. 방화벽 설정을 확인하세요."
    log_warning "   sudo ufw allow $PORT/tcp"
    log_warning "   sudo ufw reload"
fi

# 8. 외부 접속 점검 및 Windows 가이드 출력
log_info "8. 외부 접속 점검 및 Windows 가이드 생성 중..."
EXTERNAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🔎 외부 접속 점검 (HTTP) on $EXTERNAL_IP:80"
if ! curl -sI "http://${EXTERNAL_IP}" | head -n1; then
    log_warning "⚠️  http://${EXTERNAL_IP}에 접근할 수 없습니다. Windows에서 연결이 안 될 경우 확인사항:"
    echo "   • UFW가 80/443을 허용하는지 확인 (ufw status)"
    echo "   • DNS가 이 서버를 가리키는지 확인"
    echo "   • 기업/VPN 프록시가 HTTPS를 강제하지 않는지 확인"
fi

echo ""
echo "💡 Windows 빠른 테스트:"
echo "   1) ping ${EXTERNAL_IP}"
echo "   2) curl http://${EXTERNAL_IP}"
echo "   3) 브라우저 → https://${EXTERNAL_IP} (또는 도메인)"

log_success "배포 및 네트워크 검증 완료!"
