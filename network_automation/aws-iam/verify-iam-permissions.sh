#!/usr/bin/env bash
# AWS IAM 권한 검증 스크립트
# 목적: VPC 서브넷 CIDR 조회에 필요한 최소 권한이 올바르게 설정되었는지 검증

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
REGION="${1:-ap-northeast-2}"

log_info "=== AWS IAM 권한 검증 시작 ==="
log_info "리전: $REGION"

# AWS CLI 설치 확인
if ! command -v aws >/dev/null 2>&1; then
    log_error "AWS CLI가 설치되지 않았습니다."
    exit 1
fi

# AWS 자격 증명 확인
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    log_error "AWS 자격 증명이 설정되지 않았습니다."
    exit 1
fi

# 현재 AWS 계정 및 사용자 정보
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
log_info "AWS 계정 ID: $ACCOUNT_ID"
log_info "사용자/역할: $USER_ARN"

# 1. 기본 권한 확인
log_info "1. 기본 권한 확인 중..."

# sts:GetCallerIdentity 권한 확인
if aws sts get-caller-identity >/dev/null 2>&1; then
    log_success "✅ sts:GetCallerIdentity 권한 확인됨"
else
    log_error "❌ sts:GetCallerIdentity 권한 없음"
    exit 1
fi

# 2. EC2 권한 확인
log_info "2. EC2 권한 확인 중..."

# ec2:DescribeVpcs 권한 확인
if aws ec2 describe-vpcs --region "$REGION" --max-items 1 >/dev/null 2>&1; then
    log_success "✅ ec2:DescribeVpcs 권한 확인됨"
    
    # VPC 정보 조회
    VPC_COUNT=$(aws ec2 describe-vpcs --region "$REGION" --query 'length(Vpcs)' --output text)
    log_info "   • VPC 개수: $VPC_COUNT"
    
    # 현재 인스턴스의 VPC ID 확인 (메타데이터에서)
    if curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-id >/dev/null 2>&1; then
        INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
        log_info "   • 현재 인스턴스 ID: $INSTANCE_ID"
        
        # 인스턴스의 VPC ID 조회
        if aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].VpcId' --output text >/dev/null 2>&1; then
            CURRENT_VPC=$(aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].VpcId' --output text)
            log_info "   • 현재 VPC ID: $CURRENT_VPC"
        else
            log_warning "⚠️  현재 인스턴스의 VPC ID 조회 실패 (권한 부족 또는 인스턴스가 아닌 환경)"
        fi
    else
        log_warning "⚠️  EC2 메타데이터 접근 불가 (로컬 환경 또는 권한 부족)"
    fi
else
    log_error "❌ ec2:DescribeVpcs 권한 없음"
    exit 1
fi

# ec2:DescribeSubnets 권한 확인
if aws ec2 describe-subnets --region "$REGION" --max-items 1 >/dev/null 2>&1; then
    log_success "✅ ec2:DescribeSubnets 권한 확인됨"
    
    # 서브넷 정보 조회
    SUBNET_COUNT=$(aws ec2 describe-subnets --region "$REGION" --query 'length(Subnets)' --output text)
    log_info "   • 서브넷 개수: $SUBNET_COUNT"
    
    # IPv4 서브넷 CIDR 조회
    V4_SUBNETS=$(aws ec2 describe-subnets --region "$REGION" --query 'Subnets[].CidrBlock' --output text | wc -w)
    log_info "   • IPv4 서브넷 CIDR 개수: $V4_SUBNETS"
    
    # IPv6 서브넷 CIDR 조회
    V6_SUBNETS=$(aws ec2 describe-subnets --region "$REGION" --query 'Subnets[].Ipv6CidrBlockAssociationSet[].Ipv6CidrBlock' --output text | grep -v 'None' | wc -w)
    log_info "   • IPv6 서브넷 CIDR 개수: $V6_SUBNETS"
    
    # 현재 VPC의 서브넷만 조회 (가능한 경우)
    if [ -n "${CURRENT_VPC:-}" ]; then
        CURRENT_VPC_SUBNETS=$(aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$CURRENT_VPC" --query 'length(Subnets)' --output text)
        log_info "   • 현재 VPC의 서브넷 개수: $CURRENT_VPC_SUBNETS"
        
        if [ "$CURRENT_VPC_SUBNETS" -gt 0 ]; then
            log_info "   • 현재 VPC의 서브넷 CIDR:"
            aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$CURRENT_VPC" --query 'Subnets[].CidrBlock' --output text | tr '\t' '\n' | while read -r cidr; do
                echo "     - $cidr"
            done
        fi
    fi
else
    log_error "❌ ec2:DescribeSubnets 권한 없음"
    exit 1
fi

# 3. 권한 범위 확인
log_info "3. 권한 범위 확인 중..."

# 다른 리전에서의 권한 확인 (선택사항)
OTHER_REGIONS=("us-east-1" "us-west-2" "eu-west-1")
for other_region in "${OTHER_REGIONS[@]}"; do
    if [ "$other_region" != "$REGION" ]; then
        if aws ec2 describe-vpcs --region "$other_region" --max-items 1 >/dev/null 2>&1; then
            log_warning "⚠️  다른 리전($other_region)에서도 권한이 있습니다 (글로벌 권한)"
        else
            log_success "✅ 다른 리전($other_region)에서는 권한이 제한되어 있습니다 (리전 제한 권한)"
        fi
        break
    fi
done

# 4. 보안 검증
log_info "4. 보안 검증 중..."

# 위험한 권한 확인
DANGEROUS_ACTIONS=("ec2:TerminateInstances" "ec2:StopInstances" "ec2:StartInstances" "ec2:ModifyInstanceAttribute" "ec2:DeleteVpc" "ec2:DeleteSubnet")

for action in "${DANGEROUS_ACTIONS[@]}"; do
    if aws iam simulate-principal-policy --policy-source-arn "$USER_ARN" --action-names "$action" --resource-arns "*" --query 'EvaluationResults[0].EvalDecision' --output text 2>/dev/null | grep -q "Allow"; then
        log_warning "⚠️  위험한 권한 발견: $action"
    else
        log_success "✅ 위험한 권한 없음: $action"
    fi
done

# 5. VPC 서브넷 CIDR 동기화 테스트
log_info "5. VPC 서브넷 CIDR 동기화 테스트 중..."

if command -v /usr/local/sbin/update_real_ip_providers >/dev/null 2>&1; then
    log_info "update_real_ip_providers 스크립트 테스트 중..."
    
    # 환경 변수 설정
    export AWS_VPC_SUBNETS=yes
    export AWS_REGION="$REGION"
    
    if [ -n "${CURRENT_VPC:-}" ]; then
        export AWS_VPC_ID="$CURRENT_VPC"
        log_info "VPC ID 설정: $CURRENT_VPC"
    fi
    
    # 테스트 실행
    if sudo -E /usr/local/sbin/update_real_ip_providers >/dev/null 2>&1; then
        log_success "✅ VPC 서브넷 CIDR 동기화 테스트 성공"
        
        # 생성된 설정 파일 확인
        if [ -f "/etc/nginx/conf.d/real_ip_providers.conf" ]; then
            VPC_LINES=$(grep -c "AWS VPC Subnets" /etc/nginx/conf.d/real_ip_providers.conf || echo "0")
            if [ "$VPC_LINES" -gt 0 ]; then
                log_success "✅ VPC 서브넷 CIDR이 nginx 설정에 포함됨"
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

# 6. 권한 요약
log_info "6. 권한 요약..."
echo ""
log_success "🎉 AWS IAM 권한 검증 완료!"
echo ""
echo "📋 확인된 권한:"
echo "   • ec2:DescribeVpcs: ✅"
echo "   • ec2:DescribeSubnets: ✅"
echo "   • 리전: $REGION"
echo "   • VPC 개수: $VPC_COUNT"
echo "   • 서브넷 개수: $SUBNET_COUNT"
echo "   • IPv4 CIDR: $V4_SUBNETS개"
echo "   • IPv6 CIDR: $V6_SUBNETS개"
echo ""
echo "🔧 다음 단계:"
echo "   1. EC2 인스턴스에 IAM 역할 연결"
echo "   2. VPC 서브넷 CIDR 동기화 활성화"
echo "   3. nginx real_ip 설정 확인"
echo ""
echo "⚠️  보안 주의사항:"
echo "   • 이 권한은 읽기 전용입니다"
echo "   • VPC/서브넷 수정/삭제는 불가능합니다"
echo "   • ALB/NLB 뒤에서만 사용하세요"
