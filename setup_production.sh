#!/usr/bin/env bash
# DreamSeed API 프로덕션 환경 설정 스크립트

set -euo pipefail

echo "🚀 DreamSeed API 프로덕션 환경 설정 시작..."

# 1. 환경 변수 파일을 시스템 위치로 복사
echo "📁 환경 변수 파일 설정..."
sudo cp dreamseed.env /etc/dreamseed.env
sudo chown root:root /etc/dreamseed.env
sudo chmod 0644 /etc/dreamseed.env

# 2. UFW 스크립트를 시스템 위치로 복사
echo "🔥 UFW 자동 보정 스크립트 설정..."
sudo cp ufw-ensure-port.sh /usr/local/sbin/ufw-ensure-port
sudo chown root:root /usr/local/sbin/ufw-ensure-port
sudo chmod 0755 /usr/local/sbin/ufw-ensure-port

# 3. systemd 서비스 파일 복사
echo "⚙️ systemd 서비스 설정..."
sudo cp dreamseed-api.service /etc/systemd/system/dreamseed-api.service
sudo chown root:root /etc/systemd/system/dreamseed-api.service
sudo chmod 0644 /etc/systemd/system/dreamseed-api.service

# 4. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드..."
sudo systemctl daemon-reload

# 5. 서비스 활성화 및 시작
echo "▶️ 서비스 활성화 및 시작..."
sudo systemctl enable dreamseed-api
sudo systemctl start dreamseed-api

# 6. 서비스 상태 확인
echo "📊 서비스 상태 확인..."
sleep 3
sudo systemctl status dreamseed-api --no-pager

# 7. 헬스체크
echo "🏥 헬스체크..."
sleep 2
curl -s http://127.0.0.1:8000/healthz || echo "❌ 헬스체크 실패"

# 8. 포트 확인
echo "🔌 포트 리스닝 확인..."
ss -lntp | grep 8000 || echo "❌ 포트 8000이 리스닝되지 않음"

# 9. UFW 상태 확인
echo "🛡️ UFW 상태 확인..."
ufw status | grep 8000 || echo "❌ UFW에 포트 8000 규칙 없음"

echo "✅ 프로덕션 환경 설정 완료!"
echo ""
echo "📋 운영 명령어:"
echo "  상태 확인: sudo systemctl status dreamseed-api"
echo "  로그 확인: sudo journalctl -u dreamseed-api -f"
echo "  재시작: sudo systemctl restart dreamseed-api"
echo "  중지: sudo systemctl stop dreamseed-api"
echo ""
echo "🌐 접속 URL:"
echo "  로컬: http://127.0.0.1:8000/healthz"
echo "  외부: http://192.168.68.116:8000/healthz"

