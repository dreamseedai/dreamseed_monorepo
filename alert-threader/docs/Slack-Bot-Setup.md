# Slack Bot Token 설정 가이드

이 문서는 CI/CD 파이프라인에서 Slack 스레드 알림을 사용하기 위한 Slack Bot Token 설정 방법을 설명합니다.

## 📋 목차

- [개요](#개요)
- [Slack App 생성](#slack-app-생성)
- [Bot Token 생성](#bot-token-생성)
- [권한 설정](#권한-설정)
- [채널 설정](#채널-설정)
- [CI/CD 연동](#cicd-연동)
- [테스트](#테스트)

## 🎯 개요

Slack Bot Token을 사용하면 다음과 같은 기능을 제공합니다:

- **스레드 알림**: 배포 과정을 하나의 스레드로 묶어 추적
- **Rich 메시지**: Block Kit을 사용한 풍부한 메시지 형식
- **실시간 업데이트**: 각 단계별 실시간 상태 업데이트
- **승인 알림**: GitHub Environments 승인 요청 알림

## 🤖 Slack App 생성

### 1. Slack API 페이지 접근

1. [Slack API](https://api.slack.com/) 웹사이트 방문
2. **Your Apps** 클릭
3. **Create New App** 클릭

### 2. App 생성

```
App Name: DreamSeed CI/CD Bot
Development Slack Workspace: [선택한 워크스페이스]
```

### 3. App 정보 설정

```
Description: CI/CD pipeline notifications and deployment tracking
App Icon: [CI/CD 관련 아이콘 업로드]
Background Color: #2EB67D
```

## 🔑 Bot Token 생성

### 1. OAuth & Permissions 설정

1. 왼쪽 메뉴에서 **OAuth & Permissions** 클릭
2. **Scopes** 섹션에서 **Bot Token Scopes** 추가

### 2. 필요한 권한 추가

```
chat:write          # 메시지 전송
chat:write.public   # 공개 채널에 메시지 전송
channels:read       # 채널 정보 읽기
groups:read         # 비공개 채널 정보 읽기
im:read             # DM 정보 읽기
mpim:read           # 멀티파티 DM 정보 읽기
```

### 3. Bot Token 생성

1. **Install to Workspace** 클릭
2. 권한 승인
3. **Bot User OAuth Token** 복사

```
예시: xoxb-1234567890123-1234567890123-abcdefghijklmnopqrstuvwx
```

## 🔐 권한 설정

### 1. 채널 권한 확인

Bot이 메시지를 전송할 채널에 다음 권한이 필요합니다:

```
#alerts-critical    # Critical 알림
#alerts-warning     # Warning 알림  
#alerts-info        # Info 알림
#devops             # DevOps 팀 채널
```

### 2. 채널에 Bot 초대

각 채널에서 다음 명령어 실행:

```
/invite @DreamSeed CI/CD Bot
```

또는 채널 설정에서 Bot 추가

## 📱 채널 설정

### 1. 채널 ID 확인

각 채널의 ID를 확인해야 합니다:

1. Slack에서 채널 클릭
2. 채널 이름 옆의 **...** 클릭
3. **Copy link** 클릭
4. URL에서 채널 ID 추출

```
예시: https://yourworkspace.slack.com/archives/C0123456789
채널 ID: C0123456789
```

### 2. 권장 채널 구조

```
#alerts-critical    # Critical 알림 (프로덕션 이슈)
#alerts-warning     # Warning 알림 (스테이징 이슈)
#alerts-info        # Info 알림 (일반 정보)
#devops             # DevOps 팀 채널
#deployments        # 배포 알림 (선택사항)
```

## 🔗 CI/CD 연동

### 1. GitHub Secrets 설정

Repository Settings → Secrets and variables → Actions에서 다음 시크릿 추가:

```
SLACK_BOT_TOKEN=xoxb-1234567890123-1234567890123-abcdefghijklmnopqrstuvwx
SLACK_CHANNEL_ID=C0123456789
```

### 2. GitLab CI Variables 설정

Settings → CI/CD → Variables에서 다음 변수 추가:

```
SLACK_BOT_TOKEN=xoxb-1234567890123-1234567890123-abcdefghijklmnopqrstuvwx
SLACK_CHANNEL_ID=C0123456789
```

### 3. 환경별 채널 설정

#### Staging 환경
```
SLACK_BOT_TOKEN_STAGING=xoxb-...
SLACK_CHANNEL_ID_STAGING=C0123456789
```

#### Production 환경
```
SLACK_BOT_TOKEN_PROD=xoxb-...
SLACK_CHANNEL_ID_PROD=C0987654321
```

## 🧪 테스트

### 1. 기본 연결 테스트

```bash
# Bot Token 유효성 확인
curl -H "Authorization: Bearer xoxb-your-token" \
  https://slack.com/api/auth.test

# 채널에 메시지 전송 테스트
curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer xoxb-your-token" \
  -H 'Content-Type: application/json' \
  --data '{"channel":"C0123456789","text":"Test message"}'
```

### 2. 스레드 메시지 테스트

```bash
# 부모 메시지 생성
PARENT_TS=$(curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer xoxb-your-token" \
  -H 'Content-Type: application/json' \
  --data '{"channel":"C0123456789","text":"Test thread parent"}' \
  | jq -r .ts)

# 스레드 답글 전송
curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer xoxb-your-token" \
  -H 'Content-Type: application/json' \
  --data "{\"channel\":\"C0123456789\",\"thread_ts\":\"$PARENT_TS\",\"text\":\"Test thread reply\"}"
```

### 3. CI/CD 파이프라인 테스트

1. 테스트 브랜치에서 워크플로우 실행
2. Slack 채널에서 스레드 메시지 확인
3. 각 단계별 답글 확인

## 🔧 고급 설정

### 1. Block Kit 메시지

더 풍부한 메시지를 위해 Block Kit 사용:

```json
{
  "channel": "C0123456789",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚀 Deployment Started"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Repository:*\n${{ github.repository }}"
        },
        {
          "type": "mrkdwn",
          "text": "*Branch:*\n${{ github.ref_name }}"
        }
      ]
    }
  ]
}
```

### 2. 조건부 알림

환경별로 다른 채널에 알림:

```yaml
- name: Send notification
  uses: ./.github/workflows/_slack_thread_reply.yml
  with:
    thread_ts: ${{ needs.open_thread.outputs.thread_ts }}
    text: "Deployment status: ${{ job.status }}"
    channel: ${{ github.event.inputs.environment == 'production' && secrets.SLACK_CHANNEL_PROD || secrets.SLACK_CHANNEL_STAGING }}
```

### 3. 알림 억제

특정 조건에서 알림 억제:

```yaml
- name: Send notification
  if: github.event_name != 'schedule'  # 스케줄된 워크플로우 제외
  uses: ./.github/workflows/_slack_thread_reply.yml
  with:
    thread_ts: ${{ needs.open_thread.outputs.thread_ts }}
    text: "Deployment status: ${{ job.status }}"
```

## 🚨 문제 해결

### 1. Bot Token 오류

```
Error: invalid_auth
```

**해결 방법:**
- Bot Token이 올바른지 확인
- Token이 만료되지 않았는지 확인
- Workspace에 올바르게 설치되었는지 확인

### 2. 채널 접근 권한 오류

```
Error: channel_not_found
```

**해결 방법:**
- 채널 ID가 올바른지 확인
- Bot이 채널에 초대되었는지 확인
- 채널이 존재하는지 확인

### 3. 권한 부족 오류

```
Error: missing_scope
```

**해결 방법:**
- 필요한 권한이 추가되었는지 확인
- Bot을 워크스페이스에 재설치
- 권한 변경 후 재승인

### 4. 스레드 메시지 전송 실패

**해결 방법:**
- `thread_ts`가 올바른지 확인
- 부모 메시지가 존재하는지 확인
- 채널 권한 확인

## 📊 모니터링

### 1. API 사용량 확인

Slack API 사용량을 모니터링하여 제한에 도달하지 않도록 주의:

1. [Slack API 사용량](https://api.slack.com/methods/api.test) 페이지 확인
2. Rate limit 모니터링
3. 필요시 요청 빈도 조정

### 2. 로그 모니터링

CI/CD 파이프라인에서 Slack API 호출 로그 확인:

```yaml
- name: Debug Slack response
  run: |
    echo "Slack response: $SLACK_RESP"
    echo "Thread TS: $THREAD_TS"
```

## 🔒 보안 고려사항

### 1. Token 보안

- Bot Token을 코드에 하드코딩하지 않음
- GitHub Secrets 또는 GitLab Variables 사용
- 정기적으로 Token 로테이션

### 2. 권한 최소화

- 필요한 최소 권한만 부여
- 불필요한 채널 접근 권한 제거
- 정기적인 권한 검토

### 3. 감사 로그

- Bot 활동 로그 모니터링
- 의심스러운 활동 감지
- 정기적인 액세스 검토

## 📚 추가 리소스

- [Slack API 문서](https://api.slack.com/)
- [Block Kit 가이드](https://api.slack.com/block-kit)
- [Bot Token 가이드](https://api.slack.com/authentication/token-types#bot)
- [Rate Limits](https://api.slack.com/docs/rate-limits)

---

**마지막 업데이트**: 2024년 12월  
**버전**: 1.0.0


