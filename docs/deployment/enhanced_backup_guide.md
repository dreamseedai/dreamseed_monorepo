# DreamSeed 고도화된 백업 시스템 가이드

## 📖 개요

DreamSeed AI Platform의 고도화된 백업 시스템은 다음과 같은 기능을 제공합니다:

- ☁️ **AWS S3 업로드**: 안전한 클라우드 백업
- 🔐 **GPG 암호화**: 공개키 기반 암호화
- 📢 **다중 알림**: Slack, 이메일, 로그 알림
- 📊 **Grafana 모니터링**: 실시간 백업 상태 모니터링
- 🔄 **자동화**: systemd 타이머 기반 자동 백업

## 🚀 빠른 시작

### 1. 통합 설정 실행
```bash
# 고도화된 백업 시스템 설정
chmod +x setup_enhanced_backup.sh
./setup_enhanced_backup.sh
```

### 2. 개별 설정 (선택사항)

#### AWS S3 설정
```bash
# AWS S3 백업 설정
./setup_aws_s3.sh
```

#### GPG 암호화 설정
```bash
# GPG 암호화 설정
./setup_gpg_encryption.sh
```

## ☁️ AWS S3 설정

### 1. AWS CLI 설치 및 구성
```bash
# AWS CLI 설치
sudo apt update
sudo apt install -y awscli

# AWS 자격 증명 구성
aws configure --profile dreamseed-backup
```

### 2. 환경 변수 설정
```bash
# /etc/dreamseed.env에 추가
REMOTE_TYPE=s3
REMOTE_TARGET=s3://your-bucket-name/dreamseed-backups/
AWS_PROFILE=dreamseed-backup
AWS_REGION=ap-northeast-2
```

### 3. S3 버킷 정책 설정
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DreamSeedBackupAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/dreamseed-backup"
            },
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/dreamseed-backups/*"
        }
    ]
}
```

## 🔐 GPG 암호화 설정

### 1. GPG 키 생성
```bash
# GPG 키 생성
gpg --full-generate-key

# 키 타입: RSA and RSA
# 키 크기: 4096
# 만료: 0 (무제한) 또는 1~2년
# 사용자 이름/이메일 입력
# 패스프레이즈 설정
```

### 2. 공개키 내보내기
```bash
# 공개키 내보내기
gpg --armor --export your-email@example.com > dreamseed_public_key.asc

# 개인키 백업 (안전한 위치에)
gpg --armor --export-secret-keys your-email@example.com > dreamseed_private_key.asc
```

### 3. 환경 변수 설정
```bash
# /etc/dreamseed.env에 추가
ENCRYPT=gpg
GPG_RECIPIENT=your-email@example.com
GPG_KEY_ID=YOUR_KEY_ID
```

### 4. 복구 서버 설정
```bash
# 복구 서버에서 공개키 가져오기
gpg --import dreamseed_public_key.asc

# 신뢰도 설정
gpg --edit-key your-email@example.com
> trust
> 5
> quit
```

## 📢 알림 설정

### 1. Slack 알림 설정
```bash
# Slack Webhook URL 설정
# /etc/dreamseed.env에 추가
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 2. 이메일 알림 설정
```bash
# 이메일 주소 설정
# /etc/dreamseed.env에 추가
MAIL_TO=admin@dreamseed.com

# 메일 서버 설정 (선택사항)
sudo apt install -y postfix
```

### 3. 알림 테스트
```bash
# 백업 수동 실행으로 알림 테스트
sudo systemctl start dreamseed-backup-enhanced.service
```

## 📊 Grafana 모니터링 설정

### 1. Prometheus 설정
```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'dreamseed-backup'
    static_configs:
      - targets: ['localhost:9100']
    relabel_configs:
      - source_labels: [__name__]
        regex: 'node_systemd_unit_state.*dreamseed-backup.*'
        target_label: 'job'
        replacement: 'dreamseed-backup'
```

### 2. Grafana 알림 규칙 임포트
```bash
# 알림 규칙 파일 복사
sudo cp grafana-alert-rules.yml /etc/grafana/provisioning/alerting/
sudo systemctl reload grafana-server
```

### 3. Grafana 대시보드 설정
- **Prometheus 데이터소스** 추가
- **알림 채널** 설정 (Slack, 이메일)
- **대시보드** 임포트

## 🔧 백업 관리

### 1. 백업 상태 확인
```bash
# 백업 서비스 상태
sudo systemctl status dreamseed-backup-enhanced.service
sudo systemctl status dreamseed-backup-enhanced.timer

# 백업 로그 확인
sudo journalctl -u dreamseed-backup-enhanced.service -f
tail -f /var/log/dreamseed-backup.log
```

### 2. 수동 백업 실행
```bash
# 백업 수동 실행
sudo systemctl start dreamseed-backup-enhanced.service

# 백업 스크립트 직접 실행
sudo /usr/local/sbin/dreamseed-backup-enhanced
```

### 3. 백업 파일 확인
```bash
# 로컬 백업 파일 확인
ls -la /var/backups/dreamseed/

# S3 백업 파일 확인
aws s3 ls s3://your-bucket-name/dreamseed-backups/ --profile dreamseed-backup
```

## 🔄 복구 절차

### 1. 로컬 복구
```bash
# 복구 스크립트 실행
sudo /usr/local/sbin/dreamseed-restore /path/to/backup/file.db
```

### 2. S3에서 복구
```bash
# S3에서 백업 파일 다운로드
aws s3 cp s3://your-bucket-name/dreamseed-backups/dreamseed_20240115_020000.db.gz /tmp/
aws s3 cp s3://your-bucket-name/dreamseed-backups/dreamseed_20240115_020000.db.gz.sha256 /tmp/

# 복구 실행
sudo /usr/local/sbin/dreamseed-restore /tmp/dreamseed_20240115_020000.db.gz
```

### 3. GPG 암호화된 파일 복구
```bash
# GPG 복호화
gpg --decrypt dreamseed_20240115_020000.db.gz.gpg > dreamseed_20240115_020000.db.gz

# 복구 실행
sudo /usr/local/sbin/dreamseed-restore dreamseed_20240115_020000.db.gz
```

## 🚨 문제 해결

### 1. 백업 실패
```bash
# 로그 확인
sudo journalctl -u dreamseed-backup-enhanced.service --since "1 hour ago"

# 수동 실행으로 오류 확인
sudo /usr/local/sbin/dreamseed-backup-enhanced
```

### 2. S3 업로드 실패
```bash
# AWS 자격 증명 확인
aws sts get-caller-identity --profile dreamseed-backup

# S3 권한 확인
aws s3 ls s3://your-bucket-name/ --profile dreamseed-backup
```

### 3. GPG 암호화 실패
```bash
# GPG 키 확인
gpg --list-secret-keys
gpg --list-public-keys

# GPG 키 테스트
echo "test" | gpg --encrypt --recipient your-email@example.com
```

### 4. 알림 실패
```bash
# Slack Webhook 테스트
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"테스트 메시지"}' \
  $SLACK_WEBHOOK_URL

# 이메일 테스트
echo "테스트 메시지" | mail -s "테스트" admin@dreamseed.com
```

## 📋 모니터링 대시보드

### 1. 주요 메트릭
- **백업 성공률**: 백업 작업 성공/실패 비율
- **백업 크기**: 백업 파일 크기 추이
- **백업 시간**: 백업 작업 소요 시간
- **S3 업로드 시간**: S3 업로드 소요 시간

### 2. 알림 규칙
- **백업 실패**: 백업 작업 실패 시 즉시 알림
- **백업 지연**: 24시간 이상 백업이 실행되지 않은 경우
- **디스크 공간 부족**: 백업 디렉토리 공간 부족
- **S3 업로드 실패**: S3 업로드 실패 시 알림

## 🔒 보안 고려사항

### 1. AWS 자격 증명 보안
- **IAM 역할 사용**: EC2 인스턴스에서 IAM 역할 사용 권장
- **최소 권한 원칙**: 필요한 S3 권한만 부여
- **자격 증명 로테이션**: 정기적인 액세스 키 교체

### 2. GPG 키 보안
- **개인키 보안**: 개인키는 안전한 위치에 보관
- **패스프레이즈**: 강력한 패스프레이즈 사용
- **키 백업**: 개인키를 안전한 곳에 백업

### 3. 알림 보안
- **Webhook URL 보안**: Slack Webhook URL을 안전하게 관리
- **이메일 암호화**: 민감한 정보는 암호화하여 전송

## 📞 지원 및 문의

- **기술 지원**: backup@dreamseed.com
- **문서**: https://docs.dreamseed.com/backup
- **GitHub Issues**: [백업 관련 이슈](https://github.com/dreamseed/platform/issues?q=label:backup)

---

*이 가이드는 DreamSeed AI Platform v1.0.0 기준으로 작성되었습니다.*
*최신 업데이트: 2024년 1월 15일*

