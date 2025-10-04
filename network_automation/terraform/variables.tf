# Dream Seed VPC Subnet CIDR Reader - Variables
# Terraform 변수 정의 파일

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
  
  validation {
    condition = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "AWS 리전은 소문자, 숫자, 하이픈만 포함할 수 있습니다."
  }
}

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "환경은 dev, staging, prod 중 하나여야 합니다."
  }
}

variable "role_name" {
  description = "IAM 역할 이름"
  type        = string
  default     = "DreamSeedVpcSubnetReader"
  
  validation {
    condition = can(regex("^[a-zA-Z0-9+=,.@_-]+$", var.role_name))
    error_message = "IAM 역할 이름은 영문자, 숫자, 특수문자(+=,.@_-)만 포함할 수 있습니다."
  }
}

variable "policy_name" {
  description = "IAM 정책 이름"
  type        = string
  default     = "DescribeVpcSubnetsPolicy"
  
  validation {
    condition = can(regex("^[a-zA-Z0-9+=,.@_-]+$", var.policy_name))
    error_message = "IAM 정책 이름은 영문자, 숫자, 특수문자(+=,.@_-)만 포함할 수 있습니다."
  }
}

variable "instance_profile_name" {
  description = "인스턴스 프로파일 이름"
  type        = string
  default     = "DreamSeedVpcSubnetReaderProfile"
  
  validation {
    condition = can(regex("^[a-zA-Z0-9+=,.@_-]+$", var.instance_profile_name))
    error_message = "인스턴스 프로파일 이름은 영문자, 숫자, 특수문자(+=,.@_-)만 포함할 수 있습니다."
  }
}

variable "restrict_to_region" {
  description = "리전으로 권한 제한 여부"
  type        = bool
  default     = true
}

variable "multi_region" {
  description = "멀티 리전 지원 여부 (restrict_to_region이 false일 때)"
  type        = bool
  default     = false
}

variable "allowed_regions" {
  description = "허용된 리전 목록 (multi_region이 true일 때 사용)"
  type        = list(string)
  default     = ["ap-northeast-2", "us-east-1", "eu-west-1"]
  
  validation {
    condition = length(var.allowed_regions) > 0
    error_message = "허용된 리전 목록은 최소 1개 이상이어야 합니다."
  }
}

# 멀티 리전 전용 변수
variable "multi_region_enabled" {
  description = "멀티 리전 리소스 생성 여부"
  type        = bool
  default     = false
}

variable "multi_region_allowed_regions" {
  description = "멀티 리전에서 허용할 리전 목록"
  type        = list(string)
  default     = ["ap-northeast-2", "us-east-1", "eu-west-1", "ap-southeast-1"]
  
  validation {
    condition = length(var.multi_region_allowed_regions) > 0
    error_message = "멀티 리전 허용 리전 목록은 최소 1개 이상이어야 합니다."
  }
}

variable "tags" {
  description = "추가 태그"
  type        = map(string)
  default     = {}
}

variable "create_instance_profile" {
  description = "인스턴스 프로파일 생성 여부"
  type        = bool
  default     = true
}

variable "create_policy" {
  description = "IAM 정책 생성 여부"
  type        = bool
  default     = true
}

variable "policy_description" {
  description = "IAM 정책 설명"
  type        = string
  default     = "Allow only ec2:DescribeSubnets and ec2:DescribeVpcs for Dream Seed VPC subnet CIDR reading"
}

variable "role_description" {
  description = "IAM 역할 설명"
  type        = string
  default     = "Dream Seed VPC Subnet CIDR Reader Role for ALB/NLB environments"
}
