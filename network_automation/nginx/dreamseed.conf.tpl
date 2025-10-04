# DreamSeed nginx 템플릿
# 템플릿 변수: ${SERVER_NAME}, ${STATIC_ROOT}, ${API_UPSTREAM}, ${HSTS_ENABLED}
# 예시: SERVER_NAME=dreamseedai.com, STATIC_ROOT=/var/www/dreamseed/static, API_UPSTREAM=http://127.0.0.1:8000/

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

# --- Real IP (when behind a reverse proxy) ---
# If traffic may be proxied (local or external), ensure logs & $remote_addr reflect client IP.
# Local proxy (nginx on same host):
set_real_ip_from 127.0.0.1;
# Auto-synced provider ranges (managed by update_real_ip_providers.sh)
include /etc/nginx/conf.d/real_ip_providers.conf;
real_ip_header X-Forwarded-For;
real_ip_recursive on;

log_format ds_combined '$remote_addr - $remote_user [$time_local] "$request" '
                     '$status $body_bytes_sent "$http_referer" "$http_user_agent" '
                     'upstream=$upstream_status rt=$request_time urt=$upstream_response_time';

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_NAME};
    
    # ACME challenge 지원
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
        default_type "text/plain";
    }
    
    return 301 https://$host$request_uri;
}

# HTTPS 서버
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${SERVER_NAME};
    server_tokens off;

    # SSL 인증서
    ssl_certificate     /etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${SERVER_NAME}/privkey.pem;

    # 로그 설정
    access_log /var/log/nginx/${SERVER_NAME}.access.log ds_combined;
    error_log  /var/log/nginx/${SERVER_NAME}.error.log warn;

    # ---- 보안 헤더 ----
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy no-referrer-when-downgrade always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'" always;
    add_header Cross-Origin-Opener-Policy same-origin always;      # COOP
    add_header Cross-Origin-Embedder-Policy require-corp always;   # COEP
    add_header Cross-Origin-Resource-Policy same-origin always;    # CORP
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    
    # 실 IP 보존 (프록시/Cloudflare 대비)
    real_ip_header X-Forwarded-For;
    set_real_ip_from 127.0.0.1;
    # Cloudflare CIDR (도입 시 주석 해제)
    # set_real_ip_from 173.245.48.0/20;
    # set_real_ip_from 103.21.244.0/22;
    # set_real_ip_from 103.22.200.0/22;
    # set_real_ip_from 103.31.4.0/22;
    # set_real_ip_from 141.101.64.0/18;
    # set_real_ip_from 108.162.192.0/18;
    # set_real_ip_from 190.93.240.0/20;
    # set_real_ip_from 188.114.96.0/20;
    # set_real_ip_from 197.234.240.0/22;
    # set_real_ip_from 198.41.128.0/17;
    # set_real_ip_from 162.158.0.0/15;
    # set_real_ip_from 104.16.0.0/13;
    # set_real_ip_from 104.24.0.0/14;
    # set_real_ip_from 172.64.0.0/13;
    # set_real_ip_from 131.0.72.0/22;

    # HSTS (${HSTS_ENABLED}로 토글)
    set $hsts ${HSTS_ENABLED};
    if ($hsts = on) { 
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always; 
    }

    # ---- 압축 설정 ----
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 5;
    gzip_types text/plain text/css application/javascript application/json application/ld+json application/xml image/svg+xml;

    # 업로드/타임아웃 설정
    client_max_body_size 50m;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_connect_timeout 30s;
    proxy_buffering on;
    proxy_buffers 32 16k;
    proxy_busy_buffers_size 64k;

    # ACME challenge 지원 (HTTPS)
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
        default_type "text/plain";
    }

    # ---- API 프록시 ----
    location /api/ {
        proxy_pass ${API_UPSTREAM};   # 예: http://127.0.0.1:8000/ (끝에 슬래시 유지)
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }

    # ---- 정적 파일 (해시된 에셋용 장기 캐시) ----
    location ~* \.(?:js|css|png|jpg|jpeg|gif|svg|webp|ico|woff2?|ttf)$ {
        root ${STATIC_ROOT};
        access_log off;
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files $uri =404;
    }

    # HTML은 장기 캐시하지 않음 (SPA 셸 업데이트용)
    location ~* \.(?:html)$ {
        root ${STATIC_ROOT};
        add_header Cache-Control "no-cache";
        try_files $uri =404;
    }

    # 친화적인 오류 페이지
    error_page 502 503 504 /50x.html;
    location = /50x.html { 
        root /usr/share/nginx/html; 
        internal; 
    }

    # 기본 정적 파일
    location / {
        root ${STATIC_ROOT};
        try_files $uri $uri/ =404;
    }
}
