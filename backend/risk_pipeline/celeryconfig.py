"""
Celery 설정
"""
import os

# Broker 설정 (Redis)
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

# Result Backend 설정
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# 태스크 설정
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'Asia/Seoul'
enable_utc = True

# 워커 설정
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000

# Beat 스케줄러 설정
beat_scheduler = 'celery.beat:PersistentScheduler'
beat_schedule_filename = '/tmp/celerybeat-schedule'

# 로깅
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# 태스크 라우팅
task_routes = {
    'risk_pipeline.*': {'queue': 'risk_pipeline'},
}

# 태스크 타임아웃
task_time_limit = 3600  # 1시간
task_soft_time_limit = 3300  # 55분
