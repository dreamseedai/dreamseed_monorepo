#!/usr/bin/env bash
set -euo pipefail

echo "🧪 DreamSeed Alert Threader 테스트 시작"

# 1. 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
if systemctl is-active --quiet alert-threader; then
    echo "✅ Alert Threader: 실행 중"
else
    echo "❌ Alert Threader: 중지됨"
    echo "시작: sudo systemctl start alert-threader"
    exit 1
fi

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

# 4. Critical 알림 테스트
echo "🚨 Critical 알림 테스트 중..."
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
          "service": "test"
        },
        "annotations": {
          "summary": "DreamSeed Critical 테스트 알림",
          "description": "이것은 Critical 심각도의 테스트 알림입니다. 즉시 확인이 필요합니다."
        }
      }
    ]
  }' | jq .

sleep 2

# 5. 같은 알림으로 스레드 테스트
echo "🧵 스레드 답글 테스트 중..."
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
          "service": "test"
        },
        "annotations": {
          "summary": "DreamSeed Critical 테스트 알림 (업데이트)",
          "description": "이것은 같은 알림의 업데이트입니다. 스레드로 답글이 달려야 합니다."
        }
      }
    ]
  }' | jq .

sleep 2

# 6. Warning 알림 테스트
echo "⚠️ Warning 알림 테스트 중..."
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
          "service": "api"
        },
        "annotations": {
          "summary": "DreamSeed Warning 테스트 알림",
          "description": "이것은 Warning 심각도의 테스트 알림입니다. 조사가 필요합니다."
        }
      }
    ]
  }' | jq .

sleep 2

# 7. Resolved 알림 테스트
echo "✅ Resolved 알림 테스트 중..."
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
          "service": "test"
        },
        "annotations": {
          "summary": "DreamSeed Critical 테스트 알림",
          "description": "이 알림이 해제되었습니다."
        }
      }
    ]
  }' | jq .

sleep 2

# 8. 캐시 상태 확인
echo "💾 캐시 상태 확인 중..."
curl -s http://localhost:9009/cache | jq .

# 9. 로그 확인
echo "📝 최근 로그 확인 중..."
echo "--- Alert Threader 로그 (최근 10줄) ---"
sudo journalctl -u alert-threader --no-pager -n 10

echo "🎉 테스트 완료!"
echo ""
echo "📋 확인사항:"
echo "  1. Slack 채널에서 새 메시지와 스레드 답글이 생성되었는지 확인"
echo "  2. Critical 알림은 별도 스레드로 생성되었는지 확인"
echo "  3. Warning 알림은 별도 스레드로 생성되었는지 확인"
echo "  4. Resolved 알림은 기존 스레드에 답글로 추가되었는지 확인"
echo ""
echo "🔧 문제 해결:"
echo "  - 로그 확인: sudo journalctl -u alert-threader -f"
echo "  - 서비스 재시작: sudo systemctl restart alert-threader"
echo "  - 캐시 초기화: curl -X DELETE http://localhost:9009/cache"

