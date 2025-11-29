#!/bin/bash
# PostgreSQL 백업 자동화 설정
# 실행: ./setup_backup.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_info "백업 자동화 설정 시작..."

# 1. 백업 디렉토리 생성
BACKUP_DIR="../configs/backup"
mkdir -p $BACKUP_DIR

# 2. Backblaze B2 CLI 설치 확인
if ! command -v b2 &> /dev/null; then
    log_warn "b2 CLI가 설치되지 않았습니다. 설치 중..."
    pip3 install b2sdk --quiet
fi

# 3. 환경 변수 로드
source ../../../.env

# 4. B2 인증 설정 (선택 사항)
if [ -n "$B2_APPLICATION_KEY_ID" ] && [ "$B2_APPLICATION_KEY_ID" != "your_b2_key_id" ]; then
    log_info "Backblaze B2 인증 중..."
    if b2 authorize-account $B2_APPLICATION_KEY_ID $B2_APPLICATION_KEY > /dev/null 2>&1; then
        log_info "✓ B2 인증 성공"
    else
        log_warn "B2 인증 실패. 로컬 백업만 사용합니다."
    fi
else
    log_warn "B2 설정이 없습니다. 로컬 백업만 사용합니다."
fi

# 5. 백업 스크립트 생성
cat > $BACKUP_DIR/backup_postgres.sh <<'BACKUP_SCRIPT'
#!/bin/bash
# PostgreSQL 백업 스크립트
# cron에서 매일 실행됨

set -e

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
docker exec dreamseed-postgres pg_dump -U postgres -d dreamseed | gzip > $BACKUP_DIR/$BACKUP_FILE

# 백업 파일 크기 확인
BACKUP_SIZE=$(du -h $BACKUP_DIR/$BACKUP_FILE | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Backblaze B2 업로드
echo "[$(date)] Uploading to Backblaze B2..."
b2 upload-file $B2_BUCKET_NAME $BACKUP_DIR/$BACKUP_FILE backups/$BACKUP_FILE

# 로컬 백업 파일 삭제 (30일 이상 된 파일)
find $BACKUP_DIR -name "dreamseed_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Slack 알림 (선택 사항)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ PostgreSQL backup completed: $BACKUP_FILE ($BACKUP_SIZE)\"}"
fi

echo "[$(date)] Backup completed successfully!"
BACKUP_SCRIPT

chmod +x $BACKUP_DIR/backup_postgres.sh

# 6. WAL 아카이빙 스크립트 생성
cat > $BACKUP_DIR/archive_wal.sh <<'WAL_SCRIPT'
#!/bin/bash
# PostgreSQL WAL 아카이빙 스크립트
# PostgreSQL archive_command에서 호출됨

set -e

WAL_FILE=$1
WAL_PATH=$2

# Backblaze B2로 WAL 파일 업로드
b2 upload-file $B2_BUCKET_NAME $WAL_PATH wal/$WAL_FILE

echo "WAL archived: $WAL_FILE"
WAL_SCRIPT

chmod +x $BACKUP_DIR/archive_wal.sh

# 7. 복구 스크립트 생성
cat > $BACKUP_DIR/restore_postgres.sh <<'RESTORE_SCRIPT'
#!/bin/bash
# PostgreSQL 복구 스크립트
# 사용법: ./restore_postgres.sh <backup_filename>

set -e

if [ -z "$1" ]; then
    echo "사용법: $0 <backup_filename>"
    echo "예: $0 dreamseed_db_20251111_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1
BACKUP_DIR="/tmp/postgres_backups"
source /home/won/projects/dreamseed_monorepo/.env

# B2에서 백업 파일 다운로드
echo "Downloading backup from B2..."
mkdir -p $BACKUP_DIR
b2 download-file-by-name $B2_BUCKET_NAME backups/$BACKUP_FILE $BACKUP_DIR/$BACKUP_FILE

# PostgreSQL 복구
echo "Restoring PostgreSQL..."
docker exec -i dreamseed-postgres psql -U postgres -d dreamseed < <(gunzip -c $BACKUP_DIR/$BACKUP_FILE)

echo "✓ Restore completed successfully!"
RESTORE_SCRIPT

chmod +x $BACKUP_DIR/restore_postgres.sh

# 8. cron 작업 추가
log_info "cron 작업 추가 중..."

# 기존 cron 항목 백업
crontab -l > /tmp/crontab_backup 2>/dev/null || true

# 백업 cron 추가 (매일 새벽 3시 15분)
CRON_JOB="15 3 * * * $BACKUP_DIR/backup_postgres.sh >> /var/log/dreamseed_backup.log 2>&1"

if ! crontab -l 2>/dev/null | grep -q "backup_postgres.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    log_info "✓ cron 작업 추가 완료"
else
    log_warn "cron 작업이 이미 존재합니다"
fi

# 9. 첫 백업 실행 (테스트)
log_info "테스트 백업 실행 중..."
$BACKUP_DIR/backup_postgres.sh

log_info "✓ 백업 자동화 설정 완료"
log_info "  - 백업 스크립트: $BACKUP_DIR/backup_postgres.sh"
log_info "  - 복구 스크립트: $BACKUP_DIR/restore_postgres.sh"
log_info "  - cron 일정: 매일 03:15 (로컬 시간)"
log_info "  - 백업 보관 기간: 30일"
