#!/usr/bin/env python3
"""
DreamSeedAI Dashboard Real-time Data API
실시간 대시보드 데이터를 제공하는 API 서버
"""

import json
import sqlite3
import time
import random
import redis
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, g
from flask_cors import CORS
import threading
import queue
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
# from auth_middleware import require_auth, rate_limit, log_security_event, check_suspicious_activity, security_headers

app = Flask(__name__)
CORS(app, origins=['http://192.168.68.116:9000', 'http://localhost:9000', 'http://127.0.0.1:9000'])

# Prometheus 메트릭 정의
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
DB_CONNECTION_ERRORS = Counter('dreamseed_db_connection_errors_total', 'Database connection errors')
CACHE_HITS = Counter('dreamseed_cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('dreamseed_cache_misses_total', 'Cache misses')
ACTIVE_USERS = Gauge('dreamseed_active_users', 'Number of active users')
API_RESPONSE_TIME = Histogram('dreamseed_api_response_time_seconds', 'API response time')

# 보안 헤더 적용 (간단한 버전)
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Redis 캐시 설정
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # 연결 테스트
    CACHE_ENABLED = True
    print("✅ Redis 캐시 연결 성공")
except Exception as e:
    print(f"⚠️ Redis 캐시 연결 실패: {e}")
    redis_client = None
    CACHE_ENABLED = False

# 캐시 TTL 설정 (초)
CACHE_TTL = {
    'stats': 30,           # 실시간 통계: 30초
    'user_growth': 300,    # 사용자 증가: 5분
    'daily_activity': 300, # 일일 활동: 5분
    'country_data': 600,   # 국가별 데이터: 10분
    'activities': 60,      # 최근 활동: 1분
}

# 캐시 헬퍼 함수들
def get_cache_key(endpoint, **kwargs):
    """캐시 키 생성"""
    key_parts = [f"dreamseed:{endpoint}"]
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)

def get_cached_data(cache_key, ttl=None):
    """캐시에서 데이터 조회"""
    if not CACHE_ENABLED:
        CACHE_MISSES.inc()
        return None
    try:
        data = redis_client.get(cache_key)
        if data:
            CACHE_HITS.inc()
            return json.loads(data)
        else:
            CACHE_MISSES.inc()
            return None
    except Exception as e:
        print(f"캐시 조회 오류: {e}")
        CACHE_MISSES.inc()
        return None

def set_cached_data(cache_key, data, ttl=None):
    """캐시에 데이터 저장"""
    if not CACHE_ENABLED:
        return
    try:
        redis_client.setex(cache_key, ttl or 300, json.dumps(data))
    except Exception as e:
        print(f"캐시 저장 오류: {e}")

def invalidate_cache(pattern):
    """캐시 무효화"""
    if not CACHE_ENABLED:
        return
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        print(f"캐시 무효화 오류: {e}")

# Prometheus 메트릭 수집 미들웨어
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    # 요청 지속 시간 측정
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        REQUEST_DURATION.labels(method=request.method, endpoint=request.endpoint).observe(duration)
        API_RESPONSE_TIME.observe(duration)
    
    # 요청 카운트 증가
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint, status=response.status_code).inc()
    
    return response

# 헬스체크 엔드포인트
@app.route('/healthz')
def healthz():
    """헬스체크 엔드포인트"""
    cache_status = "enabled" if CACHE_ENABLED else "disabled"
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'cache': cache_status
    })

# 전역 변수
realtime_data = {
    'total_users': 1247,
    'online_users': 89,
    'total_problems': 2456,
    'solved_today': 1234,
    'ai_interactions': 5678,
    'converted_mathml': 12340,
    'user_growth': [],
    'daily_activity': [],
    'country_data': [],
    'recent_activities': []
}

# 데이터베이스 초기화
def init_database():
    """SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    # 사용자 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            country TEXT NOT NULL,
            grade INTEGER,
            user_type TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_online BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # 문제 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            grade INTEGER,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            solved_count INTEGER DEFAULT 0
        )
    ''')
    
    # 활동 로그 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # AI 상호작용 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # MathML 변환 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mathml_conversions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_mathml TEXT,
            converted_content TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_sample_data():
    """샘플 데이터 생성"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    # 샘플 사용자 데이터
    countries = ['South Korea', 'United States', 'Japan', 'China', 'United Kingdom', 
                'Germany', 'France', 'Canada', 'Australia', 'Brazil', 'India', 'Russia']
    
    user_types = ['free', 'paid', 'premium']
    for i in range(100):
        country = random.choice(countries)
        user_type = random.choices(user_types, weights=[70, 25, 5])[0]  # 70% free, 25% paid, 5% premium
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, country, grade, user_type, is_online)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (f'user{i+1}', f'user{i+1}@example.com', country, random.randint(1, 3), user_type,
              random.choice([True, False])))
    
    # 샘플 문제 데이터
    subjects = ['수학', '과학', '물리', '화학']
    difficulties = ['초급', '중급', '고급']
    
    for i in range(50):
        cursor.execute('''
            INSERT OR IGNORE INTO problems (title, subject, grade, difficulty, solved_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (f'문제 {i+1}', random.choice(subjects), random.randint(1, 3), 
              random.choice(difficulties), random.randint(0, 100)))
    
    conn.commit()
    conn.close()

def get_realtime_stats():
    """실시간 통계 데이터 조회"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    # 총 사용자 수
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # 현재 온라인 사용자 수
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_online = 1')
    online_users = cursor.fetchone()[0]
    
    # 총 문제 수
    cursor.execute('SELECT COUNT(*) FROM problems')
    total_problems = cursor.fetchone()[0]
    
    # 오늘 해결된 문제 수
    today = datetime.now().date()
    cursor.execute('''
        SELECT COUNT(*) FROM activity_logs 
        WHERE activity_type = 'problem_solved' 
        AND DATE(created_at) = ?
    ''', (today,))
    solved_today = cursor.fetchone()[0]
    
    # AI 상호작용 수
    cursor.execute('SELECT COUNT(*) FROM ai_interactions')
    ai_interactions = cursor.fetchone()[0]
    
    # 변환된 MathML 수
    cursor.execute('SELECT COUNT(*) FROM mathml_conversions WHERE status = "completed"')
    converted_mathml = cursor.fetchone()[0]
    
    # 실시간 사용자 수 (최근 5분 내 활동)
    cursor.execute('SELECT COUNT(*) FROM users WHERE datetime(last_activity) > datetime("now", "-5 minutes")')
    realtime_users = cursor.fetchone()[0]
    
    # 상세 사용자 통계
    cursor.execute('''
        SELECT 
            COUNT(CASE WHEN user_type = 'free' THEN 1 END) as free_users,
            COUNT(CASE WHEN user_type = 'paid' THEN 1 END) as paid_users,
            COUNT(CASE WHEN user_type = 'premium' THEN 1 END) as premium_users,
            COUNT(CASE WHEN user_type = 'free' AND datetime(last_activity) > datetime('now', '-5 minutes') THEN 1 END) as free_realtime,
            COUNT(CASE WHEN user_type = 'paid' AND datetime(last_activity) > datetime('now', '-5 minutes') THEN 1 END) as paid_realtime,
            COUNT(CASE WHEN user_type = 'premium' AND datetime(last_activity) > datetime('now', '-5 minutes') THEN 1 END) as premium_realtime,
            COUNT(CASE WHEN user_type = 'free' AND DATE(last_activity) = DATE('now') THEN 1 END) as free_daily,
            COUNT(CASE WHEN user_type = 'paid' AND DATE(last_activity) = DATE('now') THEN 1 END) as paid_daily,
            COUNT(CASE WHEN user_type = 'premium' AND DATE(last_activity) = DATE('now') THEN 1 END) as premium_daily
        FROM users
    ''')
    user_stats = cursor.fetchone()
    
    # 수익 통계 (샘플 데이터)
    revenue_stats = {
        'realtime': 1250.50,
        'daily': 8750.25,
        'weekly': 45250.75,
        'monthly': 187500.00,
        'quarterly': 562500.00,
        'yearly': 2250000.00,
        'total': 2250000.00
    }
    
    conn.close()
    
    return {
        'total_users': total_users,
        'online_users': online_users,
        'realtime_users': realtime_users,
        'total_problems': total_problems,
        'solved_today': solved_today,
        'ai_interactions': ai_interactions,
        'converted_mathml': converted_mathml,
        'user_stats': {
            'free': {
                'realtime': user_stats[3] if user_stats else 0,
                'daily': user_stats[6] if user_stats else 0,
                'weekly': 0,  # 계산 필요
                'monthly': 0,  # 계산 필요
                'quarterly': 0,  # 계산 필요
                'yearly': 0,  # 계산 필요
                'total': user_stats[0] if user_stats else 0
            },
            'paid': {
                'realtime': user_stats[4] if user_stats else 0,
                'daily': user_stats[7] if user_stats else 0,
                'weekly': 0,  # 계산 필요
                'monthly': 0,  # 계산 필요
                'quarterly': 0,  # 계산 필요
                'yearly': 0,  # 계산 필요
                'total': user_stats[1] if user_stats else 0
            },
            'premium': {
                'realtime': user_stats[5] if user_stats else 0,
                'daily': user_stats[8] if user_stats else 0,
                'weekly': 0,  # 계산 필요
                'monthly': 0,  # 계산 필요
                'quarterly': 0,  # 계산 필요
                'yearly': 0,  # 계산 필요
                'total': user_stats[2] if user_stats else 0
            }
        },
        'revenue_stats': revenue_stats
    }

def get_user_growth_data():
    """사용자 증가 데이터 조회"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    # 최근 10개월 데이터
    growth_data = []
    for i in range(10):
        month_date = datetime.now() - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE created_at <= ?
        ''', (month_end,))
        
        count = cursor.fetchone()[0]
        growth_data.append({
            'month': month_start.strftime('%Y-%m'),
            'users': count
        })
    
    conn.close()
    return list(reversed(growth_data))

def get_daily_activity_data():
    """일일 활동 데이터 조회"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    # 최근 7일 데이터
    activity_data = []
    days = ['월', '화', '수', '목', '금', '토', '일']
    
    for i in range(7):
        day_date = datetime.now() - timedelta(days=i)
        day_name = days[day_date.weekday()]
        
        cursor.execute('''
            SELECT COUNT(*) FROM activity_logs 
            WHERE DATE(created_at) = ?
        ''', (day_date.date(),))
        
        count = cursor.fetchone()[0]
        activity_data.append({
            'day': day_name,
            'activity': count
        })
    
    conn.close()
    return list(reversed(activity_data))

def get_country_data(user_type=None):
    """국가별 사용자 데이터 조회"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    # 사용자 유형 필터 조건
    where_clause = ""
    if user_type:
        where_clause = f"WHERE user_type = '{user_type}'"
    
    # 총 사용자 수와 오늘 활성 사용자 수, 현재 온라인, 실시간 사용자 조회
    cursor.execute(f'''
        SELECT 
            country, 
            COUNT(*) as total_users,
            COUNT(CASE WHEN DATE(last_activity) = DATE('now') THEN 1 END) as today_active_users,
            COUNT(CASE WHEN is_online = 1 THEN 1 END) as online_users,
            COUNT(CASE WHEN datetime(last_activity) > datetime('now', '-5 minutes') THEN 1 END) as realtime_users
        FROM users 
        {where_clause}
        GROUP BY country 
        ORDER BY total_users DESC
    ''')
    
    countries = cursor.fetchall()
    conn.close()
    
    # 국가 좌표 매핑
    country_coords = {
        'South Korea': {'lat': 35.9078, 'lng': 127.7669, 'name': '대한민국'},
        'United States': {'lat': 39.8283, 'lng': -98.5795, 'name': '미국'},
        'Japan': {'lat': 36.2048, 'lng': 138.2529, 'name': '일본'},
        'China': {'lat': 35.8617, 'lng': 104.1954, 'name': '중국'},
        'United Kingdom': {'lat': 55.3781, 'lng': -3.4360, 'name': '영국'},
        'Germany': {'lat': 51.1657, 'lng': 10.4515, 'name': '독일'},
        'France': {'lat': 46.2276, 'lng': 2.2137, 'name': '프랑스'},
        'Canada': {'lat': 56.1304, 'lng': -106.3468, 'name': '캐나다'},
        'Australia': {'lat': -25.2744, 'lng': 133.7751, 'name': '호주'},
        'Brazil': {'lat': -14.2350, 'lng': -51.9253, 'name': '브라질'},
        'India': {'lat': 20.5937, 'lng': 78.9629, 'name': '인도'},
        'Russia': {'lat': 61.5240, 'lng': 105.3188, 'name': '러시아'}
    }
    
    result = []
    for country, total_users, today_active, online_users, realtime_users in countries:
        if country in country_coords:
            coords = country_coords[country]
            result.append({
                'country': country,
                'name': coords['name'],
                'lat': coords['lat'],
                'lng': coords['lng'],
                'users': total_users,
                'today_active': today_active,
                'online_users': online_users,
                'realtime_users': realtime_users
            })
    
    return result

def get_recent_activities():
    """최근 활동 데이터 조회"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT al.activity_type, al.description, al.created_at, u.username
        FROM activity_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT 10
    ''')
    
    activities = cursor.fetchall()
    conn.close()
    
    activity_types = {
        'user_registered': {'icon': 'fas fa-user-plus', 'color': 'bg-success', 'title': '새 사용자 등록'},
        'problem_solved': {'icon': 'fas fa-check', 'color': 'bg-primary', 'title': '문제 해결'},
        'ai_interaction': {'icon': 'fas fa-robot', 'color': 'bg-warning', 'title': 'AI 상호작용'},
        'mathml_converted': {'icon': 'fas fa-calculator', 'color': 'bg-info', 'title': 'MathML 변환'},
        'achievement_unlocked': {'icon': 'fas fa-star', 'color': 'bg-danger', 'title': '성취 달성'},
        'study_session': {'icon': 'fas fa-book', 'color': 'bg-secondary', 'title': '학습 세션'}
    }
    
    result = []
    for activity_type, description, created_at, username in activities:
        if activity_type in activity_types:
            activity_info = activity_types[activity_type]
            time_diff = datetime.now() - datetime.fromisoformat(created_at)
            
            if time_diff.total_seconds() < 60:
                time_str = '방금 전'
            elif time_diff.total_seconds() < 3600:
                time_str = f'{int(time_diff.total_seconds() / 60)}분 전'
            else:
                time_str = f'{int(time_diff.total_seconds() / 3600)}시간 전'
            
            result.append({
                'icon': activity_info['icon'],
                'color': activity_info['color'],
                'title': activity_info['title'],
                'description': description or f'{username}님이 활동했습니다',
                'time': time_str
            })
    
    return result

def simulate_realtime_activity():
    """실시간 활동 시뮬레이션"""
    conn = sqlite3.connect('/home/won/projects/dreamseed_monorepo/dreamseed_analytics.db')
    cursor = conn.cursor()
    
    # 랜덤 활동 생성
    activities = [
        ('user_registered', '새로운 학생이 가입했습니다'),
        ('problem_solved', '수학 문제를 해결했습니다'),
        ('ai_interaction', 'AI 챗봇과 대화했습니다'),
        ('mathml_converted', 'MathML이 변환되었습니다'),
        ('achievement_unlocked', '학습 목표를 달성했습니다'),
        ('study_session', '새로운 학습 세션이 시작되었습니다')
    ]
    
    activity_type, description = random.choice(activities)
    user_id = random.randint(1, 100)
    
    cursor.execute('''
        INSERT INTO activity_logs (user_id, activity_type, description)
        VALUES (?, ?, ?)
    ''', (user_id, activity_type, description))
    
    # 사용자 온라인 상태 랜덤 업데이트
    cursor.execute('''
        UPDATE users SET is_online = ? WHERE id = ?
    ''', (random.choice([True, False]), user_id))
    
    conn.commit()
    conn.close()

# API 엔드포인트들
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """대시보드 통계 데이터"""
    cache_key = get_cache_key('stats')
    
    # 캐시에서 조회
    cached_stats = get_cached_data(cache_key, CACHE_TTL['stats'])
    if cached_stats:
        return jsonify(cached_stats)
    
    # 캐시 미스 시 DB에서 조회
    stats = get_realtime_stats()
    
    # 캐시에 저장
    set_cached_data(cache_key, stats, CACHE_TTL['stats'])
    
    return jsonify(stats)

@app.route('/api/dashboard/user-growth', methods=['GET'])
def get_user_growth():
    """사용자 증가 데이터"""
    cache_key = get_cache_key('user_growth')
    
    # 캐시에서 조회
    cached_data = get_cached_data(cache_key, CACHE_TTL['user_growth'])
    if cached_data:
        return jsonify(cached_data)
    
    # 캐시 미스 시 DB에서 조회
    growth_data = get_user_growth_data()
    
    # 캐시에 저장
    set_cached_data(cache_key, growth_data, CACHE_TTL['user_growth'])
    
    return jsonify(growth_data)

@app.route('/api/dashboard/daily-activity', methods=['GET'])
def get_daily_activity():
    """일일 활동 데이터"""
    cache_key = get_cache_key('daily_activity')
    
    # 캐시에서 조회
    cached_data = get_cached_data(cache_key, CACHE_TTL['daily_activity'])
    if cached_data:
        return jsonify(cached_data)
    
    # 캐시 미스 시 DB에서 조회
    activity_data = get_daily_activity_data()
    
    # 캐시에 저장
    set_cached_data(cache_key, activity_data, CACHE_TTL['daily_activity'])
    
    return jsonify(activity_data)

@app.route('/api/dashboard/country-data', methods=['GET'])
def get_country_data_api():
    """국가별 데이터"""
    user_type = request.args.get('user_type')
    cache_key = get_cache_key('country_data', user_type=user_type or 'all')
    
    # 캐시에서 조회
    cached_data = get_cached_data(cache_key, CACHE_TTL['country_data'])
    if cached_data:
        return jsonify(cached_data)
    
    # 캐시 미스 시 DB에서 조회
    country_data = get_country_data(user_type)
    
    # 캐시에 저장
    set_cached_data(cache_key, country_data, CACHE_TTL['country_data'])
    
    return jsonify(country_data)

@app.route('/api/dashboard/recent-activities', methods=['GET'])
def get_recent_activities_api():
    """최근 활동 데이터"""
    cache_key = get_cache_key('activities')
    
    # 캐시에서 조회
    cached_data = get_cached_data(cache_key, CACHE_TTL['activities'])
    if cached_data:
        return jsonify(cached_data)
    
    # 캐시 미스 시 DB에서 조회
    activities = get_recent_activities()
    
    # 캐시에 저장
    set_cached_data(cache_key, activities, CACHE_TTL['activities'])
    
    return jsonify(activities)

@app.route('/api/dashboard/all', methods=['GET'])
def get_all_dashboard_data():
    """모든 대시보드 데이터"""
    return jsonify({
        'stats': get_realtime_stats(),
        'user_growth': get_user_growth_data(),
        'daily_activity': get_daily_activity_data(),
        'country_data': get_country_data(),
        'recent_activities': get_recent_activities(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/simulate-activity', methods=['POST'])
def simulate_activity():
    """활동 시뮬레이션 (테스트용)"""
    simulate_realtime_activity()
    return jsonify({'status': 'success', 'message': 'Activity simulated'})

@app.route('/api/cache/invalidate', methods=['POST'])
def invalidate_cache_endpoint():
    """캐시 무효화 엔드포인트"""
    try:
        pattern = request.json.get('pattern', 'dreamseed:*')
        invalidate_cache(pattern)
        return jsonify({'message': f'Cache invalidated for pattern: {pattern}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """캐시 상태 확인"""
    if not CACHE_ENABLED:
        return jsonify({'status': 'disabled'})
    
    try:
        info = redis_client.info()
        keys = redis_client.keys('dreamseed:*')
        return jsonify({
            'status': 'enabled',
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', '0B'),
            'cached_keys': len(keys),
            'keys': keys[:10]  # 처음 10개 키만 표시
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/metrics')
def metrics():
    """Prometheus 메트릭 엔드포인트"""
    # 활성 사용자 수 업데이트
    try:
        stats = get_realtime_stats()
        ACTIVE_USERS.set(stats.get('online_users', 0))
    except:
        pass
    
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# 백그라운드 작업
def background_activity_simulator():
    """백그라운드에서 활동 시뮬레이션"""
    while True:
        time.sleep(random.randint(10, 30))  # 10-30초마다 랜덤 활동
        simulate_realtime_activity()

if __name__ == '__main__':
    # 데이터베이스 초기화
    init_database()
    generate_sample_data()
    
    # 백그라운드 시뮬레이터 시작
    simulator_thread = threading.Thread(target=background_activity_simulator, daemon=True)
    simulator_thread.start()
    
    print("DreamSeedAI Dashboard API 서버 시작...")
    print("API 엔드포인트:")
    print("  GET  /api/dashboard/stats - 실시간 통계")
    print("  GET  /api/dashboard/user-growth - 사용자 증가 데이터")
    print("  GET  /api/dashboard/daily-activity - 일일 활동 데이터")
    print("  GET  /api/dashboard/country-data - 국가별 데이터")
    print("  GET  /api/dashboard/recent-activities - 최근 활동")
    print("  GET  /api/dashboard/all - 모든 데이터")
    print("  POST /api/simulate-activity - 활동 시뮬레이션")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
