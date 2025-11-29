FROM rocker/r-ver:4.3.3

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpq-dev \
      libssl-dev \
      libxml2-dev \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN R -q -e "install.packages(c('DBI','RPostgres','glue'), repos='https://cloud.r-project.org')"

WORKDIR /opt/app
COPY aggregate_features_daily.R /opt/app/aggregate_features_daily.R

ENV TARGET_DATE=""
ENTRYPOINT ["Rscript", "/opt/app/aggregate_features_daily.R"]
