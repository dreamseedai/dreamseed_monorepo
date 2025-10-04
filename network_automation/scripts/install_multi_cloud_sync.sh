#!/bin/bash
# 멀티 클라우드 CIDR 자동 동기화 시스템 설치 스크립트
# 목적: Cloudflare, AWS ELB, GCP LB CIDR 동기화 시스템을 설치하고 활성화

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR=$(dirname "$0")

log_info "=== 멀티 클라우드 CIDR 자동 동기화 시스템 설치 시작 ==="

# 1. 의존성 확인 및 설치
log_info "1. 의존성 확인 및 설치 중..."
if ! command -v curl >/dev/null 2>&1; then
    log_info "curl 설치 중..."
    sudo apt-get update -y && sudo apt-get install -y curl
fi

if ! command -v jq >/dev/null 2>&1; then
    log_warning "jq가 설치되지 않았습니다. Python으로 JSON 파싱합니다."
    log_info "jq 설치를 권장합니다: sudo apt-get install -y jq"
else
    log_success "✅ jq 설치됨"
fi

if ! command -v aws >/dev/null 2>&1; then
    log_warning "AWS CLI가 설치되지 않았습니다. VPC 서브넷 기능을 사용하려면 설치하세요."
    log_info "AWS CLI 설치: curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip awscliv2.zip && sudo ./aws/install"
    log_info "또는: sudo apt-get install -y awscli"
else
    log_success "✅ AWS CLI 설치됨"
    # AWS 자격 증명 확인
    if aws sts get-caller-identity >/dev/null 2>&1; then
        log_success "✅ AWS 자격 증명 설정됨"
    else
        log_warning "⚠️  AWS 자격 증명이 설정되지 않았습니다. VPC 서브넷 기능을 사용하려면 설정하세요."
    fi
fi

# 2. 스크립트 설치
log_info "2. 스크립트 설치 중..."
if [ -f "$SCRIPT_DIR/update_real_ip_providers.sh" ]; then
    sudo install -m 0755 "$SCRIPT_DIR/update_real_ip_providers.sh" /usr/local/sbin/update_real_ip_providers
    log_success "✅ 스크립트 설치 완료: /usr/local/sbin/update_real_ip_providers"
else
    log_error "❌ 스크립트 파일을 찾을 수 없습니다: $SCRIPT_DIR/update_real_ip_providers.sh"
    exit 1
fi

# 3. systemd 서비스 설치
log_info "3. systemd 서비스 설치 중..."
if [ -f "$SCRIPT_DIR/update-real-ip-providers.service" ]; then
    sudo cp "$SCRIPT_DIR/update-real-ip-providers.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    log_success "✅ systemd 서비스 설치 완료"
else
    log_error "❌ 서비스 파일을 찾을 수 없습니다: $SCRIPT_DIR/update-real-ip-providers.service"
    exit 1
fi

# 4. systemd 타이머 설치
log_info "4. systemd 타이머 설치 중..."
if [ -f "$SCRIPT_DIR/update-real-ip-providers.timer" ]; then
    sudo cp "$SCRIPT_DIR/update-real-ip-providers.timer" /etc/systemd/system/
    sudo systemctl daemon-reload
    log_success "✅ systemd 타이머 설치 완료"
else
    log_error "❌ 타이머 파일을 찾을 수 없습니다: $SCRIPT_DIR/update-real-ip-providers.timer"
    exit 1
fi

# 5. nginx conf.d 디렉토리 생성
log_info "5. nginx 설정 디렉토리 생성 중..."
sudo mkdir -p /etc/nginx/conf.d
log_success "✅ nginx 설정 디렉토리 생성 완료"

# 6. 초기 실행 (Cloudflare만 활성화)
log_info "6. 초기 CIDR 동기화 실행 중 (Cloudflare만)..."
if sudo /usr/local/sbin/update_real_ip_providers; then
    log_success "✅ 초기 CIDR 동기화 완료"
else
    log_warning "⚠️  초기 동기화 실패 (네트워크 문제일 수 있음)"
fi

# 7. systemd 타이머 활성화
log_info "7. systemd 타이머 활성화 중..."
if sudo systemctl enable --now update-real-ip-providers.timer; then
    log_success "✅ systemd 타이머 활성화 완료"
else
    log_error "❌ systemd 타이머 활성화 실패"
    exit 1
fi

# 8. 타이머 상태 확인
log_info "8. 타이머 상태 확인 중..."
echo "=== 타이머 상태 ==="
sudo systemctl list-timers | grep real-ip-providers || log_warning "타이머가 표시되지 않습니다"

# 9. nginx 설정 검증
log_info "9. nginx 설정 검증 중..."
if sudo nginx -t; then
    log_success "✅ nginx 설정 검증 통과"
else
    log_error "❌ nginx 설정 검증 실패"
    exit 1
fi

# 10. AWS/GCP 활성화 안내
echo ""
log_info "10. AWS/GCP 활성화 안내..."
echo "현재 설정: Cloudflare만 활성화됨"
echo ""
echo "AWS ELB를 활성화하려면:"
echo "  sudo systemctl set-environment AWS_ENABLE=yes"
echo "  sudo /usr/local/sbin/update_real_ip_providers"
echo ""
echo "AWS VPC 서브넷 (ALB/NLB용)을 활성화하려면:"
echo "  sudo systemctl set-environment AWS_VPC_SUBNETS=yes"
echo "  sudo /usr/local/sbin/update_real_ip_providers"
echo "  # 또는 수동으로 리전/VPC 지정:"
echo "  sudo systemctl set-environment AWS_REGION=us-east-1"
echo "  sudo systemctl set-environment AWS_VPC_ID=vpc-12345678"
echo ""
echo "GCP LB를 활성화하려면:"
echo "  sudo systemctl set-environment GCP_ENABLE=yes"
echo "  sudo systemctl set-environment GCP_SCOPE=global  # 또는 asia-east1, us-central1 등"
echo "  sudo /usr/local/sbin/update_real_ip_providers"
echo ""

# 11. 설치 완료 요약
echo ""
log_success "🎉 멀티 클라우드 CIDR 자동 동기화 시스템 설치 완료!"
echo ""
echo "📋 설치된 구성요소:"
echo "   • 스크립트: /usr/local/sbin/update_real_ip_providers"
echo "   • 서비스: /etc/systemd/system/update-real-ip-providers.service"
echo "   • 타이머: /etc/systemd/system/update-real-ip-providers.timer"
echo "   • 설정 파일: /etc/nginx/conf.d/real_ip_providers.conf"
echo ""
echo "🔧 관리 명령어:"
echo "   • 수동 실행: sudo /usr/local/sbin/update_real_ip_providers"
echo "   • 타이머 상태: sudo systemctl list-timers | grep real-ip-providers"
echo "   • 서비스 로그: sudo journalctl -u update-real-ip-providers.service"
echo "   • 설정 확인: sudo nginx -T | grep real_ip_providers"
echo ""
echo "🌐 지원하는 클라우드:"
echo "   • Cloudflare: 자동 활성화 (CF_ENABLE=yes)"
echo "   • AWS ELB: 수동 활성화 (AWS_ENABLE=yes)"
echo "   • GCP LB: 수동 활성화 (GCP_ENABLE=yes, GCP_SCOPE=global)"
echo ""
echo "⚠️  보안 주의사항:"
echo "   • 해당 L7 프록시 뒤에 100% 위치한 서버에서만 사용하세요"
echo "   • 직접 접속이 가능한 환경이면 방화벽으로 원 서버 접근을 차단하세요"
echo "   • real_ip_recursive on과 함께 신뢰 범위를 최소화하세요"
echo "   • ALB/NLB 사용 시에는 VPC 서브넷 CIDR을 직접 지정하는 것을 권장합니다"
