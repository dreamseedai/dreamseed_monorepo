#!/usr/bin/env python3
"""
DreamSeed API 인증 및 권한 관리 미들웨어
"""
import jwt
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

# JWT 시크릿 키 (실제 운영에서는 환경변수로 관리)
JWT_SECRET = "dreamseed_super_secret_key_2025_change_in_production"
JWT_ALGORITHM = "HS256"

# API 키 관리
API_KEYS = {
    "admin": {
        "key": "ds_admin_2025_secure_key_12345",
        "permissions": ["read", "write", "admin", "cache_manage"],
        "rate_limit": 1000,
        "expires": None  # 영구
    },
    "monitor": {
        "key": "ds_monitor_2025_readonly_key_67890",
        "permissions": ["read"],
        "rate_limit": 100,
        "expires": None
    },
    "api_user": {
        "key": "ds_api_2025_standard_key_11111",
        "permissions": ["read"],
        "rate_limit": 50,
        "expires": None
    }
}

# 사용자 세션 관리
user_sessions = {}

def generate_api_key(prefix="ds"):
    """새로운 API 키 생성"""
    random_part = secrets.token_urlsafe(32)
    timestamp = str(int(time.time()))
    return f"{prefix}_{timestamp}_{random_part}"

def hash_password(password):
    """비밀번호 해시화"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password, hashed_password):
    """비밀번호 검증"""
    try:
        salt, password_hash = hashed_password.split(':')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return new_hash.hex() == password_hash
    except:
        return False

def generate_jwt_token(user_id, permissions, expires_hours=24):
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'permissions': permissions,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expires_hours)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_api_key(api_key):
    """API 키 검증"""
    for user_type, config in API_KEYS.items():
        if config['key'] == api_key:
            return {
                'user_type': user_type,
                'permissions': config['permissions'],
                'rate_limit': config['rate_limit']
            }
    return None

def require_auth(permissions=None):
    """인증 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # API 키 인증
            api_key = request.headers.get('X-API-Key')
            if api_key:
                auth_info = verify_api_key(api_key)
                if auth_info:
                    g.current_user = auth_info
                    if permissions and not any(p in auth_info['permissions'] for p in permissions):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                    return f(*args, **kwargs)
            
            # JWT 토큰 인증
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = verify_jwt_token(token)
                if payload:
                    g.current_user = {
                        'user_id': payload['user_id'],
                        'permissions': payload['permissions']
                    }
                    if permissions and not any(p in payload['permissions'] for p in permissions):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                    return f(*args, **kwargs)
            
            return jsonify({'error': 'Authentication required'}), 401
        return decorated_function
    return decorator

def rate_limit(max_requests=100, window_seconds=3600):
    """속도 제한 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # 클라이언트별 요청 기록 관리
            if not hasattr(g, 'rate_limits'):
                g.rate_limits = {}
            
            if client_ip not in g.rate_limits:
                g.rate_limits[client_ip] = []
            
            # 오래된 요청 기록 제거
            g.rate_limits[client_ip] = [
                req_time for req_time in g.rate_limits[client_ip]
                if current_time - req_time < window_seconds
            ]
            
            # 요청 수 확인
            if len(g.rate_limits[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window_seconds
                }), 429
            
            # 요청 기록 추가
            g.rate_limits[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_security_event(event_type, details):
    """보안 이벤트 로깅"""
    timestamp = datetime.now().isoformat()
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_entry = {
        'timestamp': timestamp,
        'event_type': event_type,
        'client_ip': client_ip,
        'user_agent': user_agent,
        'details': details
    }
    
    # 실제 운영에서는 보안 로그 시스템에 저장
    print(f"SECURITY_EVENT: {log_entry}")

def check_suspicious_activity():
    """의심스러운 활동 감지"""
    client_ip = request.remote_addr
    
    # 너무 많은 요청
    if hasattr(g, 'rate_limits') and client_ip in g.rate_limits:
        if len(g.rate_limits[client_ip]) > 50:  # 1시간에 50회 이상
            log_security_event('HIGH_REQUEST_RATE', {
                'request_count': len(g.rate_limits[client_ip])
            })
            return True
    
    # 의심스러운 User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    suspicious_patterns = ['bot', 'crawler', 'scanner', 'sqlmap', 'nikto']
    if any(pattern in user_agent for pattern in suspicious_patterns):
        log_security_event('SUSPICIOUS_USER_AGENT', {
            'user_agent': user_agent
        })
        return True
    
    return False

def security_headers():
    """보안 헤더 추가"""
    from flask import make_response
    
    @wraps(security_headers)
    def after_request(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    
    return after_request

