# DreamSeed AI Platform 문제 해결 가이드

## 📖 목차

1. [일반적인 문제](#일반적인-문제)
2. [API 관련 문제](#api-관련-문제)
3. [데이터베이스 문제](#데이터베이스-문제)
4. [캐시 문제](#캐시-문제)
5. [웹 인터페이스 문제](#웹-인터페이스-문제)
6. [성능 문제](#성능-문제)
7. [보안 문제](#보안-문제)
8. [모니터링 및 진단](#모니터링-및-진단)
9. [긴급 복구 절차](#긴급-복구-절차)

---

## 🔧 일반적인 문제

### 서비스가 시작되지 않습니다

#### 증상
- DreamSeed API 서비스가 시작되지 않음
- 500 Internal Server Error 발생
- 서비스 상태가 `failed` 또는 `inactive`

#### 진단 방법
```bash
# 서비스 상태 확인
sudo systemctl status dreamseed-api

# 상세 로그 확인
sudo journalctl -u dreamseed-api -f --no-pager

# 수동 실행으로 오류 확인
cd /opt/dreamseed
source venv/bin/activate
python api/dashboard_data.py
```

#### 해결 방법
1. **의존성 확인**
   ```bash
   # Python 패키지 확인
   pip list | grep -E "(Flask|Redis|SQLite)"
   
   # 누락된 패키지 설치
   pip install -r requirements.txt
   ```

2. **환경 변수 확인**
   ```bash
   # .env 파일 확인
   cat .env
   
   # 필수 환경 변수 확인
   echo $PORT
   echo $REDIS_URL
   echo $DB_PATH
   ```

3. **권한 확인**
   ```bash
   # 파일 권한 확인
   ls -la /opt/dreamseed/
   
   # 권한 수정
   sudo chown -R dreamseed:dreamseed /opt/dreamseed/
   chmod +x /opt/dreamseed/api/dashboard_data.py
   ```

4. **포트 충돌 확인**
   ```bash
   # 포트 사용 확인
   sudo netstat -tlnp | grep :8002
   sudo lsof -i :8002
   
   # 충돌하는 프로세스 종료
   sudo kill -9 <PID>
   ```

### 데이터베이스 연결 오류

#### 증상
- `sqlite3.OperationalError: database is locked`
- `sqlite3.DatabaseError: database disk image is malformed`
- 데이터베이스 관련 500 오류

#### 진단 방법
```bash
# 데이터베이스 파일 확인
ls -la /opt/dreamseed/data/dreamseed_analytics.db

# 데이터베이스 무결성 검사
sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "PRAGMA integrity_check;"

# 데이터베이스 스키마 확인
sqlite3 /opt/dreamseed/data/dreamseed_analytics.db ".schema"
```

#### 해결 방법
1. **데이터베이스 잠금 해제**
   ```bash
   # 모든 연결 종료
   sudo pkill -f sqlite3
   
   # 데이터베이스 파일 권한 확인
   sudo chown dreamseed:dreamseed /opt/dreamseed/data/dreamseed_analytics.db
   chmod 664 /opt/dreamseed/data/dreamseed_analytics.db
   ```

2. **데이터베이스 복구**
   ```bash
   # 백업에서 복구
   cp /var/backups/dreamseed/dreamseed_*.db /opt/dreamseed/data/dreamseed_analytics.db
   
   # 또는 새로 생성
   rm /opt/dreamseed/data/dreamseed_analytics.db
   python -c "from api.dashboard_data import init_database; init_database()"
   ```

3. **데이터베이스 최적화**
   ```bash
   # VACUUM 실행
   sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "VACUUM;"
   
   # 인덱스 재구성
   sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "REINDEX;"
   ```

---

## 🔌 API 관련 문제

### API 응답이 느립니다

#### 증상
- API 요청 응답 시간이 5초 이상
- 타임아웃 오류 발생
- 사용자 경험 저하

#### 진단 방법
```bash
# API 응답 시간 측정
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8002/api/dashboard/stats"

# curl-format.txt 내용:
#      time_namelookup:  %{time_namelookup}\n
#         time_connect:  %{time_connect}\n
#      time_appconnect:  %{time_appconnect}\n
#     time_pretransfer:  %{time_pretransfer}\n
#        time_redirect:  %{time_redirect}\n
#   time_starttransfer:  %{time_starttransfer}\n
#                      ----------\n
#           time_total:  %{time_total}\n

# 시스템 리소스 확인
top
htop
iostat -x 1
```

#### 해결 방법
1. **데이터베이스 쿼리 최적화**
   ```sql
   -- 인덱스 생성
   CREATE INDEX idx_users_created_at ON users(created_at);
   CREATE INDEX idx_activities_user_id ON activities(user_id);
   
   -- 쿼리 실행 계획 확인
   EXPLAIN QUERY PLAN SELECT * FROM users WHERE created_at > '2024-01-01';
   ```

2. **캐시 활용**
   ```bash
   # Redis 상태 확인
   redis-cli ping
   redis-cli info memory
   
   # 캐시 무효화
   curl -X POST http://localhost:8002/api/cache/invalidate \
     -H "Content-Type: application/json" \
     -d '{"pattern": "dreamseed:*"}'
   ```

3. **Gunicorn 설정 최적화**
   ```python
   # gunicorn.conf.py
   workers = multiprocessing.cpu_count() * 2 + 1
   worker_class = "gthread"
   threads = 4
   worker_connections = 1000
   max_requests = 1000
   max_requests_jitter = 100
   ```

### API가 500 오류를 반환합니다

#### 증상
- 모든 API 요청이 500 Internal Server Error
- 로그에 Python 예외 발생
- 서비스는 실행 중이지만 응답 불가

#### 진단 방법
```bash
# 애플리케이션 로그 확인
sudo tail -f /opt/dreamseed/logs/error.log

# 시스템 로그 확인
sudo journalctl -u dreamseed-api -f

# Python 스택 트레이스 확인
sudo grep -A 10 -B 5 "Traceback" /opt/dreamseed/logs/error.log
```

#### 해결 방법
1. **코드 오류 수정**
   ```python
   # 로그에서 오류 위치 확인
   # 해당 파일의 해당 라인 수정
   
   # 예외 처리 추가
   try:
       # 문제가 되는 코드
       result = risky_operation()
   except Exception as e:
       logger.error(f"오류 발생: {e}")
       return jsonify({"error": "Internal Server Error"}), 500
   ```

2. **의존성 문제 해결**
   ```bash
   # 패키지 버전 확인
   pip list | grep -E "(Flask|Redis|SQLite)"
   
   # 호환되는 버전으로 다운그레이드
   pip install Flask==2.3.0 Redis==4.5.0
   ```

3. **환경 변수 확인**
   ```bash
   # 필수 환경 변수 확인
   echo $REDIS_URL
   echo $DB_PATH
   
   # 환경 변수 수정
   export REDIS_URL="redis://localhost:6379"
   export DB_PATH="/opt/dreamseed/data/dreamseed_analytics.db"
   ```

---

## 🗄️ 데이터베이스 문제

### 데이터베이스가 잠겼습니다

#### 증상
- `sqlite3.OperationalError: database is locked`
- 데이터베이스 작업이 멈춤
- 여러 프로세스가 동시에 접근 시도

#### 해결 방법
1. **즉시 해결**
   ```bash
   # 모든 SQLite 프로세스 종료
   sudo pkill -f sqlite3
   
   # 서비스 재시작
   sudo systemctl restart dreamseed-api
   ```

2. **근본적 해결**
   ```python
   # 연결 풀 사용
   import sqlite3
   from contextlib import contextmanager
   
   class DatabaseManager:
       def __init__(self, db_path, timeout=30):
           self.db_path = db_path
           self.timeout = timeout
       
       @contextmanager
       def get_connection(self):
           conn = sqlite3.connect(
               self.db_path,
               timeout=self.timeout,
               check_same_thread=False
           )
           conn.execute("PRAGMA journal_mode=WAL")
           try:
               yield conn
           finally:
               conn.close()
   ```

### 데이터가 손실되었습니다

#### 증상
- 데이터베이스에 데이터가 없음
- 테이블이 비어있음
- 사용자 데이터가 사라짐

#### 복구 절차
1. **백업 확인**
   ```bash
   # 백업 파일 목록
   ls -la /var/backups/dreamseed/
   
   # 최신 백업 확인
   ls -lt /var/backups/dreamseed/ | head -5
   ```

2. **데이터 복구**
   ```bash
   # 서비스 중지
   sudo systemctl stop dreamseed-api
   
   # 현재 데이터베이스 백업
   cp /opt/dreamseed/data/dreamseed_analytics.db \
      /opt/dreamseed/data/dreamseed_analytics.db.bak
   
   # 백업에서 복구
   gunzip /var/backups/dreamseed/dreamseed_20240115_020000.db.gz
   cp /var/backups/dreamseed/dreamseed_20240115_020000.db \
      /opt/dreamseed/data/dreamseed_analytics.db
   
   # 서비스 재시작
   sudo systemctl start dreamseed-api
   ```

3. **데이터 무결성 검사**
   ```bash
   # 데이터베이스 무결성 검사
   sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "PRAGMA integrity_check;"
   
   # 테이블별 데이터 확인
   sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "SELECT COUNT(*) FROM users;"
   sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "SELECT COUNT(*) FROM activities;"
   ```

---

## 💾 캐시 문제

### Redis 연결이 안 됩니다

#### 증상
- `redis.exceptions.ConnectionError`
- 캐시 관련 오류 발생
- API 응답이 느려짐

#### 진단 방법
```bash
# Redis 서비스 상태 확인
sudo systemctl status redis-server

# Redis 연결 테스트
redis-cli ping

# Redis 로그 확인
sudo tail -f /var/log/redis/redis-server.log
```

#### 해결 방법
1. **Redis 서비스 재시작**
   ```bash
   sudo systemctl restart redis-server
   sudo systemctl enable redis-server
   ```

2. **Redis 설정 확인**
   ```bash
   # Redis 설정 파일 확인
   sudo cat /etc/redis/redis.conf | grep -E "(bind|port|requirepass)"
   
   # Redis 메모리 사용량 확인
   redis-cli info memory
   ```

3. **연결 설정 수정**
   ```python
   # Redis 연결 설정 수정
   import redis
   
   redis_client = redis.Redis(
       host='localhost',
       port=6379,
       db=0,
       decode_responses=True,
       socket_connect_timeout=5,
       socket_timeout=5,
       retry_on_timeout=True
   )
   ```

### 캐시가 작동하지 않습니다

#### 증상
- 캐시 히트율이 0%
- 모든 요청이 데이터베이스로 직접 전달
- 성능 저하

#### 진단 방법
```bash
# 캐시 상태 확인
curl http://localhost:8002/api/cache/status

# Redis 키 확인
redis-cli keys "dreamseed:*"

# 캐시 통계 확인
redis-cli info stats
```

#### 해결 방법
1. **캐시 설정 확인**
   ```python
   # 캐시 TTL 설정 확인
   CACHE_TTL = {
       'stats': 300,      # 5분
       'user_growth': 600, # 10분
       'country_data': 900 # 15분
   }
   ```

2. **캐시 무효화**
   ```bash
   # 전체 캐시 무효화
   curl -X POST http://localhost:8002/api/cache/invalidate \
     -H "Content-Type: application/json" \
     -d '{"pattern": "dreamseed:*"}'
   
   # Redis 캐시 초기화
   redis-cli flushdb
   ```

3. **캐시 로직 점검**
   ```python
   # 캐시 로직 확인
   def get_cached_data(key):
       try:
           data = redis_client.get(key)
           if data:
               CACHE_HITS.inc()
               return json.loads(data)
           else:
               CACHE_MISSES.inc()
               return None
       except Exception as e:
           logger.error(f"캐시 조회 오류: {e}")
           return None
   ```

---

## 🌐 웹 인터페이스 문제

### 페이지가 로드되지 않습니다

#### 증상
- 브라우저에서 페이지가 표시되지 않음
- 404 Not Found 오류
- 빈 페이지 표시

#### 진단 방법
```bash
# Nginx 상태 확인
sudo systemctl status nginx

# Nginx 설정 테스트
sudo nginx -t

# Nginx 로그 확인
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# 포트 확인
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

#### 해결 방법
1. **Nginx 설정 수정**
   ```bash
   # Nginx 설정 파일 확인
   sudo cat /etc/nginx/sites-available/dreamseedai.com
   
   # 설정 파일 수정
   sudo nano /etc/nginx/sites-available/dreamseedai.com
   
   # Nginx 재시작
   sudo nginx -t
   sudo systemctl reload nginx
   ```

2. **파일 권한 확인**
   ```bash
   # 웹 파일 권한 확인
   ls -la /opt/dreamseed/admin/
   
   # 권한 수정
   sudo chown -R www-data:www-data /opt/dreamseed/admin/
   sudo chmod -R 755 /opt/dreamseed/admin/
   ```

3. **방화벽 설정 확인**
   ```bash
   # UFW 상태 확인
   sudo ufw status
   
   # HTTP/HTTPS 포트 허용
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

### 지도가 표시되지 않습니다

#### 증상
- 세계 지도가 표시되지 않음
- 지도 영역이 비어있음
- JavaScript 오류 발생

#### 진단 방법
```bash
# 브라우저 개발자 도구에서 확인
# Console 탭에서 JavaScript 오류 확인
# Network 탭에서 리소스 로딩 확인

# API 응답 확인
curl http://localhost:8002/api/dashboard/country-data
```

#### 해결 방법
1. **JavaScript 오류 수정**
   ```javascript
   // 지도 초기화 코드 확인
   function initializeWorldMap() {
       try {
           if (typeof L === 'undefined') {
               console.error('Leaflet 라이브러리가 로드되지 않았습니다.');
               return;
           }
           
           // 지도 초기화 코드
           const map = L.map('worldMap').setView([37.5665, 126.9780], 2);
           // ...
       } catch (error) {
           console.error('지도 초기화 오류:', error);
       }
   }
   ```

2. **API 데이터 확인**
   ```bash
   # 국가별 데이터 API 테스트
   curl -H "Accept: application/json" \
        http://localhost:8002/api/dashboard/country-data
   ```

3. **CDN 리소스 확인**
   ```html
   <!-- Leaflet CSS/JS 로드 확인 -->
   <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
   <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
   ```

### 차트가 표시되지 않습니다

#### 증상
- Chart.js 차트가 렌더링되지 않음
- 차트 영역이 비어있음
- 데이터는 있지만 시각화되지 않음

#### 해결 방법
1. **Chart.js 라이브러리 확인**
   ```html
   <!-- Chart.js 로드 확인 -->
   <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   ```

2. **차트 초기화 코드 수정**
   ```javascript
   function initializeCharts() {
       // Canvas 요소 확인
       const canvas = document.getElementById('userGrowthChart');
       if (!canvas) {
           console.error('차트 Canvas 요소를 찾을 수 없습니다.');
           return;
       }
       
       // Chart.js 버전 확인
       if (typeof Chart === 'undefined') {
           console.error('Chart.js 라이브러리가 로드되지 않았습니다.');
           return;
       }
       
       // 차트 생성
       const chart = new Chart(canvas, {
           type: 'line',
           data: chartData,
           options: chartOptions
       });
   }
   ```

---

## ⚡ 성능 문제

### 서버 응답이 느립니다

#### 증상
- 페이지 로딩 시간이 10초 이상
- API 응답 시간이 5초 이상
- 사용자 경험 저하

#### 진단 방법
```bash
# 시스템 리소스 확인
top
htop
iostat -x 1
vmstat 1

# 네트워크 확인
netstat -i
ss -tuln

# 디스크 I/O 확인
iotop
iostat -x 1
```

#### 해결 방법
1. **시스템 리소스 최적화**
   ```bash
   # 메모리 사용량 확인
   free -h
   
   # 스왑 사용량 확인
   swapon -s
   
   # 불필요한 프로세스 종료
   sudo pkill -f "unused_process"
   ```

2. **데이터베이스 최적화**
   ```sql
   -- 인덱스 생성
   CREATE INDEX idx_users_created_at ON users(created_at);
   CREATE INDEX idx_activities_timestamp ON activities(created_at);
   
   -- 쿼리 최적화
   ANALYZE;
   VACUUM;
   ```

3. **캐시 최적화**
   ```python
   # 캐시 TTL 조정
   CACHE_TTL = {
       'stats': 60,        # 1분
       'user_growth': 300, # 5분
       'country_data': 600 # 10분
   }
   ```

### 메모리 사용량이 높습니다

#### 증상
- 메모리 사용량이 80% 이상
- 스왑 사용량 증가
- 시스템이 느려짐

#### 해결 방법
1. **메모리 사용량 분석**
   ```bash
   # 메모리 사용량 확인
   free -h
   ps aux --sort=-%mem | head -10
   
   # 메모리 누수 확인
   valgrind --tool=memcheck python api/dashboard_data.py
   ```

2. **Gunicorn 설정 조정**
   ```python
   # gunicorn.conf.py
   workers = 2  # 워커 수 감소
   worker_class = "sync"  # 동기 워커 사용
   max_requests = 100  # 요청 수 제한
   max_requests_jitter = 10
   ```

3. **Redis 메모리 최적화**
   ```bash
   # Redis 메모리 사용량 확인
   redis-cli info memory
   
   # 메모리 정책 설정
   redis-cli config set maxmemory-policy allkeys-lru
   ```

---

## 🔒 보안 문제

### 보안 취약점이 발견되었습니다

#### 증상
- 보안 스캔에서 취약점 발견
- 의심스러운 네트워크 활동
- 시스템 침해 의심

#### 진단 방법
```bash
# 보안 스캔 실행
bandit -r /opt/dreamseed/
safety check

# 네트워크 연결 확인
netstat -tuln
ss -tuln

# 로그 분석
sudo grep -i "failed\|error\|attack" /var/log/auth.log
sudo grep -i "suspicious" /opt/dreamseed/logs/error.log
```

#### 해결 방법
1. **즉시 조치**
   ```bash
   # 의심스러운 연결 차단
   sudo ufw deny from <suspicious_ip>
   
   # 서비스 재시작
   sudo systemctl restart dreamseed-api
   ```

2. **보안 패치 적용**
   ```bash
   # 시스템 업데이트
   sudo apt update && sudo apt upgrade
   
   # Python 패키지 업데이트
   pip install --upgrade -r requirements.txt
   ```

3. **보안 설정 강화**
   ```python
   # 보안 헤더 추가
   @app.after_request
   def add_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       response.headers['Strict-Transport-Security'] = 'max-age=31536000'
       return response
   ```

### SSL 인증서 문제

#### 증상
- SSL 인증서 만료
- 브라우저에서 보안 경고 표시
- HTTPS 연결 실패

#### 해결 방법
1. **인증서 갱신**
   ```bash
   # Let's Encrypt 인증서 갱신
   sudo certbot renew --dry-run
   sudo certbot renew
   
   # Nginx 재시작
   sudo systemctl reload nginx
   ```

2. **인증서 확인**
   ```bash
   # 인증서 정보 확인
   openssl x509 -in /etc/letsencrypt/live/dreamseedai.com/cert.pem -text -noout
   
   # 인증서 만료일 확인
   openssl x509 -in /etc/letsencrypt/live/dreamseedai.com/cert.pem -noout -dates
   ```

---

## 📊 모니터링 및 진단

### 시스템 모니터링

#### 1. 기본 모니터링 명령어
```bash
# 시스템 리소스 확인
htop
iotop
nethogs

# 네트워크 연결 확인
ss -tuln
netstat -i

# 디스크 사용량 확인
df -h
du -sh /opt/dreamseed/*
```

#### 2. 로그 모니터링
```bash
# 실시간 로그 확인
sudo tail -f /opt/dreamseed/logs/error.log
sudo journalctl -u dreamseed-api -f

# 로그 분석
sudo grep -i error /opt/dreamseed/logs/error.log | tail -20
sudo grep -i "500\|404\|403" /var/log/nginx/access.log | tail -20
```

#### 3. 성능 모니터링
```bash
# API 응답 시간 측정
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8002/api/dashboard/stats"

# 데이터베이스 성능 확인
sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "PRAGMA compile_options;"

# Redis 성능 확인
redis-cli --latency-history -i 1
```

### Prometheus 메트릭 확인

#### 1. 메트릭 수집 확인
```bash
# 메트릭 엔드포인트 확인
curl http://localhost:8002/metrics

# 특정 메트릭 확인
curl http://localhost:8002/metrics | grep dreamseed_requests_total
curl http://localhost:8002/metrics | grep dreamseed_request_duration_seconds
```

#### 2. Grafana 대시보드 확인
- Grafana 접속: http://localhost:3000
- 주요 메트릭:
  - 요청 수 (dreamseed_requests_total)
  - 응답 시간 (dreamseed_request_duration_seconds)
  - 활성 사용자 (dreamseed_active_users)
  - 캐시 히트율 (dreamseed_cache_hits)

---

## 🚨 긴급 복구 절차

### 서비스 완전 중단 시

#### 1. 즉시 조치
```bash
# 서비스 상태 확인
sudo systemctl status dreamseed-api nginx redis-server

# 로그 확인
sudo journalctl -u dreamseed-api --since "10 minutes ago"

# 시스템 리소스 확인
free -h
df -h
```

#### 2. 서비스 재시작
```bash
# 모든 서비스 재시작
sudo systemctl restart redis-server
sudo systemctl restart dreamseed-api
sudo systemctl restart nginx

# 서비스 상태 확인
sudo systemctl status dreamseed-api nginx redis-server
```

#### 3. 롤백 실행
```bash
# 이전 버전으로 롤백
sudo systemctl stop dreamseed-api
./rollback.sh
sudo systemctl start dreamseed-api
```

### 데이터 손실 시

#### 1. 즉시 조치
```bash
# 서비스 중지
sudo systemctl stop dreamseed-api

# 현재 상태 백업
cp /opt/dreamseed/data/dreamseed_analytics.db \
   /opt/dreamseed/data/dreamseed_analytics.db.emergency
```

#### 2. 데이터 복구
```bash
# 최신 백업 확인
ls -lt /var/backups/dreamseed/ | head -5

# 백업에서 복구
gunzip /var/backups/dreamseed/dreamseed_20240115_020000.db.gz
cp /var/backups/dreamseed/dreamseed_20240115_020000.db \
   /opt/dreamseed/data/dreamseed_analytics.db
```

#### 3. 서비스 복구
```bash
# 데이터 무결성 검사
sqlite3 /opt/dreamseed/data/dreamseed_analytics.db "PRAGMA integrity_check;"

# 서비스 재시작
sudo systemctl start dreamseed-api

# 기능 테스트
curl http://localhost:8002/healthz
curl http://localhost:8002/api/dashboard/stats
```

### 보안 침해 시

#### 1. 즉시 조치
```bash
# 네트워크 연결 차단
sudo ufw deny in
sudo ufw deny out

# 의심스러운 프로세스 확인
ps aux | grep -E "(python|node|bash)" | grep -v grep

# 네트워크 연결 확인
netstat -tuln | grep -E "(ESTABLISHED|LISTEN)"
```

#### 2. 시스템 격리
```bash
# 서비스 중지
sudo systemctl stop dreamseed-api nginx redis-server

# 로그 보존
sudo cp -r /var/log/ /opt/emergency/logs/
sudo cp -r /opt/dreamseed/logs/ /opt/emergency/app_logs/
```

#### 3. 복구 계획
```bash
# 시스템 재설치
sudo apt update && sudo apt upgrade
sudo apt autoremove && sudo apt autoclean

# 보안 패치 적용
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📞 지원 및 문의

### 긴급 상황
- **24시간 긴급 지원**: emergency@dreamseed.com
- **전화**: 02-1234-5678 (24시간)
- **Slack**: #emergency-support

### 일반 지원
- **기술 지원**: tech@dreamseed.com
- **문서**: https://docs.dreamseed.com
- **GitHub Issues**: [이슈 트래커](https://github.com/dreamseed/platform/issues)

### 문제 보고 시 포함할 정보
1. **환경 정보**
   - 운영체제 및 버전
   - Python 버전
   - DreamSeed 버전
   - 브라우저 및 버전

2. **오류 정보**
   - 오류 메시지
   - 스택 트레이스
   - 로그 파일
   - 스크린샷

3. **재현 단계**
   - 문제 발생 시점
   - 재현 방법
   - 예상 결과 vs 실제 결과

---

*이 문제 해결 가이드는 DreamSeed AI Platform v1.0.0 기준으로 작성되었습니다.*
*최신 업데이트: 2024년 1월 15일*

