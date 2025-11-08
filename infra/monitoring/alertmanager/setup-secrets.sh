#!/bin/bash
# infra/monitoring/alertmanager/setup-secrets.sh
# Alertmanager 시크릿 생성 스크립트

set -euo pipefail

NAMESPACE="${1:-monitoring}"
SLACK_WEBHOOK_URL="${2:-}"
PAGERDUTY_ROUTING_KEY="${3:-}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Alertmanager Secrets 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "네임스페이스: $NAMESPACE"
echo ""

# ──────────────────────────────────────────────────────────
echo "1️⃣  Slack Webhook URL Secret"
echo "───────────────────────────────────────────────────────"

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "⚠️  Slack Webhook URL이 제공되지 않았습니다."
    echo ""
    echo "사용법:"
    echo "  bash setup-secrets.sh <namespace> <slack_webhook_url> <pagerduty_routing_key>"
    echo ""
    echo "예시:"
    echo "  bash setup-secrets.sh monitoring \\"
    echo "    'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX' \\"
    echo "    'PD_ROUTING_KEY_XXXXXXXXXXXX'"
    echo ""
    echo "또는 환경 변수로 전달:"
    echo "  SLACK_WEBHOOK_URL='...' PAGERDUTY_ROUTING_KEY='...' bash setup-secrets.sh monitoring"
    exit 1
fi

if kubectl -n "$NAMESPACE" get secret alertmanager-secrets &>/dev/null; then
    echo "⚠️  Secret 'alertmanager-secrets'가 이미 존재합니다."
    read -p "덮어쓰시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 취소됨"
        exit 1
    fi
    kubectl -n "$NAMESPACE" delete secret alertmanager-secrets
fi

kubectl -n "$NAMESPACE" create secret generic alertmanager-secrets \
    --from-literal=slack_webhook_url="$SLACK_WEBHOOK_URL"

echo "✅ Secret 생성: alertmanager-secrets"
echo "   키: slack_webhook_url"
echo "   마운트 경로: /etc/alertmanager/secrets/alertmanager-secrets/slack_webhook_url"

# ──────────────────────────────────────────────────────────
echo ""
echo "2️⃣  PagerDuty Routing Key Secret"
echo "───────────────────────────────────────────────────────"

if [ -z "$PAGERDUTY_ROUTING_KEY" ]; then
    echo "⚠️  PagerDuty Routing Key가 제공되지 않았습니다."
    echo "   건너뜀 (PagerDuty 사용하지 않을 경우 OK)"
else
    if kubectl -n "$NAMESPACE" get secret pagerduty-routing-key &>/dev/null; then
        echo "⚠️  Secret 'pagerduty-routing-key'가 이미 존재합니다."
        read -p "덮어쓰시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ 건너뜀"
        else
            kubectl -n "$NAMESPACE" delete secret pagerduty-routing-key
            kubectl -n "$NAMESPACE" create secret generic pagerduty-routing-key \
                --from-literal=routing_key="$PAGERDUTY_ROUTING_KEY"
            echo "✅ Secret 생성: pagerduty-routing-key"
            echo "   키: routing_key"
            echo "   마운트 경로: /etc/alertmanager/secrets/pagerduty-routing-key/routing_key"
        fi
    else
        kubectl -n "$NAMESPACE" create secret generic pagerduty-routing-key \
            --from-literal=routing_key="$PAGERDUTY_ROUTING_KEY"
        echo "✅ Secret 생성: pagerduty-routing-key"
        echo "   키: routing_key"
        echo "   마운트 경로: /etc/alertmanager/secrets/pagerduty-routing-key/routing_key"
    fi
fi

# ──────────────────────────────────────────────────────────
echo ""
echo "3️⃣  Secret 확인"
echo "───────────────────────────────────────────────────────"
kubectl -n "$NAMESPACE" get secret alertmanager-secrets pagerduty-routing-key 2>/dev/null || \
    kubectl -n "$NAMESPACE" get secret alertmanager-secrets

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Secret 생성 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 다음 단계:"
echo "   1. Alertmanager CR 적용 (Secret 마운트):"
echo "      kubectl apply -f infra/monitoring/alertmanager/alertmanager-cr.yaml"
echo ""
echo "   2. Alertmanager 설정 적용:"
echo "      kubectl apply -f infra/monitoring/alertmanager/alertmanager-secret.yaml"
echo ""
echo "   3. 검증:"
echo "      bash infra/monitoring/alertmanager/validate-alertmanager.sh $NAMESPACE"
echo ""
