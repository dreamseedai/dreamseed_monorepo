#!/usr/bin/env bash
set -euo pipefail

echo "🚀 DreamSeed 고도화된 백업 시스템 설정 시작"

# 1. AWS S3 설정
echo "☁️ AWS S3 설정을 진행하시겠습니까? (y/n)"
read -r setup_s3
if [[ "$setup_s3" == "y" || "$setup_s3" == "Y" ]]; then
    chmod +x setup_aws_s3.sh
    ./setup_aws_s3.sh
fi

# 2. GPG 암호화 설정
echo "🔐 GPG 암호화 설정을 진행하시겠습니까? (y/n)"
read -r setup_gpg
if [[ "$setup_gpg" == "y" || "$setup_gpg" == "Y" ]]; then
    chmod +x setup_gpg_encryption.sh
    ./setup_gpg_encryption.sh
fi

# 3. 알림 설정
echo "📢 알림 설정을 진행하시겠습니까? (y/n)"
read -r setup_notifications
if [[ "$setup_notifications" == "y" || "$setup_notifications" == "Y" ]]; then
    echo "Slack Webhook URL을 입력하세요 (선택사항):"
    read -r slack_webhook
    echo "이메일 주소를 입력하세요 (선택사항):"
    read -r mail_to
    
    # 환경 변수 파일에 알림 설정 추가
    sudo tee -a /etc/dreamseed.env > /dev/null << EOF

# 알림 설정
SLACK_WEBHOOK_URL=$slack_webhook
MAIL_TO=$mail_to
EOF
fi

# 4. 고도화된 백업 스크립트 설치
echo "📦 고도화된 백업 스크립트 설치 중..."
sudo cp sqlite-backup-enhanced.sh /usr/local/sbin/dreamseed-backup-enhanced
sudo chown root:root /usr/local/sbin/dreamseed-backup-enhanced
sudo chmod 0755 /usr/local/sbin/dreamseed-backup-enhanced

# 5. systemd 서비스 업데이트
echo "⚙️ systemd 서비스 업데이트 중..."
sudo tee /etc/systemd/system/dreamseed-backup-enhanced.service > /dev/null << EOF
[Unit]
Description=DreamSeed Enhanced SQLite backup job
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=/etc/dreamseed.env
User=root
Group=root
ExecStart=/usr/local/sbin/dreamseed-backup-enhanced
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7

# 로그 디렉토리 생성
ExecStartPre=/bin/mkdir -p /var/log/dreamseed
ExecStartPre=/bin/touch /var/log/dreamseed-backup.log
ExecStartPre=/bin/chown root:root /var/log/dreamseed-backup.log
ExecStartPre=/bin/chmod 644 /var/log/dreamseed-backup.log
EOF

# 6. systemd 타이머 업데이트
echo "⏰ systemd 타이머 업데이트 중..."
sudo tee /etc/systemd/system/dreamseed-backup-enhanced.timer > /dev/null << EOF
[Unit]
Description=Daily DreamSeed Enhanced SQLite backup timer
Requires=dreamseed-backup-enhanced.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=600

[Install]
WantedBy=timers.target
EOF

# 7. Grafana 알림 규칙 설정
echo "📊 Grafana 알림 규칙 설정 중..."
if [ -d "/etc/grafana" ]; then
    sudo cp grafana-alert-rules.yml /etc/grafana/provisioning/alerting/dreamseed-alerts.yml
    sudo chown grafana:grafana /etc/grafana/provisioning/alerting/dreamseed-alerts.yml
    echo "✅ Grafana 알림 규칙 설정 완료"
else
    echo "⚠️ Grafana가 설치되지 않았습니다. 수동으로 알림 규칙을 설정해주세요."
    echo "파일 위치: $(pwd)/grafana-alert-rules.yml"
fi

# 8. 기존 백업 서비스 중지 및 새 서비스 시작
echo "🔄 백업 서비스 업데이트 중..."
sudo systemctl daemon-reload

# 기존 서비스 중지
sudo systemctl stop dreamseed-backup.timer 2>/dev/null || true
sudo systemctl disable dreamseed-backup.timer 2>/dev/null || true

# 새 서비스 시작
sudo systemctl enable dreamseed-backup-enhanced.timer
sudo systemctl start dreamseed-backup-enhanced.timer

# 9. 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
sudo systemctl status dreamseed-backup-enhanced.timer --no-pager
sudo systemctl status dreamseed-backup-enhanced.service --no-pager

# 10. 테스트 백업 실행
echo "🧪 테스트 백업 실행 중..."
sudo systemctl start dreamseed-backup-enhanced.service
sleep 5
sudo systemctl status dreamseed-backup-enhanced.service --no-pager

# 11. 설정 요약 출력
echo "🎉 DreamSeed 고도화된 백업 시스템 설정 완료!"
echo ""
echo "📋 설정 요약:"
echo "  - 백업 스크립트: /usr/local/sbin/dreamseed-backup-enhanced"
echo "  - 환경 변수: /etc/dreamseed.env"
echo "  - 로그 파일: /var/log/dreamseed-backup.log"
echo "  - 백업 디렉토리: $BACKUP_DIR"
echo "  - systemd 서비스: dreamseed-backup-enhanced.service"
echo "  - systemd 타이머: dreamseed-backup-enhanced.timer"
echo ""
echo "🔧 관리 명령어:"
echo "  - 백업 수동 실행: sudo systemctl start dreamseed-backup-enhanced.service"
echo "  - 타이머 상태 확인: sudo systemctl status dreamseed-backup-enhanced.timer"
echo "  - 로그 확인: sudo journalctl -u dreamseed-backup-enhanced.service -f"
echo "  - 백업 로그 확인: tail -f /var/log/dreamseed-backup.log"
echo ""
echo "📊 모니터링:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo "  - 알림 규칙: /etc/grafana/provisioning/alerting/dreamseed-alerts.yml"

