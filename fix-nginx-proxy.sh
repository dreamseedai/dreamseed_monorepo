#!/bin/bash

# 🛠️ Nginx 프록시 설정 수정 스크립트
# /api/ 경로를 올바른 백엔드 포트(8012)로 전달

set -e

echo "🔧 Nginx 프록시 설정 수정 중..."

# 현재 Nginx 설정 파일 찾기
NGINX_CONF=""
if [ -f "/etc/nginx/sites-available/dreamseedai.com.conf" ]; then
    NGINX_CONF="/etc/nginx/sites-available/dreamseedai.com.conf"
elif [ -f "/etc/nginx/sites-available/portal.dreamseedai.com.conf" ]; then
    NGINX_CONF="/etc/nginx/sites-available/portal.dreamseedai.com.conf"
else
    echo "❌ Nginx 설정 파일을 찾을 수 없습니다."
    echo "💡 다음 위치를 확인하세요:"
    echo "   - /etc/nginx/sites-available/dreamseedai.com.conf"
    echo "   - /etc/nginx/sites-available/portal.dreamseedai.com.conf"
    exit 1
fi

echo "📁 설정 파일: $NGINX_CONF"

# 백업 생성
sudo cp "$NGINX_CONF" "${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 백업 생성: ${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# 포트 8000을 8012로 변경
sudo sed -i 's/proxy_pass http:\/\/127\.0\.0\.1:8000/proxy_pass http:\/\/127\.0\.0\.1:8012/g' "$NGINX_CONF"

echo "✅ 포트 변경 완료: 8000 → 8012"

# Nginx 설정 테스트
echo "🧪 Nginx 설정 테스트 중..."
if sudo nginx -t; then
    echo "✅ Nginx 설정이 유효합니다."
    
    # Nginx 재시작
    echo "🔄 Nginx 재시작 중..."
    sudo systemctl reload nginx
    echo "✅ Nginx 재시작 완료!"
    
    # 테스트
    echo "🧪 API 엔드포인트 테스트 중..."
    sleep 2
    if curl -s -o /dev/null -w "%{http_code}" https://dreamseedai.com/api/auth/me | grep -q "401"; then
        echo "✅ API 엔드포인트가 정상 작동합니다! (401 = 인증 필요, 정상)"
    else
        echo "⚠️  API 엔드포인트 테스트 실패. 추가 확인이 필요합니다."
    fi
    
else
    echo "❌ Nginx 설정에 오류가 있습니다. 백업에서 복원합니다."
    sudo cp "${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)" "$NGINX_CONF"
    exit 1
fi

echo ""
echo "🎉 Nginx 프록시 설정 수정 완료!"
echo "💡 이제 '내 전략 보기' 버튼이 정상 작동할 것입니다."
echo ""
echo "🔍 추가 확인 사항:"
echo "   - 백엔드가 포트 8012에서 실행 중인지 확인"
echo "   - 브라우저에서 '내 전략 보기' 버튼 테스트"
