#!/bin/bash
# TLS 원샷 & 갱신 자동화 + 외부 접속 점검 + Windows 가이드
# 사용법: sudo ./deploy_proxy_and_tls.sh <domain> <static_root> <api_upstream_with_slash> <hsts:on|off>
# 예시: sudo ./deploy_proxy_and_tls.sh staging.dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ off

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
DOMAIN=${1:?"domain"}
STATIC_ROOT=${2:?"static_root"}
API_UPSTREAM=${3:?"api_upstream (e.g., http://127.0.0.1:8000/)"}
HSTS=${4:-off}

log_info "=== Nginx + TLS 자동 배포 시작 ==="
log_info "도메인: $DOMAIN"
log_info "정적 루트: $STATIC_ROOT"
log_info "API 업스트림: $API_UPSTREAM"
log_info "HSTS: $HSTS"

# 0. DNS 및 시간 동기화 사전 점검
log_info "0. DNS 및 시간 동기화 사전 점검 중..."
echo "=== DNS 해석 확인 ==="
dig +short "$DOMAIN" || true
getent hosts "$DOMAIN" || true
echo "=== 시간 동기화 상태 ==="
timedatectl | sed -n '1,3p'
echo ""

# 시간 동기화 활성화
if ! timedatectl show | grep -q "NTP=yes"; then
    log_info "NTP 시간 동기화 활성화 중..."
    timedatectl set-ntp true || log_warning "NTP 설정 실패"
fi

# --- 전제 조건 ---
log_info "1. 전제 조건 설치 중..."
apt-get update -y
apt-get install -y nginx curl ca-certificates certbot python3-certbot-nginx

# ACME용 웹루트
log_info "2. ACME 웹루트 설정 중..."
mkdir -p /var/www/letsencrypt
chown -R www-data:www-data /var/www/letsencrypt

# 80/443 포트 방화벽 열기
log_info "3. 방화벽 설정 중..."
ufw allow 80/tcp || true
ufw allow 443/tcp || true

# nginx 템플릿 렌더링
log_info "4. nginx 템플릿 렌더링 중..."
TPL_DIR=$(dirname "$0")/../nginx
OUT=/etc/nginx/sites-available/${DOMAIN}.conf
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

export SERVER_NAME=${DOMAIN}
export STATIC_ROOT
export API_UPSTREAM
export HSTS_ENABLED=${HSTS}

# 기존 설정 백업 (롤백용)
if [ -f "$OUT" ]; then
    cp -a "$OUT" "${OUT}.bak.$(date +%s)"
    log_info "기존 설정 백업 완료"
fi

log_info "nginx 템플릿을 $OUT에 렌더링 중..."
envsubst < "$TPL_DIR/dreamseed.conf.tpl" > "$OUT"
ln -sfn "$OUT" "/etc/nginx/sites-enabled/${DOMAIN}.conf"

# 리로드 전 검증
log_info "5. nginx 설정 검증 중..."
if ! nginx -t; then
    log_error "❌ nginx 설정 테스트 실패; 이전 설정 복원 중..."
    if ls -1 "${OUT}.bak."* >/dev/null 2>&1; then
        LATEST=$(ls -1t "${OUT}.bak."* | head -n1)
        cp -af "$LATEST" "$OUT"
        log_info "이전 설정으로 복원됨"
    fi
    nginx -t || true
    exit 1
fi
systemctl reload nginx

# TLS 발급/확보
log_info "6. TLS 인증서 발급/확보 중..."
if ! test -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"; then
    log_info "인증서가 없습니다. 발급 중..."
    certbot --nginx -d "$DOMAIN" -m "admin@${DOMAIN}" --agree-tos --non-interactive || {
        log_warning "인증서 발급 실패 (DNS 설정 확인 필요)"
    }
fi

nginx -t && systemctl reload nginx

# 헬스 체크
log_info "7. 헬스 체크 중..."
set +e
curl -skI "https://${DOMAIN}" | head -n1
curl -sk  "https://${DOMAIN}/healthz" | head -n1
certbot renew --dry-run
set -e

log_success "✅ https://${DOMAIN} 배포 완료 (HSTS=${HSTS})"

# --- 외부 접속 점검 & Windows 가이드 ---
HOST_IP=$(hostname -I | awk '{print $1}')
log_info "8. 외부 접속 점검 및 Windows 가이드 생성 중..."

echo ""
echo "🔎 외부 접속 점검 (HTTP) on $HOST_IP:80"
if ! curl -sI "http://${HOST_IP}" | head -n1; then
    log_warning "⚠️  http://${HOST_IP}에 접근할 수 없습니다. Windows에서 연결이 안 될 경우 확인사항:"
    echo "   • UFW가 80/443을 허용하는지 확인 (ufw status)"
    echo "   • DNS가 이 서버를 가리키는지 확인"
    echo "   • 기업/VPN 프록시가 HTTPS를 강제하지 않는지 확인"
fi

echo ""
echo "💡 Windows 빠른 테스트:"
echo "   1) ping ${HOST_IP}"
echo "   2) curl http://${HOST_IP}"
echo "   3) 브라우저 → https://${DOMAIN}"

echo ""
echo "🔧 문제 해결:"
echo "   • Windows 방화벽 확인"
echo "   • 브라우저 캐시 삭제 (Ctrl+Shift+Delete)"
echo "   • 시크릿 모드로 테스트 (Ctrl+Shift+N)"
echo "   • 프록시 설정 확인"

log_success "Nginx + TLS 배포 및 외부 접속 점검 완료!"
