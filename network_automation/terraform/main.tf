# Dream Seed VPC Subnet CIDR Reader - Terraform Configuration
# 목적: ALB/NLB 뒤에서 VPC 서브넷 CIDR을 안전하게 조회할 수 있는 최소 권한 IAM 역할 생성

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Provider 설정
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "DreamSeed"
      Environment = var.environment
      Purpose     = "VPCSubnetCIDRReader"
      ManagedBy   = "Terraform"
    }
  }
}

# 변수 정의
variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "role_name" {
  description = "IAM 역할 이름"
  type        = string
  default     = "DreamSeedVpcSubnetReader"
}

variable "policy_name" {
  description = "IAM 정책 이름"
  type        = string
  default     = "DescribeVpcSubnetsPolicy"
}

variable "instance_profile_name" {
  description = "인스턴스 프로파일 이름"
  type        = string
  default     = "DreamSeedVpcSubnetReaderProfile"
}

# 데이터 소스
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# IAM 정책 (최소 권한 + 리전 제한)
resource "aws_iam_policy" "describe_vpc_subnets" {
  name        = "${var.policy_name}-${var.environment}"
  description = "Allow only ec2:DescribeSubnets and ec2:DescribeVpcs for Dream Seed VPC subnet CIDR reading"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowVpcSubnetCidrRead"
        Effect = "Allow"
        Action = [
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
        Condition = var.restrict_to_region ? {
          StringEquals = {
            "aws:RequestedRegion" = var.aws_region
          }
        } : var.multi_region ? {
          StringEquals = {
            "aws:RequestedRegion" = var.allowed_regions
          }
        } : null
      }
    ]
  })

  tags = {
    Name        = "${var.policy_name}-${var.environment}"
    Description = "Dream Seed VPC Subnet CIDR Reader Policy"
    Region      = var.restrict_to_region ? var.aws_region : "multi-region"
  }
}

# IAM 역할 (EC2 인스턴스 프로파일용)
resource "aws_iam_role" "ec2_role" {
  name = "${var.role_name}-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.role_name}-${var.environment}"
    Description = "Dream Seed VPC Subnet CIDR Reader Role"
  }
}

# 정책 연결
resource "aws_iam_role_policy_attachment" "attach_describe" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.describe_vpc_subnets.arn
}

# 인스턴스 프로파일
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.instance_profile_name}-${var.environment}"
  role = aws_iam_role.ec2_role.name

  tags = {
    Name        = "${var.instance_profile_name}-${var.environment}"
    Description = "Dream Seed VPC Subnet CIDR Reader Instance Profile"
  }
}

# 추가 변수
variable "restrict_to_region" {
  description = "리전으로 권한 제한 여부"
  type        = bool
  default     = true
}

# 출력값
output "iam_role_arn" {
  description = "생성된 IAM 역할 ARN"
  value       = aws_iam_role.ec2_role.arn
}

output "iam_role_name" {
  description = "생성된 IAM 역할 이름"
  value       = aws_iam_role.ec2_role.name
}

output "instance_profile_arn" {
  description = "생성된 인스턴스 프로파일 ARN"
  value       = aws_iam_instance_profile.ec2_profile.arn
}

output "instance_profile_name" {
  description = "생성된 인스턴스 프로파일 이름"
  value       = aws_iam_instance_profile.ec2_profile.name
}

output "policy_arn" {
  description = "생성된 정책 ARN"
  value       = aws_iam_policy.describe_vpc_subnets.arn
}

output "aws_account_id" {
  description = "AWS 계정 ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS 리전"
  value       = data.aws_region.current.name
}
