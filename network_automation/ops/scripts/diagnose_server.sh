#!/usr/bin/env bash
# Linux 서버 네트워크/방화벽/포트 진단 스크립트
# 사용법: chmod +x diagnose_server.sh && ./diagnose_server.sh <PORT>
PORT=${1:-8080}
IP=$(hostname -I | awk '{print $1}')

echo "🔎 서버 진단 시작 (IP=$IP, PORT=$PORT)"

echo -e "\n[1] Listening 포트 확인"
ss -lntp | grep ":$PORT" || echo "❌ 포트 $PORT LISTEN 안됨"

echo -e "\n[2] UFW 방화벽 규칙 확인"
sudo ufw status verbose | grep "$PORT" || echo "❌ UFW에서 $PORT 허용 안됨"

echo -e "\n[3] iptables 규칙 확인"
sudo iptables -L -n -v | grep "$PORT" || echo "❌ iptables에 $PORT 관련 규칙 없음"

echo -e "\n[4] 로컬 접속 테스트 (curl)"
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:$PORT || echo "❌ 로컬 접속 실패"

echo -e "\n[5] 외부 IP 접속 테스트 (curl)"
curl -s -o /dev/null -w "%{http_code}\n" http://$IP:$PORT || echo "❌ 외부 IP 접속 실패"

echo -e "\n[6] TCP 패킷 수신 확인 (10초 동안)"
echo "Windows에서 접속 시도 후 Ctrl+C로 중단하세요"
sudo timeout 10 tcpdump -i any port $PORT -nn || echo "tcpdump 실행 실패 (권한 또는 패키지 없음)"

echo -e "\n[7] 프로세스별 포트 사용 확인"
lsof -i :$PORT || echo "lsof 실행 실패"

echo -e "\n[8] 네트워크 인터페이스 확인"
ip addr show | grep -E "inet.*192\.168" || echo "192.168.x.x 대역 IP 없음"

echo -e "\n[9] 라우팅 테이블 확인"
ip route show | head -5

echo -e "\n✅ 진단 완료"
echo "💡 해결 방법:"
echo "   - 포트가 LISTEN 안됨 → 서버 재시작"
echo "   - UFW 차단 → sudo ufw allow $PORT/tcp"
echo "   - 패킷 안옴 → Windows 방화벽/네트워크 정책 확인"
