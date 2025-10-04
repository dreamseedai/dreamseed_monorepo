# Dream Seed VPC Subnet CIDR Reader - Terraform & AWS CLI

ALB/NLB 뒤에서 VPC 서브넷 CIDR을 안전하게 조회할 수 있는 최소 권한 IAM 리소스를 생성하는 Terraform 및 AWS CLI 자동화 도구입니다.

## 🎯 목적

- **최소 권한 원칙**: `ec2:DescribeSubnets`, `ec2:DescribeVpcs`만 허용
- **보안 강화**: 읽기 전용 권한으로 VPC/서브넷 수정 불가
- **자동화**: Terraform 또는 AWS CLI로 간편한 배포
- **ALB/NLB 전용**: VPC 내부 서브넷 CIDR만 신뢰

## 📁 프로젝트 구조

```
network_automation/
├── terraform/                    # Terraform 설정
│   ├── main.tf                  # 메인 리소스 정의
│   ├── variables.tf             # 변수 정의
│   ├── outputs.tf               # 출력값 정의
│   ├── versions.tf              # 버전 정의
│   ├── terraform.tfvars.example # 변수 예시
│   └── deploy.sh                # 배포 스크립트
└── aws-iam/                     # AWS CLI 도구
    ├── create-aws-resources-cli.sh
    ├── create-iam-role.sh
    ├── verify-iam-permissions.sh
    └── install-aws-cli.sh
```

## 🚀 빠른 시작

### 방법 1: Terraform 사용 (권장)

#### 1. 사전 준비
```bash
# Terraform 설치 (Ubuntu/Debian)
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# AWS CLI 설치
./network_automation/aws-iam/install-aws-cli.sh

# AWS 자격 증명 설정
aws configure
```

#### 2. Terraform 설정
```bash
cd network_automation/terraform

# 설정 파일 복사 및 편집
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars 파일을 편집하여 값을 수정

# 배포 실행
./deploy.sh apply prod ap-northeast-2
```

#### 3. EC2 인스턴스에 적용
```bash
# 생성된 인스턴스 프로파일 이름 확인
terraform output instance_profile_name

# EC2 인스턴스에 IAM 역할 연결
aws ec2 associate-iam-instance-profile \
  --instance-id i-1234567890abcdef0 \
  --iam-instance-profile Name=DreamSeedVpcSubnetReaderProfile-prod
```

### 방법 2: AWS CLI 사용

#### 1. 사전 준비
```bash
# AWS CLI 설치
./network_automation/aws-iam/install-aws-cli.sh

# AWS 자격 증명 설정
aws configure
```

#### 2. IAM 리소스 생성
```bash
# IAM 리소스 생성
./network_automation/aws-iam/create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  ap-northeast-2 \
  prod
```

#### 3. EC2 인스턴스에 적용
```bash
# EC2 인스턴스에 IAM 역할 연결
aws ec2 associate-iam-instance-profile \
  --instance-id i-1234567890abcdef0 \
  --iam-instance-profile Name=DreamSeedVpcSubnetReaderProfile-prod
```

## 🔧 Terraform 사용법

### 기본 명령어

```bash
# 계획 생성
./deploy.sh plan prod ap-northeast-2

# 리소스 생성
./deploy.sh apply prod ap-northeast-2

# 상태 확인
./deploy.sh show

# 출력값 확인
./deploy.sh output

# 리소스 삭제
./deploy.sh destroy prod ap-northeast-2
```

### 변수 설정

`terraform.tfvars` 파일에서 다음 변수들을 설정할 수 있습니다:

```hcl
# AWS 설정
aws_region = "ap-northeast-2"
environment = "prod"

# IAM 리소스 이름
role_name = "DreamSeedVpcSubnetReader"
policy_name = "DescribeVpcSubnetsPolicy"
instance_profile_name = "DreamSeedVpcSubnetReaderProfile"

# 보안 설정
restrict_to_region = true
allowed_regions = ["ap-northeast-2", "us-east-1", "eu-west-1"]

# 생성 옵션
create_instance_profile = true
create_policy = true
```

### 환경별 배포

```bash
# 개발 환경
./deploy.sh apply dev ap-northeast-2

# 스테이징 환경
./deploy.sh apply staging us-east-1

# 프로덕션 환경
./deploy.sh apply prod ap-northeast-2
```

## 🔧 AWS CLI 사용법

### 기본 명령어

```bash
# IAM 리소스 생성
./create-aws-resources-cli.sh \
  <ROLE_NAME> \
  <POLICY_NAME> \
  <INSTANCE_PROFILE_NAME> \
  <REGION> \
  <ENVIRONMENT>

# 권한 검증
./verify-iam-permissions.sh ap-northeast-2

# AWS CLI 설치
./install-aws-cli.sh
```

### 예시

```bash
# 프로덕션 환경 생성
./create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  ap-northeast-2 \
  prod

# 개발 환경 생성
./create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  us-east-1 \
  dev
```

## 🛡️ 보안 정책

### 생성되는 IAM 정책

```json
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
```

### 보안 특징

- **최소 권한**: 필요한 권한만 부여
- **읽기 전용**: VPC/서브넷 수정/삭제 불가
- **리전 제한**: 특정 리전으로 권한 제한 가능
- **위험 권한 배제**: TerminateInstances, DeleteVpc 등 완전 금지

## 🔍 권한 검증

### AWS CLI로 테스트

```bash
# VPC 조회 테스트
aws ec2 describe-vpcs --region ap-northeast-2 --max-items 1

# 서브넷 조회 테스트
aws ec2 describe-subnets --region ap-northeast-2 --max-items 1

# 특정 VPC의 서브넷 조회 테스트
aws ec2 describe-subnets --region ap-northeast-2 --filters "Name=vpc-id,Values=vpc-12345678"
```

### Dream Seed 통합 테스트

```bash
# VPC 서브넷 CIDR 동기화 활성화
sudo systemctl set-environment AWS_VPC_SUBNETS=yes
sudo systemctl set-environment AWS_REGION=ap-northeast-2

# 동기화 실행
sudo /usr/local/sbin/update_real_ip_providers

# 결과 확인
cat /etc/nginx/conf.d/real_ip_providers.conf | grep "AWS VPC Subnets" -A 10
```

## 📊 생성되는 리소스

### IAM 리소스

| 리소스 타입 | 이름 | 설명 |
|-------------|------|------|
| IAM Role | `DreamSeedVpcSubnetReader-{env}` | EC2 인스턴스용 역할 |
| IAM Policy | `DescribeVpcSubnetsPolicy-{env}` | VPC/서브넷 조회 정책 |
| Instance Profile | `DreamSeedVpcSubnetReaderProfile-{env}` | EC2 인스턴스 프로파일 |

### 권한

| 권한 | 목적 | 보안 수준 |
|------|------|-----------|
| `ec2:DescribeVpcs` | VPC 정보 조회 | 🟢 안전 |
| `ec2:DescribeSubnets` | 서브넷 CIDR 조회 | 🟢 안전 |
| `sts:AssumeRole` | 역할 가정 | 🟢 안전 |

## 🔧 Dream Seed 통합

### 1. VPC 서브넷 CIDR 동기화 활성화

```bash
# 환경 변수 설정
sudo systemctl set-environment AWS_VPC_SUBNETS=yes
sudo systemctl set-environment AWS_REGION=ap-northeast-2

# 수동으로 VPC ID 설정 (선택사항)
sudo systemctl set-environment AWS_VPC_ID=vpc-12345678

# 동기화 실행
sudo /usr/local/sbin/update_real_ip_providers
```

### 2. 자동 동기화 설정

```bash
# systemd 타이머 활성화
sudo systemctl enable --now update-real-ip-providers.timer

# 상태 확인
systemctl status update-real-ip-providers.timer
```

### 3. nginx 설정 확인

```bash
# 생성된 설정 파일 확인
cat /etc/nginx/conf.d/real_ip_providers.conf

# nginx 설정 검증
sudo nginx -t

# nginx 재시작
sudo systemctl reload nginx
```

## 🚨 문제 해결

### 일반적인 문제

1. **AWS CLI 설치 실패**
   ```bash
   # 수동 설치
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

2. **AWS 자격 증명 오류**
   ```bash
   # 자격 증명 설정
   aws configure
   
   # 자격 증명 확인
   aws sts get-caller-identity
   ```

3. **Terraform 초기화 실패**
   ```bash
   # Terraform 초기화
   terraform init
   
   # Provider 업데이트
   terraform init -upgrade
   ```

4. **권한 테스트 실패**
   ```bash
   # 권한 검증
   ./network_automation/aws-iam/verify-iam-permissions.sh ap-northeast-2
   ```

### 로그 확인

```bash
# Dream Seed 동기화 로그
sudo journalctl -u update-real-ip-providers.service -f

# systemd 타이머 로그
sudo journalctl -u update-real-ip-providers.timer -f

# nginx 로그
sudo tail -f /var/log/nginx/error.log
```

## 📚 추가 자료

- [AWS IAM 정책 템플릿](../aws-iam/iam-policy-templates.md)
- [브라우저 호환성 가이드](../../README_BROWSER_COMPAT.md)
- [멀티 클라우드 동기화](../scripts/verify_multi_cloud_sync.sh)
- [AWS IAM 공식 문서](https://docs.aws.amazon.com/iam/)
- [Terraform AWS Provider 문서](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## ⚠️ 주의사항

1. **ALB/NLB 전용**: 이 권한은 ALB/NLB 뒤에서만 사용하세요
2. **직접 접속 차단**: 원 서버에 직접 접속이 가능한 환경에서는 방화벽으로 차단
3. **정기적 검토**: 권한 사용 현황을 정기적으로 검토
4. **모니터링**: CloudTrail로 권한 사용을 모니터링
5. **백업**: 중요한 설정은 백업해두기

---

**Dream Seed VPC Subnet CIDR Reader**로 안전하고 자동화된 VPC 서브넷 CIDR 관리를 시작하세요! 🚀
