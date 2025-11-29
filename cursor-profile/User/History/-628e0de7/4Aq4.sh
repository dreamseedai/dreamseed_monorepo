#!/bin/bash
# SSH 서버 최적화 설정 적용 스크립트
# 서버(192.168.68.116)에서 실행하세요

set -e

echo "=== SSH 서버 최적화 설정 적용 ==="
echo

# 1. 드롭인 설정 파일 생성
echo "1. sshd_config.d 드롭인 파일 생성..."
sudo mkdir -p /etc/ssh/sshd_config.d
cat <<EOF | sudo tee /etc/ssh/sshd_config.d/10-fast-login.conf
UseDNS no
GSSAPIAuthentication no
PrintMotd no
PrintLastLog no
EOF

echo "✓ 설정 파일 생성 완료"
echo

# 2. 설정 적용
echo "2. sshd 서비스 재로드..."
sudo systemctl reload sshd

echo "✓ sshd 재로드 완료"
echo

# 3. 설정 확인
echo "3. 적용된 설정 확인..."
echo "---"
sudo sshd -T | grep -E '(usedns|gssapiauthentication|printmotd|printlastlog)' | grep -v '^#'
echo "---"
echo

# 4. (선택) MOTD 스크립트 성능 측정
if [ -d /etc/update-motd.d ]; then
    echo "4. MOTD 스크립트 성능 측정 (느린 스크립트 찾기)..."
    echo
    for script in /etc/update-motd.d/*; do
        if [ -x "$script" ]; then
            echo -n "$(basename $script): "
            { time timeout 2 bash "$script" >/dev/null 2>&1; } 2>&1 | grep real || echo "완료"
        fi
    done
    echo
    echo "※ 느린 스크립트가 있으면 비활성화하세요:"
    echo "   sudo chmod -x /etc/update-motd.d/스크립트명"
    echo
fi

# 5. (선택) 클라이언트 IP 호스트 등록
echo "5. 클라이언트 IP 호스트 등록 (선택사항)"
echo "현재 연결된 클라이언트 IP:"
who | grep -oP '\([0-9.]+\)' | sed 's/[()]//g' | sort -u || echo "IP 감지 실패"
echo
read -p "클라이언트 IP를 /etc/hosts에 등록하시겠습니까? (y/N): " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    read -p "클라이언트 IP 주소를 입력하세요: " client_ip
    read -p "호스트명을 입력하세요 (예: winpc): " hostname
    if [[ -n "$client_ip" && -n "$hostname" ]]; then
        echo "$client_ip  $hostname" | sudo tee -a /etc/hosts
        echo "✓ /etc/hosts에 등록 완료"
    fi
fi

echo
echo "=== 설정 완료 ==="
echo "이제 클라이언트에서 측정해보세요:"
echo "  ssh -T dreamseed true"
echo

