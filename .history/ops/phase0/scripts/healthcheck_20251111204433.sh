#!/bin/bash
# Phase 0 헬스체크 스크립트
# 모든 서비스가 정상인지 확인

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_CHECKS=0

# 체크 함수
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "Checking $service_name... "
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo "=========================================="
echo "   Phase 0 Health Check"
echo "=========================================="
echo ""

# 1. Docker 실행 확인
check_service "Docker daemon" "docker info"

# 2. PostgreSQL (Docker 또는 호스트)
if docker ps 2>/dev/null | grep -q dreamseed-postgres; then
    check_service "PostgreSQL (Docker)" "docker exec dreamseed-postgres pg_isready -U postgres"
else
    check_service "PostgreSQL (Host)" "pg_isready -h localhost -p 5432"
fi

# 3. Redis (Docker 또는 호스트)
if docker ps 2>/dev/null | grep -q dreamseed-redis; then
    check_service "Redis (Docker)" "docker exec dreamseed-redis redis-cli ping | grep -q PONG"
else
    check_service "Redis (Host)" "redis-cli ping | grep -q PONG"
fi

# 4. Prometheus
check_service "Prometheus" "curl -sf http://localhost:9090/-/healthy"

# 5. Grafana
check_service "Grafana" "curl -sf http://localhost:3000/api/health"

# 6. Node Exporter
check_service "Node Exporter" "curl -sf http://localhost:9100/metrics"

# 7. Postgres Exporter
check_service "Postgres Exporter" "curl -sf http://localhost:9187/metrics"

# 8. Redis Exporter
check_service "Redis Exporter" "curl -sf http://localhost:9121/metrics"

# 9. 디스크 공간 확인 (20% 미만 시 경고)
echo -n "Checking disk space... "
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ OK${NC} ($DISK_USAGE% used)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} ($DISK_USAGE% used)"
fi

# 10. 메모리 확인
echo -n "Checking memory... "
MEM_AVAILABLE=$(free -m | awk 'NR==2{printf "%.0f", $7}')
if [ "$MEM_AVAILABLE" -gt 1000 ]; then
    echo -e "${GREEN}✓ OK${NC} (${MEM_AVAILABLE}MB available)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} (${MEM_AVAILABLE}MB available)"
fi

# 11. CPU 부하 확인
echo -n "Checking CPU load... "
CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
CPU_CORES=$(nproc)
if (( $(echo "$CPU_LOAD < $CPU_CORES" | bc -l) )); then
    echo -e "${GREEN}✓ OK${NC} (load: $CPU_LOAD, cores: $CPU_CORES)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} (load: $CPU_LOAD, cores: $CPU_CORES)"
fi

# 12. Docker 네트워크 확인
check_service "Docker network" "docker network inspect dreamseed-network"

# 13. 백업 파일 존재 확인
echo -n "Checking recent backups... "
LATEST_BACKUP=$(find /tmp/postgres_backups -name "dreamseed_db_*.sql.gz" -mtime -1 2>/dev/null | wc -l)
if [ "$LATEST_BACKUP" -gt 0 ]; then
    echo -e "${GREEN}✓ OK${NC} ($LATEST_BACKUP backup(s) in last 24h)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} (No backups in last 24h)"
fi

# 14. 로그 확인 (에러 체크)
echo -n "Checking logs for errors... "
ERROR_COUNT=$(docker compose -f ops/phase0/configs/monitoring/docker-compose.monitoring.yml logs --tail=100 2>&1 | grep -i "error" | wc -l)
if [ "$ERROR_COUNT" -lt 5 ]; then
    echo -e "${GREEN}✓ OK${NC} ($ERROR_COUNT errors in last 100 lines)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} ($ERROR_COUNT errors in last 100 lines)"
fi

echo ""
echo "=========================================="

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✅${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}$FAILED_CHECKS check(s) failed! ❌${NC}"
    echo "=========================================="
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check Docker containers: docker ps -a"
    echo "2. View logs: docker compose -f ops/phase0/configs/monitoring/docker-compose.monitoring.yml logs"
    echo "3. Restart services: cd ops/phase0/scripts && ./deploy_phase0.sh"
    exit 1
fi
