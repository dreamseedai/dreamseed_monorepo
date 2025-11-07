#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-portal-api.service}"
ENV_FILE="/etc/default/portal-api"
UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}"

# 기본 환경파일
sudo tee "$ENV_FILE" >/dev/null <<'ENV'
# portal-api defaults
APP_DIR=/srv/portal_api/current
VENV=/srv/portal_api/venv
APP_MODULE=app.main:app
HOST=127.0.0.1
PORT=8000
WORKERS=1
EXTRA_ARGS=--proxy-headers --forwarded-allow-ips="*"
RUN_AS=www-data
GROUP_AS=www-data
ENV

# systemd 유닛
sudo tee "$UNIT_FILE" >/dev/null <<'UNIT'
[Unit]
Description=DreamSeed Portal API (FastAPI/Uvicorn)
After=network.target

[Service]
EnvironmentFile=-/etc/default/portal-api
User=%i
Group=%G
# 위 %i/%G는 sed로 치환됩니다.

WorkingDirectory=/srv/portal_api/current
ExecStart=/usr/bin/env bash -lc '${VENV}/bin/uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT} --workers ${WORKERS} ${EXTRA_ARGS}'
Restart=always
RestartSec=2
KillMode=mixed
TimeoutStopSec=10
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
UNIT

# 유닛 내 User/Group 치환
RUN_AS="$(grep '^RUN_AS=' "$ENV_FILE" | cut -d= -f2)"
GROUP_AS="$(grep '^GROUP_AS=' "$ENV_FILE" | cut -d= -f2)"
sudo sed -i "s/User=%i/User=${RUN_AS}/" "$UNIT_FILE"
sudo sed -i "s/Group=%G/Group=${GROUP_AS}/" "$UNIT_FILE"

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME" || true

echo "installed: $UNIT_FILE (env: $ENV_FILE)"


