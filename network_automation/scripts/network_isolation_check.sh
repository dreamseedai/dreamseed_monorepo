#!/bin/bash
# 네트워크 격리 및 NAT 헤어핀 점검 스크립트
# 목적: 동일 LAN인데 접속 불가 케이스 방지

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

log_info "=== 네트워크 격리 및 NAT 헤어핀 점검 시작 ==="

# 1. 이중 NIC/서브넷 점검
log_info "1. 네트워크 인터페이스 및 라우팅 점검 중..."
echo "=== 네트워크 인터페이스 ==="
ip addr show
echo ""
echo "=== 라우팅 테이블 ==="
ip route show
echo ""

# 2. NAT 헤어핀 지원 확인
log_info "2. NAT 헤어핀 지원 확인 중..."
DOMAIN=${1:-"staging.dreamseedai.com"}
EXTERNAL_IP=$(hostname -I | awk '{print $1}')

echo "=== DNS 해석 확인 ==="
echo "도메인: $DOMAIN"
echo "서버 IP: $EXTERNAL_IP"

# DNS 해석 결과 확인
DNS_RESULT=$(dig +short "$DOMAIN" 2>/dev/null || echo "DNS 해석 실패")
echo "DNS 해석 결과: $DNS_RESULT"

if [ "$DNS_RESULT" = "$EXTERNAL_IP" ]; then
    log_success "✅ DNS가 서버 IP를 올바르게 가리킴"
elif [ "$DNS_RESULT" != "DNS 해석 실패" ] && [ "$DNS_RESULT" != "$EXTERNAL_IP" ]; then
    log_warning "⚠️  DNS가 다른 IP를 가리킴: $DNS_RESULT"
    log_warning "   내부에서 접속 시 NAT 헤어핀 문제 가능성"
    echo ""
    echo "💡 해결 방법:"
    echo "   Windows hosts 파일에 추가:"
    echo "   $EXTERNAL_IP  $DOMAIN"
    echo ""
    echo "   PowerShell 명령어:"
    echo "   Add-Content -Path \"C:\\Windows\\System32\\drivers\\etc\\hosts\" -Value \"\\n$EXTERNAL_IP  $DOMAIN\""
else
    log_warning "⚠️  DNS 해석 실패 - 도메인 설정 확인 필요"
fi

# 3. Path MTU 이슈 점검 (선택)
log_info "3. Path MTU 점검 중..."
CLIENT_IP=${2:-""}
if [ -n "$CLIENT_IP" ]; then
    echo "클라이언트 IP: $CLIENT_IP"
    echo "MTU 테스트 (1472 바이트):"
    if ping -M do -s 1472 -c 1 "$CLIENT_IP" >/dev/null 2>&1; then
        log_success "✅ MTU 1500 OK"
    else
        log_warning "⚠️  MTU 문제 가능성 - 대형 패킷 드랍 가능"
        echo "   해결: 라우터 MTU 설정 확인 또는 패킷 크기 조정"
    fi
else
    log_info "클라이언트 IP가 제공되지 않음 - MTU 테스트 스킵"
fi

# 4. Wi-Fi AP 격리 점검 안내
log_info "4. Wi-Fi AP 격리 점검 안내"
echo ""
echo "🔧 Wi-Fi AP 설정 확인사항:"
echo "   • 'Client/AP Isolation(무선 간 통신 차단)' OFF 확인"
echo "   • 'AP Isolation' 또는 'Station Isolation' 비활성화"
echo "   • 같은 SSID 내에서 기기 간 통신 허용 설정"

# 5. 네트워크 진단 요약
echo ""
echo "📋 네트워크 진단 요약:"
echo "   • 서버 IP: $EXTERNAL_IP"
echo "   • 도메인: $DOMAIN"
echo "   • DNS 해석: $DNS_RESULT"
echo "   • NAT 헤어핀: $([ "$DNS_RESULT" = "$EXTERNAL_IP" ] && echo "OK" || echo "주의 필요")"

log_success "네트워크 격리 점검 완료!"
