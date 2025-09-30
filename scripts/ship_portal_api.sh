#!/usr/bin/env bash
set -euo pipefail
DEPLOY_HOST="${DEPLOY_HOST:-local}"

MONO_ROOT="/home/won/projects/dreamseed_monorepo"
ROOT="${MONO_ROOT}/portal_api"
REPO="/home/won/projects/dreamseed_monorepo"
API_DIR="/home/won/projects/dreamseed_monorepo/portal_api"
TS="$(date +%F_%H%M%S)"
PKG="/tmp/portal_api_${TS}.tgz"
SERVICE_NAME="${SERVICE_NAME:-portal-api.service}"

# 빌드정보 파일 생성(릴리스에 포함): git → 파일해시 → 타임스탬프 폴백
TS_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SHA="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null \
   || git -C "$API_DIR" rev-parse --short HEAD 2>/dev/null \
   || (cd "$API_DIR" && find . -type d \( -path './venv' -o -path './__pycache__' -o -path './.git' \) -prune -o -type f -print0 \
        | sort -z | xargs -0 sha1sum 2>/dev/null | sha1sum | cut -c1-7) \
   || date -u +%Y%m%d%H%M%S)"
printf '{"version":"%s","build_time":"%s","git_sha":"%s","build_at":"%s"}\n' \
  "$SHA" "$TS_ISO" "$SHA" "$TS_ISO" > "${ROOT}/version.json"

# 패키징: portal_api 루트 파일들을 스테이징에 복사 + shared 포함(robust)
STAGE="/tmp/portal_api_stage_${TS}"
rm -rf "$STAGE" && mkdir -p "$STAGE"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude 'venv' --exclude '__pycache__' --exclude '.git' "${ROOT}/" "$STAGE/"
else
  cp -a ${ROOT}/. "$STAGE/"
  rm -rf "$STAGE/venv" "$STAGE/__pycache__" "$STAGE/.git" 2>/dev/null || true
fi
if [ -d "${MONO_ROOT}/shared" ]; then
  cp -a "${MONO_ROOT}/shared" "$STAGE/"
fi

tar -C "$STAGE" -czf "$PKG" .
rm -rf "$STAGE"

if [[ "$DEPLOY_HOST" == "local" || "$DEPLOY_HOST" == "won@127.0.0.1" || "$DEPLOY_HOST" == "127.0.0.1" ]]; then
  ROOT_DST=/srv/portal_api
  REL="$ROOT_DST/releases/$TS"
  sudo mkdir -p "$REL" "$ROOT_DST"
  sudo tar -xzf "$PKG" -C "$REL"
  sudo rm -f "$PKG"
  if [ ! -x "$ROOT_DST/venv/bin/python" ]; then
    sudo python3 -m venv "$ROOT_DST/venv"
  fi
  sudo "$ROOT_DST/venv/bin/pip" install --upgrade pip > /dev/null
  if [ -f "$REL/requirements.txt" ]; then
    sudo "$ROOT_DST/venv/bin/pip" install -r "$REL/requirements.txt"
  fi
  sudo chown -R www-data:www-data "$ROOT_DST" "$REL"
  sudo ln -sfn "$REL" "$ROOT_DST/current"
  sudo systemctl daemon-reload
  sudo systemctl restart "$SERVICE_NAME"
  sudo systemctl is-active --quiet "$SERVICE_NAME" && echo "$SERVICE_NAME active" || (echo "$SERVICE_NAME failed"; exit 1)
else
  REM="/tmp/$(basename "$PKG")"
  scp "$PKG" "$DEPLOY_HOST:$REM"
  ssh "$DEPLOY_HOST" bash -lc "'
set -euo pipefail
ROOT=/srv/portal_api
REL=\$ROOT/releases/${TS}
sudo mkdir -p "\$REL" "\$ROOT"
sudo tar -xzf $REM -C "\$REL"; sudo rm -f $REM
if [ ! -x "\$ROOT/venv/bin/python" ]; then
  sudo python3 -m venv "\$ROOT/venv"
fi
sudo "\$ROOT/venv/bin/pip" install --upgrade pip > /dev/null
if [ -f "\$REL/requirements.txt" ]; then
  sudo "\$ROOT/venv/bin/pip" install -r "\$REL/requirements.txt"
fi
sudo chown -R www-data:www-data "\$ROOT" "\$REL"
sudo ln -sfn "\$REL" "\$ROOT/current"
sudo systemctl daemon-reload
sudo systemctl restart ${SERVICE_NAME}
sudo systemctl is-active --quiet ${SERVICE_NAME} && echo "${SERVICE_NAME} active" || (echo "${SERVICE_NAME} failed"; exit 1)
'"
fi

echo "API shipped & restarted (${SERVICE_NAME})"


