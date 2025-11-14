# syntax=docker/dockerfile:1
FROM rocker/r-ver:4.3.2

LABEL org.opencontainers.image.source="https://example.com/seedtest/r-glmm-plumber"

ENV DEBIAN_FRONTEND=noninteractive \
    RENV_CONFIG_REPOS_OVERRIDE=https://packagemanager.posit.co/cran/__linux__/jammy/latest

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev libssl-dev libxml2-dev \
    libfreetype6-dev libharfbuzz-dev libfribidi-dev \
    libfontconfig1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('plumber','lme4','data.table','jsonlite','broom.mixed'))"

WORKDIR /app
COPY api.R /app/api.R

ENV PLUMBER_RUN=true \
    PORT=8000 \
    R_PLUMBER_VERSION=v1.0

EXPOSE 8000

CMD ["R", "-e", "pr <- plumber::plumb('api.R'); pr$run(host='0.0.0.0', port=as.integer(Sys.getenv('PORT', 8000)))"]
