# DreamSeed 보안 정책 및 시크릿 관리 가이드

## 🔐 시크릿 관리 원칙

### 1. 절대 금지 사항
- ❌ `.env` 파일을 Git에 커밋하지 마세요
- ❌ 시크릿을 코드에 하드코딩하지 마세요
- ❌ 로그에 시크릿을 출력하지 마세요
- ❌ 프로덕션 시크릿을 개발 환경에서 사용하지 마세요

### 2. 환경별 시크릿 분리

```bash
# 개발 환경
.env.development

# 스테이징 환경
.env.staging

# 프로덕션 환경
.env.production  # 서버에만 존재, Git에 없음
```

### 3. .gitignore 설정

다음 파일들이 `.gitignore`에 포함되어 있는지 확인하세요:

```gitignore
# Environment variables
.env
.env.*
!.env.example

# Secrets
secrets/
*.pem
*.key
*.crt

# Database
*.db
*.sqlite

# Logs
*.log
logs/
```

## 🔑 시크릿 생성 방법

### JWT Secret 생성
```bash
# 안전한 랜덤 시크릿 생성
openssl rand -hex 32
```

### PostgreSQL 비밀번호 생성
```bash
# 32자 랜덤 비밀번호
openssl rand -base64 32
```

### SSH 키 생성 (서버 접속용)
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

## 🛡️ 프로덕션 시크릿 관리

### GitHub Secrets 사용
GitHub Actions에서 사용할 시크릿 등록:

1. Repository → Settings → Secrets and variables → Actions
2. New repository secret 클릭
3. 다음 시크릿 추가:

```
DATABASE_URL
REDIS_URL
JWT_SECRET
B2_APPLICATION_KEY_ID
B2_APPLICATION_KEY
SLACK_WEBHOOK_URL
CLOUDFLARE_API_TOKEN
```

### 서버에서 시크릿 관리

#### 방법 1: systemd 환경 변수
```bash
# /etc/systemd/system/dreamseed-api.service
[Service]
Environment="DATABASE_URL=postgresql://..."
Environment="JWT_SECRET=..."
EnvironmentFile=/etc/dreamseed/secrets.env
```

#### 방법 2: Docker Secrets
```bash
# Docker Swarm secrets 생성
echo "my_db_password" | docker secret create db_password -

# docker-compose.yml에서 사용
services:
  api:
    secrets:
      - db_password
```

## 🔍 시크릿 스캔

### 1. git-secrets 설치 및 설정
```bash
# macOS
brew install git-secrets

# Ubuntu
git clone https://github.com/awslabs/git-secrets
cd git-secrets
sudo make install

# Git 저장소에 설정
cd /path/to/dreamseed_monorepo
git secrets --install
git secrets --register-aws
```

### 2. 커밋 전 시크릿 체크
```bash
# 현재 변경 사항 스캔
git secrets --scan

# 전체 히스토리 스캔 (최초 1회)
git secrets --scan-history
```

### 3. pre-commit 훅 설정
```bash
# .git/hooks/pre-commit 파일 생성
cat > .git/hooks/pre-commit <<'HOOK'
#!/bin/bash
# 시크릿 스캔
git secrets --scan

# 패턴 검사
if git diff --cached | grep -iE '(password|secret|api[_-]?key|token).*=.*["\x27][^"\x27]{8,}'; then
    echo "❌ 시크릿이 포함된 것 같습니다. 커밋을 중단합니다."
    exit 1
fi

echo "✅ 시크릿 스캔 통과"
HOOK

chmod +x .git/hooks/pre-commit
```

## 🚨 시크릿 유출 시 대응

### 1. 즉시 조치
1. **회전 (Rotation)**: 유출된 시크릿을 즉시 새 값으로 변경
2. **취소 (Revocation)**: API 키/토큰 비활성화
3. **Git 히스토리 정리**: BFG Repo-Cleaner 사용

```bash
# BFG로 시크릿 제거
java -jar bfg.jar --replace-text passwords.txt dreamseed_monorepo.git
cd dreamseed_monorepo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 2. 영향 범위 확인
```bash
# 유출된 시크릿이 사용된 로그 확인
grep "SECRET_VALUE" /var/log/dreamseed/*.log

# 접근 로그 확인
tail -f /var/log/nginx/access.log
```

### 3. 보고 및 모니터링
- 보안 팀에 즉시 보고
- CloudWatch/Prometheus 알람 설정
- 비정상 접근 패턴 모니터링

## 🔐 비밀번호 정책

### 최소 요구 사항
- 길이: 최소 12자 이상
- 복잡도: 대문자, 소문자, 숫자, 특수문자 포함
- 만료: 90일마다 변경 (프로덕션)
- 재사용 금지: 최근 5개 비밀번호 재사용 불가

### 안전한 비밀번호 해싱
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # 충분한 해싱 라운드
)

# 해싱
hashed = pwd_context.hash("user_password")

# 검증
pwd_context.verify("user_password", hashed)
```

## 📋 체크리스트

Phase 0 배포 전 보안 체크리스트:

- [ ] `.env.example` 파일만 Git에 커밋됨 (실제 `.env`는 제외)
- [ ] `.gitignore`에 시크릿 관련 패턴 포함
- [ ] GitHub Secrets에 프로덕션 시크릿 등록
- [ ] JWT_SECRET이 32자 이상의 랜덤 값
- [ ] PostgreSQL 비밀번호가 강력함 (16자+)
- [ ] pre-commit 훅 설정 완료
- [ ] 개발/프로덕션 시크릿 분리 완료
- [ ] Slack 알림 웹훅 테스트 완료
- [ ] B2 API 키 권한 확인 (write only for backups)
- [ ] Cloudflare API 토큰 권한 최소화

## 🔗 관련 문서

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_CheatSheet.html)
- [12-Factor App: Config](https://12factor.net/config)
- [Git Secrets GitHub](https://github.com/awslabs/git-secrets)

---
**마지막 업데이트**: 2025-11-11  
**담당자**: DevOps Team
