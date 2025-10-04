# Dream Seed VPC Subnet CIDR Reader - 리전 제한 가이드

AWS IAM 정책을 통한 리전 제한으로 보안을 강화하는 방법을 설명합니다.

## 🎯 리전 제한의 필요성

### 보안 위험
- **무단 리전 접근**: 다른 리전의 VPC/서브넷 정보 조회 가능
- **데이터 유출**: 민감한 네트워크 정보가 의도하지 않은 리전으로 노출
- **비용 증가**: 불필요한 API 호출로 인한 비용 발생
- **규정 준수**: 데이터 거주지 규정 위반 가능성

### 리전 제한의 이점
- **최소 권한**: 필요한 리전에서만 API 호출 허용
- **보안 강화**: 의도하지 않은 리전 접근 차단
- **비용 절약**: 불필요한 API 호출 방지
- **규정 준수**: 데이터 거주지 요구사항 충족

## 🛡️ 리전 제한 정책 유형

### 1. 단일 리전 제한 (권장)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowVpcSubnetCidrReadInRegion",
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

**특징:**
- 서울 리전(ap-northeast-2)에서만 API 호출 허용
- 다른 리전에서 호출 시 AccessDenied 발생
- 가장 강력한 보안 수준

### 2. 멀티 리전 허용

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowVpcSubnetCidrReadInMultipleRegions",
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

**특징:**
- 지정된 여러 리전에서만 API 호출 허용
- 글로벌 서비스 운영 시 유용
- 여전히 제한된 리전에서만 접근 가능

### 3. 모든 리전 허용 (비권장)

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

**특징:**
- 모든 리전에서 API 호출 허용
- 보안 위험이 높음
- 특별한 경우에만 사용

## 🚀 사용 방법

### Terraform으로 리전 제한 설정

#### 1. 단일 리전 제한
```hcl
# terraform.tfvars
restrict_to_region = true
multi_region = false
aws_region = "ap-northeast-2"
```

#### 2. 멀티 리전 허용
```hcl
# terraform.tfvars
restrict_to_region = false
multi_region = true
allowed_regions = ["ap-northeast-2", "us-east-1", "eu-west-1"]
```

#### 3. 모든 리전 허용
```hcl
# terraform.tfvars
restrict_to_region = false
multi_region = false
```

### AWS CLI로 리전 제한 설정

#### 1. 단일 리전 제한
```bash
./create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  ap-northeast-2 \
  prod \
  true \
  false \
  ap-northeast-2
```

#### 2. 멀티 리전 허용
```bash
./create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  ap-northeast-2 \
  prod \
  false \
  true \
  "ap-northeast-2,us-east-1,eu-west-1"
```

#### 3. 모든 리전 허용
```bash
./create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  ap-northeast-2 \
  prod \
  false \
  false \
  ""
```

## 🔍 리전 제한 테스트

### 자동 테스트 스크립트
```bash
# 리전 제한 테스트
./test-region-restrictions.sh \
  DreamSeedVpcSubnetReader \
  prod \
  ap-northeast-2 \
  "ap-northeast-2,us-east-1,eu-west-1,ap-southeast-1"
```

### 수동 테스트
```bash
# 허용된 리전에서 테스트
AWS_REGION=ap-northeast-2 aws ec2 describe-vpcs --max-items 1

# 차단된 리전에서 테스트
AWS_REGION=us-east-1 aws ec2 describe-vpcs --max-items 1
# 결과: AccessDenied
```

## 📊 리전 제한 비교

| 제한 유형 | 보안 수준 | 사용 사례 | 권장도 |
|-----------|-----------|-----------|--------|
| 단일 리전 | 🔴 높음 | 단일 리전 운영 | ⭐⭐⭐⭐⭐ |
| 멀티 리전 | 🟡 중간 | 글로벌 서비스 | ⭐⭐⭐⭐ |
| 모든 리전 | 🔴 낮음 | 특별한 경우 | ⭐ |

## 🛠️ 실제 사용 예시

### Dream Seed 프로덕션 환경
```bash
# 1. 서울 리전으로 제한된 정책 생성
./create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  ap-northeast-2 \
  prod \
  true \
  false \
  ap-northeast-2

# 2. EC2 인스턴스에 적용
aws ec2 associate-iam-instance-profile \
  --instance-id i-1234567890abcdef0 \
  --iam-instance-profile Name=DreamSeedVpcSubnetReaderProfile-prod

# 3. Dream Seed VPC 서브넷 CIDR 동기화
sudo systemctl set-environment AWS_VPC_SUBNETS=yes
sudo systemctl set-environment AWS_REGION=ap-northeast-2
sudo /usr/local/sbin/update_real_ip_providers

# 4. 리전 제한 테스트
./test-region-restrictions.sh \
  DreamSeedVpcSubnetReader \
  prod \
  ap-northeast-2 \
  "ap-northeast-2,us-east-1,eu-west-1"
```

### 멀티 리전 개발 환경
```bash
# 1. 여러 리전 허용 정책 생성
./create-aws-resources-cli.sh \
  DreamSeedVpcSubnetReader \
  DescribeVpcSubnetsPolicy \
  DreamSeedVpcSubnetReaderProfile \
  ap-northeast-2 \
  dev \
  false \
  true \
  "ap-northeast-2,us-east-1,eu-west-1"

# 2. 각 리전에서 테스트
for region in ap-northeast-2 us-east-1 eu-west-1; do
  echo "Testing region: $region"
  AWS_REGION=$region aws ec2 describe-vpcs --max-items 1
done
```

## 🔧 문제 해결

### 일반적인 문제

1. **AccessDenied 오류**
   ```bash
   # 리전 확인
   aws configure get region
   
   # 정책 확인
   aws iam get-policy --policy-arn arn:aws:iam::ACCOUNT:policy/POLICY_NAME
   ```

2. **잘못된 리전 설정**
   ```bash
   # 올바른 리전으로 설정
   aws configure set region ap-northeast-2
   
   # 환경 변수 설정
   export AWS_DEFAULT_REGION=ap-northeast-2
   ```

3. **정책 업데이트 필요**
   ```bash
   # 기존 정책 삭제
   aws iam delete-policy --policy-arn arn:aws:iam::ACCOUNT:policy/POLICY_NAME
   
   # 새 정책 생성
   ./create-aws-resources-cli.sh ...
   ```

### 로그 확인

```bash
# CloudTrail 로그 확인
aws logs describe-log-groups --log-group-name-prefix CloudTrail

# IAM 정책 사용 현황 확인
aws iam get-role --role-name ROLE_NAME
```

## ⚠️ 주의사항

1. **리전 제한은 API 호출 레벨에서 적용**
   - Terraform이나 CLI를 다른 리전에서 실행하면 차단
   - EC2 인스턴스 메타데이터를 통한 자동 리전 감지 시 자연스럽게 적용

2. **멀티 리전 운영 시 고려사항**
   - 각 리전별로 별도의 IAM 역할 생성 고려
   - 리전별 데이터 거주지 규정 확인
   - 비용 모니터링 강화

3. **정책 변경 시 영향**
   - 기존 EC2 인스턴스에 즉시 적용
   - 롤백 계획 준비
   - 테스트 환경에서 먼저 검증

## 📚 추가 자료

- [AWS IAM 조건 키 참조](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html)
- [AWS 리전 및 가용 영역](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
- [CloudTrail 로그 분석](https://docs.aws.amazon.com/cloudtrail/latest/userguide/cloudtrail-log-file-analysis.html)

---

**리전 제한으로 Dream Seed의 보안을 한 단계 더 강화하세요!** 🛡️
