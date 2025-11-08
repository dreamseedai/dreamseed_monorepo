#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:?export DOMAIN=example.com}"
WWW="www.${DOMAIN}"
ROOT="${ROOT:-/srv/portal_front/current}"
API_PORT="${API_PORT:-8000}"
CONF="/etc/nginx/sites-available/${DOMAIN}.conf"

sudo tee "$CONF" >/dev/null <<CONF
# 80 → 443 (단, /__ok는 200)
server {
  listen 80;
  listen [::]:80;
  server_name ${DOMAIN} ${WWW};

  location = /__ok { return 200 "ok\n"; add_header Content-Type text/plain; }
  return 301 https://${DOMAIN}\$request_uri;
}

# 443
upstream portal_api { server 127.0.0.1:${API_PORT}; keepalive 32; }

server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name ${DOMAIN} ${WWW};

  # certbot가 자동으로 채우는 라인들 유지됨 (이미 발급 완료 가정)
  ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

  # HSTS/OCSP 등 하드닝
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_session_cache shared:SSL:10m;
  ssl_session_timeout 1h;
  ssl_stapling on;
  ssl_stapling_verify on;
  resolver 1.1.1.1 1.0.0.1 valid=300s;
  resolver_timeout 5s;

  # 보안 헤더
  add_header X-Content-Type-Options nosniff always;
  add_header X-Frame-Options SAMEORIGIN always;
  add_header Referrer-Policy strict-origin-when-cross-origin always;
  server_tokens off;

  root ${ROOT};
  index index.html;

  # 헬스체크
  location = /__ok { return 200 "ok\n"; add_header Content-Type text/plain; }

  # 정적 캐싱
  location ~* \.(css|js|mjs|png|jpg|jpeg|gif|ico|svg|webp|woff2?)$ {
    access_log off;
    add_header Cache-Control "public, max-age=31536000, immutable";
    try_files \$uri =404;
  }

  # HTML always fresh
  location = /index.html { add_header Cache-Control "no-store"; }

  # SPA fallback
  location / {
    try_files \$uri \$uri/ /index.html;
    add_header Cache-Control "no-store";
  }

  # API 프록시
  location /api/ {
    proxy_http_version 1.1;
    proxy_set_header Host              \$host;
    proxy_set_header X-Real-IP         \$remote_addr;
    proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_connect_timeout 5s;
    proxy_send_timeout 30s;
    proxy_read_timeout 120s;
    proxy_pass http://portal_api/;
  }

  # WebSocket (있을 때)
  location /api/ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://portal_api/;
  }

  # 민감/숨김 파일 차단 + 업로드 내 PHP 실행 차단 예시
  location ~ /\.(?!well-known) { deny all; }
  location ~* \.(env|ini|log|sql|sh|bak|old)$ { deny all; }
}
CONF

sudo ln -sfn "$CONF" "/etc/nginx/sites-enabled/${DOMAIN}.conf"
if command -v nxreload_safe >/dev/null 2>&1; then
  nxreload_safe
else
  sudo nginx -t && sudo systemctl reload nginx
fi
echo "installed: $CONF"


