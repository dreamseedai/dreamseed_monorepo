# DreamSeedAI Risk Pipeline
# R + Python 환경

FROM rocker/tidyverse:4.3.2

LABEL maintainer="DreamSeedAI <ops@dreamseedai.com>"
LABEL description="Weekly risk report pipeline with R and Python"

# 시스템 라이브러리
RUN apt-get update && apt-get install -y \
    libssl-dev \
    libxml2-dev \
    libcurl4-openssl-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    python3 \
    python3-pip \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# R 패키지 설치
RUN R -q -e "install.packages(c( \
    'yaml', \
    'arrow', \
    'rmarkdown', \
    'DT', \
    'mirt', \
    'RPostgres', \
    'dplyr', \
    'readr', \
    'tidyr', \
    'purrr', \
    'lubridate', \
    'ggplot2', \
    'knitr' \
), repos='https://cran.rstudio.com/')"

# Python 패키지 설치
RUN pip3 install --no-cache-dir \
    pandas \
    numpy \
    pyyaml

# 작업 디렉토리
WORKDIR /opt/dreamseedai/risk_pipeline

# 파이프라인 코드 복사
COPY config/ ./config/
COPY jobs/ ./jobs/
COPY templates/ ./templates/
COPY scripts/ ./scripts/

# 실행 권한 부여
RUN chmod +x scripts/*.sh jobs/*.R jobs/*.py

# 환경 변수
ENV RISK_REPORTS_DIR=/opt/dreamseedai/risk_pipeline/reports
ENV RISK_EMAIL_FROM=reports@dreamseedai.com
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 리포트 디렉토리 생성
RUN mkdir -p $RISK_REPORTS_DIR

# 기본 명령
CMD ["bash", "scripts/run_all.sh"]
