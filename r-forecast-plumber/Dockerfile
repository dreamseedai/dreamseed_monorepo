FROM rocker/r-ver:4.3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libv8-dev \
    zlib1g-dev \
    libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('plumber', 'survival', 'prophet', 'jsonlite', 'dplyr'), repos='https://cloud.r-project.org/')"

# Create app directory
WORKDIR /app

# Copy API files
COPY api.R /app/
COPY plumber.R /app/

# Expose port
EXPOSE 8080

# Run plumber
CMD ["R", "-e", "pr <- plumber::plumb('/app/api.R'); pr$run(host='0.0.0.0', port=8080)"]
