#!/bin/bash
# infra/monitoring/alertmanager/setup-secrets.sh
# Alertmanager Slack Webhook Secret 생성 스크립트

set -euo pipefail

NAMESPACE="${1:-monitoring}"
SLACK_WEBHOOK_URL="${2:-}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Alertmanager Slack Webhook Secret 생성"
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
    echo "  bash setup-secrets.sh <namespace> <slack_webhook_url>"
    echo ""
    echo "예시:"
    echo "  bash setup-secrets.sh monitoring \\"
    echo "    'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX'"
    echo ""
    echo "또는 환경 변수로 전달:"
    echo "  SLACK_WEBHOOK_URL='...' bash setup-secrets.sh monitoring"
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
echo "2️⃣  Secret 확인"
echo "───────────────────────────────────────────────────────"
kubectl -n "$NAMESPACE" get secret alertmanager-secrets

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Secret 생성 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 다음 단계:"
echo "   1. Alertmanager 배포:"
echo "      kubectl apply -k infra/monitoring/alertmanager/"
echo ""
echo "   2. 검증:"
echo "      bash infra/monitoring/alertmanager/validate-alertmanager.sh $NAMESPACE"
echo ""
