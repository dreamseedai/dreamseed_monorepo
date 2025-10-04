#!/usr/bin/env bash
# 리전 제한 IAM 정책 테스트 스크립트
# 목적: 생성된 IAM 정책이 올바른 리전에서만 작동하는지 테스트

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
ENVIRONMENT="${2:-prod}"
ALLOWED_REGION="${3:-ap-northeast-2}"
TEST_REGIONS="${4:-ap-northeast-2,us-east-1,eu-west-1,ap-southeast-1}"

log_info "=== 리전 제한 IAM 정책 테스트 시작 ==="
log_info "역할 이름: ${ROLE_NAME}-${ENVIRONMENT}"
log_info "허용 리전: $ALLOWED_REGION"
log_info "테스트 리전: $TEST_REGIONS"

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

# 현재 AWS 계정 정보 확인
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_info "AWS 계정 ID: $ACCOUNT_ID"

# IAM 역할 ARN
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}-${ENVIRONMENT}"

# 역할 존재 확인
if ! aws iam get-role --role-name "${ROLE_NAME}-${ENVIRONMENT}" >/dev/null 2>&1; then
    log_error "IAM 역할 '${ROLE_NAME}-${ENVIRONMENT}'이 존재하지 않습니다."
    log_info "먼저 IAM 리소스를 생성하세요:"
    echo "  ./create-aws-resources-cli.sh $ROLE_NAME DescribeVpcSubnetsPolicy DreamSeedVpcSubnetReaderProfile $ALLOWED_REGION $ENVIRONMENT"
    exit 1
fi

log_success "✅ IAM 역할 확인됨: $ROLE_ARN"

# 테스트 함수
test_region() {
    local region="$1"
    local expected_result="$2"
    local test_name="$3"
    
    log_info "테스트: $test_name (리전: $region)"
    
    # 임시 자격 증명 생성
    local temp_creds
    temp_creds=$(aws sts assume-role \
        --role-arn "$ROLE_ARN" \
        --role-session-name "RegionTest-$(date +%s)" \
        --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
        --output text 2>/dev/null || echo "FAILED")
    
    if [ "$temp_creds" = "FAILED" ]; then
        log_error "❌ 역할 가정 실패: $region"
        return 1
    fi
    
    # 자격 증명 설정
    local access_key secret_key session_token
    read -r access_key secret_key session_token <<< "$temp_creds"
    
    # AWS CLI 환경 변수 설정
    export AWS_ACCESS_KEY_ID="$access_key"
    export AWS_SECRET_ACCESS_KEY="$secret_key"
    export AWS_SESSION_TOKEN="$session_token"
    
    # VPC 조회 테스트
    local vpc_result
    vpc_result=$(aws ec2 describe-vpcs --region "$region" --max-items 1 --query 'Vpcs[0].VpcId' --output text 2>&1 || echo "ERROR")
    
    # 서브넷 조회 테스트
    local subnet_result
    subnet_result=$(aws ec2 describe-subnets --region "$region" --max-items 1 --query 'Subnets[0].SubnetId' --output text 2>&1 || echo "ERROR")
    
    # 환경 변수 초기화
    unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
    
    # 결과 확인
    if [[ "$vpc_result" == *"AccessDenied"* ]] || [[ "$subnet_result" == *"AccessDenied"* ]]; then
        if [ "$expected_result" = "DENIED" ]; then
            log_success "✅ 예상대로 차단됨: $region"
            return 0
        else
            log_error "❌ 예상과 다르게 차단됨: $region"
            return 1
        fi
    elif [[ "$vpc_result" == "ERROR" ]] || [[ "$subnet_result" == "ERROR" ]]; then
        log_warning "⚠️  네트워크 오류 또는 권한 문제: $region"
        return 1
    else
        if [ "$expected_result" = "ALLOWED" ]; then
            log_success "✅ 예상대로 허용됨: $region"
            return 0
        else
            log_error "❌ 예상과 다르게 허용됨: $region"
            return 1
        fi
    fi
}

# 테스트 실행
log_info "1. 허용된 리전 테스트..."
test_region "$ALLOWED_REGION" "ALLOWED" "허용된 리전"

log_info "2. 차단된 리전 테스트..."
IFS=',' read -ra REGIONS <<< "$TEST_REGIONS"
for region in "${REGIONS[@]}"; do
    if [ "$region" != "$ALLOWED_REGION" ]; then
        test_region "$region" "DENIED" "차단된 리전"
    fi
done

# 정책 내용 확인
log_info "3. IAM 정책 내용 확인..."
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/DescribeVpcSubnetsPolicy-${ENVIRONMENT}"

if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
    log_info "정책 ARN: $POLICY_ARN"
    
    # 정책 버전 가져오기
    POLICY_VERSION=$(aws iam get-policy --policy-arn "$POLICY_ARN" --query 'Policy.DefaultVersionId' --output text)
    
    # 정책 내용 출력
    log_info "정책 내용:"
    aws iam get-policy-version \
        --policy-arn "$POLICY_ARN" \
        --version-id "$POLICY_VERSION" \
        --query 'PolicyVersion.Document' \
        --output json | jq '.'
else
    log_warning "정책을 찾을 수 없습니다: $POLICY_ARN"
fi

# 요약
log_info "4. 테스트 요약..."
echo ""
log_success "🎉 리전 제한 IAM 정책 테스트 완료!"
echo ""
echo "📋 테스트 결과:"
echo "   • 허용된 리전: $ALLOWED_REGION"
echo "   • 테스트된 리전: $TEST_REGIONS"
echo "   • IAM 역할: ${ROLE_NAME}-${ENVIRONMENT}"
echo "   • 정책 ARN: $POLICY_ARN"
echo ""
echo "🔧 추가 테스트:"
echo "   # 다른 리전에서 테스트"
echo "   AWS_REGION=us-east-1 aws ec2 describe-vpcs --max-items 1"
echo ""
echo "   # 정책 수정 후 재테스트"
echo "   ./test-region-restrictions.sh $ROLE_NAME $ENVIRONMENT $ALLOWED_REGION"
echo ""
echo "⚠️  주의사항:"
echo "   • 이 테스트는 임시 자격 증명을 사용합니다"
echo "   • 실제 EC2 인스턴스에서는 다른 결과가 나올 수 있습니다"
echo "   • CloudTrail에서 권한 사용을 모니터링하세요"
