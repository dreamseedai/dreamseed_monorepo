#!/usr/bin/env bash
set -euo pipefail

# Usage: sudo ./deploy_proxy_and_tls.sh dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ on
DOMAIN=${1:?"domain"}
STATIC_ROOT=${2:?"static_root"}
API_UPSTREAM=${3:?"api_upstream (e.g., http://127.0.0.1:8000/)"}
HSTS=${4:-off} # on/off

# --- prerequisites ---
apt-get update -y
apt-get install -y nginx curl ca-certificates certbot python3-certbot-nginx

# Webroot for ACME
mkdir -p /var/www/letsencrypt
chown -R www-data:www-data /var/www/letsencrypt

# Open firewall for 80/443
ufw allow 80/tcp || true
ufw allow 443/tcp || true

# Render nginx template
TPL_DIR=$(dirname "$0")/../nginx
OUT=/etc/nginx/sites-available/${DOMAIN}.conf
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

export SERVER_NAME=${DOMAIN}
export STATIC_ROOT
export API_UPSTREAM
export HSTS_ENABLED=${HSTS}

# Backup existing config (for rollback)
if [ -f "$OUT" ]; then
  cp -a "$OUT" "${OUT}.bak.$(date +%s)"
fi

echo "Rendering nginx template to $OUT"
envsubst < "$TPL_DIR/dreamseed.conf.tpl" > "$OUT"
ln -sfn "$OUT" "/etc/nginx/sites-enabled/${DOMAIN}.conf"

# Validate before reload
if ! nginx -t; then
  echo "❌ nginx config test failed; restoring previous config" >&2
  if ls -1 "${OUT}.bak."* >/dev/null 2>&1; then
    LATEST=$(ls -1t "${OUT}.bak."* | head -n1)
    cp -af "$LATEST" "$OUT"
  fi
  nginx -t || true
  exit 1
fi
systemctl reload nginx

# TLS issue/ensure
if ! test -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"; then
  certbot --nginx -d "$DOMAIN" -m "admin@${DOMAIN}" --agree-tos --non-interactive || true
fi

nginx -t && systemctl reload nginx

# Health checks
set +e
curl -skI "https://${DOMAIN}" | head -n1
curl -sk  "https://${DOMAIN}/healthz" | head -n1
certbot renew --dry-run
set -e

# --- External reachability quick check & Windows guide ---
HOST_IP=$(hostname -I | awk '{print $1}')
echo "🔎 External reachability check (HTTP) on $HOST_IP:80"
if ! curl -sI "http://${HOST_IP}" | head -n1; then
  echo "⚠️  Could not reach http://${HOST_IP}. If Windows cannot connect, verify:"
  echo "   • UFW allows 80/443 (ufw status)"
  echo "   • DNS points to this server"
  echo "   • Corporate/VPN proxy not forcing HTTPS"
fi
echo "💡 Windows quick test:"
echo "   1) ping ${HOST_IP}"
echo "   2) curl http://${HOST_IP}"
echo "   3) browser → https://${DOMAIN}"

echo "✅ Deployed https://${DOMAIN} (HSTS=${HSTS})"


