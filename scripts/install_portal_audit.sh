#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_HOST:?export DEPLOY_HOST=user@server 형태로 설정}"

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

cat > "$TMP" <<'REMOTE'
#!/usr/bin/env bash
set -euo pipefail

sudo tee /usr/local/bin/portal_audit.sh >/dev/null <<'SH'
#!/usr/bin/env bash
set -euo pipefail
DOMAIN="${DOMAIN:-dreamseedai.com}"
ROOT="/srv/portal_front"
API_UNIT="${API_UNIT:-portal-api.service}"   # 실제 서비스명 쓰면 더 정확
API_URL="https://${DOMAIN}/api/__ok"

echo "[Nginx] config test"
sudo nginx -t >/dev/null && echo "  ✔ nginx -t OK"

echo "[HTTPS] /__ok"
if curl -fsS "https://${DOMAIN}/__ok" | grep -qx 'ok'; then
  echo "  ✔ ${DOMAIN}/__ok OK"
else
  echo "  ✖ ${DOMAIN}/__ok FAIL"
fi

echo "[API] /api/__ok"
if curl -fsS "${API_URL}" | grep -qi 'true\|ok'; then
  echo "  ✔ ${API_URL} OK"
else
  echo "  ✖ ${API_URL} FAIL"
fi

echo "[Releases] ${ROOT}"
ls -ld "${ROOT}"/current || true
readlink -f "${ROOT}/current" || true
ls -1dt "${ROOT}/releases"/* 2>/dev/null | head -n3 || echo "  (no releases)"

echo "[Systemd] ${API_UNIT}"
systemctl is-active --quiet "${API_UNIT}" && echo "  ✔ ${API_UNIT} active" || echo "  ✖ ${API_UNIT} inactive"
systemctl status "${API_UNIT}" --no-pager | sed -n '1,6p' || true

echo "[Cert] expiry"
ED=$(openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:443" </dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2 || true)
if [ -n "${ED:-}" ]; then
  DAYS=$(( ( $(date -d "$ED" +%s) - $(date +%s) )/86400 ))
  echo "  ✔ ${ED} (${DAYS} days left)"
fi

echo "[Ports] 8000"
ss -ltnp | grep -E ':(8000)\s' || echo "  (no :8000 binding)"

echo "[Headers] cache/HSTS"
curl -sI "https://${DOMAIN}/" | grep -iE 'strict-transport-security|cache-control' || true
SH

sudo chmod +x /usr/local/bin/portal_audit.sh
REMOTE

scp "$TMP" "$DEPLOY_HOST:/tmp/install_portal_audit.sh"
ssh "$DEPLOY_HOST" 'bash /tmp/install_portal_audit.sh'

echo "portal_audit.sh installed on $DEPLOY_HOST"


