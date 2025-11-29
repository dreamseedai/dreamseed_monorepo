# syntax=docker/dockerfile:1
FROM rstudio/quarto:1.5.57

# Install OS deps for Python/Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip libpq-dev && rm -rf /var/lib/apt/lists/*

# Python deps for data access + S3
RUN pip3 install --no-cache-dir boto3 sqlalchemy psycopg2-binary pyyaml

WORKDIR /app
COPY reports/quarto /app/reports/quarto
COPY apps/seedtest_api/jobs/generate_weekly_report.py /app/generate_weekly_report.py

ENV S3_BUCKET=seedtest-reports \
    AWS_REGION=ap-northeast-2 \
    REPORT_FORMAT=pdf

ENTRYPOINT ["/bin/bash","-lc"]
CMD ["echo Quarto runner image built. Use as a job container to run generate_weekly_report.py"]
