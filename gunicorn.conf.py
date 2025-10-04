import multiprocessing
import os

# 바인딩 설정
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# 앱 모듈 설정
wsgi_module = "api.dashboard_data:app"

# 워커 설정 (CPU 코어 수 기반)
workers = max(2, multiprocessing.cpu_count() * 2 + 1)

# 워커 클래스 (I/O 바운드에 안전)
worker_class = "gthread"
threads = 4

# 타임아웃 설정
timeout = 60
graceful_timeout = 30
keepalive = 5

# 로그 설정 (stdout -> journald로 수집)
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 프로세스 이름
proc_name = "dreamseed-api"

# 최대 요청 수 (메모리 누수 방지)
max_requests = 1000
max_requests_jitter = 100

# 프리로드 앱 (메모리 사용량 최적화)
preload_app = True

# 사용자/그룹 (systemd에서 설정)
# user = "www-data"
# group = "www-data"
