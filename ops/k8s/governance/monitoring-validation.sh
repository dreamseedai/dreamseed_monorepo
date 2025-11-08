#!/bin/bash
# ops/k8s/governance/MONITORING_VALIDATION.sh
# PrometheusRule & Grafana 대시보드 검증 스크립트

set -euo pipefail

NAMESPACE="${1:-seedtest}"
RELEASE="${2:-prometheus}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SeedTest API 모니터링 검증"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ──────────────────────────────────────────────────────────
echo "1️⃣  PrometheusRule 리소스 확인"
echo "───────────────────────────────────────────────────────"
if kubectl -n "$NAMESPACE" get prometheusrule seedtest-api-rules &>/dev/null; then
    echo "✅ PrometheusRule 존재: seedtest-api-rules"
    
    echo ""
    echo "📋 룰 그룹 목록:"
    kubectl -n "$NAMESPACE" get prometheusrule seedtest-api-rules -o yaml \
        | grep 'name: seedtest-api\.' | sed 's/.*name: /  - /'
    
    echo ""
    echo "🔢 레코딩 룰 (Recording Rules):"
    kubectl -n "$NAMESPACE" get prometheusrule seedtest-api-rules -o yaml \
        | grep 'record:' | sed 's/.*record: /  - /' | sort -u
    
    echo ""
    echo "🚨 알림 룰 (Alert Rules):"
    kubectl -n "$NAMESPACE" get prometheusrule seedtest-api-rules -o yaml \
        | grep 'alert:' | sed 's/.*alert: /  - /' | sort -u
else
    echo "❌ PrometheusRule 없음: seedtest-api-rules"
    echo "   ArgoCD 동기화 또는 kubectl apply 필요"
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "2️⃣  ServiceMonitor 확인"
echo "───────────────────────────────────────────────────────"
if kubectl -n "$NAMESPACE" get servicemonitor seedtest-api &>/dev/null; then
    echo "✅ ServiceMonitor 존재: seedtest-api"
    
    RELEASE_LABEL=$(kubectl -n "$NAMESPACE" get servicemonitor seedtest-api \
        -o jsonpath='{.metadata.labels.release}')
    echo "   release 라벨: $RELEASE_LABEL"
    
    ENDPOINT_PATH=$(kubectl -n "$NAMESPACE" get servicemonitor seedtest-api \
        -o jsonpath='{.spec.endpoints[0].path}')
    echo "   메트릭 경로: $ENDPOINT_PATH"
else
    echo "❌ ServiceMonitor 없음: seedtest-api"
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "3️⃣  Grafana 대시보드 ConfigMap 확인"
echo "───────────────────────────────────────────────────────"
if kubectl -n "$NAMESPACE" get cm seedtest-api-dashboard &>/dev/null; then
    echo "✅ ConfigMap 존재: seedtest-api-dashboard"
    
    DASHBOARD_LABEL=$(kubectl -n "$NAMESPACE" get cm seedtest-api-dashboard \
        -o jsonpath='{.metadata.labels.grafana_dashboard}')
    echo "   grafana_dashboard 라벨: $DASHBOARD_LABEL"
    
    DASHBOARD_TITLE=$(kubectl -n "$NAMESPACE" get cm seedtest-api-dashboard \
        -o jsonpath='{.data.seedtest-api-governance\.json}' \
        | grep -o '"title":\s*"[^"]*"' | head -1)
    echo "   대시보드 제목: $DASHBOARD_TITLE"
else
    echo "❌ ConfigMap 없음: seedtest-api-dashboard"
fi

echo ""
echo "───────────────────────────────────────────────────────"
echo "4️⃣  Prometheus 타겟 등록 확인 (선택)"
echo "───────────────────────────────────────────────────────"
echo "ℹ️  Prometheus UI에서 확인:"
echo "   1. Prometheus Pod 포트포워드:"
echo "      kubectl -n monitoring port-forward svc/prometheus-operated 9090:9090"
echo ""
echo "   2. 브라우저: http://localhost:9090/targets"
echo "      검색: seedtest-api"
echo ""
echo "   3. 타겟 상태: UP (초록)"
echo "      Labels: job=seedtest-api, namespace=seedtest"

echo ""
echo "───────────────────────────────────────────────────────"
echo "5️⃣  Alertmanager 활성 알림 확인 (선택)"
echo "───────────────────────────────────────────────────────"
echo "ℹ️  Alertmanager UI에서 확인:"
echo "   1. Alertmanager Pod 포트포워드:"
echo "      ALERTM=\$(kubectl -n monitoring get pod -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].metadata.name}')"
echo "      kubectl -n monitoring port-forward \"\$ALERTM\" 9093:9093"
echo ""
echo "   2. 브라우저: http://localhost:9093"
echo ""
echo "   3. API 확인:"
echo "      curl -s http://127.0.0.1:9093/api/v2/alerts | jq '.[].labels.alertname' | sort -u"

echo ""
echo "───────────────────────────────────────────────────────"
echo "6️⃣  Grafana 대시보드 임포트 확인 (선택)"
echo "───────────────────────────────────────────────────────"
echo "ℹ️  Grafana UI에서 확인:"
echo "   1. Grafana 접속 (포트포워드 또는 Ingress)"
echo "   2. 좌측 메뉴 → Dashboards → Browse"
echo "   3. 검색: \"SeedTest API – Governance & SLO\""
echo "   4. UID: seedtest-api-governance"
echo ""
echo "   자동 임포트 안 될 경우:"
echo "   - Grafana 사이드카 설정 확인 (grafana_dashboard=\"1\" 라벨)"
echo "   - ConfigMap 변경 후 Grafana 재시작 필요할 수 있음"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 검증 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 참고 문서:"
echo "   - DEPLOYMENT_RUNBOOK.md: 배포/검증 절차"
echo "   - MONITORING_VERIFICATION.md: 모니터링 상세 가이드"
echo ""
