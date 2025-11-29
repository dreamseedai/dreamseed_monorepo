#!/bin/bash
# Prometheus + Grafana 모니터링 스택 설정
# 실행: ./setup_monitoring.sh

set -e

GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_info "모니터링 스택 설정 시작..."

# 1. 모니터링 디렉토리 생성
mkdir -p ../monitoring/dashboards
mkdir -p ../monitoring/alerts
mkdir -p ../configs/monitoring

# 2. Prometheus 설정 파일 생성
cat > ../configs/monitoring/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - "/etc/prometheus/alerts/*.yml"

scrape_configs:
  # Prometheus 자체 모니터링
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node Exporter (시스템 메트릭)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # API Server (FastAPI/Flask)
  - job_name: 'api'
    metrics_path: /metrics
    static_configs:
      - targets: ['api:8000']
EOF

# 3. 알림 규칙 생성
cat > ../monitoring/alerts/basic_alerts.yml <<'EOF'
groups:
  - name: infrastructure
    interval: 30s
    rules:
      # PostgreSQL Down
      - alert: PostgreSQLDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL has been down for more than 1 minute."

      # Redis Down
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis has been down for more than 1 minute."

      # High CPU Usage
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for more than 5 minutes."

      # High Memory Usage
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 85% for more than 5 minutes."

      # Disk Space Low
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space running low"
          description: "Available disk space is below 20%."
EOF

# 4. Grafana 대시보드 생성 (System Overview)
cat > ../monitoring/dashboards/system_overview.json <<'EOF'
{
  "dashboard": {
    "title": "DreamSeed System Overview",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Disk Usage",
        "targets": [
          {
            "expr": "(node_filesystem_size_bytes{mountpoint=\"/\"} - node_filesystem_avail_bytes{mountpoint=\"/\"}) / node_filesystem_size_bytes{mountpoint=\"/\"} * 100"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
EOF

# 5. docker-compose 파일 생성 (모니터링 스택)
cat > ../configs/monitoring/docker-compose.monitoring.yml <<'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: dreamseed-prometheus
    volumes:
      - ../configs/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ../monitoring/alerts:/etc/prometheus/alerts
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    restart: unless-stopped
    networks:
      - dreamseed-network

  grafana:
    image: grafana/grafana:latest
    container_name: dreamseed-grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ../monitoring/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3000
    ports:
      - "3000:3000"
    restart: unless-stopped
    networks:
      - dreamseed-network
    depends_on:
      - prometheus

  node-exporter:
    image: prom/node-exporter:latest
    container_name: dreamseed-node-exporter
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"
    restart: unless-stopped
    networks:
      - dreamseed-network

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: dreamseed-postgres-exporter
    environment:
      - DATA_SOURCE_NAME=${DATABASE_URL}
    ports:
      - "9187:9187"
    restart: unless-stopped
    networks:
      - dreamseed-network

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: dreamseed-redis-exporter
    environment:
      - REDIS_ADDR=${REDIS_URL}
    ports:
      - "9121:9121"
    restart: unless-stopped
    networks:
      - dreamseed-network

volumes:
  prometheus-data:
  grafana-data:

networks:
  dreamseed-network:
    external: true
EOF

# 6. Docker 네트워크 생성 (없으면)
docker network create dreamseed-network 2>/dev/null || true

# 7. 모니터링 스택 시작
log_info "모니터링 스택 시작 중..."
cd ../configs/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

log_info "✓ 모니터링 스택 배포 완료"
log_info "  - Prometheus: http://localhost:9090"
log_info "  - Grafana: http://localhost:3000 (admin/admin)"
