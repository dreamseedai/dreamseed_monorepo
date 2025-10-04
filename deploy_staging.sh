#!/bin/bash
set -euo pipefail

echo "🚀 DreamSeed 스테이징 배포 시작"

# 환경 변수 설정
DEPLOY_DIR="/opt/dreamseed/staging"
SERVICE_NAME="dreamseed-staging"
BACKUP_DIR="/opt/dreamseed/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 배포 전 백업
echo "📦 기존 버전 백업 중..."
if [ -d "$DEPLOY_DIR" ]; then
    sudo mkdir -p "$BACKUP_DIR"
    sudo cp -r "$DEPLOY_DIR" "$BACKUP_DIR/dreamseed_$TIMESTAMP"
    echo "✅ 백업 완료: $BACKUP_DIR/dreamseed_$TIMESTAMP"
fi

# 배포 디렉토리 생성
echo "📁 배포 디렉토리 준비 중..."
sudo mkdir -p "$DEPLOY_DIR"
sudo chown -R $USER:$USER "$DEPLOY_DIR"

# 코드 복사
echo "📋 코드 복사 중..."
cp -r api/ "$DEPLOY_DIR/"
cp -r admin/ "$DEPLOY_DIR/"
cp -r *.html "$DEPLOY_DIR/"
cp -r *.py "$DEPLOY_DIR/"
cp -r *.sh "$DEPLOY_DIR/"
cp -r *.conf "$DEPLOY_DIR/"
cp -r *.yml "$DEPLOY_DIR/"
cp -r *.json "$DEPLOY_DIR/"
cp -r requirements.txt "$DEPLOY_DIR/"
cp -r Dockerfile "$DEPLOY_DIR/"

# Python 가상환경 설정
echo "🐍 Python 환경 설정 중..."
cd "$DEPLOY_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 환경 변수 설정
echo "⚙️ 환경 변수 설정 중..."
cat > "$DEPLOY_DIR/.env" << EOF
# DreamSeed 스테이징 환경 설정
PORT=8003
APP_MODULE=api.dashboard_data:app
WORKDIR=$DEPLOY_DIR
VENV=$DEPLOY_DIR/venv
DB_PATH=$DEPLOY_DIR/dreamseed_analytics.db
REDIS_URL=redis://localhost:6379
ENVIRONMENT=staging
EOF

# systemd 서비스 설정
echo "🔧 systemd 서비스 설정 중..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=DreamSeed Staging API Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=$DEPLOY_DIR/.env
WorkingDirectory=$DEPLOY_DIR
User=$USER
Group=$USER

ExecStart=/usr/bin/env bash -lc '\
  cd "\${WORKDIR}" && \
  source "\${VENV}/bin/activate" && \
  exec "\${VENV}/bin/gunicorn" \
    --config gunicorn.conf.py \
    --bind "0.0.0.0:\${PORT}" \
    "\${APP_MODULE}" \
'

ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
EOF

# 서비스 시작
echo "▶️ 서비스 시작 중..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# 헬스체크
echo "🏥 헬스체크 중..."
sleep 10
for i in {1..30}; do
    if curl -f http://localhost:8003/healthz > /dev/null 2>&1; then
        echo "✅ 스테이징 배포 성공!"
        echo "🌐 스테이징 URL: http://localhost:8003"
        exit 0
    fi
    echo "⏳ 헬스체크 대기 중... ($i/30)"
    sleep 2
done

echo "❌ 스테이징 배포 실패 - 헬스체크 타임아웃"
sudo systemctl status $SERVICE_NAME --no-pager
exit 1

