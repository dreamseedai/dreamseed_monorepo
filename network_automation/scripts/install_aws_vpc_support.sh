#!/bin/bash
# AWS VPC 서브넷 CIDR 자동 주입 지원 설치 스크립트
# 목적: AWS CLI 설치 및 VPC 서브넷 기능 활성화

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

log_info "=== AWS VPC 서브넷 CIDR 자동 주입 지원 설치 시작 ==="

# 1. AWS CLI 설치 확인 및 설치
log_info "1. AWS CLI 설치 확인 중..."
if command -v aws >/dev/null 2>&1; then
    log_success "✅ AWS CLI가 이미 설치되어 있습니다"
    aws --version
else
    log_info "AWS CLI 설치 중..."
    
    # 패키지 매니저로 먼저 시도
    if command -v apt-get >/dev/null 2>&1; then
        log_info "apt-get으로 AWS CLI 설치 시도 중..."
        sudo apt-get update -y
        if sudo apt-get install -y awscli; then
            log_success "✅ apt-get으로 AWS CLI 설치 완료"
        else
            log_warning "apt-get 설치 실패, 공식 설치 방법 사용"
            install_aws_cli_official
        fi
    else
        log_info "공식 설치 방법 사용"
        install_aws_cli_official
    fi
fi

# AWS CLI 공식 설치 함수
install_aws_cli_official() {
    log_info "AWS CLI 공식 설치 중..."
    
    # 의존성 설치
    sudo apt-get update -y
    sudo apt-get install -y curl unzip
    
    # AWS CLI v2 다운로드 및 설치
    cd /tmp
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws/
    
    log_success "✅ AWS CLI 공식 설치 완료"
}

# 2. AWS 자격 증명 설정 확인
log_info "2. AWS 자격 증명 설정 확인 중..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    log_success "✅ AWS 자격 증명이 설정되어 있습니다"
    echo "=== AWS 계정 정보 ==="
    aws sts get-caller-identity
else
    log_warning "⚠️  AWS 자격 증명이 설정되지 않았습니다"
    echo ""
    echo "AWS 자격 증명을 설정하는 방법:"
    echo "1. IAM 사용자 자격 증명 사용:"
    echo "   aws configure"
    echo "   # Access Key ID, Secret Access Key, Region, Output format 입력"
    echo ""
    echo "2. IAM 역할 사용 (EC2 인스턴스에서 권장):"
    echo "   # EC2 인스턴스에 IAM 역할을 연결하고 다음 권한을 부여:"
    echo "   # - ec2:DescribeSubnets"
    echo "   # - ec2:DescribeRouteTables"
    echo ""
    echo "3. 환경 변수 사용:"
    echo "   export AWS_ACCESS_KEY_ID=your_access_key"
    echo "   export AWS_SECRET_ACCESS_KEY=your_secret_key"
    echo "   export AWS_DEFAULT_REGION=your_region"
    echo ""
    read -p "지금 AWS 자격 증명을 설정하시겠습니까? (y/N): " setup_credentials
    if [[ "$setup_credentials" =~ ^[Yy]$ ]]; then
        aws configure
    fi
fi

# 3. VPC 메타데이터 접근 확인
log_info "3. VPC 메타데이터 접근 확인 중..."
if curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-id >/dev/null 2>&1; then
    log_success "✅ AWS EC2 메타데이터 접근 가능"
    
    # 현재 인스턴스 정보 확인
    echo "=== 현재 EC2 인스턴스 정보 ==="
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
    VPC_ID=$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/ | head -n1 | xargs -I{} curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/{}/vpc-id)
    
    echo "Instance ID: $INSTANCE_ID"
    echo "Region: $REGION"
    echo "VPC ID: $VPC_ID"
    
    # VPC 서브넷 정보 확인
    if aws sts get-caller-identity >/dev/null 2>&1; then
        log_info "VPC 서브넷 정보 확인 중..."
        if aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].CidrBlock' --output text >/dev/null 2>&1; then
            log_success "✅ VPC 서브넷 정보 접근 가능"
            echo "=== VPC 서브넷 CIDR ==="
            aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].CidrBlock' --output text | tr '\t' '\n'
        else
            log_warning "⚠️  VPC 서브넷 정보 접근 실패 (권한 부족)"
        fi
    fi
else
    log_warning "⚠️  AWS EC2 메타데이터 접근 불가 (VPC 자동 감지 불가)"
    echo "이 스크립트는 AWS EC2 인스턴스에서 실행되어야 합니다."
fi

# 4. VPC 서브넷 기능 활성화
log_info "4. VPC 서브넷 기능 활성화 중..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    sudo systemctl set-environment AWS_VPC_SUBNETS=yes
    log_success "✅ AWS VPC 서브넷 기능 활성화됨"
    
    # 수동으로 리전/VPC 설정 (선택사항)
    if [ -n "${REGION:-}" ] && [ -n "${VPC_ID:-}" ]; then
        sudo systemctl set-environment AWS_REGION="$REGION"
        sudo systemctl set-environment AWS_VPC_ID="$VPC_ID"
        log_success "✅ AWS 리전 및 VPC ID 자동 설정됨"
        echo "Region: $REGION"
        echo "VPC ID: $VPC_ID"
    fi
else
    log_warning "⚠️  AWS 자격 증명이 설정되지 않아 VPC 서브넷 기능을 활성화할 수 없습니다"
fi

# 5. 테스트 실행
log_info "5. VPC 서브넷 CIDR 동기화 테스트 중..."
if sudo /usr/local/sbin/update_real_ip_providers; then
    log_success "✅ VPC 서브넷 CIDR 동기화 테스트 성공"
else
    log_warning "⚠️  VPC 서브넷 CIDR 동기화 테스트 실패"
fi

# 6. 설치 완료 요약
echo ""
log_success "🎉 AWS VPC 서브넷 CIDR 자동 주입 지원 설치 완료!"
echo ""
echo "📋 설정된 구성요소:"
echo "   • AWS CLI: $(aws --version 2>/dev/null || echo '설치되지 않음')"
echo "   • VPC 서브넷 기능: ${AWS_VPC_SUBNETS:-not set}"
echo "   • AWS 리전: ${AWS_REGION:-자동 감지}"
echo "   • AWS VPC ID: ${AWS_VPC_ID:-자동 감지}"
echo ""
echo "🔧 관리 명령어:"
echo "   • VPC 서브넷 동기화: sudo /usr/local/sbin/update_real_ip_providers"
echo "   • 설정 확인: ./network_automation/scripts/verify_multi_cloud_sync.sh"
echo "   • 서비스 로그: sudo journalctl -u update-real-ip-providers.service"
echo ""
echo "⚠️  보안 주의사항:"
echo "   • VPC 서브넷 CIDR은 ALB/NLB 뒤에 100% 위치한 서버에서만 사용하세요"
echo "   • 직접 접속이 가능한 환경이면 방화벽으로 원 서버 접근을 차단하세요"
echo "   • real_ip_recursive on과 함께 신뢰 범위를 최소화하세요"
