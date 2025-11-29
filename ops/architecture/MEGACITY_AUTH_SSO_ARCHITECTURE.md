# DreamSeedAI MegaCity – SSO & Identity Architecture

**버전:** 1.0 — 2025-11-20

---

## 0. Executive Summary

DreamSeedAI MegaCity는 9개 독립 도메인(Zone)으로 구성된 교육·AI 메가시티입니다.
각 Zone은:

- UnivPrepAI.com  
- CollegePrepAI.com  
- SkillPrepAI.com  
- MediPrepAI.com  
- MajorPrepAI.com  
- My-Ktube.com  
- My-Ktube.ai  
- mpcstudy.com  
- DreamSeedAI.com  

이러한 멀티 도메인 체계에서도 사용자는 DreamSeedAI 전체에서 **단 하나의 글로벌 계정(DreamSeed ID)** 만 가지게 됩니다.

이 문서는 MegaCity 전체의:

- 글로벌 ID 체계
- SSO (Single Sign-On)
- Multi-domain Cookie
- Multi-zone access control
- RBAC + PBAC 정책
- Parent/Student 승인 구조
- Token lifecycle
- Login/Logout propagation
- 보안 강화 정책(MFA/2FA, 시험 중 AI 차단 등)

을 공식적으로 정의하는 문서입니다.

---

## 1. DreamSeed Global Identity

### 🔵 원칙

DreamSeedAI 전체 9개 도메인 → 사용자 ID는 단 1개.

### 구조

- `users.id` (PK, int)  
- `users.email` (Unique)  
- `users.role` (`student` / `parent` / `teacher` / `tutor` / `admin`)  
- `users.global_profile` (JSONB)  
- `users.org_id` (optional)  
- `users.zone_preferences` (`['univ', 'skill', 'ktube']` 등)

### 의미

- 유저는 UnivPrep → SkillPrep → My-Ktube 등 Zone 간 자유 이동 가능 (SSO)
- 데이터는 하나의 Global Profile로 통합됨
- 로그/정책/승인 흐름이 단일 ID로 기록됨

---

## 2. Multi-Domain SSO Architecture

### 전체 흐름

`app.univprepai.com`  
`app.skillprepai.com`  
`app.my-ktube.com`  
`app.my-ktube.ai`  
`mpcstudy.com`  

↓ (Redirect / Auth 요청)

`DreamSeedAI.com` (Central Auth)

↓ (인증 성공 후)

JWT Access + Refresh 발급

↓

SSO cookie propagated

↓

각 Zone에서 자동 로그인

### 2.1 SSO 방식

DreamSeed는 **OpenID Connect(OIDC) + OAuth2 Authorization Code with PKCE** 기반의 **Centralized Authorization Server** 모델을 사용합니다.

- **Central Auth Domain**: `auth.dreamseedai.com`

기능:

- 모든 도메인 Login/Logout을 관장하는 중앙 Auth 서버
- FastAPI 또는 Keycloak 기반으로 구성 가능 (초기에는 FastAPI + OAuth2/OIDC 라이브러리, 필요 시 Keycloak 도입)

### 2.2 Cross-site SSO 구현 상세 (app.univprepai.com ↔ app.skillprepai.com)

**시나리오: 사용자가 UnivPrepAI에서 로그인 후 SkillPrepAI로 이동**

```
1. 사용자 → app.univprepai.com 방문
   └→ SSO Cookie 확인 (.dreamseedai.com)
   
2. Cookie 없음 → auth.dreamseedai.com/login으로 Redirect
   └→ OIDC Authorization Code Flow 시작
   
3. 로그인 성공 → JWT Access Token + Refresh Token 발급
   └→ Cookie 저장: domain=.dreamseedai.com
   
4. app.univprepai.com으로 Redirect Back
   └→ 로그인 상태 유지
   
5. 사용자 → app.skillprepai.com 방문
   └→ SSO Cookie 자동 전송 (.dreamseedai.com 공유)
   
6. app.skillprepai.com → auth.dreamseedai.com/validate
   └→ JWT 검증 성공
   
7. ✅ 재로그인 없이 SkillPrepAI 접근 허용
```

**핵심 기술 요소:**

- **OIDC Discovery**: `auth.dreamseedai.com/.well-known/openid-configuration`
- **Authorization Endpoint**: `auth.dreamseedai.com/authorize`
- **Token Endpoint**: `auth.dreamseedai.com/token`
- **UserInfo Endpoint**: `auth.dreamseedai.com/userinfo`
- **PKCE**: Code Verifier + Code Challenge (S256) 사용

**FastAPI 구현 예시:**

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='dreamseed',
    server_metadata_url='https://auth.dreamseedai.com/.well-known/openid-configuration',
    client_id='univprep-client',
    client_secret='***',
    client_kwargs={
        'scope': 'openid email profile',
        'code_challenge_method': 'S256'
    }
)

@app.get('/login')
async def login(request: Request):
    redirect_uri = 'https://app.univprepai.com/callback'
    return await oauth.dreamseed.authorize_redirect(request, redirect_uri)

@app.get('/callback')
async def callback(request: Request):
    token = await oauth.dreamseed.authorize_access_token(request)
    user_info = await oauth.dreamseed.userinfo(request)
    
    # SSO Cookie 발급
    response = RedirectResponse(url='/')
    response.set_cookie(
        key='sso_token',
        value=token['access_token'],
        domain='.dreamseedai.com',
        secure=True,
        httponly=True,
        samesite='none',
        max_age=900  # 15분
    )
    return response
```

### 2.3 Cross-zone Login State Probe (세션 상태 확인)

**목적:** 각 Zone의 Frontend가 사용자의 로그인 상태를 확인할 수 있는 경량 엔드포인트

**Probe Endpoint:**

```python
@app.get('/auth/session')
async def get_session_status(
    sso_token: str = Cookie(None),
    request: Request = None
):
    """
    Cross-zone 세션 상태 확인 엔드포인트
    모든 Zone의 Frontend가 이 엔드포인트를 호출하여 로그인 상태 확인
    """
    
    # 1. SSO Token 검증
    if not sso_token:
        return {
            'authenticated': False,
            'reason': 'no_token'
        }
    
    try:
        # 2. JWT 검증
        payload = jwt.decode(sso_token, SECRET_KEY, algorithms=['HS256'])
        user_id = int(payload['sub'])
        
        # 3. Blacklist 확인
        if redis_client.exists(f'blacklist:{sso_token}'):
            return {
                'authenticated': False,
                'reason': 'token_revoked'
            }
        
        # 4. 사용자 정보 조회 (간단)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                'authenticated': False,
                'reason': 'user_not_found'
            }
        
        # 5. 로그인 상태 응답
        return {
            'authenticated': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.full_name,
                'role': user.role,
                'primary_zone': user.primary_zone_id,
                'avatar': user.avatar_url
            },
            'zones_access': user.zone_preferences or [],
            'expires_at': payload['exp']
        }
        
    except jwt.ExpiredSignatureError:
        return {
            'authenticated': False,
            'reason': 'token_expired',
            'action': 'refresh_required'
        }
    except jwt.InvalidTokenError:
        return {
            'authenticated': False,
            'reason': 'invalid_token'
        }
```

**Frontend 사용 예시 (React/Next.js):**

```typescript
// hooks/useAuth.ts
import { useEffect, useState } from 'react';

interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  primary_zone: string;
  avatar: string;
}

interface SessionStatus {
  authenticated: boolean;
  user?: User;
  zones_access?: string[];
  reason?: string;
}

export function useAuth() {
  const [session, setSession] = useState<SessionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkSession() {
      try {
        // Central Auth 서버에 세션 확인
        const response = await fetch('https://auth.dreamseedai.com/auth/session', {
          credentials: 'include',
          headers: {
            'Accept': 'application/json'
          }
        });
        
        const data = await response.json();
        setSession(data);
        
        // Token 만료 시 자동 갱신
        if (data.reason === 'token_expired') {
          await refreshToken();
          // 재시도
          checkSession();
        }
      } catch (error) {
        console.error('Session check failed:', error);
        setSession({ authenticated: false, reason: 'network_error' });
      } finally {
        setLoading(false);
      }
    }

    checkSession();
    
    // 5분마다 세션 상태 재확인
    const interval = setInterval(checkSession, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return { session, loading };
}

// 컴포넌트에서 사용
export function ProtectedPage() {
  const { session, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  
  if (!session?.authenticated) {
    // 로그인 페이지로 Redirect
    window.location.href = 'https://auth.dreamseedai.com/login?redirect_uri=' + 
      encodeURIComponent(window.location.href);
    return null;
  }

  return (
    <div>
      <h1>Welcome, {session.user?.name}!</h1>
      <p>Role: {session.user?.role}</p>
      <p>Zones: {session.zones_access?.join(', ')}</p>
    </div>
  );
}
```

**Probe Endpoint 캐싱 전략:**

```python
# Redis 캐싱 (5분)
@app.get('/auth/session')
async def get_session_status_cached(
    sso_token: str = Cookie(None)
):
    if not sso_token:
        return {'authenticated': False}
    
    # 캐시 확인
    cache_key = f'session_status:{hashlib.sha256(sso_token.encode()).hexdigest()}'
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # 캐시 미스 → DB 조회
    result = await get_session_status(sso_token)
    
    # 성공 시에만 캐싱 (5분)
    if result['authenticated']:
        redis_client.setex(
            cache_key,
            300,  # 5분
            json.dumps(result)
        )
    
    return result
```

**보안 고려사항:**
- CORS: `Access-Control-Allow-Origin: https://app.univprepai.com` (각 Zone 화이트리스트)
- Rate Limiting: IP당 분당 60회 제한
- Cache: 성공한 세션만 캐싱 (실패는 캐싱하지 않음)
- Logging: 모든 Probe 요청 로깅 (이상 패턴 감지)

---

### 2.4 OAuth2 Scopes & Permissions

DreamSeed는 다음과 같은 OAuth2 Scope를 정의합니다:

| Scope | 설명 | 접근 가능 리소스 |
|-------|------|-----------------|
| `openid` | OIDC 필수 scope | User ID |
| `email` | 이메일 주소 접근 | user.email |
| `profile` | 프로필 정보 | user.name, user.avatar |
| `exams:read` | 시험 조회 권한 | GET /api/exams |
| `exams:write` | 시험 생성/수정 권한 | POST/PUT /api/exams |
| `ai:tutor` | AI 튜터 사용 권한 | POST /api/ai/tutor |
| `parent:read` | 자녀 정보 조회 | GET /api/students/{id} (승인 필요) |
| `admin:manage` | 관리자 권한 | All Admin APIs |

**Client별 Scope 제한:**

- UnivPrep Client: `openid email profile exams:read exams:write ai:tutor`
- SkillPrep Client: `openid email profile exams:read ai:tutor`
- K-Zone Client: `openid email profile ai:tutor`
- Parent Dashboard: `openid email profile parent:read`
- Admin Console: `openid email profile admin:manage`

---

## 3. Token Architecture (JWT + Refresh)

### Access Token (JWT)

- 유효기간: **15분**
- 포함 정보(Claims):
  - `sub` (user_id)
  - `email`
  - `role`
  - `zone_id`
  - `org_id`
  - `permissions[]`

### Refresh Token

- 유효기간: **14일**
- 저장 방식:
  - HttpOnly Cookie
  - `Secure` / `SameSite=None`
  - 서버 측 Redis에 Revocation List 저장 (탈취/로그아웃 처리용)

### Token Rotation

- Refresh Token은 **매 요청마다 rotate**
- 기존 Refresh Token은 즉시 혹은 일정 유예 후 폐기
- Redis Revocation List와 함께 사용하여 탈취 위험 최소화

### 3.1 Token 갱신 프로세스 (Refresh Token + Access Token)

**자동 갱신 흐름:**

```
1. Frontend → API 요청 (Access Token 포함)
   └→ API Gateway: JWT 검증
   
2. JWT 만료 (15분 경과)
   └→ 401 Unauthorized 응답
   
3. Frontend → /auth/refresh 요청 (Refresh Token 포함)
   └→ Refresh Token 검증 (Redis 확인)
   
4. ✅ 검증 성공 → 새로운 Access Token + Refresh Token 발급
   └→ 기존 Refresh Token은 Redis Revocation List에 추가
   
5. Frontend → 새 Access Token으로 재요청
   └→ ✅ API 접근 성공
```

**FastAPI 구현 예시:**

```python
from datetime import datetime, timedelta
import jwt
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Access Token 생성 (15분)
def create_access_token(user_id: int, role: str, zone_id: str, org_id: int):
    payload = {
        'sub': str(user_id),
        'role': role,
        'zone_id': zone_id,
        'org_id': org_id,
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Refresh Token 생성 (14일)
def create_refresh_token(user_id: int):
    token_id = str(uuid.uuid4())
    payload = {
        'sub': str(user_id),
        'jti': token_id,  # JWT ID (unique)
        'exp': datetime.utcnow() + timedelta(days=14),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    # Redis에 Refresh Token 저장 (14일 TTL)
    redis_client.setex(
        f'refresh_token:{token_id}',
        timedelta(days=14),
        user_id
    )
    
    return token

# Token 갱신
@app.post('/auth/refresh')
async def refresh_token(refresh_token: str = Cookie(None)):
    try:
        # Refresh Token 검증
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        token_id = payload['jti']
        user_id = int(payload['sub'])
        
        # Redis에서 확인 (Revocation 체크)
        if not redis_client.exists(f'refresh_token:{token_id}'):
            raise HTTPException(status_code=401, detail='Invalid refresh token')
        
        # 기존 Refresh Token 폐기
        redis_client.delete(f'refresh_token:{token_id}')
        
        # 사용자 정보 조회
        user = db.query(User).filter(User.id == user_id).first()
        
        # 새 토큰 발급
        new_access_token = create_access_token(
            user_id=user.id,
            role=user.role,
            zone_id=user.primary_zone_id,
            org_id=user.org_id
        )
        new_refresh_token = create_refresh_token(user_id=user.id)
        
        # Response에 새 토큰 포함
        response = JSONResponse(content={
            'access_token': new_access_token,
            'token_type': 'bearer'
        })
        
        # Refresh Token은 HttpOnly Cookie로 저장
        response.set_cookie(
            key='refresh_token',
            value=new_refresh_token,
            domain='.dreamseedai.com',
            secure=True,
            httponly=True,
            samesite='none',
            max_age=14 * 24 * 60 * 60  # 14일
        )
        
        return response
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Refresh token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid refresh token')
```

**Token Revocation (강제 로그아웃):**

```python
@app.post('/auth/logout')
async def logout(
    current_user: dict = Depends(get_current_user),
    refresh_token: str = Cookie(None)
):
    # Refresh Token 폐기
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        token_id = payload['jti']
        redis_client.delete(f'refresh_token:{token_id}')
    except:
        pass
    
    # Access Token도 Blacklist에 추가 (15분간 유지)
    access_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if access_token:
        redis_client.setex(
            f'blacklist:{access_token}',
            timedelta(minutes=15),
            'revoked'
        )
    
    # Cookie 삭제
    response = JSONResponse(content={'message': 'Logged out'})
    response.delete_cookie(
        key='refresh_token',
        domain='.dreamseedai.com'
    )
    
    return response
```

---

## 4. Multi-Domain Cookie Strategy

### 필수 옵션

- `Secure: true`
- `SameSite: None`
- `Domain: .dreamseedai.com`

### Cross-domain 적용

- 모든 Zone은 `.dreamseedai.com` 기반의 **공통 쿠키**를 공유
- 각 Zone의 프론트엔드는 공통 SSO Cookie를 사용해 Auth 서버와 통신
- 각 Zone의 API 서버는 `Authorization: Bearer <access_token>` 헤더 기반으로 접근 제어

### 로그인 흐름

1. 사용자가 `app.univprepai.com`에서 로그인 버튼 클릭  
2. `auth.dreamseedai.com`으로 Redirect (OIDC Authorization Code Flow)  
3. 로그인 성공 시 `.dreamseedai.com` 도메인에 SSO Cookie 발급  
4. 사용자는 다시 `app.univprepai.com`으로 돌아오며 로그인 상태 유지  
5. 동일 브라우저 내에서 `skillprepai.com`, `my-ktube.ai` 등으로 이동 시 SSO Cookie를 통해 자동 로그인 상태 확인

### 로그아웃

1. 사용자가 어느 Zone에서든 Logout 버튼 클릭  
2. `auth.dreamseedai.com`에 Logout 요청  
3. 중앙 Auth 서버에서 SSO Cookie 삭제 및 Refresh Token Revocation  
4. 전체 9개 도메인에서 즉시 로그인 해제 (SSO 세션 종료)

### 4.4 SSO Logout Propagation 다이어그램

**전체 도메인 로그아웃 흐름:**

```
사용자 (app.univprepai.com에서 Logout 클릭)
   ↓
1. Frontend → POST /logout (local)
   ↓
2. Redirect → auth.dreamseedai.com/logout?redirect_uri=...
   ↓
3. Central Auth Server:
   ├─ Delete SSO Cookie (.dreamseedai.com)
   ├─ Redis: DELETE refresh_token:{jti}
   ├─ Redis: SADD blacklist:{access_token} (15분 TTL)
   └─ Audit Log: user_id, logout_time, ip
   ↓
4. Response: Set-Cookie (delete) + Redirect back
   ↓
5. 사용자 → app.univprepai.com (로그아웃 완료)

동시에 다른 Zone 접근 시:
   app.skillprepai.com → Cookie 없음 → 로그인 페이지
   app.my-ktube.ai → Cookie 없음 → 로그인 페이지
   ✅ 모든 Zone에서 즉시 로그아웃 상태
```

**Backend Logout 구현:**

```python
@app.post('/auth/logout')
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    refresh_token: str = Cookie(None)
):
    """Global SSO Logout (전체 도메인)"""
    
    # 1. Refresh Token 폐기 (Redis)
    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
            token_id = payload['jti']
            redis_client.delete(f'refresh_token:{token_id}')
        except:
            pass
    
    # 2. Access Token Blacklist 추가
    access_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if access_token:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256'])
            exp_time = payload['exp']
            ttl = exp_time - int(datetime.utcnow().timestamp())
            if ttl > 0:
                redis_client.setex(
                    f'blacklist:{access_token}',
                    ttl,
                    'revoked'
                )
        except:
            pass
    
    # 3. Audit Log
    log_audit(
        user_id=current_user['id'],
        event_type='logout',
        ip=request.client.host,
        user_agent=request.headers.get('user-agent')
    )
    
    # 4. SSO Cookie 삭제 (.dreamseedai.com)
    response.delete_cookie(
        key='sso_token',
        domain='.dreamseedai.com',
        path='/'
    )
    response.delete_cookie(
        key='refresh_token',
        domain='.dreamseedai.com',
        path='/'
    )
    
    # 5. 전체 사용자 세션 무효화 (선택적)
    redis_client.delete(f'user_session:{current_user["id"]}')
    
    return {'message': 'Logged out successfully from all zones'}
```

**Frontend Logout 구현 (React/Next.js):**

```typescript
// lib/auth.ts
export async function logout() {
  try {
    // 1. Local logout API 호출
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
    
    // 2. Central Auth 서버로 Redirect
    const currentUrl = window.location.href;
    window.location.href = `https://auth.dreamseedai.com/logout?redirect_uri=${encodeURIComponent(currentUrl)}`;
    
  } catch (error) {
    console.error('Logout failed:', error);
    // Fallback: 강제 쿠키 삭제
    document.cookie = 'sso_token=; domain=.dreamseedai.com; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC';
    window.location.href = '/login';
  }
}
```

---

## 5. Role Architecture (RBAC)

### 기본 역할(Role)

- `student`
- `parent`
- `teacher`
- `tutor`
- `org_admin`
- `sys_admin`

### 주요 권한(Capability 예시)

| Role       | 주요 Capability 예시                                  |
|-----------|------------------------------------------------------|
| student   | Exam 응시, Learning 모듈 접근, AI Tutor 사용          |
| parent    | 자녀 학습 현황 조회, AI 코치, 메시징                  |
| teacher   | 반/수업 관리, 시험 관리, 대시보드                     |
| tutor     | 1:1 튜터링, 노트/피드백, AI blending                  |
| org_admin | 소속 기관 전체 사용자/클래스/정책 관리               |
| sys_admin | 전체 Zone/테넌트 관리, 시스템 레벨 설정              |

### 확장: PBAC (Policy Based Access Control)

역할 기반 권한 위에 **조건 기반 정책**을 추가합니다.

예시 정책:

```pseudo
IF user.role == 'student' AND exam.status == 'in_progress'
THEN AI_tutor_access = deny
```

- 동일 student라도 **시험 중인지 여부**, **Zone/Org 정책**, **부모/교사 승인 여부** 등에 따라 세부 권한이 달라짐

---

## 6. Parent–Student Linking (Approval Workflow)

### 6.1 Parent Approval Flow

1. `parent_user` → 특정 `student_user`에 대해 link 요청 (`request_link`)  
2. `teacher` 또는 `admin`이 해당 요청을 검토 후 승인/거절  
3. 승인 시 Parent–Student relationship이 생성됨

### 6.2 Teacher–School Linking Approval

1. `teacher_user` → 특정 `org_id`(학교/학원 등)에 소속 요청 (`request_org_link`)  
2. 해당 기관의 `org_admin` 또는 상위 `sys_admin`이 요청을 검토 후 승인/거절  
3. 승인 시 Teacher–Org relationship이 생성되고, 교사는 해당 기관 내 클래스/학생/시험 리소스에 접근 가능

DB 테이블 예시: `teacher_org_links`

```sql
CREATE TABLE teacher_org_links (
  id SERIAL PRIMARY KEY,
  teacher_user_id INTEGER NOT NULL REFERENCES users(id),
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  zone_id VARCHAR(20) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected
  request_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  approved_at TIMESTAMP,
  approved_by INTEGER REFERENCES users(id),
  rejection_reason TEXT,
  UNIQUE(teacher_user_id, org_id)
);
```

### DB 테이블 예시: `parent_approvals`

```sql
CREATE TABLE parent_student_links (
  id SERIAL PRIMARY KEY,
  parent_user_id INTEGER NOT NULL REFERENCES users(id),
  student_id INTEGER NOT NULL REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected
  relationship_type VARCHAR(50),  -- mother/father/guardian
  verification_code VARCHAR(6),  -- 6자리 인증 코드 (학생이 제공)
  created_at TIMESTAMP DEFAULT NOW(),
  approved_at TIMESTAMP,
  approved_by INTEGER REFERENCES users(id),  -- teacher/admin
  expiry_date DATE,  -- 승인 만료일 (선택적)
  UNIQUE(parent_user_id, student_id)
);
```

### 6.3 승인 프로세스 API 예시

**학부모 → 학생 연결 요청:**

```python
@app.post('/api/v1/parent/link-student')
async def request_parent_link(
    student_email: str,
    relationship_type: str,  # mother/father/guardian
    current_user: dict = Depends(get_current_user)
):
    # 학부모만 요청 가능
    if current_user['role'] != 'parent':
        raise HTTPException(status_code=403, detail='Only parents can request')
    
    # 학생 찾기
    student = db.query(User).filter(
        User.email == student_email,
        User.role == 'student'
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail='Student not found')
    
    # 6자리 인증 코드 생성
    verification_code = generate_random_code(6)
    
    # 연결 요청 생성
    link = ParentStudentLink(
        parent_user_id=current_user['id'],
        student_id=student.id,
        relationship_type=relationship_type,
        verification_code=verification_code,
        status='pending'
    )
    db.add(link)
    db.commit()
    
    # 학생에게 이메일 발송 (인증 코드 포함)
    send_email(
        to=student.email,
        subject='학부모 연결 요청',
        body=f'{current_user["email"]}님이 학부모 연결을 요청했습니다.\n'
             f'승인하려면 인증 코드를 입력하세요: {verification_code}'
    )
    
    return {'message': '연결 요청이 전송되었습니다', 'link_id': link.id}

@app.post('/api/v1/student/approve-parent')
async def approve_parent_link(
    link_id: int,
    verification_code: str,
    current_user: dict = Depends(get_current_user)
):
    # 학생만 승인 가능
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail='Only students can approve')
    
    # 연결 요청 확인
    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.id == link_id,
        ParentStudentLink.student_id == current_user['id'],
        ParentStudentLink.status == 'pending'
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail='Link request not found')
    
    # 인증 코드 확인
    if link.verification_code != verification_code:
        raise HTTPException(status_code=400, detail='Invalid verification code')
    
    # 승인 처리
    link.status = 'approved'
    link.approved_at = datetime.utcnow()
    link.approved_by = current_user['id']
    db.commit()
    
    # 학부모에게 알림
    parent = db.query(User).filter(User.id == link.parent_user_id).first()
    send_email(
        to=parent.email,
        subject='학생 연결 승인됨',
        body=f'{current_user["email"]} 학생이 연결을 승인했습니다.'
    )
    
    return {'message': '학부모 연결이 승인되었습니다'}
```

**교사 → 학교 소속 요청:**

```python
@app.post('/api/v1/teacher/request-org')
async def request_org_link(
    org_id: int,
    zone_id: str,
    request_message: str,
    current_user: dict = Depends(get_current_user)
):
    # 교사만 요청 가능
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail='Only teachers can request')
    
    # Organization 확인
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail='Organization not found')
    
    # 중복 요청 확인
    existing = db.query(TeacherOrgLink).filter(
        TeacherOrgLink.teacher_user_id == current_user['id'],
        TeacherOrgLink.org_id == org_id,
        TeacherOrgLink.status == 'pending'
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail='Request already pending')
    
    # 소속 요청 생성
    link = TeacherOrgLink(
        teacher_user_id=current_user['id'],
        org_id=org_id,
        zone_id=zone_id,
        request_message=request_message,
        status='pending'
    )
    db.add(link)
    db.commit()
    
    # org_admin에게 알림
    admins = db.query(User).filter(
        User.org_id == org_id,
        User.role == 'org_admin'
    ).all()
    
    for admin in admins:
        send_email(
            to=admin.email,
            subject='교사 소속 요청',
            body=f'{current_user["email"]} 교사가 소속 요청을 했습니다.\n'
                 f'메시지: {request_message}'
        )
    
    return {'message': '소속 요청이 전송되었습니다', 'link_id': link.id}

@app.post('/api/v1/admin/approve-teacher/{link_id}')
async def approve_teacher_link(
    link_id: int,
    approved: bool,
    rejection_reason: str = None,
    current_user: dict = Depends(get_current_user)
):
    # org_admin만 승인 가능
    if current_user['role'] not in ['org_admin', 'sys_admin']:
        raise HTTPException(status_code=403, detail='Admin only')
    
    # 연결 요청 확인
    link = db.query(TeacherOrgLink).filter(
        TeacherOrgLink.id == link_id,
        TeacherOrgLink.status == 'pending'
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail='Link request not found')
    
    # 승인/거절 처리
    if approved:
        link.status = 'approved'
        link.approved_at = datetime.utcnow()
        link.approved_by = current_user['id']
        
        # 교사의 org_id 업데이트
        teacher = db.query(User).filter(User.id == link.teacher_user_id).first()
        teacher.org_id = link.org_id
        
        message = '교사 소속이 승인되었습니다'
    else:
        link.status = 'rejected'
        link.rejection_reason = rejection_reason
        message = '교사 소속이 거절되었습니다'
    
    db.commit()
    
    # 교사에게 알림
    teacher = db.query(User).filter(User.id == link.teacher_user_id).first()
    send_email(
        to=teacher.email,
        subject='소속 요청 결과',
        body=message + (f'\n사유: {rejection_reason}' if rejection_reason else '')
    )
    
    return {'message': message}
```

### 승인 후 효과

- `parent`는 해당 `student`의 학습 데이터/진행 상황에 접근 가능
- `teacher`는 해당 `org`의 클래스/학생/시험 리소스에 접근 가능
- 이 관계는 **Zone과 무관하게 Global**하게 유효
- 단, Zone/Org별 세부 정책(PBAC)에 따라 일부 데이터 범위는 추가적으로 제한 가능

---

## 7. org_id + zone_id 기반 Access Matrix

### 개념 정의

- **zone_id**: 사용자가 **어느 도시(Zone)에서 활동 중인가**  
- **org_id**: 사용자가 **어느 교육 기관(학교/학원 등)에 속해 있는가**

### 체크 항목

- `zone_id`  
  - 도메인/서브도메인 기반으로 자동 결정 (예: `univprepai.com` → zone_id=100)
- `org_id`  
  - 학생/교사가 속한 기관 식별자
- `role`  
  - RBAC의 기본 역할
- `policies`  
  - 시험 중 AI 사용 여부, 외부 툴 허용 여부 등 세부 정책
- `approvals`  
  - 부모-자녀 / 교사-학생 / 튜터-학생 링크 승인 여부

### 예시 시나리오

학생이 `univprepai.com`에 접속하는 경우:

- `zone_id = 100`  
- `org_id = 1024`  
- `role = 'student'`  
- `policy.exam.ai_enabled = false` (시험 중에는 AI 기능 차단)

위 정보를 기반으로, API Gateway 또는 Policy Engine이 최종 접근 허용/거부를 판단합니다.

---

## 8. MFA / 2FA 정책

### MFA 필요 역할

- `org_admin`
- `teacher`
- `sys_admin`
- `parent` (선택적, 고위험 액션 또는 결제 시 필수화 가능)
- 결제/구독(Checkout) 관련 사용자

### MFA 방식

- Email OTP (One-Time Password)
- TOTP (Google Authenticator 등)
- Passkey / WebAuthn (향후 도입 예정)

MFA 설정 여부 및 적용 강도는 `org_id`, `role`, `risk_score` 등에 따라 세분화 가능.

### 8.1 Passwordless 로그인 옵션

초기 단계에서는 ID/비밀번호 + MFA 조합을 기본으로 사용하되, 중장기적으로 다음과 같은 Passwordless 옵션을 지원합니다.

#### 8.1.1 Passkey / WebAuthn 기반 인증 (FIDO2 호환)

**장점:**
- 비밀번호 없이 생체 인증 (지문, Face ID, Windows Hello)
- 피싱 공격에 강함
- 하드웨어 보안 키 지원 (YubiKey 등)

**구현 흐름:**

```python
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response
)

# 1. Passkey 등록
@app.post('/auth/passkey/register/options')
async def passkey_register_options(current_user: dict = Depends(get_current_user)):
    """Passkey 등록 옵션 생성"""
    options = generate_registration_options(
        rp_id='dreamseedai.com',
        rp_name='DreamSeed MegaCity',
        user_id=str(current_user['id']),
        user_name=current_user['email'],
        user_display_name=current_user['name']
    )
    
    # Challenge를 세션에 저장 (검증용)
    redis_client.setex(
        f'passkey_challenge:{current_user["id"]}',
        300,  # 5분
        options.challenge
    )
    
    return options

@app.post('/auth/passkey/register/verify')
async def passkey_register_verify(
    credential: dict,
    current_user: dict = Depends(get_current_user)
):
    """Passkey 등록 검증"""
    # Challenge 확인
    challenge = redis_client.get(f'passkey_challenge:{current_user["id"]}')
    
    # 검증
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=challenge,
        expected_origin='https://auth.dreamseedai.com',
        expected_rp_id='dreamseedai.com'
    )
    
    # Passkey 저장
    passkey = Passkey(
        user_id=current_user['id'],
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=credential.get('transports', [])
    )
    db.add(passkey)
    db.commit()
    
    return {'message': 'Passkey registered successfully'}

# 2. Passkey 로그인
@app.post('/auth/passkey/login/options')
async def passkey_login_options(email: str):
    """Passkey 로그인 옵션 생성"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    
    # 사용자의 등록된 Passkey 목록
    passkeys = db.query(Passkey).filter(Passkey.user_id == user.id).all()
    
    options = generate_authentication_options(
        rp_id='dreamseedai.com',
        allow_credentials=[
            {'type': 'public-key', 'id': pk.credential_id}
            for pk in passkeys
        ]
    )
    
    # Challenge 저장
    redis_client.setex(
        f'passkey_auth_challenge:{user.id}',
        300,
        options.challenge
    )
    
    return options

@app.post('/auth/passkey/login/verify')
async def passkey_login_verify(credential: dict):
    """Passkey 로그인 검증"""
    # credential_id로 사용자 찾기
    passkey = db.query(Passkey).filter(
        Passkey.credential_id == credential['id']
    ).first()
    
    if not passkey:
        raise HTTPException(status_code=404, detail='Passkey not found')
    
    # Challenge 확인
    challenge = redis_client.get(f'passkey_auth_challenge:{passkey.user_id}')
    
    # 검증
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=challenge,
        credential_public_key=passkey.public_key,
        credential_current_sign_count=passkey.sign_count,
        expected_origin='https://auth.dreamseedai.com',
        expected_rp_id='dreamseedai.com'
    )
    
    # Sign Count 업데이트 (Replay 공격 방지)
    passkey.sign_count = verification.new_sign_count
    db.commit()
    
    # 사용자 정보 조회
    user = db.query(User).filter(User.id == passkey.user_id).first()
    
    # JWT 토큰 발급
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        zone_id=user.primary_zone_id,
        org_id=user.org_id
    )
    refresh_token = create_refresh_token(user_id=user.id)
    
    response = JSONResponse(content={
        'access_token': access_token,
        'token_type': 'bearer'
    })
    
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        domain='.dreamseedai.com',
        secure=True,
        httponly=True,
        samesite='none',
        max_age=14 * 24 * 60 * 60
    )
    
    return response
```

#### 8.1.2 Email Magic Link (일회성 로그인 링크)

**장점:**
- 비밀번호 기억 불필요
- 빠른 로그인
- 이메일 주소 소유권 자동 검증

**구현 흐름:**

```python
import secrets
from datetime import datetime, timedelta

@app.post('/auth/magic-link/request')
async def request_magic_link(email: str):
    """Magic Link 요청"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # 보안상 이유로 항상 성공 메시지 반환 (사용자 존재 여부 노출 방지)
        return {'message': 'If the email exists, a magic link has been sent'}
    
    # Magic Token 생성 (32바이트 랜덤)
    magic_token = secrets.token_urlsafe(32)
    
    # Redis에 저장 (15분 유효)
    redis_client.setex(
        f'magic_token:{magic_token}',
        900,  # 15분
        user.id
    )
    
    # Magic Link 생성
    magic_link = f'https://auth.dreamseedai.com/auth/magic-link/verify?token={magic_token}'
    
    # 이메일 발송
    send_email(
        to=user.email,
        subject='DreamSeed 로그인 링크',
        body=f'다음 링크를 클릭하여 로그인하세요 (15분 유효):\n\n{magic_link}'
    )
    
    return {'message': 'If the email exists, a magic link has been sent'}

@app.get('/auth/magic-link/verify')
async def verify_magic_link(token: str):
    """Magic Link 검증 및 로그인"""
    # Redis에서 토큰 확인
    user_id = redis_client.get(f'magic_token:{token}')
    if not user_id:
        raise HTTPException(status_code=400, detail='Invalid or expired magic link')
    
    # 토큰 삭제 (일회성)
    redis_client.delete(f'magic_token:{token}')
    
    # 사용자 정보 조회
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    
    # JWT 토큰 발급
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        zone_id=user.primary_zone_id,
        org_id=user.org_id
    )
    refresh_token = create_refresh_token(user_id=user.id)
    
    # 로그인 성공 페이지로 Redirect
    response = RedirectResponse(url='https://app.dreamseedai.com/dashboard')
    
    response.set_cookie(
        key='access_token',
        value=access_token,
        domain='.dreamseedai.com',
        secure=True,
        httponly=True,
        samesite='none',
        max_age=900
    )
    
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        domain='.dreamseedai.com',
        secure=True,
        httponly=True,
        samesite='none',
        max_age=14 * 24 * 60 * 60
    )
    
    return response
```

**보안 고려사항:**
- Magic Link는 1회용 (사용 후 즉시 삭제)
- 15분 만료 시간
- HTTPS 필수
- Rate Limiting (1분당 3회 요청 제한)
- IP/User-Agent 로깅

Passwordless 방식이 활성화된 사용자는 비밀번호 없이도 안전하게 로그인할 수 있으며, 고위험 액션에 대해서는 추가 MFA(예: TOTP)를 결합할 수 있습니다.

---

## 9. AI 접근 정책 (시험 중 AI 차단 등)

### 9.1 시험 중 AI 차단 (Critical)

DreamSeedAI 전체 공통 정책:

```pseudo
IF exam.in_progress == true THEN  
   deny(ai_tutor)  
   deny(openai_api)  
   deny(my-ktube.ai endpoints)  
   deny(copilot_assistance)
END
```

- 모든 Zone/도메인에서 동일하게 적용
- CAT / ExamSession 엔진과 실시간 연동
- 시험 종료 시점에만 AI 기능 재개 허용

### 9.2 AI 접근 정책 구현

**Policy Engine 구조:**

```python
class AIAccessPolicy:
    """AI 접근 정책 엔진"""
    
    @staticmethod
    def check_ai_access(
        user_id: int,
        zone_id: str,
        org_id: int,
        ai_service: str,  # 'tutor' / 'completion' / 'speech' / 'vision'
        context: dict = None
    ) -> tuple[bool, str]:
        """
        AI 서비스 접근 권한 확인
        
        Returns:
            (allowed: bool, reason: str)
        """
        
        # 1. 시험 중인지 확인 (최우선 차단)
        if AIAccessPolicy._is_exam_in_progress(user_id):
            return False, "AI access blocked during exam"
        
        # 2. Role 기반 기본 권한 확인
        user = db.query(User).filter(User.id == user_id).first()
        if user.role == 'guest':
            return False, "Guests cannot access AI services"
        
        # 3. Zone별 AI 정책 확인
        zone_policy = AIAccessPolicy._get_zone_policy(zone_id, ai_service)
        if not zone_policy['enabled']:
            return False, f"AI service '{ai_service}' not available in zone {zone_id}"
        
        # 4. Org별 AI 정책 확인
        org_policy = AIAccessPolicy._get_org_policy(org_id, ai_service)
        if not org_policy['enabled']:
            return False, f"AI service disabled by organization policy"
        
        # 5. 사용량 제한 확인 (Rate Limiting)
        usage_key = f'ai_usage:{user_id}:{ai_service}:{datetime.utcnow().strftime("%Y%m%d")}'
        current_usage = int(redis_client.get(usage_key) or 0)
        
        if user.role == 'student':
            daily_limit = org_policy.get('student_daily_limit', 100)
        elif user.role == 'teacher':
            daily_limit = org_policy.get('teacher_daily_limit', 500)
        else:
            daily_limit = 1000
        
        if current_usage >= daily_limit:
            return False, f"Daily AI usage limit exceeded ({daily_limit})"
        
        # 6. 특수 조건 확인 (Context 기반)
        if context:
            # 예: 자정 이후 학생의 AI 사용 제한
            if user.role == 'student' and context.get('hour', 0) >= 23:
                org_night_policy = org_policy.get('allow_night_usage', False)
                if not org_night_policy:
                    return False, "AI access restricted during night hours"
        
        # ✅ 모든 체크 통과
        return True, "AI access granted"
    
    @staticmethod
    def _is_exam_in_progress(user_id: int) -> bool:
        """현재 진행 중인 시험이 있는지 확인"""
        active_exam = db.query(ExamAttempt).filter(
            ExamAttempt.user_id == user_id,
            ExamAttempt.status == 'in_progress',
            ExamAttempt.finished_at.is_(None)
        ).first()
        
        return active_exam is not None
    
    @staticmethod
    def _get_zone_policy(zone_id: str, ai_service: str) -> dict:
        """Zone별 AI 정책 조회"""
        # 기본 Zone 정책
        DEFAULT_POLICIES = {
            'univ': {'ai_tutor': True, 'ai_completion': True, 'ai_speech': True},
            'mpc': {'ai_tutor': True, 'ai_completion': False, 'ai_speech': False},  # 무료 Zone은 제한적
            'ktube-ai': {'ai_tutor': True, 'ai_completion': True, 'ai_speech': True, 'ai_vision': True}
        }
        
        zone_policy = DEFAULT_POLICIES.get(zone_id, {})
        return {'enabled': zone_policy.get(ai_service, False)}
    
    @staticmethod
    def _get_org_policy(org_id: int, ai_service: str) -> dict:
        """Organization별 AI 정책 조회"""
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {'enabled': False}
        
        # org.ai_policy (JSONB)
        # {
        #   "ai_tutor": {"enabled": true, "student_daily_limit": 50},
        #   "ai_completion": {"enabled": true, "student_daily_limit": 100}
        # }
        ai_policy = org.ai_policy or {}
        service_policy = ai_policy.get(ai_service, {'enabled': True, 'student_daily_limit': 100})
        
        return service_policy

# API Middleware로 AI 접근 제어
@app.post('/api/v1/ai/{service}')
async def ai_service_endpoint(
    service: str,
    prompt: str,
    current_user: dict = Depends(get_current_user),
    context: dict = Depends(get_tenant_context)
):
    """AI 서비스 엔드포인트"""
    
    # AI 접근 권한 확인
    allowed, reason = AIAccessPolicy.check_ai_access(
        user_id=current_user['id'],
        zone_id=context['zone_id'],
        org_id=context['org_id'],
        ai_service=service,
        context={'hour': datetime.utcnow().hour}
    )
    
    if not allowed:
        # Audit Log 기록
        log_ai_access_denial(
            user_id=current_user['id'],
            service=service,
            reason=reason
        )
        raise HTTPException(status_code=403, detail=reason)
    
    # AI 서비스 호출
    response = await call_ai_service(service, prompt, context)
    
    # 사용량 증가
    usage_key = f'ai_usage:{current_user["id"]}:{service}:{datetime.utcnow().strftime("%Y%m%d")}'
    redis_client.incr(usage_key)
    redis_client.expire(usage_key, 86400)  # 24시간
    
    # Audit Log 기록
    log_ai_usage(
        user_id=current_user['id'],
        zone_id=context['zone_id'],
        org_id=context['org_id'],
        service=service,
        prompt=prompt,
        response=response
    )
    
    return response
```

### 9.3 시험 중 AI 차단 - Frontend 구현

```typescript
// Frontend: 시험 중 AI 기능 비활성화
import { useExamStatus } from '@/hooks/useExamStatus';

export function AITutorButton() {
  const { isExamInProgress } = useExamStatus();
  
  return (
    <button
      disabled={isExamInProgress}
      className={isExamInProgress ? 'opacity-50 cursor-not-allowed' : ''}
      title={isExamInProgress ? '시험 중에는 AI 기능을 사용할 수 없습니다' : ''}
    >
      AI 튜터 질문하기
    </button>
  );
}

// Hook: 시험 상태 실시간 감지
export function useExamStatus() {
  const [isExamInProgress, setIsExamInProgress] = useState(false);
  
  useEffect(() => {
    // WebSocket으로 실시간 시험 상태 수신
    const ws = new WebSocket('wss://api.dreamseedai.com/ws/exam-status');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setIsExamInProgress(data.exam_in_progress);
    };
    
    return () => ws.close();
  }, []);
  
  return { isExamInProgress };
}
```

### 9.4 AI 정책 매트릭스

| Role | Zone | AI Tutor | AI Completion | Speech | Vision | Daily Limit |
|------|------|----------|---------------|--------|--------|-------------|
| student | univ | ✅ | ✅ | ✅ | ❌ | 50 |
| student | skill | ✅ | ✅ | ✅ | ❌ | 50 |
| student | ktube-ai | ✅ | ✅ | ✅ | ✅ | 100 |
| student | mpc | ✅ | ❌ | ❌ | ❌ | 20 (무료) |
| teacher | all | ✅ | ✅ | ✅ | ✅ | 500 |
| parent | all | ✅ | ❌ | ❌ | ❌ | 30 |
| **시험 중** | **all** | **❌** | **❌** | **❌** | **❌** | **0** |

---

## 🔍 10. Audit & Logging (Auditable Identity)

모든 인증/승인/로그인/로그아웃 이벤트는 중앙 `audit_logs` 테이블에 기록합니다.

### audit_logs 필드 예시

- `user_id`
- `event_type` (login, logout, token_refresh, policy_violation 등)
- `resource`
- `details_json`
- `ip`
- `user_agent`
- `timestamp`

이를 통해 Zone/Domain과 무관하게 100% 투명한 추적이 가능합니다.

---

## 🔒 11. Security Architecture Summary

### User Identity

- Global DreamSeed ID  
- 9개 도메인 전체에서 **단일 user_id** 사용

### Auth

- OIDC Central Auth (`auth.dreamseedai.com`)  
- JWT Access Token (15분)  
- Refresh Token (14일)  
- Token Rotation  

### Cookie

- `Secure`  
- `SameSite=None`  
- `Domain=.dreamseedai.com`

### Access Control

- RBAC + PBAC  
- Parent Approval / Teacher Approval  
- Zone/Org 기반 정책  

### Security

- MFA  
- Brute-force protection  
- IP throttling  
- Global audit trail

---

## 🏁 12. 결론

이 문서는 DreamSeedAI MegaCity 전체의 통합 SSO·인증·정책 아키텍처를 규정합니다.

### 핵심 구성 요소 요약

✅ **DreamSeed ID (Global Identity)**
- 9개 도메인 전체에서 단일 user_id 사용
- Zone 이동 시에도 계정 유지

✅ **Multi-Domain SSO**
- OpenID Connect + OAuth2 기반
- Cross-site cookie (.dreamseedai.com)
- app.univprepai.com ↔ app.skillprepai.com 자동 로그인

✅ **Token 관리**
- JWT Access Token (15분)
- Refresh Token (14일) with Rotation
- Redis 기반 Revocation List

✅ **승인 워크플로우**
- Parent–Student linking (6자리 인증 코드)
- Teacher–School linking (org_admin 승인)

✅ **RBAC + PBAC**
- 7가지 기본 역할 (student, parent, teacher, tutor, org_admin, sys_admin, guest)
- 조건 기반 정책 (시험 중, Zone별, Org별)

✅ **MFA/2FA**
- Email OTP, TOTP (Google Authenticator)
- 고위험 역할 필수 적용

✅ **Passwordless 로그인**
- WebAuthn/Passkey (FIDO2)
- Email Magic Link (일회성)

✅ **AI 접근 정책**
- 시험 중 AI 완전 차단
- Zone/Org별 사용량 제한
- Role별 Daily Limit

### 이 기반 위에 구현되는 시스템

- ✅ Multi-domain Login  
- ✅ Teacher/Parent Dashboard  
- ✅ K-Zone AI 기능  
- ✅ Adaptive Exam (CAT)  
- ✅ Multi-tenant 데이터 분리  
- ✅ AI 모델 선택 정책  
- ✅ Cross-zone SSO  
- ✅ Global Audit Trail  

모두 일관된 방식으로 작동합니다.

---

## 📚 13. 관련 문서

### 내부 문서
- `MEGACITY_DOMAIN_ARCHITECTURE.md` - 도메인 전략 및 DNS 설정
- `MEGACITY_NETWORK_ARCHITECTURE.md` - 네트워크 아키텍처 및 보안
- `MEGACITY_TENANT_ARCHITECTURE.md` - Multi-zone/Multi-tenant 구조
- `backend/API_GUIDE.md` - FastAPI Multi-tenant 구현 가이드
- `docs/RBAC_GUIDE.md` - 권한 관리 상세 가이드

### 외부 참고
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OAuth 2.0 Authorization Code Flow with PKCE](https://oauth.net/2/pkce/)
- [WebAuthn / FIDO2 Specification](https://www.w3.org/TR/webauthn-2/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**MEGACITY_AUTH_SSO_ARCHITECTURE v1.0 완성** 🛡️

DreamSeedAI MegaCity의 통합 인증·SSO·정책 체계가 완전히 문서화되었습니다. 이 문서를 기반으로 안전하고 확장 가능한 인증 시스템을 구축하세요!
