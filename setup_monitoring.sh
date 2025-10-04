#!/usr/bin/env bash
set -euo pipefail

echo "📊 DreamSeed 모니터링 시스템 설정 시작"

# 1. 필요한 패키지 설치
echo "📦 필요한 패키지 설치 중..."
sudo apt update
sudo apt install -y prometheus alertmanager node-exporter redis-tools curl jq

# 2. 사용자 생성
echo "👤 모니터링 사용자 생성 중..."
sudo useradd --no-create-home --shell /bin/false prometheus 2>/dev/null || true
sudo useradd --no-create-home --shell /bin/false alertmanager 2>/dev/null || true

# 3. 디렉토리 생성
echo "📁 디렉토리 생성 중..."
sudo mkdir -p /etc/prometheus/rules
sudo mkdir -p /etc/alertmanager
sudo mkdir -p /var/lib/prometheus
sudo mkdir -p /var/lib/alertmanager
sudo mkdir -p /etc/alertmanager/templates

# 4. 권한 설정
sudo chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus
sudo chown -R alertmanager:alertmanager /etc/alertmanager /var/lib/alertmanager

# 5. Prometheus 설정 파일 복사
echo "⚙️ Prometheus 설정 중..."
sudo cp monitoring/prometheus/prometheus.yml /etc/prometheus/
sudo cp monitoring/prometheus/rules/dreamseed-alerts.yml /etc/prometheus/rules/
sudo chown -R prometheus:prometheus /etc/prometheus

# 6. Alertmanager 설정 파일 복사
echo "📢 Alertmanager 설정 중..."
sudo cp monitoring/alertmanager/alertmanager.yml /etc/alertmanager/
sudo cp monitoring/alertmanager/alertmanager.service.d/override.conf /etc/systemd/system/alertmanager.service.d/
sudo chown -R alertmanager:alertmanager /etc/alertmanager

# 7. systemd 서비스 설정
echo "🔧 systemd 서비스 설정 중..."
sudo cp monitoring/prometheus/prometheus.service /etc/systemd/system/
sudo cp monitoring/alertmanager/alertmanager.service /etc/systemd/system/
sudo mkdir -p /etc/systemd/system/alertmanager.service.d

# 8. systemd 데몬 리로드
sudo systemctl daemon-reload

# 9. 서비스 활성화 및 시작
echo "▶️ 서비스 시작 중..."
sudo systemctl enable prometheus
sudo systemctl start prometheus
sudo systemctl enable alertmanager
sudo systemctl start alertmanager

# 10. 상태 확인
echo "📊 서비스 상태 확인 중..."
sudo systemctl status prometheus --no-pager
sudo systemctl status alertmanager --no-pager

# 11. 포트 확인
echo "🔍 포트 확인 중..."
sudo netstat -tlnp | grep -E ':(9090|9093|9100)' || true

# 12. 설정 검증
echo "✅ 설정 검증 중..."
if command -v promtool >/dev/null 2>&1; then
    sudo promtool check config /etc/prometheus/prometheus.yml
    sudo promtool check rules /etc/prometheus/rules/dreamseed-alerts.yml
fi

if command -v amtool >/dev/null 2>&1; then
    sudo amtool check-config /etc/alertmanager/alertmanager.yml
fi

# 13. 테스트 알림 전송
echo "🧪 테스트 알림 전송 중..."
if command -v amtool >/dev/null 2>&1; then
    sudo amtool --alertmanager.url=http://localhost:9093 alert add \
        -l alertname=TestAlert -l severity=info -l service=test \
        -a summary="DreamSeed 모니터링 테스트 알림" \
        -a description="모니터링 시스템이 정상적으로 설정되었습니다."
fi

echo "🎉 DreamSeed 모니터링 시스템 설정 완료!"
echo ""
echo "📋 접속 정보:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Alertmanager: http://localhost:9093"
echo "  - Node Exporter: http://localhost:9100/metrics"
echo ""
echo "🔧 관리 명령어:"
echo "  - Prometheus 상태: sudo systemctl status prometheus"
echo "  - Alertmanager 상태: sudo systemctl status alertmanager"
echo "  - 로그 확인: sudo journalctl -u prometheus -f"
echo "  - 알림 확인: sudo journalctl -u alertmanager -f"
echo ""
echo "⚠️  중요:"
echo "  1. Slack Webhook URL을 /etc/systemd/system/alertmanager.service.d/override.conf에서 설정하세요"
echo "  2. 이메일 주소를 MAIL_TO 환경변수에 설정하세요"
echo "  3. 환경변수 변경 후: sudo systemctl daemon-reload && sudo systemctl restart alertmanager"

