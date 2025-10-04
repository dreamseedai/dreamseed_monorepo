# Dream Seed VPC Subnet CIDR Reader - Terraform Versions
# Terraform 및 Provider 버전 정의

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
  
  # 기본 태그 설정
  default_tags {
    tags = {
      Project     = "DreamSeed"
      Environment = var.environment
      Purpose     = "VPCSubnetCIDRReader"
      ManagedBy   = "Terraform"
    }
  }
}
