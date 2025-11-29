# DreamSeedAI Shiny Dashboard
# 교사용 리스크 대시보드

FROM rocker/shiny:4.3.2

LABEL maintainer="DreamSeedAI <ops@dreamseedai.com>"
LABEL description="Weekly risk dashboard with Shiny"

# 시스템 라이브러리
RUN apt-get update && apt-get install -y \
    libssl-dev \
    libxml2-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# R 패키지 설치
RUN R -q -e "install.packages(c( \
    'yaml', \
    'arrow', \
    'dplyr', \
    'DT', \
    'tidyr' \
), repos='https://cran.rstudio.com/')"

# 환경 변수
ENV RISK_REPORTS_DIR=/opt/dreamseedai/risk_pipeline/reports

# Shiny 앱 복사
COPY app.R /srv/shiny-server/

# Shiny 설정
RUN echo "run_as shiny;" > /etc/shiny-server/shiny-server.conf && \
    echo "server {" >> /etc/shiny-server/shiny-server.conf && \
    echo "  listen 3838;" >> /etc/shiny-server/shiny-server.conf && \
    echo "  location / {" >> /etc/shiny-server/shiny-server.conf && \
    echo "    site_dir /srv/shiny-server;" >> /etc/shiny-server/shiny-server.conf && \
    echo "    log_dir /var/log/shiny-server;" >> /etc/shiny-server/shiny-server.conf && \
    echo "    directory_index on;" >> /etc/shiny-server/shiny-server.conf && \
    echo "  }" >> /etc/shiny-server/shiny-server.conf && \
    echo "}" >> /etc/shiny-server/shiny-server.conf

# 포트 노출
EXPOSE 3838

# Shiny 서버 실행
CMD ["/usr/bin/shiny-server"]
