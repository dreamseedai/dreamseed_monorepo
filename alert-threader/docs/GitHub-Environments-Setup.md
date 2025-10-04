# GitHub Environments 설정 가이드

이 문서는 GitHub Environments를 사용하여 CI/CD 파이프라인에 승인 게이트를 설정하는 방법을 설명합니다.

## 📋 목차

- [개요](#개요)
- [환경 생성](#환경-생성)
- [승인자 설정](#승인자-설정)
- [보호 규칙 설정](#보호-규칙-설정)
- [환경 시크릿 설정](#환경-시크릿-설정)
- [워크플로우 연동](#워크플로우-연동)
- [사용 예시](#사용-예시)

## 🎯 개요

GitHub Environments는 배포 환경을 관리하고 보호하는 기능입니다. 주요 특징:

- **환경별 시크릿 관리**: 각 환경마다 다른 시크릿 설정 가능
- **승인 게이트**: 프로덕션 배포 전 수동 승인 요구
- **보호 규칙**: 브랜치, 태그, 환경 변수 기반 배포 제한
- **배포 이력**: 환경별 배포 기록 및 상태 추적

## 🏗️ 환경 생성

### 1. Repository Settings 접근

1. GitHub 저장소로 이동
2. **Settings** 탭 클릭
3. 왼쪽 메뉴에서 **Environments** 클릭

### 2. 환경 생성

#### Staging 환경
```
Name: staging
Description: Staging environment for testing
```

#### Production 환경
```
Name: production
Description: Production environment
```

## 👥 승인자 설정

### Production 환경 승인자 설정

1. **production** 환경 클릭
2. **Required reviewers** 섹션에서 **Add people or teams** 클릭
3. 승인자 선택:
   - 개별 사용자
   - 팀
   - 최소 승인자 수 설정

### 예시 설정
```
Required reviewers: 2
Reviewers:
  - @won (개인)
  - @devops-team (팀)
```

## 🛡️ 보호 규칙 설정

### 1. Branch Protection Rules

#### Staging 환경
```
Branch protection: develop
- Require a pull request before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging
```

#### Production 환경
```
Branch protection: main
- Require a pull request before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Require linear history
- Include administrators
```

### 2. Environment Protection Rules

#### Production 환경 보호 규칙
```
Required reviewers: 2
Wait timer: 0 minutes
Deployment branches: main only
Environment secrets: All secrets required
```

## 🔐 환경 시크릿 설정

### Staging 환경 시크릿

1. **staging** 환경 클릭
2. **Environment secrets** 섹션에서 **Add secret** 클릭
3. 다음 시크릿 추가:

```
SSH_PRIVATE_KEY_STAGING
VAULT_ADDR_STAGING
VAULT_ROLE_ID_STAGING
VAULT_SECRET_ID_STAGING
SLACK_WEBHOOK_URL_STAGING
SLACK_BOT_TOKEN_STAGING
SLACK_CHANNEL_ID_STAGING
```

### Production 환경 시크릿

1. **production** 환경 클릭
2. **Environment secrets** 섹션에서 **Add secret** 클릭
3. 다음 시크릿 추가:

```
SSH_PRIVATE_KEY_PROD
VAULT_ADDR_PROD
VAULT_ROLE_ID_PROD
VAULT_SECRET_ID_PROD
SLACK_WEBHOOK_URL_PROD
SLACK_BOT_TOKEN_PROD
SLACK_CHANNEL_ID_PROD
```

## 🔗 워크플로우 연동

### 1. 환경 지정

워크플로우에서 환경을 지정하려면 `environment` 키를 사용:

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://dreamseedai.com
    steps:
      # 배포 단계
```

### 2. 승인 게이트 동작

환경에 승인자가 설정되어 있으면:

1. 워크플로우가 해당 환경에 도달
2. **Review deployments** 페이지에서 승인 대기
3. 승인자가 승인 또는 거부
4. 승인 후 워크플로우 계속 진행

## 📝 사용 예시

### 1. Canary + Blue-Green 배포

```yaml
name: Canary + Blue-Green
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options: ['staging', 'production']

jobs:
  bluegreen:
    needs: [guards, open_thread]
    environment:
      name: ${{ github.event.inputs.environment }}
      url: ${{ github.event.inputs.environment == 'production' && 'https://dreamseedai.com' || 'https://staging.dreamseedai.com' }}
    # ... 배포 단계
```

### 2. 환경별 조건부 실행

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    environment: staging
    # ... staging 배포

  deploy-production:
    if: github.ref == 'refs/heads/main'
    environment: production
    # ... production 배포
```

### 3. 승인 게이트가 있는 배포

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://dreamseedai.com
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # 실제 배포 명령
```

## 🔍 승인 프로세스

### 1. 배포 요청 시

1. 워크플로우가 production 환경에 도달
2. GitHub에서 승인자에게 이메일/알림 전송
3. **Actions** 탭에서 **Review deployments** 표시

### 2. 승인자 액션

1. **Actions** 탭으로 이동
2. **Review deployments** 클릭
3. 배포 세부사항 검토
4. **Approve and deploy** 또는 **Reject** 클릭

### 3. 승인 후

1. 워크플로우 계속 진행
2. 배포 완료 후 환경 URL 업데이트
3. 배포 이력에 기록

## 📊 환경 모니터링

### 1. 배포 이력 확인

1. **Environments** 페이지로 이동
2. 환경 클릭
3. **Deployment history** 섹션에서 이력 확인

### 2. 환경 상태

- **Active**: 최근 배포가 성공
- **Inactive**: 배포가 없거나 실패
- **Protected**: 보호 규칙이 적용됨

## 🚨 문제 해결

### 1. 승인 대기 중인 배포

```bash
# GitHub CLI로 승인 상태 확인
gh api repos/:owner/:repo/actions/runs/:run_id

# 승인 대기 중인 배포 목록
gh api repos/:owner/:repo/environments/:environment/deployments
```

### 2. 승인자 권한 문제

1. **Settings** → **Environments** → **production**
2. **Required reviewers** 확인
3. 사용자/팀 권한 검토

### 3. 시크릿 접근 문제

1. 환경별 시크릿 설정 확인
2. 워크플로우에서 올바른 환경 지정 확인
3. 시크릿 이름 대소문자 확인

## 🔧 고급 설정

### 1. 조건부 승인

```yaml
environment:
  name: production
  url: https://dreamseedai.com
  # 특정 브랜치에서만 승인 요구
  protection_rules:
    - type: required_reviewers
      required_reviewers: 2
      dismiss_stale_reviews: true
```

### 2. 환경 변수 기반 보호

```yaml
environment:
  name: production
  protection_rules:
    - type: required_reviewers
      required_reviewers: 2
    - type: wait_timer
      wait_timer: 5
```

### 3. 배포 브랜치 제한

```yaml
environment:
  name: production
  protection_rules:
    - type: deployment_branch_policy
      deployment_branch_policy:
        protected_branches: true
        custom_branch_policies: false
```

## 📚 추가 리소스

- [GitHub Environments 문서](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [환경 보호 규칙](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-protection-rules)
- [환경 시크릿](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-secrets)

---

**마지막 업데이트**: 2024년 12월  
**버전**: 1.0.0


