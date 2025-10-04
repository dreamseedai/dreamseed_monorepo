#!/usr/bin/env bash
set -euo pipefail

# SOPS 기반 환경변수 복호화 스크립트
# 사용법: alert-threader-sops-decrypt [암호화된_파일_경로]

SRC=${1:-/opt/alert-threader-sec/alert-threader.env.enc}
OUT=/run/alert-threader.env

echo "🔐 SOPS 복호화 중: $SRC → $OUT"

# SOPS 설치 확인
if ! command -v sops >/dev/null 2>&1; then
    echo "❌ SOPS가 설치되지 않았습니다. 설치 중..."
    curl -sSL https://github.com/getsops/sops/releases/latest/download/sops-v3.8.1.linux.amd64 -o /tmp/sops
    sudo mv /tmp/sops /usr/local/bin/sops
    sudo chmod +x /usr/local/bin/sops
fi

# age 키 확인
if [ ! -f ~/.config/sops/age/keys.txt ]; then
    echo "❌ age 키가 없습니다. 생성 중..."
    mkdir -p ~/.config/sops/age
    age-keygen -o ~/.config/sops/age/keys.txt
    echo "✅ age 키 생성 완료: ~/.config/sops/age/keys.txt"
    echo "⚠️  이 키를 안전한 곳에 백업하세요!"
fi

# 소스 파일 존재 확인
if [ ! -f "$SRC" ]; then
    echo "❌ 소스 파일이 없습니다: $SRC"
    exit 1
fi

# 임시 파일 생성 (원자적 교체)
umask 0177
mkdir -p /run
tmp=$(mktemp /run/alert-threader.env.XXXXXX)

# SOPS 복호화
if sops -d "$SRC" > "$tmp"; then
    # 권한 설정
    chmod 0640 "$tmp"
    chown root:root "$tmp"
    
    # 원자적 교체
    mv "$tmp" "$OUT"
    
    echo "✅ SOPS 복호화 완료: $OUT"
    echo "📊 파일 정보:"
    ls -la "$OUT"
    
    # 환경변수 검증
    echo "🔍 환경변수 검증:"
    if grep -q "SLACK_BOT_TOKEN=" "$OUT"; then
        echo "  ✅ SLACK_BOT_TOKEN: 설정됨"
    else
        echo "  ❌ SLACK_BOT_TOKEN: 누락"
    fi
    
    if grep -q "SLACK_CHANNEL=" "$OUT"; then
        echo "  ✅ SLACK_CHANNEL: 설정됨"
    else
        echo "  ❌ SLACK_CHANNEL: 누락"
    fi
    
    if grep -q "THREAD_STORE=" "$OUT"; then
        echo "  ✅ THREAD_STORE: 설정됨"
    else
        echo "  ❌ THREAD_STORE: 누락"
    fi
    
else
    echo "❌ SOPS 복호화 실패"
    rm -f "$tmp"
    exit 1
fi
