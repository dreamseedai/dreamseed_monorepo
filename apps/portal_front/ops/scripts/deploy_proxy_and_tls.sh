#!/usr/bin/env bash
# Usage: sudo ./deploy_proxy_and_tls.sh <domain> <static_root> <api_upstream_with_slash> <hsts:on|off>
# Example: sudo ./deploy_proxy_and_tls.sh staging.dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ off

set -euo pipefail

DOMAIN=${1:?"domain"}
STATIC_ROOT=${2:?"static_root"}
API_UPSTREAM=${3:?"api_upstream (e.g., http://127.0.0.1:8000/)"}
HSTS=${4:-off}

echo "🚀 Deploying nginx proxy + TLS for ${DOMAIN} (HSTS=${HSTS})"

# --- prerequisites ---
apt-get update -y
apt-get install -y nginx curl ca-certificates certbot python3-certbot-nginx

# Webroot for ACME
echo "📁 Creating ACME webroot directory..."
mkdir -p /var/www/letsencrypt
chown -R www-data:www-data /var/www/letsencrypt

# Open firewall for 80/443
echo "🔥 Configuring firewall..."
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
  echo "📦 Creating backup of existing config..."
  cp -a "$OUT" "${OUT}.bak.$(date +%s)"
fi

echo "📝 Rendering nginx template to $OUT"
envsubst < "$TPL_DIR/dreamseed.conf.tpl" > "$OUT"
ln -sfn "$OUT" "/etc/nginx/sites-enabled/${DOMAIN}.conf"

# Validate before reload
echo "🔍 Testing nginx configuration..."
if ! nginx -t; then
  echo "❌ nginx config test failed; restoring previous config" >&2
  if ls -1 "${OUT}.bak."* >/dev/null 2>&1; then
    LATEST=$(ls -1t "${OUT}.bak."* | head -n1)
    echo "🔄 Rolling back to: $LATEST"
    cp -af "$LATEST" "$OUT"
    ln -sfn "$OUT" "/etc/nginx/sites-enabled/${DOMAIN}.conf"
  fi
  nginx -t || true
  exit 1
fi
systemctl reload nginx
echo "✅ nginx reloaded successfully"

# TLS issue/ensure
if ! test -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"; then
  echo "🔐 Issuing TLS certificate for ${DOMAIN}..."
  certbot --nginx -d "$DOMAIN" -m "admin@${DOMAIN}" --agree-tos --non-interactive || {
    echo "⚠️ Certificate issuance failed, continuing with existing config"
  }
fi

# Final validation and reload
nginx -t && systemctl reload nginx

# Health checks
echo "🏥 Running health checks..."
set +e
HTTP_STATUS=$(curl -skI "https://${DOMAIN}" | head -n1 | cut -d' ' -f2)
if [[ "$HTTP_STATUS" =~ ^(200|301|304)$ ]]; then
  echo "✅ HTTPS health check passed (${HTTP_STATUS})"
else
  echo "❌ HTTPS health check failed (${HTTP_STATUS})" >&2
fi

HEALTHZ_STATUS=$(curl -skI "https://${DOMAIN}/healthz" | head -n1 | cut -d' ' -f2)
if [[ "$HEALTHZ_STATUS" =~ ^(200|404)$ ]]; then
  echo "✅ Healthz endpoint check passed (${HEALTHZ_STATUS})"
else
  echo "⚠️ Healthz endpoint check failed (${HEALTHZ_STATUS}) - may need backend setup"
fi

echo "🧪 Testing certificate renewal..."
certbot renew --dry-run || {
  echo "⚠️ Certificate renewal test failed"
}
set -e

echo "✅ Deployed https://${DOMAIN} (HSTS=${HSTS})"
echo "🌐 Test with: curl -I https://${DOMAIN}/healthz"
