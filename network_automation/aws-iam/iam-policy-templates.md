# AWS IAM 정책 템플릿 모음

Dream Seed VPC 서브넷 CIDR 자동 주입을 위한 최소 권한 IAM 정책 템플릿들입니다.

## 🎯 기본 원칙

- **최소 권한 원칙**: 필요한 권한만 부여
- **읽기 전용**: VPC/서브넷 수정/삭제 불가
- **리전 제한**: 가능한 경우 특정 리전으로 제한
- **보안 강화**: 위험한 권한 완전 배제

## 📋 정책 템플릿

### 1. 리전 제한 정책 (권장)

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
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    }
  ]
}
```

**사용 시나리오**: 특정 리전에서만 운영하는 경우

### 2. 글로벌 정책

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

**사용 시나리오**: 여러 리전에서 운영하는 경우

### 3. 다중 리전 정책

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
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": [
            "ap-northeast-2",
            "us-east-1",
            "eu-west-1"
          ]
        }
      }
    }
  ]
}
```

**사용 시나리오**: 특정 여러 리전에서 운영하는 경우

### 4. 특정 VPC 제한 정책 (고급)

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
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        },
        "StringLike": {
          "ec2:ResourceTag/VpcId": "vpc-*"
        }
      }
    }
  ]
}
```

**사용 시나리오**: 특정 VPC에서만 운영하는 경우 (태그 기반)

## 🔧 신뢰 정책 (Trust Policy)

### EC2 인스턴스용

```json
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
```

### Lambda 함수용

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### ECS Task용

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## 🚫 금지된 권한

다음 권한들은 **절대 포함하지 마세요**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "ec2:TerminateInstances",
        "ec2:StopInstances",
        "ec2:StartInstances",
        "ec2:ModifyInstanceAttribute",
        "ec2:DeleteVpc",
        "ec2:DeleteSubnet",
        "ec2:CreateVpc",
        "ec2:CreateSubnet",
        "ec2:ModifyVpcAttribute",
        "ec2:ModifySubnetAttribute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:ReplaceRoute"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🔍 권한 검증

### 1. 권한 테스트 명령어

```bash
# VPC 조회 테스트
aws ec2 describe-vpcs --region ap-northeast-2 --max-items 1

# 서브넷 조회 테스트
aws ec2 describe-subnets --region ap-northeast-2 --max-items 1

# 특정 VPC의 서브넷 조회 테스트
aws ec2 describe-subnets --region ap-northeast-2 --filters "Name=vpc-id,Values=vpc-12345678"
```

### 2. 권한 시뮬레이션

```bash
# 특정 권한 시뮬레이션
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/DreamSeedVpcSubnetReader \
  --action-names ec2:DescribeSubnets \
  --resource-arns "*"

# 위험한 권한 확인
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/DreamSeedVpcSubnetReader \
  --action-names ec2:TerminateInstances \
  --resource-arns "*"
```

## 📊 권한 요약

| 권한 | 목적 | 필수 여부 |
|------|------|-----------|
| `ec2:DescribeVpcs` | VPC 정보 조회 | ✅ 필수 |
| `ec2:DescribeSubnets` | 서브넷 CIDR 조회 | ✅ 필수 |
| `sts:AssumeRole` | 역할 가정 | ✅ 필수 (신뢰 정책) |

## 🛡️ 보안 모범 사례

1. **최소 권한 원칙**: 필요한 권한만 부여
2. **리전 제한**: 가능한 경우 특정 리전으로 제한
3. **정기적 검토**: 권한 사용 현황 정기 검토
4. **모니터링**: CloudTrail로 권한 사용 모니터링
5. **태그 기반 제어**: 리소스 태그를 활용한 세밀한 제어

## 🔧 적용 방법

### 1. AWS 콘솔에서

1. IAM → 역할 → 역할 생성
2. 신뢰할 주체 선택 (EC2, Lambda, ECS 등)
3. 위 정책 템플릿 중 하나 선택
4. 역할 이름 지정 및 생성
5. EC2 인스턴스에 역할 연결

### 2. AWS CLI로

```bash
# 역할 생성
aws iam create-role --role-name DreamSeedVpcSubnetReader --assume-role-policy-document file://trust-policy-ec2.json

# 정책 연결
aws iam put-role-policy --role-name DreamSeedVpcSubnetReader --policy-name VpcSubnetReadPolicy --policy-document file://vpc-subnet-readonly-policy.json

# 인스턴스 프로파일 생성
aws iam create-instance-profile --instance-profile-name DreamSeedVpcSubnetReaderProfile
aws iam add-role-to-instance-profile --instance-profile-name DreamSeedVpcSubnetReaderProfile --role-name DreamSeedVpcSubnetReader

# EC2 인스턴스에 연결
aws ec2 associate-iam-instance-profile --instance-id i-1234567890abcdef0 --iam-instance-profile Name=DreamSeedVpcSubnetReaderProfile
```

### 3. Terraform으로

```hcl
resource "aws_iam_role" "vpc_subnet_reader" {
  name = "DreamSeedVpcSubnetReader"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "vpc_subnet_read" {
  name = "VpcSubnetReadPolicy"
  role = aws_iam_role.vpc_subnet_reader.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = "ap-northeast-2"
          }
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "vpc_subnet_reader" {
  name = "DreamSeedVpcSubnetReaderProfile"
  role = aws_iam_role.vpc_subnet_reader.name
}
```

## ⚠️ 주의사항

1. **ALB/NLB 전용**: 이 권한은 ALB/NLB 뒤에서만 사용하세요
2. **직접 접속 차단**: 원 서버에 직접 접속이 가능한 환경에서는 방화벽으로 차단
3. **정기적 검토**: 권한 사용 현황을 정기적으로 검토하세요
4. **모니터링**: CloudTrail로 권한 사용을 모니터링하세요
5. **백업**: 중요한 설정은 백업해두세요
