# Template variables: ${SERVER_NAME}, ${STATIC_ROOT}, ${API_UPSTREAM}, ${HSTS_ENABLED}

map $http_upgrade $connection_upgrade { default upgrade; '' close; }

log_format ds_combined '$remote_addr - $remote_user [$time_local] "$request" '
                     '$status $body_bytes_sent "$http_referer" "$http_user_agent" '
                     'upstream=$upstream_status rt=$request_time urt=$upstream_response_time';

# Include upstream configuration
include /etc/nginx/upstreams/threader_active.conf;

server {
    listen 80;
    server_name ${SERVER_NAME};
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${SERVER_NAME};

    ssl_certificate     /etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${SERVER_NAME}/privkey.pem;

    access_log /var/log/nginx/${SERVER_NAME}.access.log ds_combined;
    error_log  /var/log/nginx/${SERVER_NAME}.error.log warn;

    # ---- Security headers ----
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy no-referrer-when-downgrade always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'" always;

    # HSTS (toggle via ${HSTS_ENABLED})
    set $hsts ${HSTS_ENABLED};
    if ($hsts = on) { add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always; }

    # Upload/timeouts
    client_max_body_size 50m;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;

    # ---- API proxy ----
    location /api/ {
        proxy_pass http://threader_upstream;   # Use upstream instead of direct URL
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }

    # Health check endpoint
    location /healthz {
        proxy_pass http://threader_upstream/healthz;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }

    # ---- Static files (long cache for hashed assets) ----
    location ~* \.(?:js|css|png|jpg|jpeg|gif|svg|webp|ico|woff2?|ttf)$ {
        root ${STATIC_ROOT};
        access_log off;
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files $uri =404;
    }

    # Default static
    location / {
        root ${STATIC_ROOT};
        try_files $uri $uri/ =404;
    }
}