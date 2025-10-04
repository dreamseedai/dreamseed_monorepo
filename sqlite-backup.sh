#!/usr/bin/env bash
set -euo pipefail

# Load env
source /home/won/projects/dreamseed_monorepo/dreamseed-backup.env

ts() { date -u +%Y%m%dT%H%M%SZ; }
log() { echo "[$(ts)] $*"; }
die() { echo "[$(ts)] ❌ $*" >&2; exit 1; }

[ -f "$DB_PATH" ] || die "DB not found: $DB_PATH"
mkdir -p "$BACKUP_DIR"

STAMP=$(ts)
BASENAME="dreamseed_${STAMP}.db"
TMPDIR=$(mktemp -d)
RAW="$TMPDIR/$BASENAME"

# 우선 무결성 검사(원본)
log "Integrity check on source..."
sqlite3 "$DB_PATH" "PRAGMA quick_check;" | grep -q 'ok' || die "Source DB integrity check failed"

# 읽기-일관성 백업(온라인 안전)
log "Creating online backup via sqlite .backup..."
sqlite3 "$DB_PATH" ".backup '$RAW'"

# 백업본 무결성 재검사
log "Integrity check on backup copy..."
sqlite3 "$RAW" "PRAGMA quick_check;" | grep -q 'ok' || die "Backup copy integrity check failed"

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
      openssl enc -aes-256-cbc -pbkdf2 -salt -in "$OUT" -out "${OUT}.enc" -pass pass:"$OPENSSL_PASSWORD"
      OUT="${OUT}.enc"
      ;;
    gpg)
      [ -n "${GPG_RECIPIENT:-}" ] || die "GPG_RECIPIENT missing"
      log "Encrypting with gpg"
      gpg --batch --yes -r "$GPG_RECIPIENT" -o "${OUT}.gpg" -e "$OUT"
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
  none) : ;;
  scp)   log "Uploading via scp to $REMOTE_TARGET"; scp -q "$FINAL" "${FINAL}.sha256" "$REMOTE_TARGET" ;;
  rsync) log "Uploading via rsync to $REMOTE_TARGET"; rsync -az "$FINAL" "${FINAL}.sha256" "$REMOTE_TARGET"/ ;;
  s3)    log "Uploading to S3 $REMOTE_TARGET"; command -v aws >/dev/null || die "aws cli not found"; aws s3 cp "$FINAL" "$REMOTE_TARGET" && aws s3 cp "${FINAL}.sha256" "$REMOTE_TARGET" ;;
  *)     die "Unknown REMOTE_TYPE=$REMOTE_TYPE" ;;
esac

# I/O/CPU 친화도 낮추기(옵션): systemd timer에서 설정 권장
log "✅ Backup finished: $(basename "$FINAL")"
rm -rf "$TMPDIR"

