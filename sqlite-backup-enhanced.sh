#!/usr/bin/env bash
set -euo pipefail

# Load env
source /etc/dreamseed.env

ts() { date -u +%Y%m%dT%H%M%SZ; }
log() { echo "[$(ts)] $*"; }
die() { echo "[$(ts)] ❌ $*" >&2; exit 1; }

# 알림 함수
send_notification() {
    local status="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Slack 알림 (SLACK_WEBHOOK_URL이 설정된 경우)
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color="good"
        if [ "$status" = "error" ]; then
            color="danger"
        elif [ "$status" = "warning" ]; then
            color="warning"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"DreamSeed 백업 $status\",
                    \"text\": \"$message\",
                    \"fields\": [{
                        \"title\": \"서버\",
                        \"value\": \"$(hostname)\",
                        \"short\": true
                    }, {
                        \"title\": \"시간\",
                        \"value\": \"$timestamp\",
                        \"short\": true
                    }]
                }]
            }" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    # 이메일 알림 (MAIL_TO가 설정된 경우)
    if [ -n "${MAIL_TO:-}" ] && command -v mail >/dev/null; then
        echo "$message" | mail -s "DreamSeed 백업 $status - $(hostname)" "$MAIL_TO" 2>/dev/null || true
    fi
    
    # 로그 파일에 기록
    echo "[$timestamp] $status: $message" >> /var/log/dreamseed-backup.log
}

# 백업 시작 알림
send_notification "info" "백업 작업을 시작합니다."

[ -f "$DB_PATH" ] || die "DB not found: $DB_PATH"
mkdir -p "$BACKUP_DIR"

STAMP=$(ts)
BASENAME="dreamseed_${STAMP}.db"
TMPDIR=$(mktemp -d)
RAW="$TMPDIR/$BASENAME"

# 우선 무결성 검사(원본)
log "Integrity check on source..."
if ! sqlite3 "$DB_PATH" "PRAGMA quick_check;" | grep -q 'ok'; then
    send_notification "error" "소스 데이터베이스 무결성 검사 실패"
    die "Source DB integrity check failed"
fi

# 읽기-일관성 백업(온라인 안전)
log "Creating online backup via sqlite .backup..."
if ! sqlite3 "$DB_PATH" ".backup '$RAW'"; then
    send_notification "error" "데이터베이스 백업 생성 실패"
    die "Failed to create database backup"
fi

# 백업본 무결성 재검사
log "Integrity check on backup copy..."
if ! sqlite3 "$RAW" "PRAGMA quick_check;" | grep -q 'ok'; then
    send_notification "error" "백업본 무결성 검사 실패"
    die "Backup copy integrity check failed"
fi

# 압축
OUT="$RAW"
case "${COMPRESS:-gzip}" in
  none) : ;;
  gzip) log "Compressing with gzip"; gzip -9 "$RAW"; OUT="${RAW}.gz" ;;
  xz)   log "Compressing with xz";  xz -T0 -9 "$RAW"; OUT="${RAW}.xz" ;;
  *)    die "Unknown COMPRESS=$COMPRESS" ;;
esac

# 암호화
if [ "${ENCRYPT:-none}" != "none" ]; then
  case "$ENCRYPT" in
    openssl)
      [ -n "${OPENSSL_PASSWORD:-}" ] || die "OPENSSL_PASSWORD missing"
      log "Encrypting with openssl"
      if ! openssl enc -aes-256-cbc -pbkdf2 -salt -in "$OUT" -out "${OUT}.enc" -pass pass:"$OPENSSL_PASSWORD"; then
        send_notification "error" "OpenSSL 암호화 실패"
        die "OpenSSL encryption failed"
      fi
      OUT="${OUT}.enc"
      ;;
    gpg)
      [ -n "${GPG_RECIPIENT:-}" ] || die "GPG_RECIPIENT missing"
      log "Encrypting with gpg"
      if ! gpg --batch --yes -r "$GPG_RECIPIENT" -o "${OUT}.gpg" -e "$OUT"; then
        send_notification "error" "GPG 암호화 실패"
        die "GPG encryption failed"
      fi
      OUT="${OUT}.gpg"
      ;;
    *) die "Unknown ENCRYPT=$ENCRYPT" ;;
  esac
fi

# 결과 파일 이동
FINAL="${BACKUP_DIR}/$(basename "$OUT")"
log "Saving to $FINAL"
mv "$OUT" "$FINAL"

# 체크섬
log "Writing checksum"
sha256sum "$FINAL" > "${FINAL}.sha256"

# 보존 정책
log "Retention: deleting files older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -type f -mtime +${RETENTION_DAYS} -name 'dreamseed_*' -print -delete || true

# 원격 업로드(선택)
case "${REMOTE_TYPE:-none}" in
  none) 
    log "No remote upload configured"
    ;;
  scp)   
    log "Uploading via scp to $REMOTE_TARGET"
    if scp -q "$FINAL" "${FINAL}.sha256" "$REMOTE_TARGET"; then
        log "SCP upload successful"
    else
        send_notification "error" "SCP 업로드 실패"
        die "SCP upload failed"
    fi
    ;;
  rsync) 
    log "Uploading via rsync to $REMOTE_TARGET"
    if rsync -az "$FINAL" "${FINAL}.sha256" "$REMOTE_TARGET"/; then
        log "Rsync upload successful"
    else
        send_notification "error" "Rsync 업로드 실패"
        die "Rsync upload failed"
    fi
    ;;
  s3)    
    log "Uploading to S3 $REMOTE_TARGET"
    command -v aws >/dev/null || die "aws cli not found"
    
    # AWS 프로파일 사용
    local aws_profile=""
    if [ -n "${AWS_PROFILE:-}" ]; then
        aws_profile="--profile $AWS_PROFILE"
    fi
    
    if aws s3 cp "$FINAL" "$REMOTE_TARGET" $aws_profile && \
       aws s3 cp "${FINAL}.sha256" "$REMOTE_TARGET" $aws_profile; then
        log "S3 upload successful"
    else
        send_notification "error" "S3 업로드 실패"
        die "S3 upload failed"
    fi
    ;;
  *)     
    die "Unknown REMOTE_TYPE=$REMOTE_TYPE" 
    ;;
esac

# 백업 완료 알림
local file_size=$(du -h "$FINAL" | cut -f1)
send_notification "success" "백업이 성공적으로 완료되었습니다. 파일: $(basename "$FINAL") (크기: $file_size)"

log "✅ Backup finished: $(basename "$FINAL")"
rm -rf "$TMPDIR"

