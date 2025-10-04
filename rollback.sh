#!/bin/bash
set -euo pipefail

echo "🔄 DreamSeed 롤백 시작"

# 환경 변수 설정
BACKUP_DIR="/opt/dreamseed/backups"
SERVICE_NAME="dreamseed-api"

# 최신 백업 찾기
echo "📦 최신 백업 찾는 중..."
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/dreamseed_prod_* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ 롤백할 백업을 찾을 수 없습니다."
    exit 1
fi

echo "📋 백업 발견: $LATEST_BACKUP"

# 현재 서비스 중지
echo "⏹️ 현재 서비스 중지 중..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
docker stop dreamseed-prod 2>/dev/null || true
docker rm dreamseed-prod 2>/dev/null || true

# 백업에서 복원
echo "🔄 백업에서 복원 중..."
if [ -d "$LATEST_BACKUP" ]; then
    # 파일 기반 복원
    sudo cp -r "$LATEST_BACKUP"/* /opt/dreamseed/production/
    sudo systemctl start $SERVICE_NAME
elif docker images | grep -q "dreamseed:previous"; then
    # Docker 이미지 기반 복원
    docker run -d \
      --name dreamseed-prod \
      --restart unless-stopped \
      -p 8002:8002 \
      -e PORT=8002 \
      -e ENVIRONMENT=production \
      -e REDIS_URL=redis://localhost:6379 \
      -v /opt/dreamseed/data:/app/data \
      -v /opt/dreamseed/logs:/app/logs \
      dreamseed:previous
fi

# 헬스체크
echo "🏥 롤백 후 헬스체크 중..."
sleep 15
for i in {1..30}; do
    if curl -f http://localhost:8002/healthz > /dev/null 2>&1; then
        echo "✅ 롤백 성공!"
        echo "🌐 서비스 URL: http://localhost:8002"
        
        # 알림 전송
        curl -X POST -H 'Content-type: application/json' \
          --data '{"text":"⚠️ DreamSeed 롤백 완료 - 서비스 정상화"}' \
          ${SLACK_WEBHOOK_URL:-""} 2>/dev/null || true
        
        exit 0
    fi
    echo "⏳ 헬스체크 대기 중... ($i/30)"
    sleep 2
done

echo "❌ 롤백 실패 - 헬스체크 타임아웃"
echo "🚨 수동 개입이 필요합니다!"

# 서비스 상태 확인
echo "📊 서비스 상태:"
sudo systemctl status $SERVICE_NAME --no-pager || true
docker ps -a | grep dreamseed || true

exit 1

