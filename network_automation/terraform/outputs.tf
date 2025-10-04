# Dream Seed VPC Subnet CIDR Reader - Outputs
# Terraform 출력값 정의 파일

output "iam_role_arn" {
  description = "생성된 IAM 역할 ARN"
  value       = aws_iam_role.ec2_role.arn
}

output "iam_role_name" {
  description = "생성된 IAM 역할 이름"
  value       = aws_iam_role.ec2_role.name
}

output "iam_role_id" {
  description = "생성된 IAM 역할 ID"
  value       = aws_iam_role.ec2_role.id
}

output "instance_profile_arn" {
  description = "생성된 인스턴스 프로파일 ARN"
  value       = var.create_instance_profile ? aws_iam_instance_profile.ec2_profile[0].arn : null
}

output "instance_profile_name" {
  description = "생성된 인스턴스 프로파일 이름"
  value       = var.create_instance_profile ? aws_iam_instance_profile.ec2_profile[0].name : null
}

output "instance_profile_id" {
  description = "생성된 인스턴스 프로파일 ID"
  value       = var.create_instance_profile ? aws_iam_instance_profile.ec2_profile[0].id : null
}

output "policy_arn" {
  description = "생성된 정책 ARN"
  value       = var.create_policy ? aws_iam_policy.describe_vpc_subnets[0].arn : null
}

output "policy_name" {
  description = "생성된 정책 이름"
  value       = var.create_policy ? aws_iam_policy.describe_vpc_subnets[0].name : null
}

output "policy_id" {
  description = "생성된 정책 ID"
  value       = var.create_policy ? aws_iam_policy.describe_vpc_subnets[0].id : null
}

output "aws_account_id" {
  description = "AWS 계정 ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS 리전"
  value       = data.aws_region.current.name
}

output "aws_user_id" {
  description = "AWS 사용자 ID"
  value       = data.aws_caller_identity.current.user_id
}

output "aws_caller_arn" {
  description = "AWS 호출자 ARN"
  value       = data.aws_caller_identity.current.arn
}

# EC2 인스턴스에 적용할 때 사용할 명령어
output "ec2_associate_command" {
  description = "EC2 인스턴스에 IAM 역할을 연결하는 AWS CLI 명령어"
  value = var.create_instance_profile ? "aws ec2 associate-iam-instance-profile --instance-id <INSTANCE_ID> --iam-instance-profile Name=${aws_iam_instance_profile.ec2_profile[0].name}" : "N/A"
}

# Terraform 상태 확인 명령어
output "terraform_show_command" {
  description = "Terraform 상태 확인 명령어"
  value       = "terraform show"
}

# AWS CLI로 권한 테스트하는 명령어
output "aws_test_commands" {
  description = "AWS CLI로 권한을 테스트하는 명령어들"
  value = {
    test_vpc = "aws ec2 describe-vpcs --region ${data.aws_region.current.name} --max-items 1"
    test_subnets = "aws ec2 describe-subnets --region ${data.aws_region.current.name} --max-items 1"
    test_caller = "aws sts get-caller-identity"
  }
}

# Dream Seed VPC 서브넷 CIDR 동기화 명령어
output "dreamseed_commands" {
  description = "Dream Seed VPC 서브넷 CIDR 동기화 명령어들"
  value = {
    enable_vpc_sync = "sudo systemctl set-environment AWS_VPC_SUBNETS=yes"
    set_region = "sudo systemctl set-environment AWS_REGION=${data.aws_region.current.name}"
    run_sync = "sudo /usr/local/sbin/update_real_ip_providers"
    check_status = "systemctl status update-real-ip-providers.timer"
  }
}
