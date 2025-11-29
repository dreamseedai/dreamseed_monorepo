# R Forecast Plumber - Prophet and Survival Analysis
FROM rocker/r-ver:4.3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('plumber', 'jsonlite', 'digest'), repos='https://cloud.r-project.org/')"

# Prophet (may take 5-10 minutes)
RUN R -e "install.packages('prophet', repos='https://cloud.r-project.org/')"

# Survival analysis
RUN R -e "install.packages('survival', repos='https://cloud.r-project.org/')"

# Create app directory
RUN mkdir -p /app
WORKDIR /app

# Copy API file
COPY api.R /app/api.R

# Expose port
EXPOSE 8080

# Run plumber API
CMD ["R", "-e", "pr <- plumber::plumb('/app/api.R'); pr$run(host='0.0.0.0', port=8080)"]
