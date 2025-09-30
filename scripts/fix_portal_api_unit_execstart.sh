#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_HOST:?export DEPLOY_HOST=user@server 형태로 설정}"
SERVICE_NAME="${SERVICE_NAME:-portal-api.service}"

ssh "$DEPLOY_HOST" bash -lc "sudo sed -i 's|^ExecStart=.*|ExecStart=/usr/bin/env bash -lc \"${VENV}/bin/uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT} --workers ${WORKERS} ${EXTRA_ARGS}\"|' /etc/systemd/system/${SERVICE_NAME} && sudo systemctl daemon-reload && sudo systemctl enable --now ${SERVICE_NAME} && systemctl status ${SERVICE_NAME} --no-pager | sed -n '1,10p' && ss -ltnp | grep :8000 || true"

echo "Updated ExecStart and restarted ${SERVICE_NAME} on ${DEPLOY_HOST}"


