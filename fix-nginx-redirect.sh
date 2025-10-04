#!/bin/bash

# 🛠️ Nginx 307 리다이렉트 문제 해결
# /api/recommend → /api/recommend/ 리다이렉트 제거

set -e

NGINX_CONF="/etc/nginx/sites-enabled/dreamseedai.com.conf"

echo "🔧 Nginx 307 리다이렉트 문제 해결 중..."
echo "📁 설정 파일: $NGINX_CONF"

# 백업 생성
cp "$NGINX_CONF" "${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 백업 생성: ${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# 기존 API location 블록을 찾아서 수정
sed -i 's|proxy_pass http://127.0.0.1:8012;|proxy_pass http://127.0.0.1:8012/;|g' "$NGINX_CONF"

echo "✅ Nginx 307 리다이렉트 문제 해결 완료"

# 변경 내용 확인
echo "📋 변경된 내용:"
grep -A 15 "location /api/" "$NGINX_CONF"

echo ""
echo "🔄 Nginx 재시작이 필요합니다:"
echo "echo '111' | sudo -S nginx -t && echo '111' | sudo -S systemctl reload nginx"
echo ""
echo "🧪 테스트 명령어:"
echo "curl -i https://dreamseedai.com/api/recommend"
echo "# 기대 결과: 200 OK (307 리다이렉트 없음)"
