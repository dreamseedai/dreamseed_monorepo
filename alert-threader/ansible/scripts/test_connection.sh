#!/usr/bin/env bash
set -euo pipefail

# =============================
# Ansible 연결 테스트 스크립트
# =============================
# 모든 호스트에 대한 연결을 테스트합니다.

echo "🔍 Ansible 연결 테스트 시작..."

# 1. 인벤토리 확인
echo "📋 인벤토리 확인 중..."
if [ ! -f inventory/hosts.yaml ]; then
    echo "❌ 인벤토리 파일이 없습니다: inventory/hosts.yaml"
    exit 1
fi

echo "✅ 인벤토리 파일 발견: inventory/hosts.yaml"

# 2. 호스트 목록 표시
echo "📋 등록된 호스트:"
ansible all --list-hosts

# 3. 연결 테스트
echo "🔍 연결 테스트 중..."
if ansible all -m ping; then
    echo "✅ 모든 호스트에 연결 성공!"
else
    echo "❌ 일부 호스트에 연결 실패"
    echo "SSH 설정을 확인하세요:"
    echo "1. SSH 키가 올바르게 설정되었는지 확인"
    echo "2. 대상 서버에 SSH 접근이 가능한지 확인"
    echo "3. 방화벽 설정 확인"
    exit 1
fi

# 4. 시스템 정보 수집
echo "📊 시스템 정보 수집 중..."
ansible all -m setup -a "filter=ansible_distribution*"

# 5. 서비스 상태 확인
echo "🔍 서비스 상태 확인 중..."
ansible all -m systemd -a "name=alert-threader-python" || true
ansible all -m systemd -a "name=vault-agent-alert-threader" || true

# 6. 환경변수 파일 확인
echo "📁 환경변수 파일 확인 중..."
ansible all -m stat -a "path=/run/alert-threader.env" || true

echo "🎉 연결 테스트 완료!"
