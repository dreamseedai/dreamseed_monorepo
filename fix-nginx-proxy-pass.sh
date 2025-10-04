#!/bin/bash

# 🛠️ Nginx proxy_pass 경로 수정
# /api/recommend에서 중복 경로 제거

set -e

NGINX_CONF="/etc/nginx/sites-enabled/dreamseedai.com.conf"

echo "🔧 Nginx proxy_pass 경로 수정 중..."
echo "📁 설정 파일: $NGINX_CONF"

# 백업 생성
cp "$NGINX_CONF" "${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 백업 생성: ${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# proxy_pass 경로 수정 (중복 제거)
sed -i 's|proxy_pass http://127.0.0.1:8012/api/recommend;|proxy_pass http://127.0.0.1:8012;|g' "$NGINX_CONF"
sed -i 's|proxy_pass http://127.0.0.1:8012/api/recommend/;|proxy_pass http://127.0.0.1:8012/;|g' "$NGINX_CONF"

echo "✅ proxy_pass 경로 수정 완료"

# 변경 내용 확인
echo "📋 변경된 내용:"
grep -A 2 -B 2 "proxy_pass.*8012" "$NGINX_CONF"

echo ""
echo "🔄 Nginx 재시작이 필요합니다:"
echo "echo '111' | sudo -S nginx -t && echo '111' | sudo -S systemctl reload nginx"
echo ""
echo "🧪 테스트 명령어:"
echo "curl -i -X POST https://dreamseedai.com/api/recommend -H 'Content-Type: application/json' -d '{\"test\": \"data\"}'"
echo "# 기대 결과: 401 Unauthorized (정상, 307 리다이렉트 없음)"
