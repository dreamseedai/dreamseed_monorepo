#!/usr/bin/env bash
set -euo pipefail

echo "☁️ DreamSeed AWS S3 백업 설정 시작"

# AWS CLI 설치
echo "📦 AWS CLI 설치 중..."
if ! command -v aws &> /dev/null; then
    sudo apt update
    sudo apt install -y awscli
    echo "✅ AWS CLI 설치 완료"
else
    echo "✅ AWS CLI 이미 설치됨"
fi

# AWS 자격 증명 구성
echo "🔐 AWS 자격 증명 구성 중..."
echo "AWS Access Key ID를 입력하세요:"
read -r AWS_ACCESS_KEY_ID
echo "AWS Secret Access Key를 입력하세요:"
read -s AWS_SECRET_ACCESS_KEY
echo
echo "AWS Region을 입력하세요 (기본값: ap-northeast-2):"
read -r AWS_REGION
AWS_REGION=${AWS_REGION:-ap-northeast-2}

# AWS 프로파일 생성
aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID" --profile dreamseed-backup
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY" --profile dreamseed-backup
aws configure set default.region "$AWS_REGION" --profile dreamseed-backup
aws configure set default.output json --profile dreamseed-backup

echo "✅ AWS 프로파일 'dreamseed-backup' 생성 완료"

# S3 버킷 생성 (선택사항)
echo "🪣 S3 버킷을 생성하시겠습니까? (y/n)"
read -r CREATE_BUCKET
if [[ "$CREATE_BUCKET" == "y" || "$CREATE_BUCKET" == "Y" ]]; then
    echo "버킷 이름을 입력하세요 (예: dreamseed-backups-$(date +%Y%m%d)):"
    read -r BUCKET_NAME
    BUCKET_NAME=${BUCKET_NAME:-dreamseed-backups-$(date +%Y%m%d)}
    
    # 버킷 생성
    aws s3 mb "s3://$BUCKET_NAME" --profile dreamseed-backup --region "$AWS_REGION"
    
    # 버킷 정책 설정 (버전 관리 활성화)
    aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" --versioning-configuration Status=Enabled --profile dreamseed-backup
    
    echo "✅ S3 버킷 '$BUCKET_NAME' 생성 완료"
    echo "📝 S3 버킷 이름: $BUCKET_NAME"
else
    echo "기존 S3 버킷 이름을 입력하세요:"
    read -r BUCKET_NAME
fi

# 환경 변수 파일 업데이트
echo "⚙️ 환경 변수 파일 업데이트 중..."
BACKUP_ENV_FILE="/etc/dreamseed.env"

# 기존 파일 백업
if [ -f "$BACKUP_ENV_FILE" ]; then
    sudo cp "$BACKUP_ENV_FILE" "${BACKUP_ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# S3 설정 추가
sudo tee -a "$BACKUP_ENV_FILE" > /dev/null << EOF

# AWS S3 백업 설정
REMOTE_TYPE=s3
REMOTE_TARGET=s3://$BUCKET_NAME/dreamseed-backups/
AWS_PROFILE=dreamseed-backup
AWS_REGION=$AWS_REGION
EOF

echo "✅ 환경 변수 파일 업데이트 완료"

# AWS 자격 증명 테스트
echo "🧪 AWS 연결 테스트 중..."
if aws s3 ls "s3://$BUCKET_NAME" --profile dreamseed-backup > /dev/null 2>&1; then
    echo "✅ AWS S3 연결 테스트 성공"
else
    echo "❌ AWS S3 연결 테스트 실패"
    echo "자격 증명을 다시 확인해주세요."
    exit 1
fi

echo "🎉 DreamSeed AWS S3 백업 설정 완료!"
echo "📋 설정 요약:"
echo "  - AWS 프로파일: dreamseed-backup"
echo "  - S3 버킷: $BUCKET_NAME"
echo "  - 지역: $AWS_REGION"
echo "  - 환경 변수: $BACKUP_ENV_FILE"

