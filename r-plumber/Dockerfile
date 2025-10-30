# R Plumber Dockerfile for GLMM Analysis
# Based on rocker/r-ver for reproducibility

FROM rocker/r-ver:4.3.2

LABEL maintainer="dreamseed-team"
LABEL description="R Plumber API for GLMM statistical analysis"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    zlib1g-dev \
    libsodium-dev \
    libnlopt-dev \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('plumber', 'lme4', 'data.table', 'jsonlite', 'broom.mixed'), repos='https://cloud.r-project.org/')"

# Create app directory
WORKDIR /app

# Copy API files
COPY api.R /app/
COPY api-extended.R /app/

# Expose port
EXPOSE 8000

# Environment variables
ENV PLUMBER_PORT=8000
ENV PLUMBER_HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

# Run plumber
CMD ["R", "-e", "pr <- plumber::plumb('api.R'); pr$run(host='0.0.0.0', port=8000)"]

