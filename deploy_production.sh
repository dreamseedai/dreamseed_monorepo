#!/bin/bash
set -euo pipefail

echo "🚀 DreamSeed 프로덕션 배포 시작"

# 환경 변수 설정
DEPLOY_DIR="/opt/dreamseed/production"
SERVICE_NAME="dreamseed-api"
BACKUP_DIR="/opt/dreamseed/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DOCKER_IMAGE="dreamseed:latest"

# 배포 전 백업
echo "📦 기존 버전 백업 중..."
if [ -d "$DEPLOY_DIR" ]; then
    sudo mkdir -p "$BACKUP_DIR"
    sudo cp -r "$DEPLOY_DIR" "$BACKUP_DIR/dreamseed_prod_$TIMESTAMP"
    echo "✅ 백업 완료: $BACKUP_DIR/dreamseed_prod_$TIMESTAMP"
fi

# Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 중..."
docker build -t $DOCKER_IMAGE .

# 기존 컨테이너 중지
echo "⏹️ 기존 컨테이너 중지 중..."
docker stop dreamseed-prod 2>/dev/null || true
docker rm dreamseed-prod 2>/dev/null || true

# 새 컨테이너 시작
echo "▶️ 새 컨테이너 시작 중..."
docker run -d \
  --name dreamseed-prod \
  --restart unless-stopped \
  -p 8002:8002 \
  -e PORT=8002 \
  -e ENVIRONMENT=production \
  -e REDIS_URL=redis://localhost:6379 \
  -v /opt/dreamseed/data:/app/data \
  -v /opt/dreamseed/logs:/app/logs \
  $DOCKER_IMAGE

# 헬스체크
echo "🏥 헬스체크 중..."
sleep 30
for i in {1..60}; do
    if curl -f http://localhost:8002/healthz > /dev/null 2>&1; then
        echo "✅ 프로덕션 배포 성공!"
        echo "🌐 프로덕션 URL: https://dreamseedai.com"
        
        # Nginx 설정 업데이트 (필요한 경우)
        if command -v nginx >/dev/null 2>&1; then
            echo "🔄 Nginx 설정 업데이트 중..."
            sudo nginx -t && sudo systemctl reload nginx
        fi
        
        # 모니터링 알림
        echo "📊 모니터링 시스템 업데이트 중..."
        curl -X POST -H 'Content-type: application/json' \
          --data '{"text":"🚀 DreamSeed 프로덕션 배포 완료!"}' \
          ${SLACK_WEBHOOK_URL:-""} 2>/dev/null || true
        
        exit 0
    fi
    echo "⏳ 헬스체크 대기 중... ($i/60)"
    sleep 5
done

echo "❌ 프로덕션 배포 실패 - 헬스체크 타임아웃"
echo "🔄 롤백 시작..."

# 롤백
if [ -d "$BACKUP_DIR/dreamseed_prod_$TIMESTAMP" ]; then
    echo "🔄 이전 버전으로 롤백 중..."
    docker stop dreamseed-prod 2>/dev/null || true
    docker rm dreamseed-prod 2>/dev/null || true
    
    # 이전 Docker 이미지 사용 (있다면)
    if docker images | grep -q "dreamseed:previous"; then
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
    
    echo "⚠️ 롤백 완료"
fi

exit 1

