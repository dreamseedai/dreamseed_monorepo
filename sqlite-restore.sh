#!/usr/bin/env bash
set -euo pipefail

# Usage: sqlite-restore.sh /path/to/backupfile [TARGET_DB_PATH]
BACKUP="${1:-}"; TARGET="${2:-}"
[ -n "$BACKUP" ] || { echo "usage: sqlite-restore.sh <backupfile> [target_db]"; exit 1; }

# load default env if target omitted
if [ -z "$TARGET" ] && [ -f /home/won/projects/dreamseed_monorepo/dreamseed-backup.env ]; then
  source /home/won/projects/dreamseed_monorepo/dreamseed-backup.env
  TARGET="$DB_PATH"
fi
[ -n "$TARGET" ] || { echo "TARGET_DB unknown"; exit 1; }

echo "🔄 Restoring $BACKUP -> $TARGET"

# 체크섬 검증(있으면)
if [ -f "${BACKUP}.sha256" ]; then
  echo "📋 Verifying checksum..."
  sha256sum -c "${BACKUP}.sha256"
fi

# 복호화
TMPDIR=$(mktemp -d)
IN="$BACKUP"
case "$BACKUP" in
  *.enc)
    source /home/won/projects/dreamseed_monorepo/dreamseed-backup.env
    [ -n "${OPENSSL_PASSWORD:-}" ] || { echo "OPENSSL_PASSWORD missing"; exit 1; }
    echo "🔓 Decrypting with openssl..."
    openssl enc -d -aes-256-cbc -pbkdf2 -in "$BACKUP" -out "$TMPDIR/db.bin" -pass pass:"$OPENSSL_PASSWORD"
    IN="$TMPDIR/db.bin"
    ;;
  *.gpg)
    echo "🔓 Decrypting with gpg..."
    gpg --batch --yes -o "$TMPDIR/db.bin" -d "$BACKUP"
    IN="$TMPDIR/db.bin"
    ;;
esac

# 압축 해제
case "$IN" in
  *.gz) echo "📦 Decompressing gzip..."; gunzip -c "$IN" > "$TMPDIR/db.sqlite" ;;
  *.xz) echo "📦 Decompressing xz..."; xz -dc "$IN" > "$TMPDIR/db.sqlite" ;;
  *)    echo "📋 Copying file..."; cp "$IN" "$TMPDIR/db.sqlite" ;;
esac

# 무결성 검사
echo "🔍 Integrity check..."
sqlite3 "$TMPDIR/db.sqlite" "PRAGMA quick_check;" | grep -q 'ok' || { echo "❌ integrity check failed"; exit 1; }

# 서비스 중지(필요 시)
echo "⏹️ Stopping service..."
sudo systemctl stop dreamseed-api || echo "Service not running or failed to stop"

# 백업 생성
echo "💾 Creating backup of current DB..."
cp -a "$TARGET" "${TARGET}.bak.$(date +%s)" 2>/dev/null || true

# 복구 실행
echo "🔄 Installing restored database..."
install -m 0640 "$TMPDIR/db.sqlite" "$TARGET"

# 서비스 시작
echo "▶️ Starting service..."
sudo systemctl start dreamseed-api

echo "✅ Restore complete → $TARGET"
rm -rf "$TMPDIR"

