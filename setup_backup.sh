#!/usr/bin/env bash
# DreamSeed SQLite 백업 시스템 설정 스크립트

set -euo pipefail

echo "🗄️ DreamSeed SQLite 백업 시스템 설정 시작..."

# 1. 백업 디렉터리 생성
echo "📁 백업 디렉터리 생성..."
echo '111' | sudo -S mkdir -p /var/backups/dreamseed
echo '111' | sudo -S chown root:root /var/backups/dreamseed
echo '111' | sudo -S chmod 0755 /var/backups/dreamseed

# 2. 환경 변수 파일 복사
echo "⚙️ 환경 변수 파일 설정..."
echo '111' | sudo -S cp dreamseed-backup.env /etc/dreamseed-backup.env
echo '111' | sudo -S chown root:root /etc/dreamseed-backup.env
echo '111' | sudo -S chmod 0644 /etc/dreamseed-backup.env

# 3. 백업 스크립트 복사
echo "📜 백업 스크립트 설정..."
echo '111' | sudo -S cp sqlite-backup.sh /usr/local/sbin/dreamseed-backup
echo '111' | sudo -S chown root:root /usr/local/sbin/dreamseed-backup
echo '111' | sudo -S chmod 0755 /usr/local/sbin/dreamseed-backup

# 4. 복구 스크립트 복사
echo "🔄 복구 스크립트 설정..."
echo '111' | sudo -S cp sqlite-restore.sh /usr/local/sbin/dreamseed-restore
echo '111' | sudo -S chown root:root /usr/local/sbin/dreamseed-restore
echo '111' | sudo -S chmod 0755 /usr/local/sbin/dreamseed-restore

# 5. systemd 서비스 파일 복사
echo "⚙️ systemd 서비스 설정..."
echo '111' | sudo -S cp dreamseed-backup.service /etc/systemd/system/dreamseed-backup.service
echo '111' | sudo -S cp dreamseed-backup.timer /etc/systemd/system/dreamseed-backup.timer
echo '111' | sudo -S chown root:root /etc/systemd/system/dreamseed-backup.service
echo '111' | sudo -S chown root:root /etc/systemd/system/dreamseed-backup.timer
echo '111' | sudo -S chmod 0644 /etc/systemd/system/dreamseed-backup.service
echo '111' | sudo -S chmod 0644 /etc/systemd/system/dreamseed-backup.timer

# 6. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드..."
echo '111' | sudo -S systemctl daemon-reload

# 7. 타이머 활성화
echo "⏰ 백업 타이머 활성화..."
echo '111' | sudo -S systemctl enable dreamseed-backup.timer
echo '111' | sudo -S systemctl start dreamseed-backup.timer

# 8. 즉시 백업 테스트
echo "🧪 백업 테스트 실행..."
echo '111' | sudo -S systemctl start dreamseed-backup.service

# 9. 상태 확인
echo "📊 백업 시스템 상태 확인..."
sleep 2
echo '111' | sudo -S systemctl status dreamseed-backup.service --no-pager
echo '111' | sudo -S systemctl status dreamseed-backup.timer --no-pager

# 10. 백업 파일 확인
echo "📁 백업 파일 확인..."
ls -lh /var/backups/dreamseed/ | tail -5 || echo "백업 파일이 아직 생성되지 않았습니다."

echo "✅ DreamSeed SQLite 백업 시스템 설정 완료!"
echo ""
echo "📋 운영 명령어:"
echo "  수동 백업: sudo systemctl start dreamseed-backup.service"
echo "  백업 로그: sudo journalctl -u dreamseed-backup.service -f"
echo "  타이머 상태: sudo systemctl status dreamseed-backup.timer"
echo "  복구: sudo dreamseed-restore /var/backups/dreamseed/dreamseed_YYYYMMDDTHHMMSSZ.db.gz"
echo ""
echo "📁 백업 위치: /var/backups/dreamseed/"
echo "⏰ 백업 스케줄: 매일 자동 실행"

