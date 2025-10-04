#!/bin/bash
# Script to update Nginx configuration for personalized API

echo "Updating Nginx configuration to use port 8013..."

# Create a temporary file with the updated configuration
cat > /tmp/dreamseedai_updated.conf << 'EOF'
server {
  listen 80;
  listen [::]:80;
  server_name dreamseedai.com www.dreamseedai.com;

  # Redirect HTTP to HTTPS
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name dreamseedai.com www.dreamseedai.com;

  # SSL configuration
  ssl_certificate /etc/letsencrypt/live/dreamseedai.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/dreamseedai.com/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
  ssl_prefer_server_ciphers off;
  ssl_session_cache shared:SSL:10m;
  ssl_session_timeout 10m;

  # Security headers
  add_header X-Frame-Options DENY;
  add_header X-Content-Type-Options nosniff;
  add_header X-XSS-Protection "1; mode=block";
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  server_tokens off;

  # API 프록시 설정 - Updated to use port 8013
  location /api/ {
    proxy_http_version 1.1;
    proxy_pass http://127.0.0.1:8013;
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

  # Static / SPA
  root /srv/portal_front/current;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  # Cache static assets
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
EOF

echo "Configuration file created. Please run the following commands:"
echo ""
echo "1. Copy the configuration:"
echo "   sudo cp /tmp/dreamseedai_updated.conf /etc/nginx/sites-enabled/dreamseedai.com.conf"
echo ""
echo "2. Test the configuration:"
echo "   sudo nginx -t"
echo ""
echo "3. Reload Nginx:"
echo "   sudo systemctl reload nginx"
echo ""
echo "4. Test the personalized endpoints:"
echo "   curl -s https://dreamseedai.com/api/personalized/profile -H 'Authorization: Bearer test_token'"
echo ""
echo "The personalized API endpoints should now be accessible through the web interface!"
