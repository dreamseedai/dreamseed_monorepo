#!/bin/bash

# 🛠️ Nginx 포트 수정 스크립트 (8000 → 8012)
# dreamseedai.com.conf에서 API 프록시 포트를 올바르게 수정

set -e

NGINX_CONF="/etc/nginx/sites-enabled/dreamseedai.com.conf"

echo "🔧 Nginx 포트 수정 중..."
echo "📁 설정 파일: $NGINX_CONF"

# 백업 생성
cp "$NGINX_CONF" "${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 백업 생성: ${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# 포트 8000을 8012로 변경
sed -i 's/127\.0\.0\.1:8000/127.0.0.1:8012/g' "$NGINX_CONF"

echo "✅ 포트 변경 완료: 8000 → 8012"

# 변경 내용 확인
echo "📋 변경된 내용:"
grep -n "127.0.0.1:8012" "$NGINX_CONF" || echo "변경 사항이 없습니다."

echo ""
echo "🔄 Nginx 재시작이 필요합니다:"
echo "sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "🧪 테스트 명령어:"
echo "curl -i https://dreamseedai.com/api/auth/me"
echo "# 기대 결과: 401 Unauthorized (정상)"
