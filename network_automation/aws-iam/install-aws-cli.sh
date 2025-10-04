#!/usr/bin/env bash
# AWS CLI 설치 스크립트
# 목적: VPC 서브넷 CIDR 자동 주입을 위한 AWS CLI 설치

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

log_info "=== AWS CLI 설치 시작 ==="

# AWS CLI 설치 확인
if command -v aws >/dev/null 2>&1; then
    log_success "✅ AWS CLI가 이미 설치되어 있습니다"
    aws --version
    exit 0
fi

# 1. 패키지 매니저로 설치 시도
log_info "1. 패키지 매니저로 AWS CLI 설치 시도 중..."

if command -v apt-get >/dev/null 2>&1; then
    log_info "apt-get으로 AWS CLI 설치 중..."
    sudo apt-get update -y
    if sudo apt-get install -y awscli; then
        log_success "✅ apt-get으로 AWS CLI 설치 완료"
        aws --version
        exit 0
    else
        log_warning "apt-get 설치 실패, 공식 설치 방법 사용"
    fi
elif command -v yum >/dev/null 2>&1; then
    log_info "yum으로 AWS CLI 설치 중..."
    sudo yum update -y
    if sudo yum install -y awscli; then
        log_success "✅ yum으로 AWS CLI 설치 완료"
        aws --version
        exit 0
    else
        log_warning "yum 설치 실패, 공식 설치 방법 사용"
    fi
elif command -v dnf >/dev/null 2>&1; then
    log_info "dnf으로 AWS CLI 설치 중..."
    sudo dnf update -y
    if sudo dnf install -y awscli; then
        log_success "✅ dnf으로 AWS CLI 설치 완료"
        aws --version
        exit 0
    else
        log_warning "dnf 설치 실패, 공식 설치 방법 사용"
    fi
else
    log_info "패키지 매니저를 찾을 수 없습니다. 공식 설치 방법 사용"
fi

# 2. 공식 설치 방법
log_info "2. AWS CLI v2 공식 설치 중..."

# 의존성 설치
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y curl unzip
elif command -v yum >/dev/null 2>&1; then
    sudo yum update -y
    sudo yum install -y curl unzip
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf update -y
    sudo dnf install -y curl unzip
fi

# AWS CLI v2 다운로드 및 설치
cd /tmp
log_info "AWS CLI v2 다운로드 중..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

log_info "AWS CLI v2 압축 해제 중..."
unzip awscliv2.zip

log_info "AWS CLI v2 설치 중..."
sudo ./aws/install

# 정리
rm -rf awscliv2.zip aws/

log_success "✅ AWS CLI v2 공식 설치 완료"

# 설치 확인
if command -v aws >/dev/null 2>&1; then
    log_success "✅ AWS CLI 설치 확인됨"
    aws --version
else
    log_error "❌ AWS CLI 설치 실패"
    exit 1
fi

# 3. 자격 증명 설정 안내
log_info "3. AWS 자격 증명 설정 안내..."
echo ""
log_warning "⚠️  AWS 자격 증명을 설정해야 합니다."
echo ""
echo "설정 방법:"
echo "1. IAM 사용자 자격 증명:"
echo "   aws configure"
echo "   # Access Key ID, Secret Access Key, Region, Output format 입력"
echo ""
echo "2. IAM 역할 사용 (EC2 인스턴스에서 권장):"
echo "   # EC2 인스턴스에 IAM 역할을 연결하고 다음 권한을 부여:"
echo "   # - ec2:DescribeSubnets"
echo "   # - ec2:DescribeVpcs"
echo ""
echo "3. 환경 변수 사용:"
echo "   export AWS_ACCESS_KEY_ID=your_access_key"
echo "   export AWS_SECRET_ACCESS_KEY=your_secret_key"
echo "   export AWS_DEFAULT_REGION=your_region"
echo ""
echo "4. 자격 증명 파일 사용:"
echo "   ~/.aws/credentials 파일에 자격 증명 추가"
echo ""

# 4. 테스트 실행
log_info "4. AWS CLI 테스트 중..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    log_success "✅ AWS 자격 증명이 설정되어 있습니다"
    aws sts get-caller-identity
else
    log_warning "⚠️  AWS 자격 증명이 설정되지 않았습니다"
    echo ""
    echo "다음 명령어로 자격 증명을 설정하세요:"
    echo "aws configure"
fi

log_success "🎉 AWS CLI 설치 완료!"
