#!/usr/bin/env bash
set -euo pipefail

echo "🔐 DreamSeed Alert Threader - 비밀 관리 시스템 설치"

# 1. 비밀 관리 방식 선택
echo "📋 비밀 관리 방식을 선택하세요:"
echo "  1) SOPS (age/PGP) - Git에 암호화 상태로 저장"
echo "  2) HashiCorp Vault - 중앙 비밀저장소"
echo "  3) 둘 다 설치 (테스트용)"
read -p "선택 (1-3): " choice

case $choice in
    1)
        SECRET_METHODS=("sops")
        ;;
    2)
        SECRET_METHODS=("vault")
        ;;
    3)
        SECRET_METHODS=("sops" "vault")
        ;;
    *)
        echo "❌ 잘못된 선택입니다"
        exit 1
        ;;
esac

# 2. 필수 패키지 설치
echo "📦 필수 패키지 설치 중..."
sudo apt update
sudo apt install -y curl jq age

# 3. SOPS 설치 및 설정
if [[ " ${SECRET_METHODS[@]} " =~ " sops " ]]; then
    echo "🔐 SOPS 설치 및 설정 중..."
    
    # SOPS 설치
    if ! command -v sops >/dev/null 2>&1; then
        echo "  - SOPS 설치 중..."
        curl -sSL https://github.com/getsops/sops/releases/latest/download/sops-v3.8.1.linux.amd64 -o /tmp/sops
        sudo mv /tmp/sops /usr/local/bin/sops
        sudo chmod +x /usr/local/bin/sops
    fi
    
    # age 키 생성
    if [ ! -f ~/.config/sops/age/keys.txt ]; then
        echo "  - age 키 생성 중..."
        mkdir -p ~/.config/sops/age
        age-keygen -o ~/.config/sops/age/keys.txt
        echo "✅ age 키 생성 완료: ~/.config/sops/age/keys.txt"
        echo "⚠️  이 키를 안전한 곳에 백업하세요!"
    fi
    
    # SOPS 설정 파일 복사
    echo "  - SOPS 설정 파일 복사 중..."
    sudo mkdir -p /opt/alert-threader-sec
    sudo cp ops-secrets-sops/.sops.yaml /opt/alert-threader-sec/
    sudo cp ops-secrets-sops/alert-threader.env.enc /opt/alert-threader-sec/
    sudo chown -R root:root /opt/alert-threader-sec
    sudo chmod 0640 /opt/alert-threader-sec/alert-threader.env.enc
    
    # 복호화 스크립트 설치
    echo "  - 복호화 스크립트 설치 중..."
    sudo cp ops-secrets-sops/alert-threader-sops-decrypt.sh /usr/local/sbin/alert-threader-sops-decrypt
    sudo chmod +x /usr/local/sbin/alert-threader-sops-decrypt
    
    # SOPS 서비스 파일 복사
    echo "  - SOPS 서비스 파일 복사 중..."
    sudo cp ops-services-alert-threader-python-sops.service /etc/systemd/system/alert-threader-python.service
    sudo chown root:root /etc/systemd/system/alert-threader-python.service
    sudo chmod 644 /etc/systemd/system/alert-threader-python.service
    
    echo "✅ SOPS 설정 완료"
fi

# 4. Vault 설치 및 설정
if [[ " ${SECRET_METHODS[@]} " =~ " vault " ]]; then
    echo "🔐 HashiCorp Vault 설치 및 설정 중..."
    
    # Vault 설치
    if ! command -v vault >/dev/null 2>&1; then
        echo "  - Vault 설치 중..."
        curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
        sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
        sudo apt update
        sudo apt install -y vault
    fi
    
    # Vault Agent 설정 디렉터리 생성
    echo "  - Vault Agent 설정 디렉터리 생성 중..."
    sudo mkdir -p /etc/vault-agent.d
    sudo mkdir -p /run/vault
    
    # Vault 설정 파일 복사
    echo "  - Vault 설정 파일 복사 중..."
    sudo cp ops-secrets-vault/alert-threader.tpl /etc/vault-agent.d/
    sudo cp ops-secrets-vault/alert-threader.hcl /etc/vault-agent.d/
    sudo chown -R root:root /etc/vault-agent.d
    sudo chmod 0640 /etc/vault-agent.d/alert-threader.tpl
    sudo chmod 0640 /etc/vault-agent.d/alert-threader.hcl
    
    # Vault Agent 서비스 파일 복사
    echo "  - Vault Agent 서비스 파일 복사 중..."
    sudo cp ops-services-vault-agent-alert-threader.service /etc/systemd/system/
    sudo chown root:root /etc/systemd/system/vault-agent-alert-threader.service
    sudo chmod 644 /etc/systemd/system/vault-agent-alert-threader.service
    
    # Vault 서비스 파일 복사
    echo "  - Vault 서비스 파일 복사 중..."
    sudo cp ops-services-alert-threader-python-vault.service /etc/systemd/system/alert-threader-python.service
    sudo chown root:root /etc/systemd/system/alert-threader-python.service
    sudo chmod 644 /etc/systemd/system/alert-threader-python.service
    
    echo "✅ Vault 설정 완료"
fi

# 5. 환경변수 입력
echo "🔧 환경변수 입력 중..."
read -p "Slack Bot Token (xoxb-...): " SLACK_BOT_TOKEN
read -p "Slack Channel ID (C0123456789): " SLACK_CHANNEL
read -p "Environment (staging/production): " ENVIRONMENT
read -p "Thread Store (file/redis): " THREAD_STORE

# 6. SOPS 설정 (SOPS 사용 시)
if [[ " ${SECRET_METHODS[@]} " =~ " sops " ]]; then
    echo "🔐 SOPS 환경변수 설정 중..."
    
    # 평문 환경 파일 생성
    cat > /tmp/alert-threader.env <<EOF
SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
SLACK_CHANNEL=$SLACK_CHANNEL
ENVIRONMENT=$ENVIRONMENT
THREAD_STORE=$THREAD_STORE
THREAD_STORE_FILE=/var/lib/alert-threader/threads.json
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_KEY_PREFIX=threader:ts
EOF
    
    # SOPS로 암호화
    sops -e -i /tmp/alert-threader.env
    
    # 암호화된 파일 복사
    sudo cp /tmp/alert-threader.env /opt/alert-threader-sec/alert-threader.env.enc
    sudo chown root:root /opt/alert-threader-sec/alert-threader.env.enc
    sudo chmod 0640 /opt/alert-threader-sec/alert-threader.env.enc
    
    # 임시 파일 삭제
    rm -f /tmp/alert-threader.env
    
    echo "✅ SOPS 환경변수 설정 완료"
fi

# 7. Vault 설정 (Vault 사용 시)
if [[ " ${SECRET_METHODS[@]} " =~ " vault " ]]; then
    echo "🔐 Vault 환경변수 설정 중..."
    
    echo "Vault에 비밀을 저장하려면 다음 명령어를 실행하세요:"
    echo ""
    echo "vault kv put kv/alert-threader \\"
    echo "  SLACK_BOT_TOKEN=\"$SLACK_BOT_TOKEN\" \\"
    echo "  SLACK_CHANNEL=\"$SLACK_CHANNEL\" \\"
    echo "  ENVIRONMENT=\"$ENVIRONMENT\" \\"
    echo "  THREAD_STORE=\"$THREAD_STORE\" \\"
    echo "  THREAD_STORE_FILE=\"/var/lib/alert-threader/threads.json\" \\"
    echo "  REDIS_URL=\"redis://127.0.0.1:6379/0\" \\"
    echo "  REDIS_KEY_PREFIX=\"threader:ts\""
    echo ""
    echo "또는 Vault UI에서 kv/alert-threader 경로에 비밀을 저장하세요."
    echo ""
    read -p "Vault 비밀 저장을 완료했으면 Enter를 누르세요..."
fi

# 8. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드 중..."
sudo systemctl daemon-reload

# 9. 서비스 시작
echo "▶️ 서비스 시작 중..."

if [[ " ${SECRET_METHODS[@]} " =~ " sops " ]]; then
    echo "  - SOPS 방식으로 서비스 시작 중..."
    sudo systemctl enable alert-threader-python
    sudo systemctl start alert-threader-python
elif [[ " ${SECRET_METHODS[@]} " =~ " vault " ]]; then
    echo "  - Vault 방식으로 서비스 시작 중..."
    sudo systemctl enable vault-agent-alert-threader
    sudo systemctl start vault-agent-alert-threader
    sleep 5
    sudo systemctl enable alert-threader-python
    sudo systemctl start alert-threader-python
fi

# 10. 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 5

if systemctl is-active --quiet alert-threader-python; then
    echo "✅ Alert Threader (Python): 정상 실행 중"
else
    echo "❌ Alert Threader (Python): 시작 실패"
    echo "로그 확인: sudo journalctl -u alert-threader-python -f"
    exit 1
fi

# 11. 포트 확인
echo "🔍 포트 확인 중..."
if netstat -tlnp | grep -q ":9009 "; then
    echo "✅ 포트 9009: 열림"
else
    echo "❌ 포트 9009: 닫힘"
fi

# 12. 헬스체크
echo "🏥 헬스체크 중..."
sleep 2
if curl -s http://localhost:9009/health | jq .; then
    echo "✅ 헬스체크: 성공"
else
    echo "❌ 헬스체크: 실패"
fi

# 13. 통계 확인
echo "📊 통계 확인 중..."
if curl -s http://localhost:9009/stats | jq .; then
    echo "✅ 통계 조회: 성공"
else
    echo "❌ 통계 조회: 실패"
fi

echo "🎉 DreamSeed Alert Threader 비밀 관리 시스템 설치 완료!"
echo ""
echo "📋 설정 요약:"
echo "  - 비밀 관리 방식: ${SECRET_METHODS[*]}"
echo "  - 서비스: alert-threader-python"
echo "  - 포트: 9009"
echo "  - 채널: $SLACK_CHANNEL"
echo "  - 환경: $ENVIRONMENT"
echo "  - 저장소: $THREAD_STORE"

if [[ " ${SECRET_METHODS[@]} " =~ " sops " ]]; then
    echo "  - SOPS 설정: /opt/alert-threader-sec/alert-threader.env.enc"
    echo "  - 복호화 스크립트: /usr/local/sbin/alert-threader-sops-decrypt"
fi

if [[ " ${SECRET_METHODS[@]} " =~ " vault " ]]; then
    echo "  - Vault Agent: vault-agent-alert-threader"
    echo "  - Vault 설정: /etc/vault-agent.d/alert-threader.hcl"
    echo "  - 템플릿: /etc/vault-agent.d/alert-threader.tpl"
fi

echo ""
echo "🔧 다음 단계:"
echo "  1. 로그 확인:"
echo "     sudo journalctl -u alert-threader-python -f"
if [[ " ${SECRET_METHODS[@]} " =~ " vault " ]]; then
    echo "     sudo journalctl -u vault-agent-alert-threader -f"
fi
echo ""
echo "  2. 환경변수 확인:"
echo "     sudo cat /run/alert-threader.env"
echo ""
echo "  3. 서비스 관리:"
echo "     sudo systemctl status alert-threader-python"
if [[ " ${SECRET_METHODS[@]} " =~ " vault " ]]; then
    echo "     sudo systemctl status vault-agent-alert-threader"
fi
echo ""
echo "  4. 비밀 업데이트:"
if [[ " ${SECRET_METHODS[@]} " =~ " sops " ]]; then
    echo "     # SOPS 방식:"
    echo "     sudo nano /opt/alert-threader-sec/alert-threader.env.enc"
    echo "     sudo systemctl restart alert-threader-python"
fi
if [[ " ${SECRET_METHODS[@]} " =~ " vault " ]]; then
    echo "     # Vault 방식:"
    echo "     vault kv put kv/alert-threader SLACK_BOT_TOKEN=\"new_token\""
    echo "     # 자동으로 /run/alert-threader.env가 업데이트됨"
fi
echo ""
echo "  5. 테스트 실행:"
echo "     chmod +x test-all-advanced.sh"
echo "     ./test-all-advanced.sh"
