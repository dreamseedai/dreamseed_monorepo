#!/bin/bash

# 🛠️ Nginx 307 리다이렉트 문제 해결
# /api/recommend에서 307 리다이렉트 제거

set -e

NGINX_CONF="/etc/nginx/sites-enabled/dreamseedai.com.conf"

echo "🔧 Nginx 307 리다이렉트 문제 해결 중..."
echo "📁 설정 파일: $NGINX_CONF"

# 백업 생성
cp "$NGINX_CONF" "${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 백업 생성: ${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# 307 리다이렉트를 방지하는 올바른 설정으로 교체
cat > /tmp/nginx_fix.conf << 'EOF'
  # --- canonical API locations begin ---
  # POST /api/recommend (슬래시 없음)
  location = /api/recommend {
    proxy_http_version 1.1;
    proxy_pass http://127.0.0.1:8012/api/recommend;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 5s;
    proxy_read_timeout    60s;
    proxy_send_timeout    60s;
  }

  # GET /api/recommend/ (슬래시 있음)
  location = /api/recommend/ {
    proxy_http_version 1.1;
    proxy_pass http://127.0.0.1:8012/api/recommend/;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 5s;
    proxy_read_timeout    60s;
    proxy_send_timeout    60s;
  }

  # 기타 /api/ 경로들
  location ^~ /api/ {
    proxy_http_version 1.1;
    proxy_pass http://127.0.0.1:8012;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 5s;
    proxy_read_timeout    60s;
    proxy_send_timeout    60s;
    proxy_set_header Upgrade           $http_upgrade;
    proxy_set_header Connection        "upgrade";
  }
  # --- canonical API locations end ---
EOF

# 기존 API 섹션을 새 설정으로 교체
sed -i '/# --- canonical API locations begin ---/,/# --- canonical API locations end ---/c\
# --- canonical API locations begin ---\
  # POST /api/recommend (슬래시 없음)\
  location = /api/recommend {\
    proxy_http_version 1.1;\
    proxy_pass http://127.0.0.1:8012/api/recommend;\
    proxy_set_header Host              $host;\
    proxy_set_header X-Real-IP         $remote_addr;\
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;\
    proxy_set_header X-Forwarded-Proto $scheme;\
    proxy_connect_timeout 5s;\
    proxy_read_timeout    60s;\
    proxy_send_timeout    60s;\
  }\
\
  # GET /api/recommend/ (슬래시 있음)\
  location = /api/recommend/ {\
    proxy_http_version 1.1;\
    proxy_pass http://127.0.0.1:8012/api/recommend/;\
    proxy_set_header Host              $host;\
    proxy_set_header X-Real-IP         $remote_addr;\
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;\
    proxy_set_header X-Forwarded-Proto $scheme;\
    proxy_connect_timeout 5s;\
    proxy_read_timeout    60s;\
    proxy_send_timeout    60s;\
  }\
\
  # 기타 /api/ 경로들\
  location ^~ /api/ {\
    proxy_http_version 1.1;\
    proxy_pass http://127.0.0.1:8012;\
    proxy_set_header Host              $host;\
    proxy_set_header X-Real-IP         $remote_addr;\
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;\
    proxy_set_header X-Forwarded-Proto $scheme;\
    proxy_connect_timeout 5s;\
    proxy_read_timeout    60s;\
    proxy_send_timeout    60s;\
    proxy_set_header Upgrade           $http_upgrade;\
    proxy_set_header Connection        "upgrade";\
  }\
  # --- canonical API locations end ---' "$NGINX_CONF"

echo "✅ 307 리다이렉트 문제 해결 완료"

# 변경 내용 확인
echo "📋 변경된 내용:"
grep -A 5 -B 5 "location.*recommend" "$NGINX_CONF"

echo ""
echo "🔄 Nginx 재시작이 필요합니다:"
echo "echo '111' | sudo -S nginx -t && echo '111' | sudo -S systemctl reload nginx"
echo ""
echo "🧪 테스트 명령어:"
echo "curl -i https://dreamseedai.com/api/recommend"
echo "# 기대 결과: 401 Unauthorized (정상, 307 리다이렉트 없음)"
