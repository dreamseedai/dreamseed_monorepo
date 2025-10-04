#!/bin/bash

# 🛠️ Nginx 설정 완전 재작성
# 307 리다이렉트 문제 완전 해결

set -e

NGINX_CONF="/etc/nginx/sites-enabled/dreamseedai.com.conf"

echo "🔧 Nginx 설정 완전 재작성 중..."
echo "📁 설정 파일: $NGINX_CONF"

# 백업 생성
cp "$NGINX_CONF" "${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 백업 생성: ${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# 기존 API 섹션을 완전히 제거하고 새로 작성
sed -i '/# --- canonical API locations begin ---/,/# --- canonical API locations end ---/d' "$NGINX_CONF"

# 새로운 API 설정 삽입
sed -i '/server_tokens off;/a\\n  # API 프록시 설정\n  location /api/ {\n    proxy_http_version 1.1;\n    proxy_pass http://127.0.0.1:8012/;\n    proxy_set_header Host              $host;\n    proxy_set_header X-Real-IP         $remote_addr;\n    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;\n    proxy_set_header X-Forwarded-Proto $scheme;\n    proxy_connect_timeout 5s;\n    proxy_read_timeout    60s;\n    proxy_send_timeout    60s;\n    proxy_set_header Upgrade           $http_upgrade;\n    proxy_set_header Connection        "upgrade";\n  }' "$NGINX_CONF"

echo "✅ Nginx 설정 완전 재작성 완료"

# 변경 내용 확인
echo "📋 변경된 내용:"
grep -A 15 "location /api/" "$NGINX_CONF"

echo ""
echo "🔄 Nginx 재시작이 필요합니다:"
echo "echo '111' | sudo -S nginx -t && echo '111' | sudo -S systemctl reload nginx"
echo ""
echo "🧪 테스트 명령어:"
echo "curl -i -X POST https://dreamseedai.com/api/recommend -H 'Content-Type: application/json' -d '{\"test\": \"data\"}'"
echo "# 기대 결과: 401 Unauthorized (정상, 307 리다이렉트 없음)"
