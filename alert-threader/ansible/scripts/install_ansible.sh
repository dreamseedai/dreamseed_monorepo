#!/usr/bin/env bash
set -euo pipefail

# =============================
# Ansible 설치 스크립트
# =============================
# Ubuntu/Debian 시스템에 Ansible을 설치합니다.

echo "🚀 Ansible 설치 시작..."

# 1. 시스템 업데이트
echo "📦 시스템 패키지 업데이트 중..."
sudo apt update
sudo apt upgrade -y

# 2. 필수 패키지 설치
echo "📦 필수 패키지 설치 중..."
sudo apt install -y \
    software-properties-common \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    jq \
    age

# 3. Ansible 저장소 추가
echo "📦 Ansible 저장소 추가 중..."
sudo apt-add-repository --yes --update ppa:ansible/ansible

# 4. Ansible 설치
echo "📦 Ansible 설치 중..."
sudo apt install -y ansible

# 5. Ansible 버전 확인
echo "✅ Ansible 설치 완료!"
ansible --version

# 6. Python 가상환경 생성 (선택사항)
echo "🐍 Python 가상환경 생성 중..."
python3 -m venv ~/.ansible-venv
source ~/.ansible-venv/bin/activate

# 7. Ansible 컬렉션 설치
echo "📦 Ansible 컬렉션 설치 중..."
cd "$(dirname "$0")/.."
ansible-galaxy collection install -r requirements.yml

# 8. SSH 키 생성 (없는 경우)
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "🔑 SSH 키 생성 중..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    echo "✅ SSH 키 생성 완료: ~/.ssh/id_rsa"
fi

# 9. SSH 키 복사 (자동화)
echo "🔑 SSH 키 복사 중..."
if command -v ssh-copy-id >/dev/null 2>&1; then
    echo "SSH 키를 대상 서버에 복사하려면 다음 명령어를 실행하세요:"
    echo "ssh-copy-id user@target-server"
else
    echo "SSH 키를 수동으로 복사하세요:"
    echo "cat ~/.ssh/id_rsa.pub | ssh user@target-server 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'"
fi

# 10. Ansible 설정 확인
echo "⚙️ Ansible 설정 확인 중..."
if [ -f ansible.cfg ]; then
    echo "✅ ansible.cfg 파일이 있습니다."
else
    echo "⚠️ ansible.cfg 파일이 없습니다. 기본 설정을 사용합니다."
fi

# 11. 인벤토리 확인
echo "📋 인벤토리 확인 중..."
if [ -f inventory/hosts.yaml ]; then
    echo "✅ 인벤토리 파일이 있습니다."
    echo "인벤토리 내용:"
    cat inventory/hosts.yaml
else
    echo "⚠️ 인벤토리 파일이 없습니다. inventory/hosts.yaml을 생성하세요."
fi

# 12. 연결 테스트
echo "🔍 연결 테스트 중..."
if ansible all -m ping >/dev/null 2>&1; then
    echo "✅ 모든 호스트에 연결 가능합니다."
else
    echo "⚠️ 일부 호스트에 연결할 수 없습니다. SSH 설정을 확인하세요."
fi

echo "🎉 Ansible 설치 및 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 인벤토리 파일 수정: inventory/hosts.yaml"
echo "2. 변수 설정: inventory/group_vars/all.yml"
echo "3. 플레이북 실행: ansible-playbook playbooks/deploy_env.yaml"
echo ""
echo "🔧 유용한 명령어:"
echo "- 연결 테스트: ansible all -m ping"
echo "- 플레이북 실행: ansible-playbook playbooks/deploy_env.yaml"
echo "- 특정 호스트만: ansible-playbook playbooks/deploy_env.yaml --limit threader-1"
echo "- 체크 모드: ansible-playbook playbooks/deploy_env.yaml --check"
echo "- 디버그 모드: ansible-playbook playbooks/deploy_env.yaml -vvv"
