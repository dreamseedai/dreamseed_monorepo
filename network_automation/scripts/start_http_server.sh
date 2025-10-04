#!/bin/bash
# 안전한 포트 + 바인딩 + UFW 자동 허용 + 외부 접속 점검 + Windows 가이드
# 목적: 개발용 HTTP 서버를 브라우저 호환성 문제 없이 안전하게 시작

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

# 매개변수
PORT=${1:-8080}
DIR=${2:-$(pwd)}

log_info "=== 안전한 HTTP 서버 시작 ==="
log_info "포트: $PORT"
log_info "디렉토리: $DIR"

# 1. 포트 정책 검사
log_info "1. 포트 정책 검사 중..."
if [[ "$PORT" =~ ^(6000|6665|6666|6667|6668|6669|10080)$ ]]; then
    log_error "브라우저가 차단하는 포트입니다: $PORT"
    log_error "안전한 포트를 사용하세요: 8000, 8080, 3000, 5173"
    exit 1
fi

# 2. UFW 방화벽 자동 설정
log_info "2. UFW 방화벽 설정 중..."
if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        log_info "UFW가 활성화되어 있습니다. 포트 $PORT 허용 중..."
        ufw allow "$PORT"/tcp >/dev/null 2>&1 || {
            log_warning "UFW 포트 허용 실패 (권한 부족일 수 있음)"
        }
        ufw reload >/dev/null 2>&1 || {
            log_warning "UFW 재로드 실패"
        }
        log_success "UFW 설정 완료"
    else
        log_info "UFW가 비활성화되어 있습니다."
    fi
else
    log_warning "UFW가 설치되지 않았습니다."
fi

# 3. 외부 접속 점검 준비
HOST_IP=$(hostname -I | awk '{print $1}')
log_info "3. 외부 접속 점검 준비 중..."
log_info "서버 IP: $HOST_IP"

# 4. 기존 프로세스 정리
log_info "4. 기존 프로세스 정리 중..."
pkill -f "python3 -m http.server.*${PORT}" || true
sleep 2

# 5. 서버 시작
log_info "5. HTTP 서버 시작 중..."
python3 -m http.server "$PORT" --directory "$DIR" --bind 0.0.0.0 &
SERVER_PID=$!
sleep 3

# 서버 시작 확인
if ! kill -0 $SERVER_PID 2>/dev/null; then
    log_error "서버 시작 실패"
    exit 1
fi

log_success "서버 시작 완료 (PID: $SERVER_PID)"

# 6. 외부 접속 점검
log_info "6. 외부 접속 점검 중..."
log_info "🔎 접속 가능성 사전 점검: http://$HOST_IP:$PORT"

if timeout 2 bash -lc "</dev/tcp/$HOST_IP/$PORT" 2>/dev/null; then
    log_success "✅ 서버가 외부에서 접근 가능합니다: http://$HOST_IP:$PORT"
else
    log_warning "⚠️  외부에서 접근할 수 없습니다. UFW, 바인딩 주소, 또는 호스트 방화벽을 확인하세요."
fi

# 7. HTTP 응답 테스트
if curl -sI "http://$HOST_IP:$PORT" | head -n1; then
    log_success "✅ HTTP 응답 정상"
else
    log_warning "⚠️  HTTP 응답 테스트 실패"
fi

# 8. Windows 클라이언트 가이드 출력
echo ""
echo "💡 Windows 빠른 테스트:"
echo "   1) ping $HOST_IP"
echo "   2) curl http://$HOST_IP:$PORT"
echo "   3) 브라우저 → http://$HOST_IP:$PORT"

echo ""
echo "🔧 문제 해결:"
echo "   • Windows 방화벽 확인"
echo "   • 브라우저 캐시 삭제 (Ctrl+Shift+Delete)"
echo "   • 시크릿 모드로 테스트 (Ctrl+Shift+N)"
echo "   • 프록시 설정 확인"

echo ""
echo "📊 서버 정보:"
echo "   • 서버 IP: $HOST_IP"
echo "   • 포트: $PORT"
echo "   • 디렉토리: $DIR"
echo "   • PID: $SERVER_PID"
echo "   • 중지 명령: kill $SERVER_PID"

log_success "HTTP 서버 설정 완료!"

# 서버 대기
wait $SERVER_PID
