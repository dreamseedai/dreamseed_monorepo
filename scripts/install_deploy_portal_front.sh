#!/usr/bin/env bash
set -euo pipefail

sudo tee /usr/local/bin/deploy_portal_front.sh >/dev/null <<'SH'
#!/usr/bin/env bash
set -euo pipefail
REL="/srv/portal_front/releases/$(date +%F_%H%M%S)"
PKG="${1:-}"
[ -n "$PKG" ] && [ -f "$PKG" ] || { echo "Usage: deploy_portal_front.sh <dist.tgz>"; exit 1; }

sudo mkdir -p "$REL"
# dist/ 안의 파일들을 루트로 풀린 tgz라고 가정 (build 시 --directory dist 사용 권장)
sudo tar -xzf "$PKG" -C "$REL"
sudo chown -R www-data:www-data "$REL"
sudo find "$REL" -type d -exec chmod 755 {} \;
sudo find "$REL" -type f -exec chmod 644 {} \;

# 필수 파일 확인
sudo test -f "$REL/index.html"

sudo ln -sfn "$REL" /srv/portal_front/current
if command -v nxreload_safe >/dev/null 2>&1; then
  nxreload_safe
else
  sudo nginx -t && sudo systemctl reload nginx
fi

# 스모크
curl -fsS https://$DOMAIN/__ok >/dev/null 2>&1 && echo "ok /__ok" || true
curl -fsS https://$DOMAIN/       >/dev/null 2>&1 && echo "ok /"     || true
echo "deployed: $REL"
SH
sudo chmod +x /usr/local/bin/deploy_portal_front.sh

echo "installed: /usr/local/bin/deploy_portal_front.sh"


