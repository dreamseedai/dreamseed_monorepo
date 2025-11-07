FROM rocker/r-ver:4.3

# Install system dependencies for Stan/brms
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libv8-dev \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install R packages (brms will install rstan automatically)
# Note: This can take 30-60 minutes due to Stan compilation
RUN R -e "install.packages(c('plumber', 'jsonlite', 'dplyr'), repos='https://cloud.r-project.org/')"
RUN R -e "install.packages('brms', repos='https://cloud.r-project.org/')"

# Pre-compile a simple Stan model to cache compilation
RUN R -e "library(brms); brm(mpg ~ wt, data = mtcars, chains = 1, iter = 100, refresh = 0, silent = 2)"

# Create app directory
WORKDIR /app

# Copy API files
COPY api.R /app/
COPY plumber.R /app/

# Expose port
EXPOSE 8080

# Run plumber
CMD ["R", "-e", "pr <- plumber::plumb('/app/api.R'); pr$run(host='0.0.0.0', port=8080)"]
