# 주간 리스크 리포트 자동화 파이프라인

Celery + R을 사용한 다중 테넌트 주간 리스크 리포트 자동 생성 시스템

## 📋 개요

매주 월요일 06:00에 자동으로 실행되어 다음 작업을 수행합니다:

1. **데이터 수집**: PostgreSQL에서 지난 14일 학습/출석 데이터 추출
2. **메트릭 계산**: R로 Δθ, omit rate, attendance, c_hat 계산
3. **집계**: Python으로 테넌트별 리스크 요약 생성
4. **렌더링**: RMarkdown으로 HTML 리포트 생성
5. **배포**: 이메일/슬랙으로 리포트 전송

## 🏗️ 아키텍처

```
PostgreSQL → Celery Task 1 (SQL) → CSV
                ↓
         Celery Task 2 (R) → Metrics CSV
                ↓
         Celery Task 3 (Python) → Aggregated Data
                ↓
         Celery Task 4 (RMarkdown) → HTML Reports (병렬)
                ↓
         Celery Task 5 (Email/Slack) → Delivery
```

## 📁 디렉토리 구조

```
backend/risk_pipeline/
├── config/
│   ├── tenants.yaml.example          # 테넌트 설정
│   └── thresholds.yaml.example       # 리스크 임계치
├── jobs/
│   ├── 00_fetch_snapshots.sql        # 데이터 추출 SQL
│   ├── 10_compute_metrics.R          # R 메트릭 계산
│   └── 20_aggregate.py               # Python 집계
├── templates/
│   └── weekly_report.Rmd             # RMarkdown 템플릿
├── reports/                          # 생성된 리포트 저장
│   └── 2025-11-09/
│       ├── summary.csv
│       ├── dreamseedai-seoul_report.html
│       └── ...
├── tasks.py                          # Celery 태스크 정의
├── celeryconfig.py                   # Celery 설정
└── README.md                         # 이 문서
```

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
# Python 패키지
pip install celery redis pyyaml pandas

# R 패키지
Rscript -e 'install.packages(c("dplyr", "readr", "yaml", "lubridate", "rmarkdown", "ggplot2", "DT", "knitr"))'
```

### 2. 설정 파일 생성

```bash
cd backend/risk_pipeline/config

# 테넌트 설정
cp tenants.yaml.example tenants.yaml
# 실제 org_id, 이메일, 슬랙 웹훅 등 수정

# 임계치 설정
cp thresholds.yaml.example thresholds.yaml
# 필요 시 임계치 조정
```

### 3. Redis 실행

```bash
# Docker로 Redis 실행
docker run -d -p 6379:6379 redis:latest

# 또는 시스템 Redis 사용
sudo systemctl start redis
```

### 4. Celery 워커 실행

```bash
cd backend/risk_pipeline

# 워커 시작
celery -A tasks worker --loglevel=info --queue=risk_pipeline

# Beat 스케줄러 시작 (별도 터미널)
celery -A tasks beat --loglevel=info
```

### 5. 수동 실행 (테스트)

```bash
# Python 인터프리터에서
python3 -c "
from tasks import run_weekly_pipeline
result = run_weekly_pipeline.delay()
print(f'Task ID: {result.id}')
"

# 또는 Celery CLI로
celery -A tasks call risk_pipeline.run_weekly_pipeline
```

## 📊 리스크 메트릭

### 능력치 (θ) 리스크
- **WARN**: Δθ_7d < -0.15 또는 Δθ_14d < -0.25
- **CRIT**: Δθ_7d < -0.30 또는 Δθ_14d < -0.50
- **연속 하락**: 3주 연속 θ 하락

### 무응답 (Omit) 리스크
- **WARN**: Omit rate ≥ 8%
- **CRIT**: Omit rate ≥ 15%

### 추측 (Guessing) 리스크
- **WARN**: c_hat ≥ 0.30 (80th percentile)
- **CRIT**: c_hat ≥ 0.40

### 출석 (Attendance) 리스크
- **WARN**: 주간 결석률 ≥ 10% 또는 2주 결석률 ≥ 15%
- **CRIT**: 주간 결석률 ≥ 20% 또는 2주 결석률 ≥ 30% 또는 5일 연속 결석

## 🔧 커스터마이징

### 스케줄 변경

`tasks.py`의 `beat_schedule` 수정:

```python
app.conf.beat_schedule = {
    'weekly-risk-report': {
        'task': 'risk_pipeline.run_weekly_pipeline',
        'schedule': crontab(hour=8, minute=30, day_of_week=3),  # 수요일 08:30
    },
}
```

### 임계치 조정

`config/thresholds.yaml` 수정:

```yaml
theta:
  delta_7d_warn: -0.10  # 더 민감하게
  delta_7d_crit: -0.20
```

### 리포트 템플릿 수정

`templates/weekly_report.Rmd` 수정:
- 섹션 추가/제거
- 차트 스타일 변경
- 브랜딩 커스터마이징

## 📧 이메일/슬랙 전송

### 이메일 설정 (tasks.py에 구현 필요)

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email(to_addresses, subject, html_body, attachments):
    msg = MIMEMultipart()
    msg['From'] = os.getenv('SMTP_FROM')
    msg['To'] = ', '.join(to_addresses)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(html_body, 'html'))
    
    for file_path in attachments:
        with open(file_path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=Path(file_path).name)
            part['Content-Disposition'] = f'attachment; filename="{Path(file_path).name}"'
            msg.attach(part)
    
    with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
        server.starttls()
        server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
```

### 슬랙 웹훅 (tasks.py에 구현 필요)

```python
import requests

def send_slack_notification(webhook_url, summary_data):
    payload = {
        "text": f"📊 Weekly Risk Report - {summary_data['org_name']}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{summary_data['org_name']}* Weekly Risk Report\n"
                            f"• Total Students: {summary_data['total_students']}\n"
                            f"• 🔴 CRITICAL: {summary_data['crit_count']} ({summary_data['crit_pct']:.1f}%)\n"
                            f"• 🟡 WARNING: {summary_data['warn_count']} ({summary_data['warn_pct']:.1f}%)\n"
                            f"• 🟢 OK: {summary_data['ok_count']}"
                }
            }
        ]
    }
    
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()
```

## 🐳 Docker 배포

### Dockerfile

```dockerfile
FROM python:3.11-slim

# R 설치
RUN apt-get update && apt-get install -y \
    r-base \
    r-base-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# R 패키지 설치
RUN Rscript -e 'install.packages(c("dplyr", "readr", "yaml", "lubridate", "rmarkdown", "ggplot2", "DT", "knitr"), repos="https://cran.rstudio.com/")'

# Python 패키지 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# 파이프라인 코드 복사
COPY backend/risk_pipeline /app/risk_pipeline

WORKDIR /app/risk_pipeline

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info", "--queue=risk_pipeline"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
  
  celery-worker:
    build: .
    command: celery -A tasks worker --loglevel=info --queue=risk_pipeline
    volumes:
      - ./backend/risk_pipeline:/app/risk_pipeline
      - ./reports:/app/risk_pipeline/reports
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - PGHOST=postgres
      - PGDATABASE=dreamseed
      - PGUSER=dreamseed
      - PGPASSWORD=password
    depends_on:
      - redis
  
  celery-beat:
    build: .
    command: celery -A tasks beat --loglevel=info
    volumes:
      - ./backend/risk_pipeline:/app/risk_pipeline
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
```

## 🔍 모니터링

### Celery Flower (웹 UI)

```bash
pip install flower
celery -A tasks flower --port=5555

# http://localhost:5555 접속
```

### 로그 확인

```bash
# 워커 로그
tail -f /var/log/celery/worker.log

# Beat 로그
tail -f /var/log/celery/beat.log
```

### 태스크 상태 확인

```python
from tasks import run_weekly_pipeline
from celery.result import AsyncResult

# 태스크 실행
result = run_weekly_pipeline.delay()

# 상태 확인
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE

# 결과 가져오기 (블로킹)
output = result.get(timeout=3600)
```

## 🛠️ 트러블슈팅

### 태스크가 실행되지 않음

```bash
# Redis 연결 확인
redis-cli ping

# Celery 워커 상태 확인
celery -A tasks inspect active

# Beat 스케줄 확인
celery -A tasks inspect scheduled
```

### R 스크립트 오류

```bash
# R 패키지 설치 확인
Rscript -e 'library(dplyr); library(readr); library(yaml)'

# 수동 실행으로 디버깅
Rscript jobs/10_compute_metrics.R /tmp/snapshot.csv config/tenants.yaml config/thresholds.yaml /tmp/metrics.csv
```

### PostgreSQL 연결 오류

```bash
# 환경 변수 확인
echo $PGHOST $PGDATABASE $PGUSER

# psql 직접 테스트
psql -f jobs/00_fetch_snapshots.sql
```

## 📚 참고 문서

- [Celery 공식 문서](https://docs.celeryproject.org/)
- [RMarkdown 가이드](https://rmarkdown.rstudio.com/)
- [DreamSeed IRT 시스템](../shared/irt/README.md)
- [교사용 대시보드](../../portal_front/dashboard/README.md)

---

**작성일**: 2025-11-09  
**버전**: 1.0.0  
**상태**: ✅ Production Ready
