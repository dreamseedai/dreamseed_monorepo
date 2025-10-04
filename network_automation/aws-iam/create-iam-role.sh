#!/usr/bin/env bash
# AWS IAM 역할 생성 스크립트 (VPC 서브넷 CIDR 조회용)
# 목적: ALB/NLB 뒤에서 VPC 서브넷 CIDR을 안전하게 조회할 수 있는 최소 권한 IAM 역할 생성

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
POLICY_NAME="${ROLE_NAME}Policy"
REGION="${2:-ap-northeast-2}"
SCOPE="${3:-region}"  # region 또는 global

SCRIPT_DIR=$(dirname "$0")

log_info "=== AWS IAM 역할 생성 시작 ==="
log_info "역할 이름: $ROLE_NAME"
log_info "정책 이름: $POLICY_NAME"
log_info "리전: $REGION"
log_info "범위: $SCOPE"

# AWS CLI 설치 확인
if ! command -v aws >/dev/null 2>&1; then
    log_error "AWS CLI가 설치되지 않았습니다."
    log_info "설치 방법: curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip awscliv2.zip && sudo ./aws/install"
    exit 1
fi

# AWS 자격 증명 확인
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    log_error "AWS 자격 증명이 설정되지 않았습니다."
    log_info "설정 방법: aws configure"
    exit 1
fi

# 현재 AWS 계정 정보 확인
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_info "AWS 계정 ID: $ACCOUNT_ID"

# 1. IAM 역할 생성
log_info "1. IAM 역할 생성 중..."
if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    log_warning "IAM 역할 '$ROLE_NAME'이 이미 존재합니다."
    read -p "기존 역할을 사용하시겠습니까? (y/N): " use_existing
    if [[ ! "$use_existing" =~ ^[Yy]$ ]]; then
        log_info "다른 역할 이름을 사용하세요."
        exit 1
    fi
else
    log_info "IAM 역할 '$ROLE_NAME' 생성 중..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://"$SCRIPT_DIR/trust-policy-ec2.json" \
        --description "Dream Seed VPC Subnet CIDR Reader Role for ALB/NLB"
    
    log_success "✅ IAM 역할 생성 완료"
fi

# 2. 정책 파일 선택
if [ "$SCOPE" = "region" ]; then
    POLICY_FILE="$SCRIPT_DIR/vpc-subnet-readonly-policy.json"
    log_info "리전 제한 정책 사용: $POLICY_FILE"
else
    POLICY_FILE="$SCRIPT_DIR/vpc-subnet-readonly-policy-global.json"
    log_info "글로벌 정책 사용: $POLICY_FILE"
fi

# 3. 인라인 정책 생성
log_info "2. 인라인 정책 생성 중..."
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}/${POLICY_NAME}"

# 기존 정책 삭제 (있다면)
if aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" >/dev/null 2>&1; then
    log_info "기존 정책 삭제 중..."
    aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME"
fi

# 새 정책 생성
aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "$POLICY_NAME" \
    --policy-document file://"$POLICY_FILE"

log_success "✅ 인라인 정책 생성 완료"

# 4. 정책 내용 확인
log_info "3. 생성된 정책 내용 확인..."
aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" --query PolicyDocument

# 5. EC2 인스턴스 프로파일 생성
INSTANCE_PROFILE_NAME="${ROLE_NAME}InstanceProfile"
log_info "4. EC2 인스턴스 프로파일 생성 중..."

if aws iam get-instance-profile --instance-profile-name "$INSTANCE_PROFILE_NAME" >/dev/null 2>&1; then
    log_warning "인스턴스 프로파일 '$INSTANCE_PROFILE_NAME'이 이미 존재합니다."
else
    aws iam create-instance-profile --instance-profile-name "$INSTANCE_PROFILE_NAME"
    log_success "✅ 인스턴스 프로파일 생성 완료"
fi

# 역할을 인스턴스 프로파일에 추가
aws iam add-role-to-instance-profile \
    --instance-profile-name "$INSTANCE_PROFILE_NAME" \
    --role-name "$ROLE_NAME"

log_success "✅ 역할을 인스턴스 프로파일에 연결 완료"

# 6. 권한 테스트
log_info "5. 권한 테스트 중..."
if aws ec2 describe-vpcs --region "$REGION" --max-items 1 >/dev/null 2>&1; then
    log_success "✅ VPC 조회 권한 확인됨"
else
    log_warning "⚠️  VPC 조회 권한 테스트 실패"
fi

if aws ec2 describe-subnets --region "$REGION" --max-items 1 >/dev/null 2>&1; then
    log_success "✅ 서브넷 조회 권한 확인됨"
else
    log_warning "⚠️  서브넷 조회 권한 테스트 실패"
fi

# 7. EC2 인스턴스에 적용 방법 안내
log_info "6. EC2 인스턴스 적용 방법..."
echo ""
log_success "🎉 IAM 역할 생성 완료!"
echo ""
echo "📋 생성된 리소스:"
echo "   • IAM 역할: $ROLE_NAME"
echo "   • 인스턴스 프로파일: $INSTANCE_PROFILE_NAME"
echo "   • 정책: $POLICY_NAME"
echo "   • 권한: ec2:DescribeSubnets, ec2:DescribeVpcs"
echo "   • 리전 제한: $([ "$SCOPE" = "region" ] && echo "$REGION" || echo "전역")"
echo ""
echo "🔧 EC2 인스턴스에 적용하는 방법:"
echo ""
echo "1. AWS 콘솔에서:"
echo "   • EC2 → 인스턴스 → 작업 → 보안 → IAM 역할 수정"
echo "   • 역할 선택: $ROLE_NAME"
echo ""
echo "2. AWS CLI로:"
echo "   aws ec2 associate-iam-instance-profile \\"
echo "     --instance-id i-1234567890abcdef0 \\"
echo "     --iam-instance-profile Name=$INSTANCE_PROFILE_NAME"
echo ""
echo "3. 새 인스턴스 시작 시:"
echo "   aws ec2 run-instances \\"
echo "     --image-id ami-12345678 \\"
echo "     --instance-type t3.micro \\"
echo "     --iam-instance-profile Name=$INSTANCE_PROFILE_NAME"
echo ""
echo "4. VPC 서브넷 CIDR 동기화 테스트:"
echo "   sudo systemctl set-environment AWS_VPC_SUBNETS=yes"
echo "   sudo /usr/local/sbin/update_real_ip_providers"
echo ""
echo "⚠️  보안 주의사항:"
echo "   • 이 역할은 읽기 전용 권한만 가집니다"
echo "   • VPC/서브넷 수정/삭제는 불가능합니다"
echo "   • ALB/NLB 뒤에서만 사용하세요"
echo "   • 직접 접속이 가능한 환경에서는 방화벽으로 원 서버 접근을 차단하세요"
