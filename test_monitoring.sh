#!/usr/bin/env bash
set -euo pipefail

echo "🧪 DreamSeed 모니터링 시스템 테스트 시작"

# 1. 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
services=("prometheus" "alertmanager" "node-exporter")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service: 실행 중"
    else
        echo "❌ $service: 중지됨"
    fi
done

# 2. 포트 확인
echo "🔍 포트 확인 중..."
ports=("9090:Prometheus" "9093:Alertmanager" "9100:Node Exporter")
for port_info in "${ports[@]}"; do
    port=$(echo "$port_info" | cut -d: -f1)
    service=$(echo "$port_info" | cut -d: -f2)
    if netstat -tlnp | grep -q ":$port "; then
        echo "✅ $service (포트 $port): 열림"
    else
        echo "❌ $service (포트 $port): 닫힘"
    fi
done

# 3. Prometheus 설정 검증
echo "⚙️ Prometheus 설정 검증 중..."
if command -v promtool >/dev/null 2>&1; then
    if sudo promtool check config /etc/prometheus/prometheus.yml; then
        echo "✅ Prometheus 설정: 유효"
    else
        echo "❌ Prometheus 설정: 오류"
    fi
    
    if sudo promtool check rules /etc/prometheus/rules/dreamseed-alerts.yml; then
        echo "✅ Prometheus 규칙: 유효"
    else
        echo "❌ Prometheus 규칙: 오류"
    fi
else
    echo "⚠️ promtool이 설치되지 않음"
fi

# 4. Alertmanager 설정 검증
echo "📢 Alertmanager 설정 검증 중..."
if command -v amtool >/dev/null 2>&1; then
    if sudo amtool check-config /etc/alertmanager/alertmanager.yml; then
        echo "✅ Alertmanager 설정: 유효"
    else
        echo "❌ Alertmanager 설정: 오류"
    fi
else
    echo "⚠️ amtool이 설치되지 않음"
fi

# 5. HTTP 엔드포인트 테스트
echo "🌐 HTTP 엔드포인트 테스트 중..."
endpoints=("http://localhost:9090" "http://localhost:9093" "http://localhost:9100/metrics")
for endpoint in "${endpoints[@]}"; do
    if curl -s -o /dev/null -w "%{http_code}" "$endpoint" | grep -q "200"; then
        echo "✅ $endpoint: 응답 정상"
    else
        echo "❌ $endpoint: 응답 오류"
    fi
done

# 6. 테스트 알림 전송
echo "📨 테스트 알림 전송 중..."
if command -v amtool >/dev/null 2>&1; then
    # 테스트 알림 생성
    sudo amtool --alertmanager.url=http://localhost:9093 alert add \
        -l alertname=DreamSeedTestAlert -l severity=info -l service=test \
        -a summary="DreamSeed 모니터링 테스트" \
        -a description="모니터링 시스템이 정상적으로 작동하고 있습니다." \
        2>/dev/null || true
    
    # 알림 목록 확인
    echo "📋 현재 알림 목록:"
    sudo amtool --alertmanager.url=http://localhost:9093 alert query 2>/dev/null || echo "알림을 가져올 수 없습니다"
else
    echo "⚠️ amtool이 설치되지 않음"
fi

# 7. DreamSeed 서비스 상태 확인
echo "🔍 DreamSeed 서비스 상태 확인 중..."
dreamseed_services=("dreamseed-api.service" "dreamseed-backup-enhanced.service")
for service in "${dreamseed_services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service: 실행 중"
    else
        echo "❌ $service: 중지됨"
    fi
done

# 8. 로그 확인
echo "📝 최근 로그 확인 중..."
echo "--- Prometheus 로그 (최근 5줄) ---"
sudo journalctl -u prometheus --no-pager -n 5 || echo "로그를 가져올 수 없습니다"

echo "--- Alertmanager 로그 (최근 5줄) ---"
sudo journalctl -u alertmanager --no-pager -n 5 || echo "로그를 가져올 수 없습니다"

# 9. 메트릭 확인
echo "📊 메트릭 확인 중..."
if curl -s http://localhost:9100/metrics | grep -q "node_"; then
    echo "✅ Node Exporter 메트릭: 정상"
else
    echo "❌ Node Exporter 메트릭: 오류"
fi

if curl -s http://localhost:8002/metrics | grep -q "dreamseed_"; then
    echo "✅ DreamSeed API 메트릭: 정상"
else
    echo "❌ DreamSeed API 메트릭: 오류"
fi

echo "🎉 모니터링 시스템 테스트 완료!"
echo ""
echo "📋 다음 단계:"
echo "  1. Slack Webhook URL 설정"
echo "  2. Grafana 대시보드 구성"
echo "  3. 알림 규칙 테스트"
echo "  4. 정기적인 모니터링 확인"

