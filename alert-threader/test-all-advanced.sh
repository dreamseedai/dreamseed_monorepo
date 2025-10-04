#!/usr/bin/env bash
set -euo pipefail

echo "🧪 DreamSeed Alert Threader - All Languages Advanced 테스트 시작"

# 1. 실행 중인 서비스 확인
echo "📊 실행 중인 서비스 확인 중..."
ACTIVE_SERVICES=()
for lang in python nodejs go; do
    if systemctl is-active --quiet alert-threader-$lang 2>/dev/null; then
        ACTIVE_SERVICES+=($lang)
        echo "✅ Alert Threader ($lang): 실행 중"
    else
        echo "❌ Alert Threader ($lang): 중지됨"
    fi
done

if [ ${#ACTIVE_SERVICES[@]} -eq 0 ]; then
    echo "❌ 실행 중인 서비스가 없습니다"
    echo "시작: sudo systemctl start alert-threader-<language>"
    exit 1
fi

echo "실행 중인 서비스: ${ACTIVE_SERVICES[*]}"

# 2. 포트 확인
echo "🔍 포트 확인 중..."
if netstat -tlnp | grep -q ":9009 "; then
    echo "✅ 포트 9009: 열림"
else
    echo "❌ 포트 9009: 닫힘"
    exit 1
fi

# 3. 헬스체크
echo "🏥 헬스체크 중..."
if curl -s http://localhost:9009/health | jq .; then
    echo "✅ 헬스체크: 성공"
else
    echo "❌ 헬스체크: 실패"
    exit 1
fi

# 4. 통계 확인
echo "📊 통계 확인 중..."
if curl -s http://localhost:9009/stats | jq .; then
    echo "✅ 통계 조회: 성공"
else
    echo "❌ 통계 조회: 실패"
fi

# 5. Critical 알림 테스트 (Block Kit + Attachments)
echo "🚨 Critical 알림 테스트 중 (Block Kit + Attachments)..."
curl -X POST http://localhost:9009/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "firing",
    "groupKey": "test-group-1",
    "alerts": [
      {
        "labels": {
          "alertname": "DreamSeedTestCritical",
          "severity": "critical",
          "service": "database",
          "cluster": "production",
          "instance": "db01.example.com",
          "job": "mysql-exporter"
        },
        "annotations": {
          "summary": "DreamSeed Database Critical Failure",
          "description": "MySQL 데이터베이스 연결이 완전히 실패했습니다. 즉시 조치가 필요합니다.",
          "runbook_url": "https://docs.dreamseed.com/runbooks/database-failure"
        },
        "startsAt": "2024-01-15T14:30:25Z"
      }
    ]
  }' | jq .

sleep 3

# 6. 같은 알림으로 스레드 테스트 (업데이트)
echo "🧵 스레드 답글 테스트 중 (업데이트)..."
curl -X POST http://localhost:9009/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "firing",
    "groupKey": "test-group-1",
    "alerts": [
      {
        "labels": {
          "alertname": "DreamSeedTestCritical",
          "severity": "critical",
          "service": "database",
          "cluster": "production",
          "instance": "db01.example.com",
          "job": "mysql-exporter"
        },
        "annotations": {
          "summary": "DreamSeed Database Critical Failure (Escalated)",
          "description": "데이터베이스 상태가 더욱 악화되었습니다. 백업 서버도 영향을 받고 있습니다.",
          "runbook_url": "https://docs.dreamseed.com/runbooks/database-failure"
        },
        "startsAt": "2024-01-15T14:30:25Z"
      }
    ]
  }' | jq .

sleep 3

# 7. Warning 알림 테스트 (다른 서비스)
echo "⚠️ Warning 알림 테스트 중 (다른 서비스)..."
curl -X POST http://localhost:9009/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "firing",
    "groupKey": "test-group-2",
    "alerts": [
      {
        "labels": {
          "alertname": "DreamSeedTestWarning",
          "severity": "warning",
          "service": "api",
          "cluster": "production",
          "instance": "api01.example.com",
          "job": "api-exporter"
        },
        "annotations": {
          "summary": "DreamSeed API High Response Time",
          "description": "API 응답 시간이 2초를 초과했습니다. 모니터링이 필요합니다.",
          "runbook_url": "https://docs.dreamseed.com/runbooks/api-performance"
        },
        "startsAt": "2024-01-15T14:35:10Z"
      }
    ]
  }' | jq .

sleep 3

# 8. Info 알림 테스트
echo "ℹ️ Info 알림 테스트 중..."
curl -X POST http://localhost:9009/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "firing",
    "groupKey": "test-group-3",
    "alerts": [
      {
        "labels": {
          "alertname": "DreamSeedTestInfo",
          "severity": "info",
          "service": "monitoring",
          "cluster": "production",
          "instance": "mon01.example.com",
          "job": "prometheus"
        },
        "annotations": {
          "summary": "DreamSeed Monitoring System Update",
          "description": "모니터링 시스템이 성공적으로 업데이트되었습니다.",
          "runbook_url": "https://docs.dreamseed.com/runbooks/monitoring-update"
        },
        "startsAt": "2024-01-15T14:40:00Z"
      }
    ]
  }' | jq .

sleep 3

# 9. Resolved 알림 테스트 (Critical 해결)
echo "✅ Resolved 알림 테스트 중 (Critical 해결)..."
curl -X POST http://localhost:9009/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "resolved",
    "groupKey": "test-group-1",
    "alerts": [
      {
        "labels": {
          "alertname": "DreamSeedTestCritical",
          "severity": "critical",
          "service": "database",
          "cluster": "production",
          "instance": "db01.example.com",
          "job": "mysql-exporter"
        },
        "annotations": {
          "summary": "DreamSeed Database Critical Failure",
          "description": "데이터베이스 연결이 정상적으로 복구되었습니다.",
          "runbook_url": "https://docs.dreamseed.com/runbooks/database-failure"
        },
        "startsAt": "2024-01-15T14:30:25Z",
        "endsAt": "2024-01-15T14:45:30Z"
      }
    ]
  }' | jq .

sleep 3

# 10. 캐시 상태 확인
echo "💾 캐시 상태 확인 중..."
curl -s http://localhost:9009/cache | jq .

# 11. 통계 확인
echo "📊 최종 통계 확인 중..."
curl -s http://localhost:9009/stats | jq .

# 12. 로그 확인
echo "📝 최근 로그 확인 중..."
for lang in "${ACTIVE_SERVICES[@]}"; do
    echo "--- Alert Threader ($lang) 로그 (최근 5줄) ---"
    sudo journalctl -u alert-threader-$lang --no-pager -n 5
    echo ""
done

echo "🎉 고급 테스트 완료!"
echo ""
echo "📋 확인사항:"
echo "  1. Slack 채널에서 Block Kit 메시지가 생성되었는지 확인"
echo "  2. Attachments의 컬러와 필드가 올바르게 표시되는지 확인"
echo "  3. Critical 알림은 별도 스레드로 생성되었는지 확인"
echo "  4. Warning 알림은 별도 스레드로 생성되었는지 확인"
echo "  5. Info 알림은 별도 스레드로 생성되었는지 확인"
echo "  6. Resolved 알림은 기존 스레드에 답글로 추가되었는지 확인"
echo "  7. Runbook URL이 클릭 가능한 링크로 표시되는지 확인"
echo "  8. 시간 정보가 올바르게 포맷팅되었는지 확인"
echo ""
echo "🔧 문제 해결:"
for lang in "${ACTIVE_SERVICES[@]}"; do
    echo "  - $lang 로그 확인: sudo journalctl -u alert-threader-$lang -f"
    echo "  - $lang 서비스 재시작: sudo systemctl restart alert-threader-$lang"
done
echo "  - 캐시 초기화: curl -X DELETE http://localhost:9009/cache"
echo "  - 통계 확인: curl http://localhost:9009/stats | jq ."
echo ""
echo "📊 저장소별 확인:"
echo "  - 파일 저장소: ls -la /var/lib/alert-threader/threads.json"
echo "  - Redis 저장소: redis-cli keys 'threader:ts:*'"
echo ""
echo "🔄 언어 전환:"
for lang in "${ACTIVE_SERVICES[@]}"; do
    echo "  - $lang 중지: sudo systemctl stop alert-threader-$lang"
    echo "  - $lang 시작: sudo systemctl start alert-threader-$lang"
done

