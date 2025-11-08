#!/bin/bash
# infra/monitoring/alertmanager/validate-alertmanager.sh
# Alertmanager 설정 및 라우팅 검증 스크립트

set -euo pipefail

NAMESPACE="${1:-monitoring}"
ALERTMANAGER_NAME="${2:-alertmanager-main}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚨 Alertmanager 설정 검증"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ──────────────────────────────────────────────────────────
echo "1️⃣  Secret 리소스 확인"
echo "───────────────────────────────────────────────────────"
if kubectl -n "$NAMESPACE" get secret "$ALERTMANAGER_NAME" &>/dev/null; then
    echo "✅ Secret 존재: $ALERTMANAGER_NAME"
    
    echo ""
    echo "📋 설정 미리보기 (첫 20줄):"
    kubectl -n "$NAMESPACE" get secret "$ALERTMANAGER_NAME" \
        -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d | head -20
else
    echo "❌ Secret 없음: $ALERTMANAGER_NAME"
    echo "   배포 필요: kubectl apply -f infra/monitoring/alertmanager/alertmanager-secret.yaml"
    exit 1
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "2️⃣  Alertmanager Pod 상태 확인"
echo "───────────────────────────────────────────────────────"
if kubectl -n "$NAMESPACE" get pod -l app.kubernetes.io/name=alertmanager &>/dev/null; then
    POD_STATUS=$(kubectl -n "$NAMESPACE" get pod -l app.kubernetes.io/name=alertmanager \
        -o jsonpath='{.items[0].status.phase}')
    POD_NAME=$(kubectl -n "$NAMESPACE" get pod -l app.kubernetes.io/name=alertmanager \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ "$POD_STATUS" = "Running" ]; then
        echo "✅ Alertmanager Pod 실행 중: $POD_NAME"
    else
        echo "⚠️  Alertmanager Pod 상태: $POD_STATUS ($POD_NAME)"
    fi
else
    echo "❌ Alertmanager Pod 없음"
    echo "   Prometheus Operator 설치 확인 필요"
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "3️⃣  설정 내용 검증"
echo "───────────────────────────────────────────────────────"
CONFIG=$(kubectl -n "$NAMESPACE" get secret "$ALERTMANAGER_NAME" \
    -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d)

echo "📦 수신자(Receivers) 확인:"
echo "$CONFIG" | grep -A1 "name:" | grep "name:" | sed 's/.*name: /  - /' || echo "  (없음)"

echo ""
echo "🔀 라우팅 규칙(Routes) 확인:"
ROUTES=$(echo "$CONFIG" | grep -A2 "matchers:" | grep -E "(matchers|receiver)" || echo "")
if [ -n "$ROUTES" ]; then
    echo "$ROUTES" | sed 's/^/  /'
else
    echo "  (기본 route만 존재)"
fi

echo ""
echo "🔇 억제 규칙(Inhibit Rules) 확인:"
INHIBIT=$(echo "$CONFIG" | grep -A1 "inhibit_rules:" | tail -1)
if echo "$INHIBIT" | grep -q "source_matchers"; then
    echo "  ✅ 억제 규칙 설정됨 (Critical → Warning)"
else
    echo "  ℹ️  억제 규칙 없음"
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "4️⃣  Secret 마운트 확인"
echo "───────────────────────────────────────────────────────"
if [ -n "${POD_NAME:-}" ] && [ "$POD_STATUS" = "Running" ]; then
    echo "ℹ️  Secret 파일 확인 (Pod 내부):"
    echo ""
    echo "   Slack Webhook:"
    if kubectl -n "$NAMESPACE" exec "$POD_NAME" -- \
        test -f /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url 2>/dev/null; then
        echo "   ✅ /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url"
    else
        echo "   ❌ /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url (없음)"
    fi
    
    echo ""
    echo "   PagerDuty Routing Key:"
    if kubectl -n "$NAMESPACE" exec "$POD_NAME" -- \
        test -f /etc/alertmanager/secrets/pagerduty-routing-key/routing_key 2>/dev/null; then
        echo "   ✅ /etc/alertmanager/secrets/pagerduty-routing-key/routing_key"
    else
        echo "   ⚠️  /etc/alertmanager/secrets/pagerduty-routing-key/routing_key (없음)"
    fi
else
    echo "⚠️  Pod가 Running 상태가 아니어서 Secret 마운트 확인 불가"
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "5️⃣  Alertmanager UI 접근 (포트포워드)"
echo "───────────────────────────────────────────────────────"
if [ -n "${POD_NAME:-}" ]; then
    echo "ℹ️  포트포워드 명령어:"
    echo "   kubectl -n $NAMESPACE port-forward $POD_NAME 9093:9093"
    echo ""
    echo "   브라우저: http://127.0.0.1:9093"
    echo "   - Status → Config: 전체 설정 확인"
    echo "   - Status → Routes: 라우팅 트리 시각화"
    echo "   - Alerts: 활성 알림 목록"
else
    echo "⚠️  Pod가 실행 중이 아니어서 포트포워드 불가"
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "6️⃣  테스트 알림 전송 (amtool 필요)"
echo "───────────────────────────────────────────────────────"
echo "ℹ️  amtool 설치 (없을 경우):"
echo "   # macOS"
echo "   brew install amtool"
echo ""
echo "   # Linux"
echo "   wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz"
echo "   tar xzf alertmanager-0.26.0.linux-amd64.tar.gz"
echo "   sudo cp alertmanager-0.26.0.linux-amd64/amtool /usr/local/bin/"
echo ""
echo "ℹ️  테스트 알림 전송 (포트포워드 후):"
echo ""
echo "   # Critical → PagerDuty"
echo "   amtool --alertmanager.url=http://127.0.0.1:9093 alert add \\"
echo "     alertname=TestCritical \\"
echo "     service=seedtest-api \\"
echo "     severity=critical \\"
echo "     summary=\"PagerDuty 라우팅 테스트\" \\"
echo "     description=\"Critical 알림이 PagerDuty로 전송되어야 합니다\""
echo ""
echo "   # Warning → Slack"
echo "   amtool --alertmanager.url=http://127.0.0.1:9093 alert add \\"
echo "     alertname=TestWarning \\"
echo "     service=seedtest-api \\"
echo "     severity=warning \\"
echo "     summary=\"Slack 라우팅 테스트\" \\"
echo "     description=\"Warning 알림이 #seedtest-alerts로 전송되어야 합니다\""

echo ""
echo "───────────────────────────────────────────────────────"
echo "7️⃣  활성 알림 확인 (Prometheus)"
echo "───────────────────────────────────────────────────────"
echo "ℹ️  Prometheus UI에서 확인:"
echo "   1. 포트포워드:"
echo "      kubectl -n $NAMESPACE port-forward svc/prometheus-operated 9090:9090"
echo ""
echo "   2. 브라우저: http://127.0.0.1:9090/alerts"
echo "      필터: service=\"seedtest-api\""
echo ""
echo "   3. API 확인:"
echo "      curl -s 'http://127.0.0.1:9090/api/v1/alerts' | jq '.data.alerts[] | {name: .labels.alertname, severity: .labels.severity}'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 검증 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 참고 문서:"
echo "   - ALERTMANAGER_ROUTING_GUIDE.md: 상세 설정 가이드"
echo "   - ops/k8s/governance/MONITORING_QUICKREF.md: 알림 룰 목록"
echo ""
