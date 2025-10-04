# Dream Seed Multi-Region IAM Policy + EC2 Role/Profile
# 멀티 리전 지원 IAM 정책을 가진 EC2 역할 및 인스턴스 프로파일

# IAM 정책 (멀티 리전 허용) - 조건부 생성
resource "aws_iam_policy" "describe_vpc_subnets_multi_region" {
  count = var.multi_region_enabled ? 1 : 0
  name        = "DescribeVpcSubnetsPolicy-MultiRegion"
  description = "Allow DescribeSubnets and DescribeVpcs only in selected regions"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowVpcSubnetCidrReadInRegions"
        Effect   = "Allow"
        Action   = [
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = var.multi_region_allowed_regions
          }
        }
      }
    ]
  })

  tags = {
    Name        = "DescribeVpcSubnetsPolicy-MultiRegion"
    Description = "Dream Seed VPC Subnet CIDR Reader Policy (Multi-Region)"
    Regions     = join(",", var.multi_region_allowed_regions)
  }
}

# IAM 역할 (EC2 신뢰) - 조건부 생성
resource "aws_iam_role" "ec2_role_multi_region" {
  count = var.multi_region_enabled ? 1 : 0
  name = "EC2DescribeVpcSubnetsRole-MultiRegion"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action   = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "EC2DescribeVpcSubnetsRole-MultiRegion"
    Description = "Dream Seed VPC Subnet CIDR Reader Role (Multi-Region)"
    Regions     = join(",", var.multi_region_allowed_regions)
  }
}

# 정책 연결 - 조건부 생성
resource "aws_iam_role_policy_attachment" "attach_describe_multi_region" {
  count      = var.multi_region_enabled ? 1 : 0
  role       = aws_iam_role.ec2_role_multi_region[0].name
  policy_arn = aws_iam_policy.describe_vpc_subnets_multi_region[0].arn
}

# 인스턴스 프로파일 - 조건부 생성
resource "aws_iam_instance_profile" "ec2_profile_multi_region" {
  count = var.multi_region_enabled ? 1 : 0
  name = "EC2DescribeVpcSubnetsProfile-MultiRegion"
  role = aws_iam_role.ec2_role_multi_region[0].name

  tags = {
    Name        = "EC2DescribeVpcSubnetsProfile-MultiRegion"
    Description = "Dream Seed VPC Subnet CIDR Reader Instance Profile (Multi-Region)"
    Regions     = join(",", var.multi_region_allowed_regions)
  }
}

# 출력값 - 조건부
output "multi_region_role_arn" {
  description = "멀티 리전 EC2 역할 ARN"
  value       = var.multi_region_enabled ? aws_iam_role.ec2_role_multi_region[0].arn : null
}

output "multi_region_role_name" {
  description = "멀티 리전 EC2 역할 이름"
  value       = var.multi_region_enabled ? aws_iam_role.ec2_role_multi_region[0].name : null
}

output "multi_region_instance_profile_arn" {
  description = "멀티 리전 EC2 인스턴스 프로파일 ARN"
  value       = var.multi_region_enabled ? aws_iam_instance_profile.ec2_profile_multi_region[0].arn : null
}

output "multi_region_instance_profile_name" {
  description = "멀티 리전 EC2 인스턴스 프로파일 이름"
  value       = var.multi_region_enabled ? aws_iam_instance_profile.ec2_profile_multi_region[0].name : null
}

output "multi_region_policy_arn" {
  description = "멀티 리전 EC2 정책 ARN"
  value       = var.multi_region_enabled ? aws_iam_policy.describe_vpc_subnets_multi_region[0].arn : null
}

# EC2 인스턴스에 적용하는 명령어
output "multi_region_associate_command" {
  description = "멀티 리전 EC2 인스턴스에 IAM 역할을 연결하는 AWS CLI 명령어"
  value = var.multi_region_enabled ? "aws ec2 associate-iam-instance-profile --instance-id <INSTANCE_ID> --iam-instance-profile Name=${aws_iam_instance_profile.ec2_profile_multi_region[0].name}" : null
}
