# 🔐 DreamSeedAI MegaCity – Security Architecture

## WAF · Rate Limit · Token Hardening · AI Abuse Prevention · PII Protection · Zero-Trust

**버전:** 1.0  
**작성일:** 2025-11-21  
**작성자:** DreamSeedAI Security & Architecture Team

---

# 📌 0. 개요 (Overview)

DreamSeedAI MegaCity는 9개 Zone(도메인) + 중앙 Core City + AI Cluster까지 포함하는 대규모 멀티테넌트 AI 플랫폼입니다.
이 문서는 MegaCity 전체의 **보안 구조(Security Architecture)** 를 정의하며 아래 7개 계층을 모두 포함합니다.

```
1. Edge Security (Cloudflare WAF / DDoS / Bot Management)
2. API Gateway Security (Nginx/Traefik Rate Limit & Filters)
3. Authentication Security (Token Hardening / SSO Protection)
4. Authorization Security (RBAC/PBAC)
5. AI Abuse Prevention (Prompt Injection / Abuse detection)
6. Data Security (PII Encryption / RLS / Column Encryption)
7. Infrastructure Security (Firewall / SSH / Secrets / Backups)
```

MegaCity는 **Zero-Trust 원칙**을 채택합니다:

* "**Never trust, always verify**"
* 모든 Zone · Tenant 별 **Context-Aware Security** 적용
* 모든 AI 요청은 **Threat-Aware Router**를 통해 검사

---

# 🛡️ 1. Edge Security (Cloudflare Layer)

Edge 보안은 DreamSeedAI의 첫 번째 방어선입니다.

## 1.1 Cloudflare WAF (OWASP Top-10 Protection)

다음 공격 자동 차단:

* **SQLi** (SQL Injection)
* **XSS** (Cross-Site Scripting)
* **RCE** (Remote Code Execution)
* **Path Traversal**
* **CSRF** (Cross-Site Request Forgery)
* **SSRF** (Server-Side Request Forgery)
* **Command Injection**

### Custom WAF Rules

```javascript
// SQL Injection
(http.request.uri.query contains "union select" or
 http.request.uri.query contains "' or 1=1" or
 http.request.body contains "DROP TABLE") → Block

// XSS
(http.request.body contains "<script>" or
 http.request.uri.query contains "javascript:" or
 http.request.uri.query contains "onerror=") → Block

// Malicious Bots
(http.user_agent contains "sqlmap" or 
 http.user_agent contains "nikto" or 
 http.user_agent contains "nmap") → Block

// Directory Traversal
(http.request.uri.path contains "../" or
 http.request.uri.path contains "..\\") → Block
```

## 1.2 DDoS 방어

L3/L4/L7 공격 방어:

* **SYN Flood** (L4)
* **UDP Flood** (L4)
* **HTTP Flood** (L7 rate control)
* **Slowloris** (Slow HTTP attacks)

### DDoS Mitigation Settings

```yaml
ddos_protection: automatic
challenge_on_attack: true
rate_limiting: aggressive
connection_timeout: 30s
```

## 1.3 Bot Management

Cloudflare Bot Score 기반 차단:

```
score < 30 → Block (Definitely Bot)
30 ≤ score < 50 → Challenge (Likely Bot)
score ≥ 50 → Allow (Likely Human)
```

### Bot Detection Rules

```javascript
// Block known bad bots
(cf.bot_management.score < 30) → Block

// Challenge suspicious bots
(cf.bot_management.score < 50 and 
 http.request.uri.path eq "/api/login") → Challenge

// Allow verified bots (Google, Bing)
(cf.bot_management.verified_bot) → Allow
```

## 1.4 Edge Rate Limit

도메인별/엔드포인트별:

| Endpoint | Rate Limit | Window | Action |
|----------|------------|--------|--------|
| `/api/auth/login` | 5 req/min | per IP | Block |
| `/api/v1/*` | 100 req/min | per IP | Block |
| `/api/v1/kzone/ai/*` | 50 req/min | per IP | Challenge |
| `/api/v1/ai-tutor` | 30 req/min | per user | Block |

### Rate Limit Configuration

```javascript
// Login protection
(http.request.uri.path eq "/api/auth/login" and
 rate(1m) > 5) → Block

// API protection
(http.request.uri.path matches "^/api/v1/" and
 rate(1m) > 100) → Block

// AI endpoint protection
(http.request.uri.path matches "^/api/v1/kzone/ai/" and
 rate(1m) > 50) → Challenge
```

---

# 🚦 2. API Gateway Security (Nginx / Traefik)

Edge를 통과한 트래픽은 Gateway에서 2차 검사.

## 2.1 IP 기반 Rate Limit (Nginx)

```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=ai_limit:10m rate=2r/s;

# Apply rate limits
location /api/v1/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://backend;
}

location /api/auth/login {
    limit_req zone=login_limit burst=3 nodelay;
    proxy_pass http://backend;
}

location /api/v1/ai-tutor {
    limit_req zone=ai_limit burst=5 nodelay;
    proxy_pass http://backend;
}
```

## 2.2 CORS 제한

Zone별 App만 허용:

```nginx
# CORS whitelist
map $http_origin $cors_origin {
    default "";
    "https://app.univprepai.com" $http_origin;
    "https://app.skillprepai.com" $http_origin;
    "https://app.my-ktube.ai" $http_origin;
    "https://app.dreamseedai.com" $http_origin;
}

add_header Access-Control-Allow-Origin $cors_origin always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
add_header Access-Control-Allow-Credentials "true" always;
```

## 2.3 Request Size 제한

AI 영상 업로드 보호:

```nginx
# Default
client_max_body_size 50M;

# K-Zone video upload
location /api/v1/kzone/upload {
    client_max_body_size 500M;
    client_body_timeout 300s;
}

# Exam attachments
location /api/v1/exams/upload {
    client_max_body_size 100M;
}
```

## 2.4 WebSocket 보안

```nginx
# WebSocket upgrade with auth check
location /ws {
    # Auth header required
    if ($http_authorization = "") {
        return 401;
    }
    
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Timeouts
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

## 2.5 TLS Configuration

```nginx
# TLS 1.2+ only
ssl_protocols TLSv1.2 TLSv1.3;

# Strong ciphers
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;

# HTTP/3 support
http3 on;
quic_retry on;
```

## 2.6 Security Headers

```nginx
# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

---

# 🔑 3. Authentication Security (Token Hardening)

DreamSeed Global ID + SSO는 MegaCity 전체의 보안 중심.

## 3.1 Access Token 보안

```python
ACCESS_TOKEN_CONFIG = {
    "expiry": "15 minutes",
    "algorithm": "RS256",  # Asymmetric for better security
    "issuer": "auth.dreamseedai.com",
    "audience": ["api.dreamseedai.com", "api.univprepai.com", ...],
    "claims": {
        "user_id": "required",
        "zone_id": "required",
        "org_id": "required",
        "role": "required",
        "jti": "required"  # JWT ID for revocation
    },
    "no_pii": True  # Never include email, phone, name
}
```

### Token Generation

```python
import jwt
from datetime import datetime, timedelta

def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "zone_id": user.zone_id,
        "org_id": user.org_id,
        "role": user.role,
        "jti": generate_jti(),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iss": "auth.dreamseedai.com",
        "aud": ["api.dreamseedai.com"]
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
```

## 3.2 Refresh Token 보안

```python
REFRESH_TOKEN_CONFIG = {
    "expiry": "14 days",
    "storage": "httpOnly cookie",
    "flags": "Secure; SameSite=Strict",
    "rotation": True,  # Issue new refresh token on use
    "family_tracking": True  # Detect token theft
}
```

### Refresh Token Rotation

```python
@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    old_refresh_token = request.cookies.get("refresh_token")
    
    # Verify old token
    payload = verify_refresh_token(old_refresh_token)
    
    # Check if token family is compromised
    if await is_token_family_compromised(payload["jti"]):
        await revoke_all_tokens(payload["user_id"])
        raise HTTPException(401, "Token theft detected")
    
    # Generate new tokens
    new_access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)
    
    # Store token family
    await store_token_family(payload["jti"], new_refresh_token.jti)
    
    # Return new tokens
    response = JSONResponse({"access_token": new_access_token})
    response.set_cookie(
        "refresh_token",
        new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=14*24*3600
    )
    return response
```

## 3.3 Token Replay 방지

Redis Blacklist 저장:

```python
async def revoke_token(jti: str, exp: int):
    ttl = exp - int(datetime.utcnow().timestamp())
    await redis.setex(f"blacklist:{jti}", ttl, "revoked")

async def is_token_revoked(jti: str) -> bool:
    return await redis.exists(f"blacklist:{jti}")

# Check in middleware
@app.middleware("http")
async def check_token_revocation(request: Request, call_next):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    if token:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        if await is_token_revoked(payload["jti"]):
            return JSONResponse(status_code=401, content={"error": "Token revoked"})
    return await call_next(request)
```

## 3.4 Session Binding

토큰 → User-Agent + IP 조합 묶기:

```python
def create_session_token(user: User, request: Request) -> str:
    fingerprint = hashlib.sha256(
        f"{request.client.host}{request.headers.get('user-agent')}".encode()
    ).hexdigest()
    
    payload = {
        "sub": str(user.id),
        "fingerprint": fingerprint,
        ...
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

def verify_session_token(token: str, request: Request):
    payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    
    current_fingerprint = hashlib.sha256(
        f"{request.client.host}{request.headers.get('user-agent')}".encode()
    ).hexdigest()
    
    if payload["fingerprint"] != current_fingerprint:
        raise HTTPException(401, "Session hijacking detected")
    
    return payload
```

## 3.5 Device Fingerprinting (선택)

새 기기 로그인 시 승인 필요:

```python
async def check_device_trust(user_id: int, device_fingerprint: str):
    trusted_devices = await redis.smembers(f"trusted_devices:{user_id}")
    
    if device_fingerprint not in trusted_devices:
        # Send approval email/SMS
        await send_device_approval_request(user_id, device_fingerprint)
        raise HTTPException(403, "New device detected. Please check your email.")
    
    return True
```

## 3.6 MFA / TOTP 지원

교사/학부모/관리자 계정은 2FA 필수:

```python
import pyotp

# Setup TOTP
def setup_2fa(user: User) -> dict:
    secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="DreamSeedAI"
    )
    
    # Store secret
    await db.execute(
        "UPDATE users SET totp_secret = :secret WHERE id = :id",
        {"secret": secret, "id": user.id}
    )
    
    return {"secret": secret, "qr_uri": totp_uri}

# Verify TOTP
def verify_2fa(user: User, code: str) -> bool:
    totp = pyotp.TOTP(user.totp_secret)
    return totp.verify(code, valid_window=1)

# Enforce 2FA
@app.post("/api/auth/login")
async def login(credentials: LoginCredentials):
    user = authenticate(credentials)
    
    if user.role in ["teacher", "parent", "org_admin", "sys_admin"]:
        if not user.totp_secret:
            raise HTTPException(403, "2FA setup required")
        
        if not credentials.totp_code:
            return {"status": "2fa_required"}
        
        if not verify_2fa(user, credentials.totp_code):
            raise HTTPException(401, "Invalid 2FA code")
    
    return create_session(user)
```

---

# 🛂 4. Authorization Security (RBAC + PBAC)

## 4.1 RBAC (Role-Based Access Control)

역할 정의:

```python
ROLES = {
    "student": {
        "permissions": [
            "exam:attempt",
            "ai_tutor:access",
            "dashboard:view_self"
        ]
    },
    "parent": {
        "permissions": [
            "dashboard:view_children",
            "report:download_children"
        ]
    },
    "teacher": {
        "permissions": [
            "exam:create",
            "exam:edit",
            "class:manage",
            "student:view",
            "dashboard:view_class"
        ]
    },
    "org_admin": {
        "permissions": [
            "*:*"  # All permissions within org
        ]
    },
    "sys_admin": {
        "permissions": [
            "*:*:*"  # All permissions across all zones/orgs
        ]
    }
}
```

### Permission Check

```python
def has_permission(user: User, permission: str) -> bool:
    user_permissions = ROLES.get(user.role, {}).get("permissions", [])
    
    # Check wildcard permissions
    if "*:*" in user_permissions or "*:*:*" in user_permissions:
        return True
    
    # Check exact match
    if permission in user_permissions:
        return True
    
    # Check wildcard prefix
    resource, action = permission.split(":")
    if f"{resource}:*" in user_permissions:
        return True
    
    return False

# Decorator
def require_permission(permission: str):
    async def check(request: Request):
        user = request.state.user
        if not has_permission(user, permission):
            raise HTTPException(403, f"Permission denied: {permission}")
        return user
    return Depends(check)

# Usage
@app.post("/api/v1/exams")
async def create_exam(
    user: User = require_permission("exam:create")
):
    # Create exam logic
    pass
```

## 4.2 PBAC (Policy-Based Access Control)

상황 기반 동적 정책:

```python
class PolicyEngine:
    async def evaluate(
        self,
        user: User,
        resource: str,
        action: str,
        context: dict = None
    ) -> bool:
        # Policy 1: Block AI tutor during exam
        if action == "ai_tutor:access":
            exam_session = await get_active_exam_session(user.id)
            if exam_session and exam_session.status == "in_progress":
                return False
        
        # Policy 2: Time-based access
        if action == "exam:attempt" and context:
            exam = context.get("exam")
            if exam.start_time > datetime.utcnow():
                return False
            if exam.end_time < datetime.utcnow():
                return False
        
        # Policy 3: Subscription-based access
        if action == "kzone:premium_feature":
            subscription = await get_user_subscription(user.id)
            if not subscription or subscription.tier != "pro":
                return False
        
        # Policy 4: Age-based restrictions
        if action == "content:access" and context:
            content = context.get("content")
            if content.age_rating > user.age:
                return False
        
        # Fallback to RBAC
        return has_permission(user, f"{resource}:{action}")
```

## 4.3 Multi-Tenant Access

* 다른 org_id 데이터 접근 시 **자동 차단**
* DB RLS로 서버단 필터링 강제

```python
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    user = request.state.user
    
    # Set tenant context
    await db.execute(f"SET app.current_org_id = {user.org_id}")
    await db.execute(f"SET app.current_zone_id = '{user.zone_id}'")
    
    response = await call_next(request)
    return response
```

---

# 🧨 5. AI Abuse Prevention (AI 남용 방지)

MegaCity는 AI가 교육/문화 목적 외 남용되거나 악용되지 않도록 **AI Abuse Detection Layer** 를 둠.

## 5.1 Prompt Injection 방지

### Input Sanitization

```python
PROMPT_INJECTION_PATTERNS = [
    r"system\s*:",
    r"ignore\s+previous\s+instructions",
    r"override\s+your\s+programming",
    r"forget\s+everything",
    r"act\s+as\s+if",
    r"jailbreak",
    r"bypass\s+filters",
    r"admin\s+mode"
]

def detect_prompt_injection(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, prompt_lower):
            return True
    
    return False

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest, user: User = Depends(get_current_user)):
    if detect_prompt_injection(request.prompt):
        # Log security event
        await log_security_event(
            user_id=user.id,
            event_type="prompt_injection_attempt",
            details={"prompt": request.prompt[:100]}
        )
        raise HTTPException(400, "Invalid prompt detected")
    
    # Process AI request
    response = await call_llm(request.prompt)
    return response
```

### Keyword Firewall

```python
BLOCKED_KEYWORDS = [
    "jailbreak", "override", "ignore previous", "bypass",
    "admin mode", "developer mode", "god mode",
    "system prompt", "hidden instructions"
]

def contains_blocked_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in BLOCKED_KEYWORDS)
```

## 5.2 Harmful Content Filter

```python
from transformers import pipeline

# Content moderation model
moderation_model = pipeline("text-classification", model="unitary/toxic-bert")

async def moderate_content(text: str) -> dict:
    result = moderation_model(text)[0]
    
    toxicity_score = result["score"] if result["label"] == "toxic" else 0
    
    if toxicity_score > 0.7:
        return {
            "is_safe": False,
            "reason": "toxic_content",
            "score": toxicity_score
        }
    
    # Check explicit categories
    explicit_patterns = {
        "violence": [r"\b(kill|murder|attack|assault)\b"],
        "hate": [r"\b(hate|racist|sexist)\b"],
        "sexual": [r"\b(sex|porn|nude)\b"],
        "self_harm": [r"\b(suicide|kill myself|self harm)\b"]
    }
    
    for category, patterns in explicit_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                return {
                    "is_safe": False,
                    "reason": category,
                    "score": 1.0
                }
    
    return {"is_safe": True, "score": 0}

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest):
    # Moderate input
    moderation = await moderate_content(request.prompt)
    if not moderation["is_safe"]:
        # Alert admin
        await notify_admin("content_violation", {
            "user_id": user.id,
            "reason": moderation["reason"]
        })
        raise HTTPException(400, "Content violates community guidelines")
    
    # Process request
    response = await call_llm(request.prompt)
    
    # Moderate output
    output_moderation = await moderate_content(response)
    if not output_moderation["is_safe"]:
        # Log and return safe fallback
        await log_ai_safety_issue("unsafe_output", response)
        return {"response": "I cannot provide that information."}
    
    return {"response": response}
```

## 5.3 K-Zone 안전 규칙

```python
class KZoneSafetyEngine:
    async def check_face_synthesis_consent(self, user_id: int, image: bytes):
        # Check if user owns the face
        face_id = await detect_face_id(image)
        
        # Verify ownership
        is_owner = await verify_face_ownership(user_id, face_id)
        if not is_owner:
            # Check consent database
            has_consent = await check_consent(user_id, face_id)
            if not has_consent:
                raise HTTPException(403, "Face synthesis requires consent")
        
        return True
    
    async def check_voice_clone_consent(self, user_id: int, audio: bytes):
        # Extract voice fingerprint
        voice_id = await extract_voice_id(audio)
        
        # Check if user owns the voice
        is_owner = await verify_voice_ownership(user_id, voice_id)
        if not is_owner:
            # Require explicit consent
            has_consent = await check_voice_consent(user_id, voice_id)
            if not has_consent:
                raise HTTPException(403, "Voice cloning requires consent")
        
        return True
    
    async def filter_adult_content(self, content_id: str):
        content = await get_content(content_id)
        
        if content.age_rating >= 19:
            raise HTTPException(403, "19+ content not allowed")
        
        return True
```

## 5.4 Rate Limit for AI Engines

```python
AI_RATE_LIMITS = {
    "whisper": {"limit": 10, "window": 60},  # 10 req/min
    "posenet": {"limit": 5, "window": 60},   # 5 req/min
    "diffusion": {"limit": 2, "window": 60}, # 2 req/min
    "llm": {"limit": 30, "window": 60}       # 30 req/min
}

async def check_ai_rate_limit(user_id: int, engine: str):
    rate_limit = AI_RATE_LIMITS.get(engine)
    key = f"ai_rate:{engine}:{user_id}"
    
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, rate_limit["window"])
    
    if current > rate_limit["limit"]:
        raise HTTPException(429, f"Rate limit exceeded for {engine}")
    
    return True
```

---

# 🧬 6. Data Security (PII 보호 · Encryption · RLS)

## 6.1 PII 필드 암호화 (Fernet)

```python
from cryptography.fernet import Fernet

class PIIEncryptor:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()

# Usage
encryptor = PIIEncryptor(ENCRYPTION_KEY)

# Encrypt PII fields
user.phone_encrypted = encryptor.encrypt(user.phone)
user.ssn_encrypted = encryptor.encrypt(user.ssn)
user.address_encrypted = encryptor.encrypt(user.address)
```

## 6.2 Column-Level Encryption (pgcrypto)

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt column
UPDATE users 
SET phone_encrypted = pgp_sym_encrypt(phone, 'encryption_key')
WHERE phone IS NOT NULL;

-- Decrypt column
SELECT 
    id,
    name,
    pgp_sym_decrypt(phone_encrypted::bytea, 'encryption_key') AS phone
FROM users;
```

## 6.3 Row-Level Security (RLS)

특정 org_id와 zone_id만 조회 가능:

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation_policy ON users
    USING (
        org_id = current_setting('app.current_org_id')::integer
        AND zone_id = current_setting('app.current_zone_id')
    );

-- Create admin bypass policy
CREATE POLICY admin_bypass_policy ON users
    USING (
        current_setting('app.user_role') = 'sys_admin'
    );
```

## 6.4 DB 암호화 (At-Rest)

```bash
# LUKS volume encryption
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb pgdata
mkfs.ext4 /dev/mapper/pgdata
mount /dev/mapper/pgdata /var/lib/postgresql/data
```

## 6.5 In-Transit Encryption

```yaml
# PostgreSQL SSL
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'

# Redis TLS (optional)
tls-port 6380
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
tls-ca-cert-file /path/to/ca.crt
```

## 6.6 PII 삭제 정책

```python
@app.delete("/api/v1/users/me")
async def delete_account(user: User = Depends(get_current_user)):
    # Hard delete PII
    await db.execute("""
        UPDATE users SET
            email = 'deleted_' || id || '@deleted.local',
            phone = NULL,
            name = 'Deleted User',
            ssn_encrypted = NULL,
            address_encrypted = NULL,
            deleted_at = NOW()
        WHERE id = :user_id
    """, {"user_id": user.id})
    
    # Anonymize audit logs
    await db.execute("""
        UPDATE audit_log SET
            user_id = NULL,
            metadata = jsonb_set(metadata, '{anonymized}', 'true')
        WHERE user_id = :user_id
    """, {"user_id": user.id})
    
    return {"status": "deleted"}
```

---

# 🧱 7. Infrastructure Security (서버/네트워크)

## 7.1 Firewall 규칙

```bash
# UFW Firewall
ufw default deny incoming
ufw default allow outgoing

# Allow Cloudflare IP ranges only
for ip in $(curl https://www.cloudflare.com/ips-v4); do
    ufw allow from $ip to any port 80
    ufw allow from $ip to any port 443
done

# Allow SSH from VPN only
ufw allow from 10.0.0.0/24 to any port 22

# Enable firewall
ufw enable
```

## 7.2 SSH 보안

```bash
# /etc/ssh/sshd_config
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
MaxAuthTries 3
LoginGraceTime 30

# Install Fail2ban
apt-get install fail2ban

# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600
```

## 7.3 Secrets 관리

```python
# Never commit secrets to Git
# Use environment variables or secret managers

# .env (local development)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ENCRYPTION_KEY=...

# Docker Secrets (production)
docker secret create db_password ./db_password.txt

# GitHub Secrets (CI/CD)
# Set in GitHub repo settings
```

## 7.4 Malware 방지

```bash
# Install ClamAV
apt-get install clamav clamav-daemon

# Update virus database
freshclam

# Scan uploads directory
clamscan -r /var/uploads --infected --remove
```

### File Upload Validation

```python
import magic

ALLOWED_MIMETYPES = {
    "image/jpeg", "image/png", "image/gif",
    "video/mp4", "video/webm",
    "audio/mpeg", "audio/wav",
    "application/pdf"
}

async def validate_upload(file: UploadFile):
    # Check MIME type
    content = await file.read(1024)
    mime = magic.from_buffer(content, mime=True)
    
    if mime not in ALLOWED_MIMETYPES:
        raise HTTPException(400, f"File type not allowed: {mime}")
    
    # Scan for malware (optional)
    if ENABLE_VIRUS_SCAN:
        is_clean = await scan_with_clamav(file)
        if not is_clean:
            raise HTTPException(400, "Malware detected")
    
    return True
```

## 7.5 백업 보안

```bash
# Encrypted WAL archive
archive_command = 'gpg -e -r backup@dreamseedai.com %p | aws s3 cp - s3://wal-archive/%f.gpg'

# Encrypted daily backup
pg_dump dreamseed | gzip | gpg -e -r backup@dreamseedai.com > backup.sql.gz.gpg
aws s3 cp backup.sql.gz.gpg s3://backups/$(date +%F).sql.gz.gpg
```

---

# 🚨 8. Incident Response

## 8.1 자동 탐지

```yaml
# AlertManager rules
groups:
  - name: security
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High 5xx error rate detected"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        annotations:
          summary: "High API latency detected"
      
      - alert: SuspiciousLoginAttempts
        expr: rate(auth_login_attempts{status="failed"}[5m]) > 10
        for: 1m
        annotations:
          summary: "Multiple failed login attempts detected"
```

## 8.2 비상조치 Runbook

```python
class IncidentResponse:
    async def isolate_zone(self, zone_id: str):
        # 1. Block traffic to zone
        await cloudflare.update_firewall_rule(zone_id, action="block")
        
        # 2. Drain connections
        await nginx.drain_upstream(zone_id)
        
        # 3. Take zone offline
        await kubernetes.scale_deployment(f"{zone_id}-api", replicas=0)
        
        await notify_team(f"Zone {zone_id} isolated")
    
    async def throttle_api(self, endpoint: str, limit: int):
        # Reduce rate limit
        await redis.set(f"rate_limit:{endpoint}", limit)
        await nginx.reload()
    
    async def limit_db_connections(self, max_conn: int):
        await db.execute(f"ALTER SYSTEM SET max_connections = {max_conn}")
        await db.execute("SELECT pg_reload_conf()")
    
    async def ai_offline_mode(self):
        # Disable AI endpoints
        await redis.set("ai_engine:enabled", "false")
        await notify_users("AI services temporarily unavailable")
    
    async def gradual_recovery(self, zone_id: str):
        # 1. Enable health checks
        await enable_health_checks(zone_id)
        
        # 2. Scale up gradually
        for replicas in [1, 2, 5, 10]:
            await kubernetes.scale_deployment(f"{zone_id}-api", replicas=replicas)
            await asyncio.sleep(60)
            
            # Check health
            if not await check_zone_health(zone_id):
                await self.isolate_zone(zone_id)
                raise Exception("Recovery failed")
        
        # 3. Re-enable traffic
        await cloudflare.update_firewall_rule(zone_id, action="allow")
        await notify_team(f"Zone {zone_id} recovered")
```

## 8.3 Post-Mortem

```python
POST_MORTEM_TEMPLATE = """
# Incident Post-Mortem

## Summary
- **Date**: {date}
- **Duration**: {duration}
- **Impact**: {impact}
- **Root Cause**: {root_cause}

## Timeline
{timeline}

## Root Cause Analysis
{analysis}

## Action Items
{action_items}

## Prevention
{prevention}
"""

async def create_post_mortem(incident_id: str):
    incident = await get_incident(incident_id)
    
    post_mortem = POST_MORTEM_TEMPLATE.format(
        date=incident.started_at,
        duration=incident.duration,
        impact=incident.impact_assessment,
        root_cause=incident.root_cause,
        timeline=incident.timeline,
        analysis=incident.analysis,
        action_items=incident.action_items,
        prevention=incident.prevention_plan
    )
    
    # Store in documentation
    await store_document(f"post-mortem-{incident_id}.md", post_mortem)
    
    # Notify team
    await notify_team("Post-mortem available", post_mortem_url)
```

---

# 🏁 9. 결론

이 문서는 DreamSeedAI MegaCity 전체의 보안 구조를 다루는 최상위 문서로,
**Edge → Gateway → Auth → AI → Data → Infrastructure → Incident Response** 까지 모든 보안 계층을 포함합니다.

MegaCity가 글로벌 교육·문화·AI 서비스로 확장될수록, 이 보안 아키텍처는 더욱 중요한 역할을 수행합니다.

## 핵심 보안 원칙

1. **Defense in Depth**: 7계층 보안 (Edge → Gateway → Auth → Authz → AI → Data → Infra)
2. **Zero Trust**: 모든 요청은 검증 필요
3. **Least Privilege**: 최소 권한 원칙
4. **Fail Secure**: 오류 시 차단
5. **Audit Everything**: 모든 행동 기록
6. **Encrypt Everywhere**: At-rest & In-transit 암호화
7. **Incident Readiness**: 비상 대응 절차 준비

---

**문서 완료 - DreamSeedAI MegaCity Security Architecture v1.0**
