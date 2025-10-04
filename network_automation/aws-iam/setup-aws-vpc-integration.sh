#!/usr/bin/env bash
# AWS VPC 통합 설정 종합 스크립트
# 목적: VPC 서브넷 CIDR 자동 주입을 위한 모든 AWS 설정을 자동화

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

# 설정
ROLE_NAME="${1:-DreamSeedVpcSubnetReader}"
REGION="${2:-ap-northeast-2}"
SCOPE="${3:-region}"  # region 또는 global

SCRIPT_DIR=$(dirname "$0")

log_info "=== AWS VPC 통합 설정 시작 ==="
log_info "역할 이름: $ROLE_NAME"
log_info "리전: $REGION"
log_info "범위: $SCOPE"

# 1. AWS CLI 설치
log_info "1. AWS CLI 설치 확인 중..."
if ! command -v aws >/dev/null 2>&1; then
    log_info "AWS CLI 설치 중..."
    "$SCRIPT_DIR/install-aws-cli.sh"
else
    log_success "✅ AWS CLI가 이미 설치되어 있습니다"
    aws --version
fi

# 2. AWS 자격 증명 확인
log_info "2. AWS 자격 증명 확인 중..."
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    log_error "AWS 자격 증명이 설정되지 않았습니다."
    echo ""
    echo "다음 중 하나의 방법으로 자격 증명을 설정하세요:"
    echo "1. aws configure"
    echo "2. 환경 변수 설정"
    echo "3. IAM 역할 연결 (EC2 인스턴스에서 권장)"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_success "✅ AWS 자격 증명 확인됨 (계정: $ACCOUNT_ID)"

# 3. IAM 역할 생성
log_info "3. IAM 역할 생성 중..."
if "$SCRIPT_DIR/create-iam-role.sh" "$ROLE_NAME" "$REGION" "$SCOPE"; then
    log_success "✅ IAM 역할 생성 완료"
else
    log_error "❌ IAM 역할 생성 실패"
    exit 1
fi

# 4. 권한 검증
log_info "4. 권한 검증 중..."
if "$SCRIPT_DIR/verify-iam-permissions.sh" "$REGION"; then
    log_success "✅ 권한 검증 완료"
else
    log_warning "⚠️  권한 검증에서 일부 문제가 발견되었습니다"
fi

# 5. 멀티 클라우드 CIDR 동기화 설치
log_info "5. 멀티 클라우드 CIDR 동기화 설치 중..."
if [ -f "../scripts/install_multi_cloud_sync.sh" ]; then
    if sudo "../scripts/install_multi_cloud_sync.sh"; then
        log_success "✅ 멀티 클라우드 CIDR 동기화 설치 완료"
    else
        log_warning "⚠️  멀티 클라우드 CIDR 동기화 설치 실패"
    fi
else
    log_warning "⚠️  멀티 클라우드 CIDR 동기화 스크립트를 찾을 수 없습니다"
fi

# 6. AWS VPC 서브넷 기능 활성화
log_info "6. AWS VPC 서브넷 기능 활성화 중..."
sudo systemctl set-environment AWS_VPC_SUBNETS=yes
sudo systemctl set-environment AWS_REGION="$REGION"

# 현재 VPC ID 자동 감지
if curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-id >/dev/null 2>&1; then
    CURRENT_VPC=$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/ | head -n1 | xargs -I{} curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/{}/vpc-id 2>/dev/null || echo "")
    if [ -n "$CURRENT_VPC" ]; then
        sudo systemctl set-environment AWS_VPC_ID="$CURRENT_VPC"
        log_success "✅ VPC ID 자동 감지됨: $CURRENT_VPC"
    else
        log_warning "⚠️  VPC ID 자동 감지 실패"
    fi
else
    log_warning "⚠️  EC2 메타데이터 접근 불가 (로컬 환경 또는 권한 부족)"
fi

# 7. VPC 서브넷 CIDR 동기화 테스트
log_info "7. VPC 서브넷 CIDR 동기화 테스트 중..."
if command -v /usr/local/sbin/update_real_ip_providers >/dev/null 2>&1; then
    if sudo /usr/local/sbin/update_real_ip_providers; then
        log_success "✅ VPC 서브넷 CIDR 동기화 테스트 성공"
        
        # 생성된 설정 파일 확인
        if [ -f "/etc/nginx/conf.d/real_ip_providers.conf" ]; then
            VPC_LINES=$(grep -c "AWS VPC Subnets" /etc/nginx/conf.d/real_ip_providers.conf || echo "0")
            if [ "$VPC_LINES" -gt 0 ]; then
                log_success "✅ VPC 서브넷 CIDR이 nginx 설정에 포함됨"
                echo ""
                echo "=== 생성된 VPC 서브넷 CIDR ==="
                grep -A 10 "AWS VPC Subnets" /etc/nginx/conf.d/real_ip_providers.conf || true
            else
                log_warning "⚠️  VPC 서브넷 CIDR이 nginx 설정에 포함되지 않음"
            fi
        fi
    else
        log_warning "⚠️  VPC 서브넷 CIDR 동기화 테스트 실패"
    fi
else
    log_warning "⚠️  update_real_ip_providers 스크립트가 설치되지 않음"
fi

# 8. systemd 서비스 상태 확인
log_info "8. systemd 서비스 상태 확인 중..."
if systemctl is-active --quiet update-real-ip-providers.timer; then
    log_success "✅ 멀티 클라우드 CIDR 동기화 타이머 활성화됨"
    systemctl status update-real-ip-providers.timer --no-pager -l
else
    log_warning "⚠️  멀티 클라우드 CIDR 동기화 타이머가 비활성화됨"
    log_info "활성화하려면: sudo systemctl enable --now update-real-ip-providers.timer"
fi

# 9. 최종 설정 요약
log_info "9. 최종 설정 요약..."
echo ""
log_success "🎉 AWS VPC 통합 설정 완료!"
echo ""
echo "📋 설정된 구성요소:"
echo "   • AWS CLI: $(aws --version 2>/dev/null || echo '설치되지 않음')"
echo "   • IAM 역할: $ROLE_NAME"
echo "   • 인스턴스 프로파일: ${ROLE_NAME}InstanceProfile"
echo "   • VPC 서브넷 기능: ${AWS_VPC_SUBNETS:-not set}"
echo "   • AWS 리전: ${AWS_REGION:-not set}"
echo "   • AWS VPC ID: ${AWS_VPC_ID:-not set}"
echo "   • 멀티 클라우드 동기화: $(systemctl is-active update-real-ip-providers.timer 2>/dev/null || echo '비활성화')"
echo ""
echo "🔧 관리 명령어:"
echo "   • VPC 서브넷 동기화: sudo /usr/local/sbin/update_real_ip_providers"
echo "   • 권한 검증: ./network_automation/aws-iam/verify-iam-permissions.sh $REGION"
echo "   • 서비스 로그: sudo journalctl -u update-real-ip-providers.service"
echo "   • 타이머 상태: systemctl status update-real-ip-providers.timer"
echo ""
echo "⚠️  보안 주의사항:"
echo "   • VPC 서브넷 CIDR은 ALB/NLB 뒤에 100% 위치한 서버에서만 사용하세요"
echo "   • 직접 접속이 가능한 환경이면 방화벽으로 원 서버 접근을 차단하세요"
echo "   • real_ip_recursive on과 함께 신뢰 범위를 최소화하세요"
echo "   • 정기적으로 권한 사용 현황을 검토하세요"
echo ""
echo "📚 추가 정보:"
echo "   • IAM 정책 템플릿: ./network_automation/aws-iam/iam-policy-templates.md"
echo "   • 브라우저 호환성: ./README_BROWSER_COMPAT.md"
echo "   • 멀티 클라우드 동기화: ./network_automation/scripts/verify_multi_cloud_sync.sh"
