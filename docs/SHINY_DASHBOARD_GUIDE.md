# Shiny 관리자 대시보드 운영 가이드

## 1. Shiny 관리자 대시보드 실행 가이드

### 실행 명령어

```bash
cd /home/won/projects/dreamseed_monorepo/portal_front
Rscript -e '.libPaths("~/R/library"); shiny::runApp("dashboard", host="0.0.0.0", port=8080)'
```

### 필수 패키지

- `shiny`
- `shinydashboard`
- `DT`
- `arrow`
- `dplyr`
- `plotly`
- `lubridate`
- `stringr`
- `tidyr`
- `tibble`
- `readr`

### 패키지 설치

```bash
Rscript -e '.libPaths("~/R/library"); install.packages(c("shiny", "shinydashboard", "DT", "arrow", "dplyr", "plotly", "lubridate", "stringr", "tidyr", "tibble", "readr"), repos="https://cran.rstudio.com/", lib="~/R/library")'
```

### 로컬 개발 환경변수 예시 (.env.example)

```bash
export DEV_USER=alice
export DEV_ORG_ID=org_001
export DEV_ROLES=analyst
export DATASET_ROOT="$(pwd)/data/datasets"
```

## 2. 프록시 연동 (OIDC/JWT) 예시

### nginx + oauth2-proxy 설정

현재 적용된 Nginx 설정 (`/etc/nginx/sites-enabled/dreamseedai.com.conf`):

```nginx
# Shiny Dashboard 프록시
location /admin/dashboard/ {
  proxy_pass http://127.0.0.1:8080/;
  proxy_http_version 1.1;
  
  # WebSocket 지원 (Shiny는 WebSocket 사용)
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  
  # 기본 헤더
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  
  # 타임아웃 설정 (Shiny 앱이 오래 걸릴 수 있음)
  proxy_connect_timeout 60s;
  proxy_send_timeout 300s;
  proxy_read_timeout 300s;
  
  # 버퍼링 비활성화 (실시간 업데이트를 위해)
  proxy_buffering off;
  
  add_header X-Debug-Dashboard 'shiny-dashboard' always;
}
```

### OIDC 인증 추가 (향후 적용 예시)

```nginx
location /admin/dashboard/ {
  auth_request /oauth2/auth;
  error_page 401 = /oauth2/sign_in;
  
  # 인증 헤더 전달
  proxy_set_header X-User  $upstream_http_x_auth_request_user;
  proxy_set_header X-Roles $upstream_http_x_auth_request_groups;
  proxy_set_header X-Org-Id $http_x_org_id;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  
  proxy_pass http://127.0.0.1:8080/;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_buffering off;
}

location = /oauth2/auth { 
  internal; 
  proxy_pass http://127.0.0.1:4180/oauth2/auth; 
}

location /oauth2/ { 
  proxy_pass http://127.0.0.1:4180; 
}
```

### oauth2-proxy.cfg 예시

```ini
provider = "oidc"
oidc_issuer_url = "https://<your-idp>/"
client_id = "<client_id>"
client_secret = "<client_secret>"
cookie_secret = "<32-byte-base64>"
email_domains = ["*"]
set_xauthrequest = true
pass_authorization_header = true
pass_access_token = true
user_claims = "preferred_username"
oidc_groups_claim = "roles"
```

## 3. 데이터/성능 팁

### Arrow 최적화
- `open_dataset`으로 컬럼 푸시다운/파티션 프루닝(`org_id`) 활용
- `collect()`는 최종 단계에서만 사용
- 필터링과 집계는 Arrow 레벨에서 수행

### DT (DataTables) 최적화
- `server=TRUE` 사용 (대용량 데이터)
- `Scroller` 확장 활용
- `deferRender` 옵션 사용

### 다운로드 최적화
- 제한된 `head(n)`만 `collect()`하여 처리
- `write_csv()`로 스트리밍 방식 사용

### Content Bank 권한 관리
- `role`이 `content_editor` 또는 `admin`이 아니면 `status == "published"`만 노출
- 조직별 필터링 적용 (`org_id`)

## 4. 확장 아이디어

### A/B Lab
- 유의성 지표 추가: 우도비, 베이즈, 클러스터-강건 SE
- 효과 크기 시각화 개선

### Churn Monitor
- 이동평균/분해(추세·계절성) 옵션 추가
- 예측 모델 통합

### IRT
- 테스트 정보 함수(Test Information Function) 추가
- 심화 파라미터 필터 옵션
- 문항 특성 곡선(ICC) 시각화 개선

## 5. 대시보드 메뉴 구성

### 관리자용 메뉴
1. **Cohort Overview** - 코호트 전체 현황
2. **IRT Calibration** - IRT 캘리브레이션 결과
3. **A/B Lab** - A/B 테스트 분석
4. **Churn Monitor** - 이탈률 모니터링
5. **Content Bank** - 콘텐츠 관리

### 권한 체계
- 프록시가 주입한 헤더 신뢰:
  - `X-User`: 사용자 ID
  - `X-Org-Id`: 조직 ID
  - `X-Roles`: 사용자 역할 (예: `admin`, `analyst`, `content_editor`)
- 조직별/역할별 필터 자동 적용

## 6. 접속 URL

- **로컬**: http://localhost:8080
- **프로덕션**: https://dreamseedai.com/admin/dashboard/

## 7. 운영 관리

### 프로세스 관리

대시보드 시작:
```bash
cd /home/won/projects/dreamseed_monorepo/portal_front
Rscript -e '.libPaths("~/R/library"); shiny::runApp("dashboard", host="0.0.0.0", port=8080)' &
```

프로세스 확인:
```bash
ps aux | grep "shiny::runApp"
```

프로세스 종료:
```bash
pkill -f "shiny::runApp"
```

### Nginx 관리

설정 테스트:
```bash
sudo nginx -t
```

Nginx 재시작:
```bash
sudo systemctl reload nginx
```

로그 확인:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## 8. 트러블슈팅

### 패키지 설치 오류

시스템 의존성 설치:
```bash
sudo apt-get install -y libcurl4-openssl-dev libssl-dev libxml2-dev
```

### 포트 충돌

8080 포트 사용 확인:
```bash
sudo lsof -i :8080
```

### WebSocket 연결 오류

Nginx 설정에서 다음 헤더가 있는지 확인:
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## 9. 인증 통합 (IdP)

### 현재 인증 구조

**seedtest_api (JWT 기반)**
- 인증 방식: JWT Bearer Token
- 검증: `JWT_PUBLIC_KEY` 또는 `JWKS_URL`
- 클레임 구조:
  ```json
  {
    "sub": "user_id",
    "org_id": 1,
    "roles": ["admin", "teacher", "student"],
    "scope": "exam:read exam:write",
    "aud": "...",
    "iss": "..."
  }
  ```

**portal_api (세션 기반)**
- 인증 방식: 쿠키 기반 세션 (`portal_session`)
- 검증: `itsdangerous.URLSafeSerializer`

**Shiny Dashboard (헤더 기반)**
- 인증 방식: 역방향 프록시가 주입한 헤더 신뢰
- 헤더: `X-User`, `X-Org-Id`, `X-Roles`

### 통합 방안

#### 옵션 1: nginx-jwt 모듈 (추천)

JWT를 nginx에서 직접 검증하고 헤더로 변환:

```nginx
location /admin/dashboard/ {
  # JWT 검증
  auth_jwt "DreamSeed Admin";
  auth_jwt_key_file /etc/nginx/jwt_public_key.pem;
  
  # JWT 클레임 → 헤더 변환
  proxy_set_header X-User $jwt_claim_sub;
  proxy_set_header X-Org-Id $jwt_claim_org_id;
  proxy_set_header X-Roles $jwt_claim_roles;
  
  proxy_pass http://127.0.0.1:8080/;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
}
```

#### 옵션 2: oauth2-proxy + 기존 JWT

oauth2-proxy를 JWT 검증 레이어로 사용:

```nginx
location /admin/dashboard/ {
  auth_request /oauth2/auth;
  error_page 401 = /oauth2/sign_in;
  
  proxy_set_header X-User $upstream_http_x_auth_request_user;
  proxy_set_header X-Org-Id $upstream_http_x_auth_request_claim_org_id;
  proxy_set_header X-Roles $upstream_http_x_auth_request_claim_roles;
  
  proxy_pass http://127.0.0.1:8080/;
}
```

#### 옵션 3: Keycloak 통합 (향후 확장)

완전한 IdP 솔루션으로 마이그레이션:

```bash
# Keycloak 설치
docker run -p 8180:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest start-dev
```

### 개발 환경 JWT 생성

테스트용 JWT 토큰 생성 스크립트:

```python
import jwt
import datetime

payload = {
    "sub": "dev_user",
    "org_id": 1,
    "roles": ["admin"],
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    "iss": "dreamseedai"
}

# 개발용 비밀키 (프로덕션에서는 절대 사용 금지)
secret = "dev-secret-key"
token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Authorization: Bearer {token}")
```

## 11. 문의 및 지원

추가 요청이나 수정사항이 있으면 개발팀에 문의하세요.

---

**문서 업데이트**: 2025-11-05  
**버전**: 1.0
