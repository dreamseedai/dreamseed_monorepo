# Slack Webhook URL 발급 상세 가이드# Slack Webhook URL 발급 상세 가이드# Slack Webhook URL 발급 상세 가이드



**대상**: Alertmanager Slack 알림 설정  

**소요 시간**: 5-10분  

**전제 조건**: Slack 워크스페이스 관리자 권한**대상**: Alertmanager Slack 알림 설정  **대상**: Alertmanager Slack 알림 설정  



---**소요 시간**: 5-10분  **소요 시간**: 5-10분  



## 📋 목차**전제 조건**: Slack 워크스페이스 관리자 권한**전제 조건**: Slack 워크스페이스 관리자 권한



1. [Slack App 생성](#1-slack-app-생성)

2. [Incoming Webhooks 설정](#2-incoming-webhooks-설정)

3. [채널별 Webhook URL 발급](#3-채널별-webhook-url-발급)------

4. [Webhook URL 테스트](#4-webhook-url-테스트)

5. [Kubernetes Secret 저장](#5-kubernetes-secret-저장)

6. [다중 채널 설정 (선택)](#6-다중-채널-설정-선택)

7. [보안 권장사항](#7-보안-권장사항)## 📋 목차## 📋 목차

8. [트러블슈팅](#8-트러블슈팅)



---

1. [Slack App 생성](#1-slack-app-생성)1. [Slack App 생성](#1-slack-app-생성)

## 1. Slack App 생성

2. [Incoming Webhooks 설정](#2-incoming-webhooks-설정)2. [Incoming Webhooks 설정](#2-incoming-webhooks-설정)

### 1-1. Slack API 콘솔 접속

3. [채널별 Webhook URL 발급](#3-채널별-webhook-url-발급)3. [채널별 Webhook URL 발급](#3-채널별-webhook-url-발급)

**URL**: https://api.slack.com/apps

4. [Webhook URL 테스트](#4-webhook-url-테스트)4. [Webhook URL 테스트](#4-webhook-url-테스트)

브라우저에서 Slack 계정으로 로그인합니다.

5. [Kubernetes Secret 저장](#5-kubernetes-secret-저장)5. [Kubernetes Secret 저장](#5-kubernetes-secret-저장)

### 1-2. 새 앱 생성 시작

6. [다중 채널 설정 (선택)](#6-다중-채널-설정-선택)6. [다중 채널 설정 (선택)](#6-다중-채널-설정-선택)

1. **Create New App** 버튼 클릭

7. [보안 권장사항](#7-보안-권장사항)7. [보안 권장사항](#7-보안-권장사항)

2. **From scratch** 선택

   - 템플릿 없이 새로 만들기를 선택합니다8. [트러블슈팅](#8-트러블슈팅)8. [트러블슈팅](#8-트러블슈팅)



### 1-3. Step 1 of 3 - 앱 이름 입력



**App Name** (필수):------

- 입력값: `Alertmanager`

- 또는 목적이 명확한 이름: `DreamSeedAI Alerts`, `Monitoring Alerts` 등



**권장 사항**:## 1. Slack App 생성## 1. Slack Webhook 발급

- 나중에 Slack 채널에서 메시지를 보낸 주체로 표시되는 이름입니다

- 팀원들이 쉽게 알아볼 수 있는 이름으로 지정하세요



**Next** 클릭### 1-1. Slack API 콘솔 접속### A. Slack 앱 생성 & Webhook 활성화



### 1-4. Step 2 of 3 - 워크스페이스 선택



**Pick a workspace to develop your app**:**URL**: https://api.slack.com/apps**필수 조건**: Slack 워크스페이스 관리자 권한

- 드롭다운에서 **DreamSeedAI** 워크스페이스 선택

- 알림을 받을 실제 워크스페이스를 선택합니다



**참고**:브라우저에서 Slack 계정으로 로그인합니다.#### Step 1: Slack 앱 생성

- 개발용/테스트용 워크스페이스가 따로 있다면 먼저 테스트 워크스페이스에서 연습해보세요

- 한 번 선택한 워크스페이스는 나중에 변경할 수 없으므로 신중히 선택하세요



**Next** 클릭### 1-2. 새 앱 생성1. **Slack API 페이지 접속**



### 1-5. Step 3 of 3 - 앱 검토 및 생성   ```



**이 화면에서 할 일**:1. **Create New App** 클릭   https://api.slack.com/apps



#### Workspace 확인   ```

- **DreamSeedAI**로 선택되어 있는지 확인

- 맞으면 그대로 두기2. **From scratch** 선택



#### 웹후크를 보낼 채널 (Post to channel)   - **App Name**: `Alertmanager` 입력2. **Create New App 클릭**

- 드롭다운에서 **기본으로 사용할 채널** 하나 선택

- 예시: `#seedtest-alerts` (알림 전용 채널)     - *권장 이름*: 목적이 명확한 이름 (예: `DreamSeedAI Alerts`)   - "From scratch" 선택

- 채널이 없다면:

  1. 드롭다운 하단 **"Create a channel"** 클릭      - App Name: `Alertmanager` (또는 원하는 이름)

  2. 새 채널 이름 입력 (예: `seedtest-alerts`)

  3. Public/Private 선택   - **Pick a workspace**: 워크스페이스 선택   - Workspace: 알림을 받을 워크스페이스 선택

  4. 생성 후 자동으로 선택됨

     - DreamSeedAI 워크스페이스 선택   - **Create App** 클릭

**참고**:

- 이 단계는 **초기 기본 포스트 채널**만 정하는 것입니다   

- 나중에 다른 채널용 Webhook을 추가로 만들 수 있습니다

   - **Create App** 클릭#### Step 2: Incoming Webhooks 활성화

#### Review app permissions

- 권한 목록에 **Incoming Webhooks**만 보이면 정상입니다

- 추가 입력은 필요 없습니다

3. **앱 생성 완료**1. **좌측 메뉴에서 "Features" → "Incoming Webhooks" 선택**

#### 승인 화면 (워크스페이스 정책에 따라 표시)

- 워크스페이스 정책에 따라 **"Allow"** (허용) 화면이 나올 수 있습니다   - 앱 상세 화면으로 자동 이동

- **Allow** 버튼을 클릭하세요

   - 좌측 메뉴에서 다양한 설정 가능2. **Activate Incoming Webhooks → ON 전환**

#### 앱 생성 완료

- **Create** 또는 **Create App** 버튼 클릭

- 앱 생성이 완료되면 **앱 설정 화면**으로 자동 이동합니다

### 1-3. 앱 아이콘 설정 (선택)3. **Add New Webhook to Workspace 클릭**

### 1-6. 앱 아이콘 설정 (선택 사항)



앱 생성 후 **Basic Information** 페이지에서:

**좌측 메뉴**: Settings → **Basic Information**4. **채널 선택**

**좌측 메뉴**: Settings → **Basic Information**

   - `#seedtest-alerts` (Critical/Warning 알림용)

**Display Information** 섹션:

- **App icon**: 알림 메시지에 표시될 아이콘 업로드**Display Information** 섹션:   - **Allow** 클릭

  - 권장 크기: 512x512px PNG

  - 예시: Alertmanager 로고, 회사 로고, 🚨 이모지 이미지- **App icon**: 알림 메시지에 표시될 아이콘 업로드



**저장**: **Save Changes** 클릭  - 권장: 512x512px PNG5. **Webhook URL 복사**



---  - 예시: Alertmanager 로고, 회사 로고   ```



## 2. Incoming Webhooks 설정   형식: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX



앱을 생성한 후에야 실제 Webhook URL을 발급할 수 있습니다.**저장**: **Save Changes** 클릭   ```



### 2-1. Incoming Webhooks 페이지 이동



**좌측 메뉴**: Features → **Incoming Webhooks** 클릭---#### Step 3: 추가 채널 Webhook 생성 (선택)



### 2-2. Incoming Webhooks 활성화



**Activate Incoming Webhooks**:## 2. Incoming Webhooks 설정**저우선 알림용 채널**:

- 우측 상단의 스위치를 **OFF** → **ON** 으로 전환

- 페이지가 새로고침되면서 하단에 **Webhook URLs for Your Workspace** 섹션이 나타납니다- "Add New Webhook to Workspace" 다시 클릭



### 2-3. 권한 확인 (자동)### 2-1. Incoming Webhooks 활성화- `#seedtest-notify` 선택



Incoming Webhooks 활성화 시 자동으로 부여되는 권한:- 두 번째 Webhook URL 복사

- `incoming-webhook`: 특정 채널에 메시지 게시

**좌측 메뉴**: Features → **Incoming Webhooks**

**참고**: 

- 추가 권한 설정은 필요 없습니다**참고**: 

- OAuth & Permissions 페이지에서 확인 가능합니다

**Activate Incoming Webhooks**:- Webhook은 채널당 하나씩 발급됩니다

---

- 스위치를 **OFF** → **ON** 전환- 동일한 Webhook URL을 여러 채널에 공유할 수 있지만, 채널별 분리 권장

## 3. 채널별 Webhook URL 발급

- 페이지 새로고침 시 **Webhook URLs** 섹션 표시- Private 채널의 경우 Webhook App을 채널에 초대해야 합니다

### 3-1. 첫 번째 Webhook 생성



**Webhook URLs for Your Workspace** 섹션에서:

### 2-2. 권한 확인 (자동)---

1. **Add New Webhook to Workspace** 버튼 클릭



2. **채널 선택 화면 표시**:

   - Slack이 권한 요청 페이지를 표시합니다Incoming Webhooks 활성화 시 자동으로 부여되는 권한:## 2. PagerDuty Routing Key 발급

   - **"Where should [앱 이름] post?"** 메시지가 보입니다

- `incoming-webhook`: 채널에 메시지 게시

3. **채널 선택**:

   - 검색창에 `#seedtest-alerts` 입력하여 검색### A. PagerDuty Service Integration 생성

   - 또는 드롭다운에서 직접 선택

   - 채널이 없으면 **"Create a channel"** 클릭하여 즉시 생성**참고**: 추가 권한 설정 불필요 (OAuth & Permissions에서 확인 가능)



4. **Allow** (허용) 버튼 클릭**필수 조건**: PagerDuty 계정 및 Service 생성 권한

   - Slack이 Webhook URL을 생성하고 앱을 채널에 추가합니다

---

5. **Webhook URL 생성 완료**:

   ```#### Step 1: Service 선택 또는 생성

   형식: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

   ## 3. 채널별 Webhook URL 발급

   구성:

   - T00000000: 워크스페이스 ID1. **PagerDuty 로그인**

   - B00000000: Webhook ID

   - XXXXXXXXXXXXXXXXXXXXXXXX: Secret Token### 3-1. 첫 번째 Webhook 생성   ```

   ```

   https://yourcompany.pagerduty.com

6. **Webhook URL 복사**:

   - **Copy** 버튼 클릭**Webhook URLs for Your Workspace** 섹션:   ```

   - 메모장이나 안전한 곳에 **임시 저장**

   - ⚠️ **절대 Git에 커밋하지 마세요!**



### 3-2. Webhook URL 형식 확인1. **Add New Webhook to Workspace** 클릭2. **Services → Service Directory**



**유효한 Webhook URL**:

```

✅ https://hooks.slack.com/services/T.../B.../XXX...2. **채널 선택 화면**:3. **기존 서비스 선택 또는 "New Service" 생성**

```

   - **채널 검색**: `#seedtest-alerts` 검색 또는 선택   - Service Name: `seedtest-api` (또는 원하는 이름)

**잘못된 URL** (사용 불가):

```   - 없으면 **Create a channel** 클릭하여 새로 생성   - Escalation Policy: 알림 받을 정책 선택

❌ https://api.slack.com/...

❌ https://slack.com/oauth/...      - **Create Service** 클릭

```

3. **Allow** (허용) 클릭

### 3-3. Private 채널에 Webhook 추가

#### Step 2: Events API v2 Integration 추가

**Private 채널을 선택한 경우 추가 단계 필요**:

4. **Webhook URL 생성 완료**:

1. Webhook URL 발급 완료 후

   ```1. **Service 페이지에서 "Integrations" 탭 클릭**

2. **Slack 데스크톱/웹 앱에서 해당 Private 채널 열기**

   형식: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

3. **채널 상세 정보**:

   - 채널 이름 옆 **드롭다운 (∨)** 클릭   2. **Add Integration 클릭**

   - 또는 우측 상단 **⚙️ (설정)** 아이콘 클릭

   구성:

4. **Integrations** 탭 선택

   - T00000000: 워크스페이스 ID3. **Integration 검색**

5. **Add apps** 클릭

   - B00000000: Webhook ID   - 검색어: `Events API v2` 입력

6. **검색창에 앱 이름 입력**:

   - `Alertmanager` 또는 생성한 앱 이름 검색   - XXXXXXXXXXXXXXXXXXXXXXXX: Secret Token   - **Events API v2** 선택 (⚠️ v1이 아닌 v2 확인!)



7. **Add** 버튼 클릭   ```



**확인**:4. **Add** 클릭

- 채널에 "[앱 이름] added an integration to this channel" 메시지가 표시되면 성공

- Private 채널에서도 이제 Webhook 메시지를 받을 수 있습니다5. **Webhook URL 복사**:



---   - **Copy** 버튼 클릭5. **Integration Key (=Routing Key) 복사**



## 4. Webhook URL 테스트   - 메모장이나 안전한 곳에 임시 저장   ```



### 4-1. cURL 테스트 (권장)   형식: R00000000000000000000000000000000 (32자 영숫자)



**터미널에서 실행**:### 3-2. Webhook URL 형식 확인   ```



```bash

# Webhook URL을 환경변수로 설정 (실제 URL로 교체)

export SLACK_WEBHOOK='https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'**유효한 Webhook URL**:**중요 체크사항**:



# 간단한 메시지 전송```- ✅ Integration Name이 "Events API v2"인지 확인

curl -X POST -H 'Content-type: application/json' \

  --data '{"text":"🧪 [TEST] Alertmanager Webhook 연결 확인"}' \✅ https://hooks.slack.com/services/T.../B.../XXX...- ✅ Integration Key 길이가 32자인지 확인

  "$SLACK_WEBHOOK"

``````- ❌ Generic API v1 키는 사용 불가



**성공 응답**:

```

ok**잘못된 URL** (사용 불가):---

```

```

**Slack 채널 확인**:

- 지정한 채널에 테스트 메시지가 게시되면 ✅ 성공❌ https://api.slack.com/...## 3. Kubernetes Secret 생성



### 4-2. 서식 있는 메시지 테스트❌ https://slack.com/oauth/...



```bash```### Option A: 자동화 스크립트 사용 (권장)

curl -X POST -H 'Content-type: application/json' \

  --data '{

    "text": "🚨 Alertmanager 테스트",

    "attachments": [### 3-3. Private 채널에 Webhook 추가```bash

      {

        "color": "#FF0000",# 발급받은 키를 사용하여 Secret 생성

        "title": "Critical Alert",

        "text": "This is a test alert from Alertmanager",**Private 채널 선택 시 추가 단계**:bash infra/monitoring/alertmanager/setup-secrets.sh monitoring \

        "footer": "Alertmanager",

        "ts": 1699437600  'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX' \

      }

    ]1. Webhook URL 발급 완료 후  'R00000000000000000000000000000000'

  }' \

  "$SLACK_WEBHOOK"

```

2. **Slack 앱에서 해당 채널 열기**# 출력 예시:

**Slack 채널 확인**:

- 빨간색 attachment가 포함된 서식 있는 메시지가 표시됩니다# ✅ Secret 생성: alertmanager-secrets



### 4-3. 실패 응답 처리3. **채널 상세**: 우측 상단 ⚙️ (설정) 클릭#    키: slack_webhook_url



**오류 메시지 예시**:#    마운트 경로: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url



```json4. **Integrations** 탭 → **Add apps**# ✅ Secret 생성: pagerduty-routing-key

{

  "ok": false,#    키: routing_key

  "error": "invalid_token"

}5. **Alertmanager** 앱 검색 → **Add** 클릭#    마운트 경로: /etc/alertmanager/secrets/pagerduty-routing-key/routing_key

```

```

**원인**:

- Webhook URL이 잘못됨 (복사 오류)**확인**: 채널에 "Alertmanager added an integration to this channel" 메시지 표시

- Webhook가 삭제/비활성화됨

- 채널이 삭제됨### Option B: kubectl 직접 사용



**해결**:---

1. Slack API 콘솔에서 Webhook URL 재확인

2. 필요 시 Webhook 삭제 후 재생성 (섹션 3 참고)#### Slack Webhook Secret 생성



---## 4. Webhook URL 테스트



## 5. Kubernetes Secret 저장```bash



### 5-1. Secret 생성 (자동화 스크립트 권장)### 4-1. cURL 테스트 (권장)kubectl -n monitoring create secret generic alertmanager-secrets \



**권장 방법**:  --from-literal=slack_webhook_url='https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX'



```bash**터미널에서 실행**:

# setup-secrets.sh 스크립트 사용

cd infra/monitoring/alertmanager# 확인



bash setup-secrets.sh monitoring \```bashkubectl -n monitoring get secret alertmanager-secrets -o yaml

  'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'

```# Webhook URL을 환경변수로 설정```



**스크립트 동작**:export SLACK_WEBHOOK='https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'

1. 기존 Secret 존재 시 삭제

2. 새 Secret 생성 (`alertmanager-secrets`)#### PagerDuty Routing Key Secret 생성

3. Webhook URL을 `slack_webhook_url` 키로 base64 인코딩하여 저장

4. Secret 생성 확인 메시지 출력# 간단한 메시지 전송



### 5-2. Secret 직접 생성 (수동)curl -X POST -H 'Content-type: application/json' \```bash



```bash  --data '{"text":"🧪 [TEST] Alertmanager Webhook 연결 확인"}' \kubectl -n monitoring create secret generic pagerduty-routing-key \

kubectl -n monitoring create secret generic alertmanager-secrets \

  --from-literal=slack_webhook_url='https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'  "$SLACK_WEBHOOK"  --from-literal=routing_key='R00000000000000000000000000000000'

```

```

### 5-3. Secret 확인

# 확인

```bash

# Secret 존재 확인**성공 응답**:kubectl -n monitoring get secret pagerduty-routing-key -o yaml

kubectl -n monitoring get secret alertmanager-secrets

``````

# Webhook URL 복호화 확인 (base64 디코딩)

kubectl -n monitoring get secret alertmanager-secrets \ok

  -o jsonpath='{.data.slack_webhook_url}' | base64 -d

``````### Option C: External Secrets Operator (프로덕션 권장)



**예상 출력**:

```

https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX**Slack 채널 확인**:```yaml

```

- 메시지가 게시되면 ✅ 성공# external-secret-slack.yaml

### 5-4. Secret 보안 강화 (프로덕션 권장)

apiVersion: external-secrets.io/v1beta1

#### 방법 1: SealedSecrets 사용

### 4-2. 서식 있는 메시지 테스트kind: ExternalSecret

```bash

# kubeseal 설치 (macOS)metadata:

brew install kubeseal

```bash  name: alertmanager-secrets

# Secret 암호화 (Git에 커밋 가능)

kubectl -n monitoring create secret generic alertmanager-secrets \curl -X POST -H 'Content-type: application/json' \  namespace: monitoring

  --from-literal=slack_webhook_url='YOUR_WEBHOOK_URL' \

  --dry-run=client -o yaml | \  --data '{spec:

  kubeseal -o yaml > sealed-secret.yaml

    "text": "🚨 Alertmanager 테스트",  refreshInterval: 1h

# Git에 안전하게 커밋

git add sealed-secret.yaml    "attachments": [  secretStoreRef:

git commit -m "chore: add sealed Slack webhook secret"

```      {    name: vault-backend



#### 방법 2: External Secrets Operator (ESO)        "color": "#FF0000",    kind: SecretStore



```yaml        "title": "Critical Alert",  target:

# external-secret-slack.yaml

apiVersion: external-secrets.io/v1beta1        "text": "This is a test alert from Alertmanager",    name: alertmanager-secrets

kind: ExternalSecret

metadata:        "footer": "Alertmanager",    creationPolicy: Owner

  name: alertmanager-secrets

  namespace: monitoring        "ts": 1699437600  data:

spec:

  refreshInterval: 1h      }    - secretKey: slack_webhook_url

  secretStoreRef:

    name: vault-backend    ]      remoteRef:

    kind: SecretStore

  target:  }' \        key: alertmanager/slack

    name: alertmanager-secrets

    creationPolicy: Owner  "$SLACK_WEBHOOK"        property: webhook_url

  data:

    - secretKey: slack_webhook_url``````

      remoteRef:

        key: alertmanager/slack

        property: webhook_url

```**Slack 채널 확인**:```yaml



**적용**:- 빨간색 attachment가 포함된 메시지 표시# external-secret-pagerduty.yaml

```bash

kubectl apply -f external-secret-slack.yamlapiVersion: external-secrets.io/v1beta1

```

### 4-3. 실패 응답 처리kind: ExternalSecret

---

metadata:

## 6. 다중 채널 설정 (선택)

**오류 메시지 예시**:  name: pagerduty-routing-key

다른 채널로도 알림을 보내려면 Webhook을 추가로 만들어 각 채널과 연결하세요.

  namespace: monitoring

### 6-1. 추가 채널용 Webhook 발급

```jsonspec:

**여러 채널로 알림을 보내려면**:

{  refreshInterval: 1h

1. **Slack API 콘솔** → Features → Incoming Webhooks 화면

  "ok": false,  secretStoreRef:

2. **Add New Webhook to Workspace** 버튼 다시 클릭

  "error": "invalid_token"    name: vault-backend

3. **다른 채널 선택**:

   - `#seedtest-critical` (Critical 알림 전용)}    kind: SecretStore

   - `#seedtest-warnings` (Warning 알림 전용)

   - `#ops-alerts` (운영팀 전용)```  target:



4. **Allow** 클릭 → 새 Webhook URL 발급됨    name: pagerduty-routing-key



5. 각 Webhook URL을 복사하여 별도로 저장**원인**:    creationPolicy: Owner



### 6-2. 다중 Webhook Secret 저장- Webhook URL이 잘못됨  data:



#### 방법 1: 여러 Secret 생성- Webhook가 비활성화됨    - secretKey: routing_key



```bash- 채널이 삭제됨      remoteRef:

# Critical 전용

kubectl -n monitoring create secret generic slack-critical-webhook \        key: alertmanager/pagerduty

  --from-literal=url='https://hooks.slack.com/services/T.../B1.../XXX...'

**해결**:        property: routing_key

# Warning 전용

kubectl -n monitoring create secret generic slack-warning-webhook \1. Slack API 콘솔에서 Webhook URL 재확인```

  --from-literal=url='https://hooks.slack.com/services/T.../B2.../YYY...'

```2. 필요 시 Webhook 삭제 후 재생성



#### 방법 2: 단일 Secret에 여러 키 저장 (권장)---



```bash---

kubectl -n monitoring create secret generic alertmanager-secrets \

  --from-literal=slack_webhook_critical='https://hooks.slack.com/services/T.../B1.../XXX...' \## 4. 동작 확인

  --from-literal=slack_webhook_warning='https://hooks.slack.com/services/T.../B2.../YYY...' \

  --from-literal=slack_webhook_info='https://hooks.slack.com/services/T.../B3.../ZZZ...'## 5. Kubernetes Secret 저장

```

### A. Slack Webhook 단독 테스트 (직접 호출)

### 6-3. Alertmanager 설정 업데이트

### 5-1. Secret 생성 (자동화 스크립트)

**alertmanager-cr.yaml**:

```bash

```yaml

receivers:**권장 방법**:# Webhook URL 테스트

  - name: 'slack-critical'

    slack_configs:curl -X POST -H 'Content-type: application/json' \

      - channel: '#seedtest-critical'

        send_resolved: true```bash  --data '{"text":"[TEST] Alertmanager Slack Webhook 연결 확인"}' \

        api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_critical

        color: 'danger'# setup-secrets.sh 스크립트 사용  'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX'

        title: '🚨 {{ .GroupLabels.alertname }}'

cd infra/monitoring/alertmanager

  - name: 'slack-warning'

    slack_configs:# 성공 시 응답: ok

      - channel: '#seedtest-warnings'

        send_resolved: truebash setup-secrets.sh monitoring \# 실패 시: invalid_token, channel_not_found 등

        api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_warning

        color: 'warning'  'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'```

        title: '⚠️ {{ .GroupLabels.alertname }}'

```

route:

  routes:**확인 사항**:

    - receiver: 'slack-critical'

      match:**스크립트 동작**:- ✅ 지정한 Slack 채널에 메시지 수신 확인

        severity: critical

    1. 기존 Secret 존재 시 삭제- ✅ 응답 코드 200 확인

    - receiver: 'slack-warning'

      match:2. 새 Secret 생성 (`alertmanager-secrets`)

        severity: warning

```3. Webhook URL을 `slack_webhook_url` 키로 저장### B. PagerDuty Events API v2 단독 테스트



---4. Secret 생성 확인



## 7. 보안 권장사항```bash



### 7-1. Webhook URL 보안### 5-2. Secret 직접 생성# PagerDuty Events API 테스트



#### 절대 금지 ❌curl -X POST 'https://events.pagerduty.com/v2/enqueue' \



- ❌ Git에 Webhook URL 평문 저장```bash  -H 'Content-Type: application/json' \

- ❌ 공개 문서/README에 URL 노출

- ❌ 로그에 URL 출력kubectl -n monitoring create secret generic alertmanager-secrets \  -d '{

- ❌ 슬랙 메시지/이메일로 URL 공유

  --from-literal=slack_webhook_url='https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'    "routing_key": "R00000000000000000000000000000000",

#### 권장 사항 ✅

```    "event_action": "trigger",

- ✅ Kubernetes Secret 사용

- ✅ SealedSecrets 또는 ESO로 암호화    "payload": {

- ✅ 환경변수로만 전달

- ✅ Secret 값은 base64 인코딩 상태로 유지### 5-3. Secret 확인      "summary": "TEST – Alertmanager PagerDuty 연결 확인",

- ✅ RBAC으로 Secret 접근 제한

      "severity": "critical",

### 7-2. Webhook URL 회전 (Rotation)

```bash      "source": "seedtest-api",

#### 언제 회전하나요?

# Secret 존재 확인      "component": "manual-test",

- 유출 의심 시 (즉시)

- 정기 보안 감사 (연 1회 권장)kubectl -n monitoring get secret alertmanager-secrets      "group": "monitoring",

- 담당자 변경 시

- 보안 정책 변경 시      "class": "test"



#### 회전 절차# Webhook URL 복호화 확인    }



1. **Slack API 콘솔** → Features → Incoming Webhookskubectl -n monitoring get secret alertmanager-secrets \  }'



2. **기존 Webhook 삭제**:  -o jsonpath='{.data.slack_webhook_url}' | base64 -d

   - 해당 Webhook URL 옆 **Remove** 또는 **Delete** 클릭

   - 확인 대화상자에서 **Delete** 클릭```# 성공 응답:



3. **새 Webhook 발급**:# {"status":"success","message":"Event processed","dedup_key":"..."}

   - **Add New Webhook to Workspace** 클릭

   - 동일한 채널 선택**예상 출력**:

   - **Allow** 클릭

```# 실패 응답:

4. **Kubernetes Secret 업데이트**:

   ```bashhttps://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX# {"status":"invalid","message":"Invalid routing_key","errors":["..."]}

   # Secret 삭제

   kubectl -n monitoring delete secret alertmanager-secrets``````

   

   # 새 Secret 생성

   kubectl -n monitoring create secret generic alertmanager-secrets \

     --from-literal=slack_webhook_url='NEW_WEBHOOK_URL'### 5-4. Secret 보안 강화 (선택)**확인 사항**:

   ```

- ✅ 응답 status가 "success"인지 확인

5. **Alertmanager Pod 재시작**:

   ```bash**SealedSecrets 사용**:- ✅ PagerDuty Service → Incidents 페이지에서 새 인시던트 생성 확인

   kubectl -n monitoring rollout restart statefulset alertmanager

   ```- ✅ dedup_key 값 받음 확인



6. **테스트**:```bash

   ```bash

   curl -X POST "$NEW_WEBHOOK_URL" \# kubeseal 설치 (macOS)### C. Alertmanager를 통한 종단 테스트 (amtool)

     -H 'Content-type: application/json' \

     -d '{"text":"🔄 Webhook 회전 완료 테스트"}'brew install kubeseal

   ```

#### 1️⃣ Alertmanager 포트포워드

7. **Slack 채널에서 메시지 수신 확인**

# Secret 암호화

### 7-3. 접근 제한

kubectl -n monitoring create secret generic alertmanager-secrets \```bash

#### Slack 워크스페이스 설정

  --from-literal=slack_webhook_url='YOUR_WEBHOOK_URL' \# Alertmanager Pod 이름 가져오기

- Admin → Settings & permissions → Permissions

- **App Management**: Restrict to admins  --dry-run=client -o yaml | \ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')

- 앱 설치/삭제 권한을 관리자로 제한

  kubeseal -o yaml > sealed-secret.yaml

#### Kubernetes RBAC

# 포트포워드 (백그라운드)

```yaml

apiVersion: v1# Git에 커밋 가능kubectl -n monitoring port-forward "$ALERTM" 9093:9093 >/dev/null 2>&1 &

kind: Role

metadata:git add sealed-secret.yaml

  name: alertmanager-secret-reader

  namespace: monitoring```# UI 접속 확인

rules:

  - apiGroups: [""]open http://127.0.0.1:9093

    resources: ["secrets"]

    resourceNames: ["alertmanager-secrets"]**External Secrets Operator (ESO)**:```

    verbs: ["get"]

---

apiVersion: v1

kind: RoleBinding```yaml#### 2️⃣ Critical → PagerDuty 라우팅 테스트

metadata:

  name: alertmanager-secret-bindingapiVersion: external-secrets.io/v1beta1

  namespace: monitoring

roleRef:kind: ExternalSecret```bash

  apiGroup: rbac.authorization.k8s.io

  kind: Rolemetadata:amtool --alertmanager.url=http://127.0.0.1:9093 alert add \

  name: alertmanager-secret-reader

subjects:  name: alertmanager-secrets  alertname=SeedtestRouteTest \

  - kind: ServiceAccount

    name: alertmanager  namespace: monitoring  service=seedtest-api \

    namespace: monitoring

```spec:  severity=critical \



---  secretStoreRef:  summary="[TEST] PagerDuty 라우팅 확인" \



## 8. 트러블슈팅    name: vault-backend  description="이 알림은 pagerduty-seedtest receiver로 라우팅되어야 합니다"



### 8-1. Webhook URL이 작동하지 않음    kind: SecretStore



**증상**:  target:# 확인:

```

curl: (22) The requested URL returned error: 404    name: alertmanager-secrets# 1. Alertmanager UI → Alerts에서 firing 상태 확인

```

  data:# 2. PagerDuty Incidents에서 새 인시던트 생성 확인 (30초 이내)

**원인 & 해결**:

    - secretKey: slack_webhook_url```

#### 1. URL 형식 확인

```bash      remoteRef:

# ✅ 올바른 형식

https://hooks.slack.com/services/T.../B.../XXX...        key: alertmanager/slack#### 3️⃣ Warning → Slack 라우팅 테스트



# ❌ 잘못된 형식 (OAuth URL)        property: webhook_url

https://slack.com/api/oauth.v2.access

`````````bash



#### 2. Webhook 비활성화 확인amtool --alertmanager.url=http://127.0.0.1:9093 alert add \

- Slack API 콘솔 → Incoming Webhooks

- Webhook URLs 목록에서 해당 URL이 있는지 확인---  alertname=SeedtestRouteTest \

- 없으면 삭제된 것이므로 재발급 (섹션 3 참고)

  service=seedtest-api \

#### 3. 워크스페이스 변경 확인

- 워크스페이스를 전환했다면 해당 워크스페이스에서 새로 발급## 6. 다중 채널 설정 (선택)  severity=warning \



### 8-2. Private 채널에 메시지 안 보임  summary="[TEST] Slack 라우팅 확인" \



**증상**:### 6-1. 추가 채널용 Webhook 발급  description="이 알림은 slack-seedtest receiver (#seedtest-alerts)로 라우팅되어야 합니다"

```

ok  # 응답은 성공이지만 채널에 메시지가 보이지 않음

```

**여러 채널로 알림을 보내려면**:# 확인:

**해결**:

# 1. Alertmanager UI → Alerts에서 firing 상태 확인

#### 1. Slack 앱을 채널에 초대

```1. **Slack API 콘솔** → Incoming Webhooks 화면# 2. Slack #seedtest-alerts 채널에서 메시지 수신 확인 (30초 이내)

# Private 채널에서 실행

/invite @Alertmanager```

```

2. **Add New Webhook to Workspace** 클릭

#### 2. 채널 멤버 확인

- 채널 상세 정보 → Integrations 탭#### 4️⃣ Info → Slack 저우선 라우팅 테스트

- Alertmanager 앱이 목록에 있어야 함

- 없으면 **Add apps** → 앱 검색 → **Add**3. **다른 채널 선택**:



### 8-3. Kubernetes Secret 마운트 실패   - `#seedtest-critical` (Critical 전용)```bash



**증상**:   - `#seedtest-warnings` (Warning 전용)amtool --alertmanager.url=http://127.0.0.1:9093 alert add \

```bash

kubectl -n monitoring logs alertmanager-0   - `#ops-alerts` (운영팀)  alertname=SeedtestRouteTest \

# Error: secrets "alertmanager-secrets" not found

```  namespace=seedtest \



**해결**:4. **Allow** 클릭 → 새 Webhook URL 발급  severity=info \



#### 1. Secret 존재 확인  summary="[TEST] Slack 저우선 라우팅 확인" \

```bash

kubectl -n monitoring get secret alertmanager-secrets### 6-2. 다중 Webhook Secret 저장  description="이 알림은 slack-lowprio receiver (#seedtest-notify)로 라우팅되어야 합니다"



# Secret이 없으면 NAME 열에 아무것도 안 나옴

```

**방법 1: 여러 Secret 생성**# 확인:

#### 2. Secret 재생성

```bash# 1. Alertmanager UI → Alerts에서 firing 상태 확인

bash setup-secrets.sh monitoring 'YOUR_WEBHOOK_URL'

``````bash# 2. Slack #seedtest-notify 채널에서 메시지 수신 확인 (30초 이내)



#### 3. Alertmanager CR 확인# Critical 전용```

```bash

kubectl -n monitoring get alertmanager main -o yaml | grep -A 5 secretskubectl -n monitoring create secret generic slack-critical-webhook \

```

  --from-literal=url='https://hooks.slack.com/services/T.../B1.../XXX...'#### 5️⃣ Alert 삭제 (테스트 종료)

**예상 출력**:

```yaml

spec:

  secrets:# Warning 전용```bash

    - alertmanager-secrets  # Secret 이름이 정확히 일치해야 함

```kubectl -n monitoring create secret generic slack-warning-webhook \# 모든 테스트 알림 삭제



#### 4. Pod 재시작  --from-literal=url='https://hooks.slack.com/services/T.../B2.../YYY...'amtool --alertmanager.url=http://127.0.0.1:9093 silence add \

```bash

kubectl -n monitoring rollout restart statefulset alertmanager```  alertname=SeedtestRouteTest \

```

  --duration=1m \

### 8-4. Webhook URL이 Secret에 없음

**방법 2: 단일 Secret에 여러 키**  --author="test" \

**증상**:

```bash  --comment="테스트 종료"

kubectl -n monitoring exec alertmanager-0 -- \

  cat /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url```bash

# cat: can't open '/etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url': No such file or directory

```kubectl -n monitoring create secret generic alertmanager-secrets \# 또는 Alertmanager UI에서 수동 삭제



**해결**:  --from-literal=slack_webhook_critical='https://hooks.slack.com/services/T.../B1.../XXX...' \# http://127.0.0.1:9093/#/alerts → 각 Alert 클릭 → Silence



#### 1. Secret 데이터 키 확인  --from-literal=slack_webhook_warning='https://hooks.slack.com/services/T.../B2.../YYY...' \```

```bash

kubectl -n monitoring get secret alertmanager-secrets -o yaml  --from-literal=slack_webhook_info='https://hooks.slack.com/services/T.../B3.../ZZZ...'

```

```---

**data 섹션 확인**:

```yaml

data:

  slack_webhook_url: aHR0cHM6Ly9ob29rcy5zbGFjay5jb20v...  # base64 인코딩됨### 6-3. Alertmanager 설정 업데이트## 5. 키 회전 (운영 절차)

```



#### 2. 키 이름 불일치 시 재생성

```bash**alertmanager-cr.yaml**:### A. Slack Webhook 회전

kubectl -n monitoring delete secret alertmanager-secrets



kubectl -n monitoring create secret generic alertmanager-secrets \

  --from-literal=slack_webhook_url='YOUR_WEBHOOK_URL'```yaml#### Step 1: 새 Webhook 발급

```

receivers:

#### 3. 마운트 경로 확인

```yaml  - name: 'slack-critical'1. Slack API 페이지 접속

# alertmanager-cr.yaml

receivers:    slack_configs:   ```

  - name: 'slack-seedtest'

    slack_configs:      - channel: '#seedtest-critical'   https://api.slack.com/apps → 기존 Alertmanager App 선택

      - api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url

        # Secret 이름과 키 이름이 정확히 일치해야 함        send_resolved: true   ```

```

        api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_critical

### 8-5. Alertmanager가 Secret을 읽지 못함

        color: 'danger'2. Features → Incoming Webhooks

**증상**:

```        title: '🚨 {{ .GroupLabels.alertname }}'

level=error msg="Notify for alerts failed" num_alerts=1 err="slack/default[0]: notify retry canceled: context deadline exceeded"

```3. **Revoke** (기존 Webhook 무효화) 또는 **Add New Webhook to Workspace**



**해결**:  - name: 'slack-warning'



#### 1. Secret 마운트 확인    slack_configs:4. 새 Webhook URL 복사

```bash

kubectl -n monitoring exec alertmanager-0 -- ls -la /etc/alertmanager/secrets/      - channel: '#seedtest-warnings'

```

        send_resolved: true#### Step 2: Kubernetes Secret 갱신

**예상 출력**:

```        api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_warning

drwxr-xr-x 3 root root ... alertmanager-secrets

```        color: 'warning'```bash



#### 2. 파일 내용 확인        title: '⚠️ {{ .GroupLabels.alertname }}'# Secret 갱신 (기존 Secret 덮어쓰기)

```bash

kubectl -n monitoring exec alertmanager-0 -- \kubectl -n monitoring create secret generic alertmanager-secrets \

  cat /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url

```route:  --from-literal=slack_webhook_url='https://hooks.slack.com/services/NEW/WEBHOOK/URL' \



**예상 출력**:  routes:  -o yaml --dry-run=client | kubectl apply -f -

```

https://hooks.slack.com/services/T.../B.../XXX...    - receiver: 'slack-critical'

```

      match:# 확인

#### 3. Prometheus Operator 버전 확인

```bash        severity: criticalkubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.slack_webhook_url}' | base64 -d

kubectl -n monitoring get deployment prometheus-operator -o yaml | grep image:

```    ```



**요구사항**:    - receiver: 'slack-warning'

- Alertmanager CR의 `secrets` 필드 지원 버전: v0.50.0 이상

- 이전 버전은 업그레이드 필요      match:#### Step 3: Alertmanager 재시작



---        severity: warning



## 📚 참고 자료``````bash



### 공식 문서# StatefulSet 롤아웃 재시작



- **Slack API - Incoming Webhooks**: https://api.slack.com/messaging/webhooks---kubectl -n monitoring rollout restart statefulset/alertmanager-main

- **Slack API - App Management**: https://api.slack.com/apps

- **Alertmanager - Slack Configuration**: https://prometheus.io/docs/alerting/latest/configuration/#slack_config



### 내부 문서## 7. 보안 권장사항# Pod 재시작 확인



- `QUICKSTART_SLACK.md`: 빠른 배포 가이드 (10분 완료)kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -w

- `README.md`: 전체 Alertmanager 구성 개요

- `OPERATIONS_RUNBOOK.md`: 운영 절차 (키 회전, 장애 대응)### 7-1. Webhook URL 보안```

- `ALERTMANAGER_ROUTING_GUIDE.md`: 고급 라우팅 설정



### 예제 코드

**절대 금지**:#### Step 4: 검증

- `setup-secrets.sh`: Secret 자동 생성 스크립트

- `validate-alertmanager.sh`: 배포 검증 스크립트- ❌ Git에 Webhook URL 평문 저장

- `alertmanager-cr.yaml`: Alertmanager CustomResource 예제

- ❌ 공개 문서에 URL 노출```bash

---

- ❌ 로그에 URL 출력# Secret 마운트 확인

## ✅ 체크리스트

ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')

완료된 항목에 체크하세요:

**권장**:kubectl -n monitoring exec "$ALERTM" -- cat /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url

### Slack App 생성

- [ ] Slack API 콘솔 접속- ✅ Kubernetes Secret 사용

- [ ] Create New App → From scratch

- [ ] Step 1: 앱 이름 입력 (`Alertmanager`)- ✅ SealedSecrets 또는 ESO로 암호화# 테스트 알림 전송

- [ ] Step 2: 워크스페이스 선택 (`DreamSeedAI`)

- [ ] Step 3: 채널 선택 및 권한 확인- ✅ 환경변수로만 전달amtool --alertmanager.url=http://127.0.0.1:9093 alert add \

- [ ] Create App 클릭 완료

- ✅ Secret 값은 base64 인코딩 상태로 유지  alertname=WebhookRotationTest service=seedtest-api severity=warning \

### Webhook 발급

- [ ] Incoming Webhooks 활성화 (ON)  summary="Webhook 회전 테스트"

- [ ] Add New Webhook to Workspace

- [ ] 채널 선택 (`#seedtest-alerts`)### 7-2. Webhook URL 회전 (Rotation)

- [ ] Allow 클릭

- [ ] Webhook URL 복사 완료# Slack 채널에서 메시지 수신 확인



### 테스트**언제 회전하나요?**:```

- [ ] Webhook URL cURL 테스트 성공 (응답: `ok`)

- [ ] Slack 채널에서 메시지 수신 확인- 유출 의심 시



### Kubernetes 설정- 정기 보안 감사 (연 1회 권장)### B. PagerDuty Routing Key 회전

- [ ] Kubernetes Secret 생성

- [ ] Secret 마운트 확인- 담당자 변경 시

- [ ] Alertmanager 배포

- [ ] 종단 테스트 성공 (Critical/Warning)#### Step 1: 새 Routing Key 발급



### 추가 설정 (선택)**회전 절차**:

- [ ] Private 채널 앱 초대 (해당 시)

- [ ] 다중 채널 Webhook 설정1. PagerDuty → Services → seedtest-api

- [ ] 보안 강화 (SealedSecrets/ESO)

1. **Slack API 콘솔** → Incoming Webhooks

### 운영

- [ ] 운영 문서 작성 (회전 절차, 담당자)2. Integrations 탭

- [ ] RBAC 적용

- [ ] 모니터링 대시보드 설정2. **기존 Webhook 삭제**:



---   - 해당 Webhook URL 옆 **Remove** 클릭3. 기존 Events API v2 Integration → **Edit**



**작성일**: 2025-11-08  

**버전**: 3.0 (Step-by-Step 상세 가이드)  

**작성자**: DreamSeedAI Infrastructure Team  3. **새 Webhook 발급**:4. **Regenerate Key** 클릭 (또는 새 Integration 추가)

**최종 업데이트**: Step 3 of 3 상세 설명 추가

   - **Add New Webhook to Workspace** 클릭

   - 동일한 채널 선택5. 새 Routing Key 복사



4. **Kubernetes Secret 업데이트**:#### Step 2: Kubernetes Secret 갱신

   ```bash

   kubectl -n monitoring delete secret alertmanager-secrets```bash

   # Secret 갱신

   kubectl -n monitoring create secret generic alertmanager-secrets \kubectl -n monitoring create secret generic pagerduty-routing-key \

     --from-literal=slack_webhook_url='NEW_WEBHOOK_URL'  --from-literal=routing_key='NEW_PD_ROUTING_KEY_XXXXXXXXXXXX' \

   ```  -o yaml --dry-run=client | kubectl apply -f -



5. **Alertmanager Pod 재시작**:# 확인

   ```bashkubectl -n monitoring get secret pagerduty-routing-key -o jsonpath='{.data.routing_key}' | base64 -d

   kubectl -n monitoring rollout restart statefulset alertmanager```

   ```

#### Step 3: Alertmanager 재시작

6. **테스트**:

   ```bash```bash

   curl -X POST "$NEW_WEBHOOK_URL" \kubectl -n monitoring rollout restart statefulset/alertmanager-main

     -H 'Content-type: application/json' \```

     -d '{"text":"🔄 Webhook 회전 완료 테스트"}'

   ```#### Step 4: 검증



### 7-3. 접근 제한```bash

# Secret 마운트 확인

**Slack 워크스페이스 설정**:kubectl -n monitoring exec "$ALERTM" -- cat /etc/alertmanager/secrets/pagerduty-routing-key/routing_key

- Admin → Settings & permissions → Permissions

- **App Management**: Restrict to admins# 테스트 알림 전송

- 앱 설치/삭제 권한 제한amtool --alertmanager.url=http://127.0.0.1:9093 alert add \

  alertname=PDKeyRotationTest service=seedtest-api severity=critical \

**Kubernetes RBAC**:  summary="PD 키 회전 테스트"

```yaml

apiVersion: v1# PagerDuty Incidents에서 수신 확인

kind: Role```

metadata:

  name: alertmanager-secret-reader---

  namespace: monitoring

rules:## 6. 트러블슈팅

  - apiGroups: [""]

    resources: ["secrets"]### 🚨 Slack 메시지 미수신

    resourceNames: ["alertmanager-secrets"]

    verbs: ["get"]#### 체크리스트

---

apiVersion: v1**1. Webhook URL 유효성**

kind: RoleBinding```bash

metadata:# Webhook 직접 테스트

  name: alertmanager-secret-bindingWEBHOOK=$(kubectl -n monitoring get secret alertmanager-secrets -o jsonpath='{.data.slack_webhook_url}' | base64 -d)

  namespace: monitoring

roleRef:curl -X POST -H 'Content-type: application/json' \

  apiGroup: rbac.authorization.k8s.io  --data '{"text":"Direct test"}' \

  kind: Role  "$WEBHOOK"

  name: alertmanager-secret-reader

subjects:# 응답 확인:

  - kind: ServiceAccount# - "ok" → Webhook 정상

    name: alertmanager# - "invalid_token" → Webhook URL 오류

    namespace: monitoring# - "channel_not_found" → 채널 삭제됨 또는 App 초대 안됨

``````



---**2. 채널 권한**

- Private 채널의 경우: Alertmanager App이 채널에 초대되어 있는지 확인

## 8. 트러블슈팅- Slack에서 채널 → Integrations → Alertmanager App 확인



### 8-1. Webhook URL이 작동하지 않음**3. Alertmanager 라우팅**

```bash

**증상**:# Alertmanager 로그에서 Slack 전송 확인

```kubectl -n monitoring logs "$ALERTM" --tail=100 | grep -i slack

curl: (22) The requested URL returned error: 404

```# 에러 예시:

# - "context deadline exceeded" → 네트워크 타임아웃

**원인 & 해결**:# - "invalid_token" → Webhook URL 오류

# - "channel_not_found" → 채널 문제

1. **URL 형식 확인**:```

   ```bash

   # 올바른 형식**4. NetworkPolicy**

   https://hooks.slack.com/services/T.../B.../XXX...```bash

   # Alertmanager에서 Slack(HTTPS 443) egress 허용 확인

   # 잘못된 형식 (OAuth URL)kubectl -n monitoring get networkpolicy -o yaml | grep -A 20 egress

   https://slack.com/api/oauth.v2.access  # ❌

   ```# 필요 시 egress 추가 (OPERATIONS_RUNBOOK.md 참고)

```

2. **Webhook 비활성화 확인**:

   - Slack API 콘솔 → Incoming Webhooks**5. Alert 라벨 확인**

   - 해당 URL이 목록에 있는지 확인```bash

   - 없으면 재발급# Alertmanager UI에서 Alert 클릭 → Labels 확인

# service=seedtest-api, severity=warning 있는지 확인

3. **워크스페이스 변경 확인**:# Receiver가 "slack-seedtest"인지 확인

   - 워크스페이스를 전환했다면 해당 워크스페이스에서 재발급```



### 8-2. Private 채널에 메시지 안 보임---



**증상**:### 🚨 PagerDuty Incident 미생성

```

ok  # 응답은 성공이지만 메시지가 보이지 않음#### 체크리스트

```

**1. Routing Key 유효성**

**해결**:```bash

# Routing Key 직접 테스트

1. **Slack 앱 초대**:PD_KEY=$(kubectl -n monitoring get secret pagerduty-routing-key -o jsonpath='{.data.routing_key}' | base64 -d)

   ```

   # 채널에서 실행curl -X POST 'https://events.pagerduty.com/v2/enqueue' \

   /invite @Alertmanager  -H 'Content-Type: application/json' \

   ```  -d "{

    \"routing_key\": \"$PD_KEY\",

2. **채널 멤버 확인**:    \"event_action\": \"trigger\",

   - 채널 상세 → Integrations    \"payload\": {

   - Alertmanager 앱이 목록에 있어야 함      \"summary\": \"Direct test\",

      \"severity\": \"critical\",

### 8-3. Kubernetes Secret 마운트 실패      \"source\": \"manual\"

    }

**증상**:  }"

```bash

kubectl -n monitoring logs alertmanager-0# 응답 확인:

# Error: secrets "alertmanager-secrets" not found# - {"status":"success",...} → Key 정상

```# - {"status":"invalid","message":"Invalid routing_key"} → Key 오류

```

**해결**:

**2. Integration 타입 확인**

1. **Secret 존재 확인**:- PagerDuty → Services → seedtest-api → Integrations

   ```bash- Integration Name이 **"Events API v2"**인지 확인 (v1 아님!)

   kubectl -n monitoring get secret alertmanager-secrets- Integration Key 길이가 32자인지 확인

   ```

**3. Service 설정**

2. **Secret 재생성**:- Service 상태가 **Active**인지 확인

   ```bash- Escalation Policy에 On-call Engineer가 있는지 확인

   bash setup-secrets.sh monitoring 'YOUR_WEBHOOK_URL'- Integration이 **Enabled** 상태인지 확인

   ```

**4. Alertmanager 라우팅**

3. **Alertmanager CR 확인**:```bash

   ```yaml# Alertmanager 로그에서 PagerDuty 전송 확인

   spec:kubectl -n monitoring logs "$ALERTM" --tail=100 | grep -i pagerduty

     secrets:

       - alertmanager-secrets  # Secret 이름 일치 확인# 에러 예시:

   ```# - "403 Forbidden" → Integration 비활성화 또는 권한 문제

# - "Invalid routing_key" → Key 오류

4. **Pod 재시작**:# - "context deadline exceeded" → 네트워크 타임아웃

   ```bash```

   kubectl -n monitoring rollout restart statefulset alertmanager

   ```**5. Alert 라벨 확인**

```bash

### 8-4. Webhook URL이 Secret에 없음# Alertmanager UI에서 Alert 클릭 → Labels 확인

# service=seedtest-api, severity=critical 있는지 확인

**증상**:# Receiver가 "pagerduty-seedtest"인지 확인

```bash```

kubectl -n monitoring exec alertmanager-0 -- \

  cat /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url---

# cat: can't open '/etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url': No such file or directory

```### 🚨 Alert 라우팅 오작동



**해결**:#### 문제: Alert가 잘못된 receiver로 라우팅됨



1. **Secret 데이터 키 확인**:**1. PrometheusRule 라벨 확인**

   ```bash```bash

   kubectl -n monitoring get secret alertmanager-secrets -o yaml# PrometheusRule에서 알림 정의 확인

   ```kubectl -n monitoring get prometheusrule -o yaml | grep -A 10 "HTTPHighErrorRate"

   

   **data 섹션에 `slack_webhook_url` 키 존재 확인**# labels:

#   severity: critical      ← 이 라벨이 route matcher와 일치해야 함

2. **키 이름 불일치 시 재생성**:#   service: seedtest-api   ← 이 라벨 필수

   ```bash```

   kubectl -n monitoring delete secret alertmanager-secrets

   **2. Firing Alert 라벨 확인**

   kubectl -n monitoring create secret generic alertmanager-secrets \```bash

     --from-literal=slack_webhook_url='YOUR_WEBHOOK_URL'# Prometheus UI → Alerts

   ```kubectl -n monitoring port-forward svc/prometheus-k8s 9090:9090 &

open http://127.0.0.1:9090/alerts

3. **마운트 경로 확인**:

   ```yaml# ALERTS{alertname="HTTPHighErrorRate"} 쿼리로 라벨 확인

   # alertmanager-cr.yaml```

   receivers:

     - name: 'slack-seedtest'**3. Route Matchers 확인**

       slack_configs:```bash

         - api_url_file: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url# Alertmanager UI → Status → Routes

           # Secret 이름과 키 이름 정확히 일치해야 함open http://127.0.0.1:9093/#/status

   ```

# Route 트리에서 matchers 확인:

### 8-5. Alertmanager가 Secret을 읽지 못함# - service="seedtest-api"

# - severity="critical"

**증상**:# - severity=~"warning|info"

``````

level=error msg="Notify for alerts failed" num_alerts=1 err="slack/default[0]: notify retry canceled: context deadline exceeded"

```**4. amtool로 라우팅 시뮬레이션**

```bash

**해결**:# 실제 전송 없이 라우팅만 테스트

amtool --alertmanager.url=http://127.0.0.1:9093 config routes test \

1. **Secret 마운트 확인**:  service=seedtest-api \

   ```bash  severity=critical

   kubectl -n monitoring exec alertmanager-0 -- ls -la /etc/alertmanager/secrets/

   ```# 출력 예상: pagerduty-seedtest

   

   **alertmanager-secrets 디렉토리 존재 확인**amtool --alertmanager.url=http://127.0.0.1:9093 config routes test \

  service=seedtest-api \

2. **파일 내용 확인**:  severity=warning

   ```bash

   kubectl -n monitoring exec alertmanager-0 -- \# 출력 예상: slack-seedtest

     cat /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url```

   ```

---

3. **Prometheus Operator 버전 확인**:

   - Alertmanager CR의 `secrets` 필드 지원 버전 확인### 🚨 Secret 마운트 누락

   - v0.50.0 이상 필요

#### 문제: /etc/alertmanager/secrets/ 디렉토리가 비어있음

---

**1. Alertmanager CR 확인**

## 📚 참고 자료```bash

kubectl -n monitoring get alertmanager main -o yaml | yq '.spec.secrets'

### 공식 문서

# 출력 예상:

- **Slack API - Incoming Webhooks**: https://api.slack.com/messaging/webhooks# - alertmanager-secrets

- **Slack API - App Management**: https://api.slack.com/apps# - pagerduty-routing-key

- **Alertmanager - Slack Configuration**: https://prometheus.io/docs/alerting/latest/configuration/#slack_config

# 출력이 null이거나 빈 배열이면 문제!

### 내부 문서```



- `QUICKSTART_SLACK.md`: 빠른 배포 가이드**2. Kustomize 패치 재적용**

- `README.md`: 전체 구성 개요```bash

- `OPERATIONS_RUNBOOK.md`: 운영 절차# alertmanager-cr-patch.yaml 포함 확인

- `ALERTMANAGER_ROUTING_GUIDE.md`: 고급 라우팅 설정kubectl kustomize infra/monitoring/alertmanager/ | grep -A 5 "spec.secrets"



### 예제 코드# 전체 재적용

kubectl apply -k infra/monitoring/alertmanager/

- `setup-secrets.sh`: Secret 자동 생성 스크립트```

- `validate-alertmanager.sh`: 배포 검증 스크립트

- `alertmanager-cr.yaml`: Alertmanager CustomResource**3. Pod 재시작**

```bash

---kubectl -n monitoring rollout restart statefulset/alertmanager-main

```

## ✅ 체크리스트

**4. 마운트 검증**

완료된 항목에 체크하세요:```bash

ALERTM=$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')

- [ ] Slack App 생성 완료kubectl -n monitoring exec "$ALERTM" -- ls -R /etc/alertmanager/secrets/

- [ ] Incoming Webhooks 활성화

- [ ] 채널별 Webhook URL 발급# 출력 예상:

- [ ] Webhook URL cURL 테스트 성공# /etc/alertmanager/secrets/alertmanager-secrets:

- [ ] Kubernetes Secret 생성# slack_webhook_url

- [ ] Secret 마운트 확인#

- [ ] Alertmanager 배포# /etc/alertmanager/secrets/pagerduty-routing-key:

- [ ] 종단 테스트 성공 (Critical/Warning)# routing_key

- [ ] Private 채널 앱 초대 (해당 시)```

- [ ] 다중 채널 설정 (선택)

- [ ] 보안 강화 (SealedSecrets/ESO)---

- [ ] 운영 문서화

## 📅 운영 체크리스트

---

### 정기 점검 (월 1회)

**작성일**: 2025-11-08  

**버전**: 2.0 (Slack Only)  - [ ] Slack Webhook 유효성 테스트 (curl)

**작성자**: DreamSeedAI Infrastructure Team- [ ] PagerDuty Routing Key 유효성 테스트 (curl)

- [ ] Alertmanager 테스트 알림 전송 (amtool)
- [ ] PagerDuty Incidents 수신 확인
- [ ] Slack 채널 메시지 수신 확인
- [ ] Alertmanager UI에서 라우팅 확인

### 키 회전 (분기 1회 권장)

- [ ] 새 Slack Webhook 발급
- [ ] 새 PagerDuty Routing Key 발급
- [ ] Kubernetes Secret 갱신
- [ ] Alertmanager 재시작
- [ ] 테스트 알림으로 검증
- [ ] 이전 키 무효화 (Slack/PD UI)

### 보안 점검

- [ ] 키가 Git에 커밋되지 않았는지 확인 (`git log -S "hooks.slack.com"`)
- [ ] Secret에 적절한 RBAC 적용 확인
- [ ] External Secrets Operator 사용 여부 검토
- [ ] Audit Log에서 Secret 접근 기록 확인

---

## 📚 관련 문서

- **OPERATIONS_RUNBOOK.md**: 운영 절차 (키 회전, 장애 대응, ArgoCD 통합)
- **ALERTMANAGER_ROUTING_GUIDE.md**: 라우팅 설정 (보안, 트러블슈팅)
- **validate-alertmanager.sh**: 자동 검증 스크립트
- **setup-secrets.sh**: Secret 생성 자동화 스크립트

---

**작성일**: 2025-11-08  
**버전**: 1.0  
**최종 업데이트**: 2025-11-08
