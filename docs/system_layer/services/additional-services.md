# DreamSeedAI: 기타 주요 서비스 상세

DreamSeedAI 시스템 계층의 추가 핵심 서비스들에 대한 상세 설명입니다.

## 목차

1. [사용자 관리 서비스](#1-사용자-관리-서비스)
2. [인증/인가 서비스](#2-인증인가-서비스)
3. [결제 서비스](#3-결제-서비스)
4. [외부 연동 API](#4-외부-연동-api)
5. [기술 스택](#5-기술-스택)

---

## 1. 사용자 관리 서비스 (User Management Service)

### 개요

**목표**: DreamSeedAI 플랫폼의 모든 사용자 계정을 안전하고 효율적으로 관리합니다.

### 주요 기능

#### 1.1 사용자 가입 및 등록

```python
# FastAPI 사용자 등록 엔드포인트
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

router = APIRouter(prefix="/api/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "student"  # student, teacher, admin

@router.post("/register")
async def register_user(user: UserCreate):
    """신규 사용자 등록"""
    # 중복 검사
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 비밀번호 해싱
    hashed_password = pwd_context.hash(user.password)

    # 사용자 생성
    new_user = {
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed_password,
        "role": user.role,
        "created_at": datetime.utcnow(),
        "is_active": True
    }

    result = await db.users.insert_one(new_user)
    return {"user_id": str(result.inserted_id), "message": "User created successfully"}
```

#### 1.2 사용자 프로필 관리

```sql
-- PostgreSQL 사용자 스키마
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    role VARCHAR(50) NOT NULL DEFAULT 'student',
    grade_level INTEGER,
    school_id INTEGER REFERENCES schools(school_id),
    profile_image_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE
);

-- 사용자-학급 연결 테이블
CREATE TABLE user_classes (
    user_class_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    class_id INTEGER REFERENCES classes(class_id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'student',  -- student, teacher, assistant
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, class_id)
);

-- 인덱스
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_user_classes_user ON user_classes(user_id);
CREATE INDEX idx_user_classes_class ON user_classes(class_id);
```

#### 1.3 프로필 업데이트 API

```python
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    grade_level: Optional[int] = None
    profile_image_url: Optional[str] = None
    preferences: Optional[Dict] = None

@router.patch("/profile/{user_id}")
@require_policy("user_management", "update_profile")
async def update_profile(user_id: int, update: UserUpdate, current_user = Depends(get_current_user)):
    """사용자 프로필 업데이트"""
    # 권한 확인 (본인 또는 관리자만)
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # 업데이트할 필드만 추출
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    result = await db.execute(
        """
        UPDATE users
        SET full_name = COALESCE(:full_name, full_name),
            grade_level = COALESCE(:grade_level, grade_level),
            profile_image_url = COALESCE(:profile_image_url, profile_image_url),
            preferences = COALESCE(:preferences, preferences),
            updated_at = :updated_at
        WHERE user_id = :user_id
        RETURNING *
        """,
        {**update_data, "user_id": user_id}
    )

    return result.fetchone()
```

#### 1.4 학급 배정 관리

```python
@router.post("/classes/{class_id}/assign")
@require_policy("user_management", "assign_class")
async def assign_user_to_class(
    class_id: int,
    user_id: int,
    role: str = "student",
    current_user = Depends(get_current_user)
):
    """사용자를 학급에 배정"""
    # 교사 또는 관리자만 가능
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Only teachers or admins can assign users")

    # 학급 존재 확인
    class_exists = await db.classes.find_one({"class_id": class_id})
    if not class_exists:
        raise HTTPException(status_code=404, detail="Class not found")

    # 중복 배정 확인
    existing = await db.user_classes.find_one({
        "user_id": user_id,
        "class_id": class_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="User already assigned to this class")

    # 배정
    assignment = {
        "user_id": user_id,
        "class_id": class_id,
        "role": role,
        "joined_at": datetime.utcnow()
    }

    result = await db.user_classes.insert_one(assignment)

    # 감사 로그
    await audit_log("user_class_assignment", {
        "assigned_by": current_user.user_id,
        "user_id": user_id,
        "class_id": class_id,
        "role": role
    })

    return {"message": "User assigned to class successfully"}
```

---

## 2. 인증/인가 서비스 (Authentication/Authorization Service)

### 개요

**목표**: 사용자 인증 및 권한 부여를 중앙 집중식으로 관리하여 시스템 보안을 강화합니다.

### 구현 기술

- **JWT (JSON Web Tokens)**: 사용자 인증 정보를 안전하게 전달하고 검증
- **OAuth 2.0**: 외부 서비스에 대한 접근 권한 관리
- **OIDC (OpenID Connect)**: 소셜 로그인 지원

### 2.1 JWT 기반 인증

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int
    email: str
    role: str
    exp: datetime

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """액세스 토큰 생성"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """리프레시 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> TokenData:
    """토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return TokenData(
            user_id=user_id,
            email=email,
            role=role,
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
```

### 2.2 로그인 엔드포인트

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """사용자 로그인"""
    # 사용자 조회
    user = await db.execute(
        "SELECT * FROM users WHERE email = :email",
        {"email": form_data.username}
    )
    user = user.fetchone()

    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # 토큰 생성
    token_data = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # 마지막 로그인 시간 업데이트
    await db.execute(
        "UPDATE users SET last_login = :now WHERE user_id = :user_id",
        {"now": datetime.utcnow(), "user_id": user.user_id}
    )

    # 감사 로그
    await audit_log("user_login", {
        "user_id": user.user_id,
        "email": user.email,
        "ip_address": request.client.host
    })

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )
```

### 2.3 OAuth 2.0 소셜 로그인

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()

# Google OAuth 설정
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/oauth/google")
async def google_login(request: Request):
    """Google OAuth 로그인 시작"""
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/oauth/google/callback")
async def google_callback(request: Request):
    """Google OAuth 콜백"""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')

    # 사용자 조회 또는 생성
    user = await db.users.find_one({"email": user_info['email']})

    if not user:
        # 신규 사용자 생성
        user = {
            "email": user_info['email'],
            "username": user_info.get('name', user_info['email'].split('@')[0]),
            "full_name": user_info.get('name'),
            "profile_image_url": user_info.get('picture'),
            "is_verified": True,
            "oauth_provider": "google",
            "oauth_id": user_info['sub'],
            "created_at": datetime.utcnow()
        }
        result = await db.users.insert_one(user)
        user['user_id'] = result.inserted_id

    # JWT 토큰 생성
    token_data = {
        "user_id": user['user_id'],
        "email": user['email'],
        "role": user.get('role', 'student')
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # 프론트엔드로 리다이렉트 (토큰 전달)
    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    )
```

### 2.4 권한 검사 미들웨어

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """현재 인증된 사용자 조회"""
    token_data = await verify_token(token)

    # 사용자 활성 상태 확인
    user = await db.execute(
        "SELECT is_active FROM users WHERE user_id = :user_id",
        {"user_id": token_data.user_id}
    )
    user = user.fetchone()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")

    return token_data

def require_role(allowed_roles: List[str]):
    """역할 기반 권한 검사 데코레이터"""
    def role_checker(current_user: TokenData = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{current_user.role}' not authorized. Required: {allowed_roles}"
            )
        return current_user
    return role_checker

# 사용 예시
@router.get("/admin/users")
async def list_all_users(current_user = Depends(require_role(["admin"]))):
    """관리자만 접근 가능한 사용자 목록"""
    users = await db.users.find().to_list(length=None)
    return users
```

---

## 3. 결제 서비스 (Payment Service)

### 개요

**목표**: 구독형 상품에 대한 결제 처리 및 라이선스 관리를 담당합니다.

### 주요 기능

#### 3.1 결제 처리 (Stripe 연동)

```python
import stripe
from decimal import Decimal

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class SubscriptionPlan(BaseModel):
    plan_id: int
    name: str
    price: Decimal
    currency: str = "USD"
    interval: str  # month, year
    features: Dict

@router.post("/payments/create-checkout-session")
@require_policy("payment", "create_checkout")
async def create_checkout_session(
    plan_id: int,
    current_user = Depends(get_current_user)
):
    """Stripe 결제 세션 생성"""
    # 플랜 조회
    plan = await db.execute(
        "SELECT * FROM subscription_plans WHERE plan_id = :plan_id",
        {"plan_id": plan_id}
    )
    plan = plan.fetchone()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Stripe Checkout Session 생성
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': plan.currency,
                    'product_data': {
                        'name': plan.name,
                        'description': plan.description,
                    },
                    'unit_amount': int(plan.price * 100),  # cents
                    'recurring': {
                        'interval': plan.interval,
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/payment/cancel",
            metadata={
                'user_id': current_user.user_id,
                'plan_id': plan_id
            }
        )

        return {"checkout_url": checkout_session.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### 3.2 구독 관리

```sql
-- 구독 플랜 테이블
CREATE TABLE subscription_plans (
    plan_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    interval VARCHAR(20) NOT NULL,  -- month, year
    features JSONB DEFAULT '{}',
    seat_count INTEGER DEFAULT 1,  -- 학교 라이선스용
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 구독 테이블
CREATE TABLE user_subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES subscription_plans(plan_id),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL,  -- active, canceled, past_due
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 결제 내역 테이블
CREATE TABLE payment_transactions (
    transaction_id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES user_subscriptions(subscription_id),
    stripe_payment_intent_id VARCHAR(255),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL,  -- succeeded, failed, refunded
    payment_method VARCHAR(50),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_transactions_subscription ON payment_transactions(subscription_id);
```

#### 3.3 Stripe Webhook 처리

```python
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Stripe 웹훅 이벤트 처리"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 이벤트 타입별 처리
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_completed(session)

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        await handle_subscription_updated(subscription)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await handle_subscription_canceled(subscription)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        await handle_payment_succeeded(invoice)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        await handle_payment_failed(invoice)

    return {"status": "success"}

async def handle_checkout_completed(session):
    """결제 완료 처리"""
    user_id = int(session['metadata']['user_id'])
    plan_id = int(session['metadata']['plan_id'])

    # 구독 생성
    subscription_data = {
        "user_id": user_id,
        "plan_id": plan_id,
        "stripe_subscription_id": session['subscription'],
        "status": "active",
        "current_period_start": datetime.fromtimestamp(session['current_period_start']),
        "current_period_end": datetime.fromtimestamp(session['current_period_end'])
    }

    await db.user_subscriptions.insert_one(subscription_data)

    # 결제 트랜잭션 기록
    transaction_data = {
        "stripe_payment_intent_id": session['payment_intent'],
        "amount": session['amount_total'] / 100,
        "currency": session['currency'],
        "status": "succeeded",
        "payment_method": "card"
    }

    await db.payment_transactions.insert_one(transaction_data)

    # 이메일 알림
    await send_subscription_confirmation_email(user_id, plan_id)
```

#### 3.4 학교 라이선스 관리

```python
class SchoolLicense(BaseModel):
    license_id: int
    school_id: int
    plan_id: int
    total_seats: int
    used_seats: int
    expires_at: datetime

@router.post("/licenses/assign-seat")
@require_policy("payment", "manage_license")
async def assign_seat_to_user(
    license_id: int,
    user_id: int,
    current_user = Depends(get_current_user)
):
    """라이선스 좌석을 사용자에게 할당"""
    # 라이선스 조회
    license = await db.execute(
        """
        SELECT * FROM school_licenses
        WHERE license_id = :license_id AND expires_at > NOW()
        """,
        {"license_id": license_id}
    )
    license = license.fetchone()

    if not license:
        raise HTTPException(status_code=404, detail="License not found or expired")

    # 좌석 가용성 확인
    if license.used_seats >= license.total_seats:
        raise HTTPException(status_code=400, detail="No available seats")

    # 좌석 할당
    await db.execute(
        """
        INSERT INTO license_assignments (license_id, user_id, assigned_at)
        VALUES (:license_id, :user_id, NOW())
        ON CONFLICT (license_id, user_id) DO NOTHING
        """,
        {"license_id": license_id, "user_id": user_id}
    )

    # 사용 좌석 수 증가
    await db.execute(
        """
        UPDATE school_licenses
        SET used_seats = used_seats + 1
        WHERE license_id = :license_id
        """,
        {"license_id": license_id}
    )

    return {"message": "Seat assigned successfully"}
```

---

## 4. 외부 연동 API (External Integration API)

### 개요

**목표**: DreamSeedAI를 다른 시스템과 통합하고, 데이터 교환을 용이하게 합니다.

### 4.1 LTI (Learning Tools Interoperability) 연동

```python
from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskRequest
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration

# LTI 설정
lti_config = ToolConfJsonFile('lti_config.json')

@router.post("/lti/login")
async def lti_login(request: Request):
    """LTI 1.3 로그인 시작"""
    tool_conf = lti_config
    launch_data_storage = get_launch_data_storage()

    oidc_login = FlaskOIDCLogin.new(
        FlaskRequest(request),
        tool_conf,
        launch_data_storage=launch_data_storage
    )

    return oidc_login.redirect(get_launch_url())

@router.post("/lti/launch")
async def lti_launch(request: Request):
    """LTI 리소스 런칭"""
    tool_conf = lti_config
    launch_data_storage = get_launch_data_storage()

    message_launch = FlaskMessageLaunch.from_cache(
        launch_id,
        FlaskRequest(request),
        tool_conf,
        launch_data_storage=launch_data_storage
    )

    # 사용자 정보 추출
    user_data = message_launch.get_launch_data()
    email = user_data.get('email')
    name = user_data.get('name')
    role = user_data.get('https://purl.imsglobal.org/spec/lti/claim/roles')[0]

    # 사용자 조회 또는 생성
    user = await get_or_create_lti_user(email, name, role)

    # JWT 토큰 생성
    access_token = create_access_token({
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role
    })

    # LMS로부터 제공된 context (과정/클래스) 정보
    context = user_data.get('https://purl.imsglobal.org/spec/lti/claim/context')

    return RedirectResponse(
        url=f"{FRONTEND_URL}/lti/session?token={access_token}&context={context['id']}"
    )
```

### 4.2 API Gateway 구조

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import httpx

app = FastAPI(title="DreamSeedAI API Gateway")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.dreamseedai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트만 허용
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.dreamseedai.com", "*.dreamseedai.com"]
)

# 서비스 엔드포인트 매핑
SERVICE_ROUTES = {
    "/api/users": "http://user-service:8001",
    "/api/auth": "http://auth-service:8002",
    "/api/content": "http://content-service:8003",
    "/api/assessments": "http://assessment-service:8004",
    "/api/analytics": "http://analytics-service:8005",
    "/api/payments": "http://payment-service:8006",
}

@app.middleware("http")
async def api_gateway_middleware(request: Request, call_next):
    """API Gateway 라우팅 미들웨어"""
    path = request.url.path

    # 서비스 엔드포인트 찾기
    service_url = None
    for prefix, url in SERVICE_ROUTES.items():
        if path.startswith(prefix):
            service_url = url + path[len(prefix):]
            break

    if not service_url:
        # 로컬 라우트
        return await call_next(request)

    # 요청 전달
    async with httpx.AsyncClient() as client:
        headers = dict(request.headers)
        headers.pop('host', None)

        response = await client.request(
            method=request.method,
            url=service_url,
            headers=headers,
            content=await request.body(),
            params=request.query_params
        )

    # 응답 반환
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
```

### 4.3 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.get("/api/public/data")
@limiter.limit("100/hour")
async def public_api(request: Request):
    """Public API - Rate Limited"""
    return {"message": "Public data"}

@router.get("/api/premium/data")
@limiter.limit("1000/hour")
async def premium_api(request: Request, current_user = Depends(get_current_user)):
    """Premium API - Higher Rate Limit"""
    return {"message": "Premium data"}
```

### 4.4 API 문서 및 버전 관리

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# API 버전별 라우터
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

# v1 엔드포인트
@v1_router.get("/users/{user_id}")
async def get_user_v1(user_id: int):
    """V1: 기본 사용자 정보"""
    return {"user_id": user_id, "version": "v1"}

# v2 엔드포인트 (확장된 정보)
@v2_router.get("/users/{user_id}")
async def get_user_v2(user_id: int):
    """V2: 확장된 사용자 정보"""
    return {
        "user_id": user_id,
        "version": "v2",
        "extended_profile": {...}
    }

app.include_router(v1_router)
app.include_router(v2_router)

# OpenAPI 스키마 커스터마이징
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="DreamSeedAI Public API",
        version="2.0.0",
        description="""
        DreamSeedAI Platform API

        ## Authentication
        Use Bearer token in Authorization header

        ## Rate Limits
        - Free tier: 100 requests/hour
        - Premium tier: 1000 requests/hour
        """,
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

---

## 5. 기술 스택

### 프로그래밍 언어

- **Python 3.11+**: 백엔드 서비스
- **TypeScript/JavaScript**: 프론트엔드 및 Node.js 서비스

### 프레임워크

- **FastAPI**: REST API 서버
- **React/Next.js**: 프론트엔드 애플리케이션
- **Pydantic**: 데이터 검증

### 인증 & 보안

- **JWT (JSON Web Tokens)**: 토큰 기반 인증
- **OAuth 2.0**: 소셜 로그인 및 서드파티 연동
- **OIDC (OpenID Connect)**: 표준 인증 프로토콜
- **bcrypt**: 비밀번호 해싱
- **python-jose**: JWT 구현

### 결제

- **Stripe API**: 구독 결제 및 청구
- **PayPal API**: 대체 결제 수단

### 데이터베이스

- **PostgreSQL**: 관계형 데이터 저장
- **Redis**: 세션 캐싱, Rate Limiting

### 메시지 큐

- **Apache Kafka**: 이벤트 스트리밍
- **RabbitMQ**: 비동기 작업 큐

### 모니터링 & 로깅

- **Prometheus**: 메트릭 수집
- **Grafana**: 대시보드
- **ELK Stack**: 로그 집계 및 분석

### 인프라

- **Docker**: 컨테이너화
- **Kubernetes**: 오케스트레이션
- **Nginx**: 리버스 프록시

---

## 6. 요약

DreamSeedAI의 추가 핵심 서비스들은 다음과 같이 플랫폼의 완성도를 높입니다:

1. **사용자 관리**: 안전하고 효율적인 계정 관리
2. **인증/인가**: JWT, OAuth 2.0 기반 보안 강화
3. **결제**: Stripe 연동을 통한 구독 및 라이선스 관리
4. **외부 연동**: LTI, API Gateway를 통한 확장성

모든 서비스는 **OPA 거버넌스 정책**과 통합되어 일관된 보안 및 감사 체계를 유지합니다.

---

**참고 문서**:

- [사용자 관리 서비스](./user-management.md) (향후 추가 예정)
- [인증 서비스](./authentication.md) (향후 추가 예정)
- [결제 서비스](./payment-service.md) (향후 추가 예정)
- [Governance Integration Examples](../governance-integration/examples.md)
