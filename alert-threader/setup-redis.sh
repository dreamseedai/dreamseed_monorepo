#!/usr/bin/env bash
set -euo pipefail

echo "🔴 Redis 설정 시작"

# 1. Redis 설치
echo "📦 Redis 설치 중..."
sudo apt update
sudo apt install -y redis-server

# 2. Redis 설정 최적화
echo "⚙️ Redis 설정 최적화 중..."
sudo tee /etc/redis/redis.conf.d/threader.conf > /dev/null << 'EOF'
# DreamSeed Alert Threader 최적화 설정

# 메모리 설정
maxmemory 256mb
maxmemory-policy allkeys-lru

# 지속성 설정 (RDB + AOF)
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# 네트워크 설정
tcp-keepalive 300
timeout 0

# 로그 설정
loglevel notice
logfile /var/log/redis/redis-server.log

# 보안 설정
protected-mode yes
bind 127.0.0.1
port 6379

# 성능 설정
tcp-backlog 511
databases 16
EOF

# 3. Redis 서비스 시작
echo "▶️ Redis 서비스 시작 중..."
sudo systemctl enable redis-server
sudo systemctl restart redis-server

# 4. Redis 연결 테스트
echo "🔍 Redis 연결 테스트 중..."
sleep 2
if redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis: 정상 실행 중"
else
    echo "❌ Redis: 시작 실패"
    exit 1
fi

# 5. Redis 정보 확인
echo "📊 Redis 정보 확인 중..."
redis-cli info server | grep -E "(redis_version|uptime_in_seconds|used_memory_human)"

# 6. 데이터베이스 선택 (0번 사용)
echo "🗄️ 데이터베이스 설정 중..."
redis-cli select 0

# 7. 테스트 데이터 저장
echo "🧪 테스트 데이터 저장 중..."
redis-cli set "threader:ts:test-key" "test-thread-ts"
if redis-cli get "threader:ts:test-key" | grep -q "test-thread-ts"; then
    echo "✅ Redis 저장/조회: 성공"
    redis-cli del "threader:ts:test-key"
else
    echo "❌ Redis 저장/조회: 실패"
    exit 1
fi

# 8. Redis 모니터링 설정
echo "📈 Redis 모니터링 설정 중..."
sudo tee /etc/systemd/system/redis-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Redis Monitor for Alert Threader
After=redis-server.service
Wants=redis-server.service

[Service]
Type=simple
ExecStart=/usr/bin/redis-cli monitor
Restart=always
RestartSec=5
User=redis
Group=redis

[Install]
WantedBy=multi-user.target
EOF

# 9. Redis 백업 스크립트
echo "💾 Redis 백업 스크립트 생성 중..."
sudo tee /usr/local/bin/redis-backup.sh > /dev/null << 'EOF'
#!/usr/bin/env bash
BACKUP_DIR="/var/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/redis_backup_$DATE.rdb"

mkdir -p "$BACKUP_DIR"
redis-cli BGSAVE
sleep 5

if [ -f "/var/lib/redis/dump.rdb" ]; then
    cp /var/lib/redis/dump.rdb "$BACKUP_FILE"
    echo "Redis 백업 완료: $BACKUP_FILE"
else
    echo "Redis 백업 실패"
    exit 1
fi

# 오래된 백업 파일 삭제 (7일 이상)
find "$BACKUP_DIR" -name "redis_backup_*.rdb" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/redis-backup.sh

# 10. 크론 작업 설정 (매일 새벽 2시 백업)
echo "⏰ 크론 작업 설정 중..."
echo "0 2 * * * root /usr/local/bin/redis-backup.sh" | sudo tee /etc/cron.d/redis-backup

echo "🎉 Redis 설정 완료!"
echo ""
echo "📋 설정 요약:"
echo "  - Redis 버전: $(redis-cli info server | grep redis_version | cut -d: -f2 | tr -d ' ')"
echo "  - 포트: 6379"
echo "  - 바인딩: 127.0.0.1"
echo "  - 최대 메모리: 256MB"
echo "  - 지속성: RDB + AOF"
echo "  - 백업: 매일 새벽 2시"
echo ""
echo "🔧 관리 명령어:"
echo "  - Redis 상태: sudo systemctl status redis-server"
echo "  - Redis 재시작: sudo systemctl restart redis-server"
echo "  - Redis 클라이언트: redis-cli"
echo "  - Redis 모니터링: redis-cli monitor"
echo "  - 수동 백업: sudo /usr/local/bin/redis-backup.sh"
echo ""
echo "📊 모니터링:"
echo "  - 메모리 사용량: redis-cli info memory"
echo "  - 키 개수: redis-cli dbsize"
echo "  - 연결 수: redis-cli info clients"
echo "  - 통계: redis-cli info stats"

