#!/usr/bin/env bash
# Terraform 배포 스크립트
# 목적: Dream Seed VPC 서브넷 CIDR Reader IAM 리소스 자동 배포

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
ACTION="${1:-plan}"  # plan, apply, destroy
ENVIRONMENT="${2:-prod}"
REGION="${3:-ap-northeast-2}"

SCRIPT_DIR=$(dirname "$0")

log_info "=== Terraform 배포 시작 ==="
log_info "작업: $ACTION"
log_info "환경: $ENVIRONMENT"
log_info "리전: $REGION"

# Terraform 설치 확인
if ! command -v terraform >/dev/null 2>&1; then
    log_error "Terraform이 설치되지 않았습니다."
    log_info "설치 방법:"
    echo "  # Ubuntu/Debian"
    echo "  wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg"
    echo "  echo \"deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main\" | sudo tee /etc/apt/sources.list.d/hashicorp.list"
    echo "  sudo apt update && sudo apt install terraform"
    echo ""
    echo "  # 또는 직접 다운로드"
    echo "  wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip"
    echo "  unzip terraform_1.6.0_linux_amd64.zip"
    echo "  sudo mv terraform /usr/local/bin/"
    exit 1
fi

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

# 현재 디렉토리 확인
if [ ! -f "$SCRIPT_DIR/main.tf" ]; then
    log_error "Terraform 설정 파일을 찾을 수 없습니다."
    log_info "올바른 디렉토리에서 실행하세요: $SCRIPT_DIR"
    exit 1
fi

cd "$SCRIPT_DIR"

# 1. Terraform 초기화
log_info "1. Terraform 초기화 중..."
if [ ! -d ".terraform" ]; then
    terraform init
    log_success "✅ Terraform 초기화 완료"
else
    log_info "Terraform이 이미 초기화되어 있습니다."
fi

# 2. terraform.tfvars 파일 확인
if [ ! -f "terraform.tfvars" ]; then
    if [ -f "terraform.tfvars.example" ]; then
        log_warning "terraform.tfvars 파일이 없습니다."
        log_info "예시 파일을 복사하여 설정하세요:"
        echo "  cp terraform.tfvars.example terraform.tfvars"
        echo "  # terraform.tfvars 파일을 편집하여 값을 수정하세요"
        exit 1
    else
        log_error "terraform.tfvars 파일이 없습니다."
        exit 1
    fi
fi

# 3. Terraform 검증
log_info "2. Terraform 설정 검증 중..."
if terraform validate; then
    log_success "✅ Terraform 설정 검증 완료"
else
    log_error "❌ Terraform 설정 검증 실패"
    exit 1
fi

# 4. Terraform 포맷팅
log_info "3. Terraform 포맷팅 중..."
terraform fmt -recursive
log_success "✅ Terraform 포맷팅 완료"

# 5. 작업 실행
case "$ACTION" in
    "plan")
        log_info "4. Terraform 계획 생성 중..."
        terraform plan \
            -var="environment=$ENVIRONMENT" \
            -var="aws_region=$REGION" \
            -out="terraform.tfplan"
        log_success "✅ Terraform 계획 생성 완료"
        log_info "적용하려면: $0 apply $ENVIRONMENT $REGION"
        ;;
    
    "apply")
        log_info "4. Terraform 적용 중..."
        if [ -f "terraform.tfplan" ]; then
            terraform apply "terraform.tfplan"
        else
            terraform apply \
                -var="environment=$ENVIRONMENT" \
                -var="aws_region=$REGION" \
                -auto-approve
        fi
        log_success "✅ Terraform 적용 완료"
        
        # 출력값 표시
        log_info "5. 생성된 리소스 정보..."
        terraform output
        ;;
    
    "destroy")
        log_warning "⚠️  모든 리소스를 삭제합니다!"
        read -p "정말로 삭제하시겠습니까? (yes/no): " confirm
        if [[ "$confirm" == "yes" ]]; then
            log_info "4. Terraform 리소스 삭제 중..."
            terraform destroy \
                -var="environment=$ENVIRONMENT" \
                -var="aws_region=$REGION" \
                -auto-approve
            log_success "✅ Terraform 리소스 삭제 완료"
        else
            log_info "삭제가 취소되었습니다."
        fi
        ;;
    
    "show")
        log_info "4. Terraform 상태 표시 중..."
        terraform show
        ;;
    
    "output")
        log_info "4. Terraform 출력값 표시 중..."
        terraform output
        ;;
    
    *)
        log_error "알 수 없는 작업: $ACTION"
        echo ""
        echo "사용법: $0 <action> [environment] [region]"
        echo ""
        echo "작업:"
        echo "  plan    - 계획 생성 (기본값)"
        echo "  apply   - 리소스 생성"
        echo "  destroy - 리소스 삭제"
        echo "  show    - 상태 표시"
        echo "  output  - 출력값 표시"
        echo ""
        echo "예시:"
        echo "  $0 plan prod ap-northeast-2"
        echo "  $0 apply staging us-east-1"
        echo "  $0 destroy dev eu-west-1"
        exit 1
        ;;
esac

# 6. Dream Seed 통합 안내
if [ "$ACTION" = "apply" ]; then
    log_info "6. Dream Seed 통합 안내..."
    echo ""
    log_success "🎉 Terraform 배포 완료!"
    echo ""
    echo "📋 다음 단계:"
    echo "1. EC2 인스턴스에 IAM 역할 연결"
    echo "2. Dream Seed VPC 서브넷 CIDR 동기화 활성화"
    echo "3. nginx real_ip 설정 확인"
    echo ""
    echo "🔧 명령어:"
    echo "  # EC2 인스턴스에 IAM 역할 연결"
    echo "  aws ec2 associate-iam-instance-profile \\"
    echo "    --instance-id <INSTANCE_ID> \\"
    echo "    --iam-instance-profile Name=\$(terraform output -raw instance_profile_name)"
    echo ""
    echo "  # Dream Seed VPC 서브넷 CIDR 동기화 활성화"
    echo "  sudo systemctl set-environment AWS_VPC_SUBNETS=yes"
    echo "  sudo systemctl set-environment AWS_REGION=\$(terraform output -raw aws_region)"
    echo "  sudo /usr/local/sbin/update_real_ip_providers"
    echo ""
    echo "  # 상태 확인"
    echo "  systemctl status update-real-ip-providers.timer"
    echo "  sudo journalctl -u update-real-ip-providers.service"
fi
