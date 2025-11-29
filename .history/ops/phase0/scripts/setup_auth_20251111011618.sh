#!/bin/bash
# JWT 인증 및 RBAC 시스템 설정
# 실행: ./setup_auth.sh

set -e

GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_info "인증/RBAC 시스템 설정 시작..."

# 1. 인증 설정 디렉토리 생성
AUTH_DIR="../configs/auth"
mkdir -p $AUTH_DIR

# 2. JWT 인증 모듈 생성
cat > $AUTH_DIR/auth.py <<'AUTH_CODE'
"""
JWT 인증 및 RBAC 시스템
역할: student, parent, teacher, admin
"""

from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os


# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1시간
REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30일

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer 스키마
security = HTTPBearer()


# 역할 정의
class Role:
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"
    
    ALL_ROLES = [STUDENT, PARENT, TEACHER, ADMIN]


# Pydantic 모델
class TokenData(BaseModel):
    user_id: str
    email: str
    role: str
    permissions: List[str] = []


class User(BaseModel):
    id: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool = True


# 비밀번호 해싱/검증
def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT 토큰 생성
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Access Token 생성"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Refresh Token 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# JWT 토큰 검증
def verify_token(token: str) -> TokenData:
    """JWT 토큰 검증 및 데이터 추출"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None or email is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        # 역할별 권한 설정
        permissions = get_permissions(role)
        
        return TokenData(
            user_id=user_id,
            email=email,
            role=role,
            permissions=permissions
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


# 권한 관리
def get_permissions(role: str) -> List[str]:
    """역할별 권한 반환"""
    permissions_map = {
        Role.STUDENT: [
            "problem:view",
            "problem:solve",
            "solution:submit",
            "progress:view_own",
        ],
        Role.PARENT: [
            "problem:view",
            "progress:view_children",
            "report:view",
        ],
        Role.TEACHER: [
            "problem:view",
            "problem:create",
            "problem:edit",
            "student:view",
            "progress:view_all",
            "report:create",
        ],
        Role.ADMIN: [
            "problem:*",
            "user:*",
            "system:*",
            "analytics:*",
        ],
    }
    return permissions_map.get(role, [])


def has_permission(token_data: TokenData, required_permission: str) -> bool:
    """권한 확인"""
    # Admin은 모든 권한 보유
    if token_data.role == Role.ADMIN:
        return True
    
    # 와일드카드 권한 체크 (예: "problem:*")
    for perm in token_data.permissions:
        if perm.endswith(":*"):
            category = perm.split(":")[0]
            if required_permission.startswith(f"{category}:"):
                return True
    
    return required_permission in token_data.permissions


# FastAPI Dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """현재 로그인된 사용자 정보 반환"""
    token = credentials.credentials
    return verify_token(token)


def require_role(*allowed_roles: str):
    """특정 역할만 접근 가능하도록 제한하는 데코레이터"""
    async def role_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker


def require_permission(required_permission: str):
    """특정 권한이 있어야 접근 가능하도록 제한하는 데코레이터"""
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if not has_permission(current_user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {required_permission}",
            )
        return current_user
    return permission_checker
AUTH_CODE

# 3. FastAPI 통합 예제 생성
cat > $AUTH_DIR/fastapi_auth_example.py <<'FASTAPI_AUTH_EXAMPLE'
"""
FastAPI JWT 인증 통합 예제
"""

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from auth import (
    TokenData,
    Role,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    get_current_user,
    require_role,
    require_permission,
)

app = FastAPI(title="DreamSeed Auth API")


# 요청/응답 모델
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # student, parent, teacher


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# 임시 사용자 DB (실제로는 PostgreSQL 사용)
fake_users_db = {
    "student@example.com": {
        "id": "user_001",
        "email": "student@example.com",
        "hashed_password": hash_password("password123"),
        "role": Role.STUDENT,
        "full_name": "김학생",
    },
    "teacher@example.com": {
        "id": "user_002",
        "email": "teacher@example.com",
        "hashed_password": hash_password("password123"),
        "role": Role.TEACHER,
        "full_name": "이선생",
    },
    "admin@example.com": {
        "id": "user_003",
        "email": "admin@example.com",
        "hashed_password": hash_password("admin123"),
        "role": Role.ADMIN,
        "full_name": "관리자",
    },
}


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """로그인"""
    user = fake_users_db.get(request.email)
    
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # JWT 토큰 생성
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@app.post("/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """회원가입"""
    if request.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    if request.role not in [Role.STUDENT, Role.PARENT, Role.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Use: student, parent, teacher",
        )
    
    # 사용자 생성
    user_id = f"user_{len(fake_users_db) + 1:03d}"
    fake_users_db[request.email] = {
        "id": user_id,
        "email": request.email,
        "hashed_password": hash_password(request.password),
        "role": request.role,
        "full_name": request.full_name,
    }
    
    # JWT 토큰 생성
    token_data = {
        "sub": user_id,
        "email": request.email,
        "role": request.role,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@app.get("/auth/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """현재 로그인된 사용자 정보"""
    return current_user


@app.get("/api/problems")
async def get_problems(current_user: TokenData = Depends(get_current_user)):
    """문제 목록 조회 (모든 역할 접근 가능)"""
    return {"problems": [], "user": current_user.email}


@app.post("/api/problems")
async def create_problem(
    current_user: TokenData = Depends(require_role(Role.TEACHER, Role.ADMIN))
):
    """문제 생성 (선생님, 관리자만 가능)"""
    return {"message": "Problem created", "created_by": current_user.email}


@app.get("/api/analytics")
async def get_analytics(
    current_user: TokenData = Depends(require_permission("analytics:view"))
):
    """분석 데이터 조회 (관리자만 가능)"""
    return {"analytics": "data", "requested_by": current_user.email}


@app.get("/health")
async def health_check():
    """헬스체크 (인증 불필요)"""
    return {"status": "ok"}
FASTAPI_AUTH_EXAMPLE

# 4. 인증 테스트 스크립트 생성
cat > $AUTH_DIR/test_auth.sh <<'TEST_AUTH'
#!/bin/bash
# JWT 인증 테스트 스크립트

set -e

API_URL="http://localhost:8000"

echo "=========================================="
echo "   JWT 인증 시스템 테스트"
echo "=========================================="
echo ""

# 1. 학생 로그인
echo "1. 학생 로그인 테스트..."
STUDENT_TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"student@example.com","password":"password123"}' \
    | jq -r '.access_token')

if [ -n "$STUDENT_TOKEN" ]; then
    echo "✓ 학생 로그인 성공"
else
    echo "✗ 학생 로그인 실패"
    exit 1
fi

# 2. 선생님 로그인
echo "2. 선생님 로그인 테스트..."
TEACHER_TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"teacher@example.com","password":"password123"}' \
    | jq -r '.access_token')

if [ -n "$TEACHER_TOKEN" ]; then
    echo "✓ 선생님 로그인 성공"
else
    echo "✗ 선생님 로그인 실패"
    exit 1
fi

# 3. 학생이 문제 조회 (성공해야 함)
echo "3. 학생이 문제 조회..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/problems" \
    -H "Authorization: Bearer $STUDENT_TOKEN")

if [ "$RESPONSE" -eq 200 ]; then
    echo "✓ 학생 문제 조회 성공"
else
    echo "✗ 학생 문제 조회 실패 (HTTP $RESPONSE)"
    exit 1
fi

# 4. 학생이 문제 생성 시도 (403 에러 예상)
echo "4. 학생이 문제 생성 시도 (403 예상)..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/problems" \
    -H "Authorization: Bearer $STUDENT_TOKEN")

if [ "$RESPONSE" -eq 403 ]; then
    echo "✓ 학생 권한 제한 정상 작동 (HTTP 403)"
else
    echo "✗ 권한 제한 실패 (HTTP $RESPONSE, 예상: 403)"
    exit 1
fi

# 5. 선생님이 문제 생성 (성공해야 함)
echo "5. 선생님이 문제 생성..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/problems" \
    -H "Authorization: Bearer $TEACHER_TOKEN")

if [ "$RESPONSE" -eq 200 ]; then
    echo "✓ 선생님 문제 생성 성공"
else
    echo "✗ 선생님 문제 생성 실패 (HTTP $RESPONSE)"
    exit 1
fi

echo ""
echo "=========================================="
echo "JWT 인증 테스트 완료! ✅"
echo "=========================================="
TEST_AUTH

chmod +x $AUTH_DIR/test_auth.sh

log_info "✓ 인증/RBAC 시스템 설정 완료"
log_info "  - JWT 인증 모듈: $AUTH_DIR/auth.py"
log_info "  - FastAPI 예제: $AUTH_DIR/fastapi_auth_example.py"
log_info "  - 테스트 스크립트: $AUTH_DIR/test_auth.sh"
log_info ""
log_info "지원되는 역할:"
log_info "  - student: 문제 풀이, 진도 확인"
log_info "  - parent: 자녀 진도 조회"
log_info "  - teacher: 문제 생성, 학생 관리"
log_info "  - admin: 모든 권한"
