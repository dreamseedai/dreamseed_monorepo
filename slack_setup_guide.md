# Slack 채널 설정 가이드

## 📢 권장 채널 구조

### 1. **#dreamseed-ai-dev** (개발 채널)
- 모든 개발 관련 알림
- 코드 커밋, PR, 빌드 상태
- Background Agent 작업 진행 상황

### 2. **#curriculum-classification** (프로젝트 전용)
- 교과과정 분류 시스템 관련 논의
- 분류 결과 및 품질 지표
- 새로운 교육과정 표준 추가

### 3. **#system-alerts** (시스템 알림)
- 시스템 오류 및 경고
- 성능 이슈 알림
- 보안 관련 알림

## 🔧 Slack 봇 설정

### 1. **Cursor Bot 추가**
```
/invite @cursor-bot
```

### 2. **알림 설정**
```
/cursor notifications on
/cursor linear-sync on
/cursor background-agents on
```

### 3. **채널별 알림 설정**
```
#dreamseed-ai-dev: 모든 알림
#curriculum-classification: 프로젝트 관련만
#system-alerts: 오류 및 경고만
```

## 📊 대시보드 설정

### 1. **Slack Workflow Builder**
- Linear 이슈 생성 → Slack 알림
- 코드 커밋 → 자동 PR 생성
- 테스트 실패 → 버그 이슈 생성

### 2. **Slack Apps 추가**
- **Linear App**: Linear 이슈 직접 관리
- **GitHub App**: 코드 리뷰 및 PR 관리
- **Custom Bot**: Background Agent 상태 모니터링
