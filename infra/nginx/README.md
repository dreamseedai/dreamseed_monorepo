# Nginx Configuration

보안 및 성능 최적화된 Nginx 설정 모음.

## 🔐 JWT Authentication for Shiny Dashboard

Nginx에서 JWT 검증 후 Shiny Dashboard에 사용자 헤더를 주입하는 인증 흐름을 제공합니다.

### Quick Start

**1. RSA 키 페어 생성**
```bash
cd /srv/dreamseed/infra/nginx
./generate_jwt_keypair.sh /etc/nginx
```

**2. 인증 방식 선택**

#### Option A: OpenResty + Lua (권장)
```bash
# OpenResty 설치
sudo apt-get install openresty luarocks
sudo luarocks install lua-resty-jwt

# 설정 적용
sudo cp jwt_auth.lua /etc/nginx/lua/
sudo cp dashboard.dreamseedai.com.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### Option B: External JWT Verifier
```bash
# JWT 검증 서비스 설치
pip install fastapi uvicorn python-jose[cryptography] httpx
sudo cp ../systemd/jwt-verifier.service.example /etc/systemd/system/jwt-verifier.service
sudo systemctl enable jwt-verifier && sudo systemctl start jwt-verifier

# nginx 설정
sudo cp jwt_auth_simple.conf /etc/nginx/sites-enabled/dashboard.dreamseedai.com.conf
sudo nginx -t && sudo systemctl reload nginx
```

**3. 테스트 토큰 생성 (개발용)**
```bash
python dev_generate_jwt.py --user alice --org 1 --roles admin,analyst
```

### 인증 흐름

```
┌─────────┐  JWT Bearer    ┌────────────┐  Verify JWT   ┌─────────────┐
│ Client  │───────────────>│   Nginx    │──────────────>│ Lua / Verifier│
└─────────┘  Authorization  └────────────┘               └─────────────┘
                                   │                              │
                                   │ ✓ Valid JWT                  │
                                   │<─────────────────────────────┘
                                   │
                                   │ Inject headers:
                                   │ - X-User: alice
                                   │ - X-Org-Id: 1
                                   │ - X-Roles: admin,analyst
                                   ▼
                           ┌────────────────┐
                           │ Shiny Dashboard│
                           │ (port 8080)    │
                           └────────────────┘
```

### 헤더 스키마

| Header | Source JWT Claim | Example | Description |
|--------|------------------|---------|-------------|
| `X-User` | `sub` or `user_id` | `alice` | 사용자 식별자 |
| `X-Org-Id` | `org_id` | `1` | 조직 ID (데이터 필터링) |
| `X-Roles` | `roles` | `admin,analyst` | 역할 (콤마 구분) |

### JWT Claims 예시

```json
{
  "sub": "alice",
  "user_id": "alice",
  "org_id": 1,
  "roles": ["admin", "analyst"],
  "scope": "dashboard:read dashboard:write",
  "iss": "dreamseedai",
  "aud": "dashboard",
  "iat": 1730822400,
  "exp": 1730908800
}
```

### 설정 파일

| File | Purpose |
|------|---------|
| `jwt_auth.lua` | Lua 기반 JWT 검증 (OpenResty) |
| `dashboard.dreamseedai.com.conf` | Nginx vhost (Lua 방식) |
| `jwt_auth_simple.conf` | Nginx vhost (auth_request 방식) |
| `jwt_verifier.py` | 외부 JWT 검증 서비스 (FastAPI) |
| `generate_jwt_keypair.sh` | RSA 키 페어 생성 스크립트 |
| `dev_generate_jwt.py` | 개발용 JWT 토큰 생성기 |

### 환경변수

```bash
# JWT 검증 설정
export JWT_PUBLIC_KEY_PATH=/etc/nginx/jwt_public.pem
export JWT_ISSUER=dreamseedai
export JWT_AUDIENCE=dashboard
export JWT_ALGORITHM=RS256

# Optional: JWKS URL (동적 키 로테이션)
export JWT_JWKS_URL=https://auth.dreamseedai.com/.well-known/jwks.json
```

### 트러블슈팅

**"Missing Authorization header"**
```bash
# 요청에 Bearer 토큰 포함 확인
curl -H "Authorization: Bearer <token>" https://dashboard.dreamseedai.com/admin/
```

**"Invalid token"**
```bash
# 공개키 경로 확인
ls -la /etc/nginx/jwt_public.pem

# 토큰 디코딩 (검증 없이)
python -c "from jose import jwt; print(jwt.get_unverified_claims('$TOKEN'))"

# issuer/audience 일치 확인
```

**"lua-resty-jwt not found"**
```bash
sudo luarocks install lua-resty-jwt
sudo nginx -t
```

### 보안 권장사항

1. **Private key 보호**: `jwt_private.pem`은 600 권한, JWT 발급 서버에만 배포
2. **Public key 배포**: `jwt_public.pem`은 검증 서버(nginx/verifier)에만 644 권한
3. **키 로테이션**: 주기적(3-6개월)으로 키 페어 재생성 및 배포
4. **짧은 만료시간**: 프로덕션은 1-4시간, 개발은 24시간
5. **localhost 바인딩**: Shiny는 `127.0.0.1:8080`에만 바인딩 (외부 직접 접근 차단)

---

## 📁 기존 설정 파일

| File | Description |
|------|-------------|
| `portal.dreamseedai.com.conf.example` | 포털 프론트엔드 (Vite) |
| `limit_req_login.conf.example` | 로그인 rate limiting |
| `rate_limit.conf` | 전역 rate limit 존 정의 |
| `security_headers.conf` | 보안 헤더 (CSP, HSTS 등) |

자세한 내용은 각 파일 주석 참고.

---

## 🔗 관련 문서

### 인증/보안
- **[IdP 통합 질문지](IDP_INTEGRATION_QUESTIONNAIRE.md)** - 귀사 환경에 맞춘 설정 파일 요청
- **[보안 체크리스트](SECURITY_CHECKLIST.md)** - 배포 전 필수 보안 점검 항목
- **[Keycloak 설정 가이드](KEYCLOAK_SETUP.md)** - 오픈소스 IdP 통합
- **[Auth0 설정 가이드](AUTH0_SETUP.md)** - SaaS IdP 통합

### 운영
- [Shiny Dashboard README](../../portal_front/dashboard/README.md)
- [SystemD Services](../systemd/README.md)
- [IRT Deployment Guide](../../shared/irt/docs/06_DEPLOYMENT_GUIDE.md)
