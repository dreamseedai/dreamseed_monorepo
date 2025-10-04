#!/usr/bin/env bash
set -euo pipefail

echo "🔐 DreamSeed GPG 암호화 설정 시작"

# GPG 설치 확인
echo "📦 GPG 설치 확인 중..."
if ! command -v gpg &> /dev/null; then
    sudo apt update
    sudo apt install -y gnupg
    echo "✅ GPG 설치 완료"
else
    echo "✅ GPG 이미 설치됨"
fi

# GPG 키 생성
echo "🔑 GPG 키 생성 중..."
echo "이메일 주소를 입력하세요 (예: admin@dreamseed.com):"
read -r GPG_EMAIL
GPG_EMAIL=${GPG_EMAIL:-admin@dreamseed.com}

echo "이름을 입력하세요 (예: DreamSeed Admin):"
read -r GPG_NAME
GPG_NAME=${GPG_NAME:-DreamSeed Admin}

# GPG 키 생성 스크립트
cat > /tmp/gpg_key_config << EOF
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: $GPG_NAME
Name-Email: $GPG_EMAIL
Expire-Date: 0
%no-protection
%commit
EOF

# GPG 키 생성
gpg --batch --full-generate-key /tmp/gpg_key_config

# 생성된 키 ID 가져오기
GPG_KEY_ID=$(gpg --list-secret-keys --keyid-format LONG | grep -E "sec.*rsa4096" | head -1 | awk '{print $2}' | cut -d'/' -f2)

echo "✅ GPG 키 생성 완료 (ID: $GPG_KEY_ID)"

# 공개키 내보내기
echo "📤 공개키 내보내기 중..."
GPG_PUBLIC_KEY_FILE="/home/won/projects/dreamseed_monorepo/dreamseed_public_key.asc"
gpg --armor --export "$GPG_EMAIL" > "$GPG_PUBLIC_KEY_FILE"
echo "✅ 공개키 내보내기 완료: $GPG_PUBLIC_KEY_FILE"

# 개인키 백업 (안전한 위치에)
echo "💾 개인키 백업 중..."
GPG_PRIVATE_KEY_FILE="/home/won/projects/dreamseed_monorepo/dreamseed_private_key.asc"
gpg --armor --export-secret-keys "$GPG_EMAIL" > "$GPG_PRIVATE_KEY_FILE"
echo "✅ 개인키 백업 완료: $GPG_PRIVATE_KEY_FILE"

# 환경 변수 파일 업데이트
echo "⚙️ 환경 변수 파일 업데이트 중..."
BACKUP_ENV_FILE="/etc/dreamseed.env"

# 기존 파일 백업
if [ -f "$BACKUP_ENV_FILE" ]; then
    sudo cp "$BACKUP_ENV_FILE" "${BACKUP_ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# GPG 설정 추가
sudo tee -a "$BACKUP_ENV_FILE" > /dev/null << EOF

# GPG 암호화 설정
ENCRYPT=gpg
GPG_RECIPIENT=$GPG_EMAIL
GPG_KEY_ID=$GPG_KEY_ID
EOF

echo "✅ 환경 변수 파일 업데이트 완료"

# GPG 키 테스트
echo "🧪 GPG 암호화 테스트 중..."
TEST_FILE="/tmp/gpg_test.txt"
echo "DreamSeed GPG 암호화 테스트" > "$TEST_FILE"

# 암호화 테스트
if gpg --encrypt --recipient "$GPG_EMAIL" --armor "$TEST_FILE"; then
    echo "✅ GPG 암호화 테스트 성공"
    rm -f "$TEST_FILE" "${TEST_FILE}.asc"
else
    echo "❌ GPG 암호화 테스트 실패"
    exit 1
fi

# 키 정보 출력
echo "📋 GPG 키 정보:"
echo "  - 키 ID: $GPG_KEY_ID"
echo "  - 이메일: $GPG_EMAIL"
echo "  - 이름: $GPG_NAME"
echo "  - 공개키 파일: $GPG_PUBLIC_KEY_FILE"
echo "  - 개인키 파일: $GPG_PRIVATE_KEY_FILE"

# 보안 권한 설정
chmod 600 "$GPG_PRIVATE_KEY_FILE"
chmod 644 "$GPG_PUBLIC_KEY_FILE"

echo "🔒 보안 권한 설정 완료"

# 복구 서버용 공개키 배포 가이드
echo "📖 복구 서버용 공개키 배포 가이드:"
echo "1. 공개키 파일을 복구 서버로 복사:"
echo "   scp $GPG_PUBLIC_KEY_FILE user@recovery-server:/tmp/"
echo ""
echo "2. 복구 서버에서 공개키 가져오기:"
echo "   gpg --import /tmp/dreamseed_public_key.asc"
echo ""
echo "3. 신뢰도 설정:"
echo "   gpg --edit-key $GPG_EMAIL"
echo "   trust"
echo "   5"
echo "   quit"

echo "🎉 DreamSeed GPG 암호화 설정 완료!"

