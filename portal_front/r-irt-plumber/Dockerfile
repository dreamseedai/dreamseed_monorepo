# syntax=docker/dockerfile:1
FROM rocker/r-ver:4.3.2

ENV DEBIAN_FRONTEND=noninteractive \
    RENV_CONFIG_REPOS_OVERRIDE=https://packagemanager.posit.co/cran/__linux__/jammy/latest

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev libssl-dev libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# mirt depends on several packages available on CRAN
RUN R -e "install.packages(c('plumber','mirt','data.table','jsonlite'))"

WORKDIR /app
COPY api.R /app/api.R

ENV PLUMBER_RUN=true \
    PORT=8000 \
    R_IRT_VERSION=v0.1

EXPOSE 8000

CMD ["R", "-e", "pr <- plumber::plumb('api.R'); pr$run(host='0.0.0.0', port=as.integer(Sys.getenv('PORT', 8000)))"]
