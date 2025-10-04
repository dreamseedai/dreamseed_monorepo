# DreamSeed Multi-stage Docker Build
FROM python:3.11-slim as builder

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 프로덕션 이미지
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 사용자 생성
RUN groupadd -r dreamseed && useradd -r -g dreamseed dreamseed

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 복사
COPY --from=builder /root/.local /home/dreamseed/.local
ENV PATH=/home/dreamseed/.local/bin:$PATH

# 애플리케이션 코드 복사
COPY api/ ./api/
COPY admin/ ./admin/
COPY *.html ./
COPY *.py ./
COPY *.sh ./
COPY *.conf ./
COPY *.yml ./
COPY *.json ./
COPY gunicorn.conf.py ./
COPY requirements.txt ./

# 데이터 및 로그 디렉토리 생성
RUN mkdir -p /app/data /app/logs && \
    chown -R dreamseed:dreamseed /app

# 포트 노출
EXPOSE 8002

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/healthz || exit 1

# 사용자 전환
USER dreamseed

# 환경 변수 설정
ENV PORT=8002
ENV APP_MODULE=api.dashboard_data:app
ENV WORKDIR=/app
ENV VENV=/home/dreamseed/.local
ENV DB_PATH=/app/data/dreamseed_analytics.db
ENV REDIS_URL=redis://redis:6379
ENV ENVIRONMENT=production

# 시작 명령
CMD ["sh", "-c", "cd ${WORKDIR} && exec gunicorn --config gunicorn.conf.py --bind 0.0.0.0:${PORT} ${APP_MODULE}"]

