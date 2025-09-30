#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_HOST:?export DEPLOY_HOST=user@server 먼저 설정}"
: "${DOMAIN:?export DOMAIN=your.domain 먼저 설정}"
: "${SERVICE_NAME:=portal-api.service}"

echo "==[1/6] 가드레일"
bash scripts/install_nxreload_safe.sh
bash scripts/lock_mpcstudy_configs.sh

echo "==[2/6] vhost/배포기/서비스 설치"
bash scripts/install_portal_vhost.sh
bash scripts/install_deploy_portal_front.sh
bash scripts/install_portal_api_service.sh

echo "==[3/6] API 코드 전송/재시작"
bash scripts/ship_portal_api.sh

echo "==[4/6] 프런트 빌드·전송·원자적 전환"
./scripts/ship_portal_front.sh

echo "==[5/6] 15분 점검 (요약 출력)"
sudo DOMAIN="$DOMAIN" API_UNIT="$SERVICE_NAME" /usr/local/bin/portal_audit.sh || true

echo "==[6/6] 핵심 헬스"
curl -fsS "https://${DOMAIN}/__ok" | grep -qx 'ok' && echo "✔ HTTPS /__ok OK" || echo "✖ /__ok FAIL"
curl -fsS "https://${DOMAIN}/api/__ok" | grep -qi 'true\|ok' && echo "✔ /api/__ok OK" || echo "✖ /api/__ok FAIL"

echo "완료 ✅"
