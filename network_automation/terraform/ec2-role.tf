# Dream Seed EC2 Role with Region-Restricted IAM Policy
# 리전 제한 IAM 정책을 가진 EC2 역할 및 인스턴스 프로파일

# IAM 정책 (서울 리전 한정)
resource "aws_iam_policy" "describe_vpc_subnets_region" {
  name        = "DescribeVpcSubnetsPolicy-SeoulOnly"
  description = "Allow DescribeSubnets and DescribeVpcs only in ap-northeast-2"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowVpcSubnetCidrReadInRegion"
        Effect   = "Allow"
        Action   = [
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

  tags = {
    Name        = "DescribeVpcSubnetsPolicy-SeoulOnly"
    Description = "Dream Seed VPC Subnet CIDR Reader Policy (Seoul Only)"
    Region      = "ap-northeast-2"
  }
}

# IAM 역할 (EC2 신뢰)
resource "aws_iam_role" "ec2_role_region" {
  name = "EC2DescribeVpcSubnetsRole-SeoulOnly"

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
    Name        = "EC2DescribeVpcSubnetsRole-SeoulOnly"
    Description = "Dream Seed VPC Subnet CIDR Reader Role (Seoul Only)"
    Region      = "ap-northeast-2"
  }
}

# 정책 연결
resource "aws_iam_role_policy_attachment" "attach_describe_region" {
  role       = aws_iam_role.ec2_role_region.name
  policy_arn = aws_iam_policy.describe_vpc_subnets_region.arn
}

# 인스턴스 프로파일
resource "aws_iam_instance_profile" "ec2_profile_region" {
  name = "EC2DescribeVpcSubnetsProfile-SeoulOnly"
  role = aws_iam_role.ec2_role_region.name

  tags = {
    Name        = "EC2DescribeVpcSubnetsProfile-SeoulOnly"
    Description = "Dream Seed VPC Subnet CIDR Reader Instance Profile (Seoul Only)"
    Region      = "ap-northeast-2"
  }
}

# 출력값
output "ec2_role_arn" {
  description = "EC2 역할 ARN"
  value       = aws_iam_role.ec2_role_region.arn
}

output "ec2_role_name" {
  description = "EC2 역할 이름"
  value       = aws_iam_role.ec2_role_region.name
}

output "ec2_instance_profile_arn" {
  description = "EC2 인스턴스 프로파일 ARN"
  value       = aws_iam_instance_profile.ec2_profile_region.arn
}

output "ec2_instance_profile_name" {
  description = "EC2 인스턴스 프로파일 이름"
  value       = aws_iam_instance_profile.ec2_profile_region.name
}

output "ec2_policy_arn" {
  description = "EC2 정책 ARN"
  value       = aws_iam_policy.describe_vpc_subnets_region.arn
}

# EC2 인스턴스에 적용하는 명령어
output "ec2_associate_command" {
  description = "EC2 인스턴스에 IAM 역할을 연결하는 AWS CLI 명령어"
  value = "aws ec2 associate-iam-instance-profile --instance-id <INSTANCE_ID> --iam-instance-profile Name=${aws_iam_instance_profile.ec2_profile_region.name}"
}
