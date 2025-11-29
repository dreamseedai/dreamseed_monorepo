#!/bin/bash
# PostgreSQL 백업 스크립트
# cron에서 매일 실행됨

# 환경 변수 로드
source /home/won/projects/dreamseed_monorepo/.env

# 변수 설정
BACKUP_DIR="/tmp/postgres_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="dreamseed_db_${DATE}.sql.gz"
RETENTION_DAYS=30

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# PostgreSQL 덤프 (압축)
echo "[$(date)] Starting PostgreSQL backup..."

# Docker 또는 호스트 PostgreSQL 확인
if docker ps | grep -q dreamseed-postgres; then
    docker exec dreamseed-postgres pg_dump -U postgres -d dreamseed | gzip > $BACKUP_DIR/$BACKUP_FILE
else
    # 호스트 PostgreSQL 사용
    PGPASSWORD="${DB_PASSWORD}" pg_dump -h ${DB_HOST:-localhost} -U ${DB_USER:-postgres} -d ${DB_NAME:-dreamseed} | gzip > $BACKUP_DIR/$BACKUP_FILE
fi

# 백업 파일 크기 확인
BACKUP_SIZE=$(du -h $BACKUP_DIR/$BACKUP_FILE | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Backblaze B2 업로드 (설정된 경우만)
if [ -n "$B2_APPLICATION_KEY_ID" ] && [ "$B2_APPLICATION_KEY_ID" != "your_b2_key_id" ]; then
    echo "[$(date)] Uploading to Backblaze B2..."
    if b2 file upload $B2_BUCKET_NAME $BACKUP_DIR/$BACKUP_FILE backups/$BACKUP_FILE 2>/dev/null; then
        echo "[$(date)] ✓ B2 upload successful"
    else
        echo "[$(date)] ⚠ B2 upload failed, keeping local backup only"
    fi
else
    echo "[$(date)] B2 not configured, keeping local backup only"
fi

# 로컬 백업 파일 삭제 (30일 이상 된 파일)
find $BACKUP_DIR -name "dreamseed_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Slack 알림 (선택 사항)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ PostgreSQL backup completed: $BACKUP_FILE ($BACKUP_SIZE)\"}"
fi

echo "[$(date)] Backup completed successfully!"
