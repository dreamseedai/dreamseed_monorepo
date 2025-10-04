#!/usr/bin/env bash
# diagnose_server.sh
PORT=${1:-5000}
IP=$(hostname -I | awk '{print $1}')

echo "=== Linux 서버 진단 (IP=$IP, PORT=$PORT) ==="

echo "[1] 서비스 바인딩 확인"
ss -lntp | grep ":$PORT" || echo "❌ $PORT 포트 LISTEN 없음"

echo "[2] Flask 프로세스 확인"
ps -ef | grep flask | grep -v grep

echo "[3] UFW 방화벽 상태"
sudo ufw status | grep "$PORT" || echo "❌ UFW에 $PORT 허용 없음 → sudo ufw allow $PORT/tcp"

echo "[4] iptables 규칙 확인"
sudo iptables -L -n -v | grep "$PORT" || echo "ℹ️ iptables 규칙 없음 (기본 ACCEPT인지 확인 필요)"

echo "[5] 로컬 접근(curl)"
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:$PORT || echo "❌ 로컬 실패"

echo "[6] 외부 IP 접근(curl)"
curl -s -o /dev/null -w "%{http_code}\n" http://$IP:$PORT || echo "❌ 외부 실패"

echo "[7] 패킷 캡처(10초 동안) - 브라우저에서 접속 시도하세요"
sudo timeout 10 tcpdump -i any port $PORT -nn