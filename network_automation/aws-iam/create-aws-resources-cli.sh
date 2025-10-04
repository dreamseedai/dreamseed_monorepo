#!/usr/bin/env bash
# AWS CLI로 IAM 리소스 생성 스크립트
# 목적: Terraform 없이 AWS CLI만으로 VPC 서브넷 CIDR 조회용 IAM 리소스 생성

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
POLICY_NAME="${2:-DescribeVpcSubnetsPolicy}"
INSTANCE_PROFILE_NAME="${3:-DreamSeedVpcSubnetReaderProfile}"
REGION="${4:-ap-northeast-2}"
ENVIRONMENT="${5:-prod}"
RESTRICT_TO_REGION="${6:-true}"
MULTI_REGION="${7:-false}"
ALLOWED_REGIONS="${8:-ap-northeast-2,us-east-1,eu-west-1}"

SCRIPT_DIR=$(dirname "$0")

log_info "=== AWS CLI로 IAM 리소스 생성 시작 ==="
log_info "역할 이름: $ROLE_NAME"
log_info "정책 이름: $POLICY_NAME"
log_info "인스턴스 프로파일: $INSTANCE_PROFILE_NAME"
log_info "리전: $REGION"
log_info "환경: $ENVIRONMENT"
log_info "리전 제한: $RESTRICT_TO_REGION"
log_info "멀티 리전: $MULTI_REGION"
log_info "허용 리전: $ALLOWED_REGIONS"

# AWS CLI 설치 확인
if ! command -v aws >/dev/null 2>&1; then
    log_error "AWS CLI가 설치되지 않았습니다."
    log_info "설치 방법: ./network_automation/aws-iam/install-aws-cli.sh"
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

# 1. IAM 정책 생성
log_info "1. IAM 정책 생성 중..."
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}-${ENVIRONMENT}"

# 정책 JSON 생성 (리전 제한 포함)
if [ "$RESTRICT_TO_REGION" = "true" ]; then
    # 단일 리전 제한
    POLICY_JSON=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowVpcSubnetCidrReadInRegion",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "$REGION"
        }
      }
    }
  ]
}
EOF
)
elif [ "$MULTI_REGION" = "true" ]; then
    # 멀티 리전 허용
    IFS=',' read -ra REGIONS <<< "$ALLOWED_REGIONS"
    REGIONS_JSON=$(printf '"%s",' "${REGIONS[@]}")
    REGIONS_JSON="[${REGIONS_JSON%,}]"
    
    POLICY_JSON=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowVpcSubnetCidrReadInMultipleRegions",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": $REGIONS_JSON
        }
      }
    }
  ]
}
EOF
)
else
    # 모든 리전 허용 (기존)
    POLICY_JSON=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowVpcSubnetCidrRead",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ],
      "Resource": "*"
    }
  ]
}
EOF
)
fi

# 정책 생성
if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
    log_warning "IAM 정책 '${POLICY_NAME}-${ENVIRONMENT}'이 이미 존재합니다."
    read -p "기존 정책을 사용하시겠습니까? (y/N): " use_existing
    if [[ ! "$use_existing" =~ ^[Yy]$ ]]; then
        log_info "다른 정책 이름을 사용하세요."
        exit 1
    fi
else
    log_info "IAM 정책 '${POLICY_NAME}-${ENVIRONMENT}' 생성 중..."
    echo "$POLICY_JSON" > /tmp/policy.json
    
    aws iam create-policy \
        --policy-name "${POLICY_NAME}-${ENVIRONMENT}" \
        --policy-document file:///tmp/policy.json \
        --description "Allow only ec2:DescribeSubnets and ec2:DescribeVpcs for Dream Seed VPC subnet CIDR reading"
    
    rm -f /tmp/policy.json
    log_success "✅ IAM 정책 생성 완료"
fi

# 2. IAM 역할 생성
log_info "2. IAM 역할 생성 중..."
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}-${ENVIRONMENT}"

# 신뢰 정책 JSON 생성
TRUST_POLICY_JSON=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
)

if aws iam get-role --role-name "${ROLE_NAME}-${ENVIRONMENT}" >/dev/null 2>&1; then
    log_warning "IAM 역할 '${ROLE_NAME}-${ENVIRONMENT}'이 이미 존재합니다."
    read -p "기존 역할을 사용하시겠습니까? (y/N): " use_existing
    if [[ ! "$use_existing" =~ ^[Yy]$ ]]; then
        log_info "다른 역할 이름을 사용하세요."
        exit 1
    fi
else
    log_info "IAM 역할 '${ROLE_NAME}-${ENVIRONMENT}' 생성 중..."
    echo "$TRUST_POLICY_JSON" > /tmp/trust-policy.json
    
    aws iam create-role \
        --role-name "${ROLE_NAME}-${ENVIRONMENT}" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "Dream Seed VPC Subnet CIDR Reader Role for ALB/NLB environments"
    
    rm -f /tmp/trust-policy.json
    log_success "✅ IAM 역할 생성 완료"
fi

# 3. 정책 연결
log_info "3. 정책 연결 중..."
aws iam attach-role-policy \
    --role-name "${ROLE_NAME}-${ENVIRONMENT}" \
    --policy-arn "$POLICY_ARN"

log_success "✅ 정책 연결 완료"

# 4. 인스턴스 프로파일 생성
log_info "4. 인스턴스 프로파일 생성 중..."
INSTANCE_PROFILE_ARN="arn:aws:iam::${ACCOUNT_ID}:instance-profile/${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}"

if aws iam get-instance-profile --instance-profile-name "${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}" >/dev/null 2>&1; then
    log_warning "인스턴스 프로파일 '${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}'이 이미 존재합니다."
    read -p "기존 인스턴스 프로파일을 사용하시겠습니까? (y/N): " use_existing
    if [[ ! "$use_existing" =~ ^[Yy]$ ]]; then
        log_info "다른 인스턴스 프로파일 이름을 사용하세요."
        exit 1
    fi
else
    log_info "인스턴스 프로파일 '${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}' 생성 중..."
    aws iam create-instance-profile --instance-profile-name "${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}"
    log_success "✅ 인스턴스 프로파일 생성 완료"
fi

# 5. 역할을 인스턴스 프로파일에 추가
log_info "5. 역할을 인스턴스 프로파일에 연결 중..."
aws iam add-role-to-instance-profile \
    --instance-profile-name "${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}" \
    --role-name "${ROLE_NAME}-${ENVIRONMENT}"

log_success "✅ 역할을 인스턴스 프로파일에 연결 완료"

# 6. 권한 테스트
log_info "6. 권한 테스트 중..."
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

# 7. 생성된 리소스 정보 출력
log_info "7. 생성된 리소스 정보..."
echo ""
log_success "🎉 AWS IAM 리소스 생성 완료!"
echo ""
echo "📋 생성된 리소스:"
echo "   • IAM 역할: ${ROLE_NAME}-${ENVIRONMENT}"
echo "   • IAM 역할 ARN: $ROLE_ARN"
echo "   • 인스턴스 프로파일: ${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}"
echo "   • 인스턴스 프로파일 ARN: $INSTANCE_PROFILE_ARN"
echo "   • 정책: ${POLICY_NAME}-${ENVIRONMENT}"
echo "   • 정책 ARN: $POLICY_ARN"
echo "   • 권한: ec2:DescribeSubnets, ec2:DescribeVpcs"
echo "   • 리전: $REGION"
echo ""
echo "🔧 EC2 인스턴스에 적용하는 방법:"
echo ""
echo "1. AWS 콘솔에서:"
echo "   • EC2 → 인스턴스 → 작업 → 보안 → IAM 역할 수정"
echo "   • 역할 선택: ${ROLE_NAME}-${ENVIRONMENT}"
echo ""
echo "2. AWS CLI로:"
echo "   aws ec2 associate-iam-instance-profile \\"
echo "     --instance-id <INSTANCE_ID> \\"
echo "     --iam-instance-profile Name=${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}"
echo ""
echo "3. 새 인스턴스 시작 시:"
echo "   aws ec2 run-instances \\"
echo "     --image-id ami-12345678 \\"
echo "     --instance-type t3.micro \\"
echo "     --iam-instance-profile Name=${INSTANCE_PROFILE_NAME}-${ENVIRONMENT}"
echo ""
echo "4. Dream Seed VPC 서브넷 CIDR 동기화:"
echo "   sudo systemctl set-environment AWS_VPC_SUBNETS=yes"
echo "   sudo systemctl set-environment AWS_REGION=$REGION"
echo "   sudo /usr/local/sbin/update_real_ip_providers"
echo ""
echo "⚠️  보안 주의사항:"
echo "   • 이 역할은 읽기 전용 권한만 가집니다"
echo "   • VPC/서브넷 수정/삭제는 불가능합니다"
echo "   • ALB/NLB 뒤에서만 사용하세요"
echo "   • 직접 접속이 가능한 환경에서는 방화벽으로 원 서버 접근을 차단하세요"
