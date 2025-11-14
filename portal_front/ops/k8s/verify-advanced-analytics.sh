#!/bin/bash
# Advanced Analytics Pipeline Verification Script
# Usage: ./verify-advanced-analytics.sh

set -e

NAMESPACE="seedtest"
FAILED=0

echo "🔍 Verifying Advanced Analytics Pipeline in namespace: $NAMESPACE"
echo ""

# ============================================================================
# 1. Check R Services
# ============================================================================
echo "📦 [1/7] Checking R services..."
if kubectl -n $NAMESPACE get pods -l app=r-brms-plumber -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
    echo "   ✅ r-brms-plumber is running"
else
    echo "   ❌ r-brms-plumber is not running"
    FAILED=$((FAILED + 1))
fi

if kubectl -n $NAMESPACE get pods -l app=r-forecast-plumber -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
    echo "   ✅ r-forecast-plumber is running"
else
    echo "   ❌ r-forecast-plumber is not running"
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 2. Check Secrets
# ============================================================================
echo "📦 [2/7] Checking secrets..."
if kubectl -n $NAMESPACE get secret r-brms-credentials &>/dev/null; then
    echo "   ✅ r-brms-credentials exists"
else
    echo "   ⚠️  r-brms-credentials not found (optional)"
fi

if kubectl -n $NAMESPACE get secret r-forecast-credentials &>/dev/null; then
    echo "   ✅ r-forecast-credentials exists"
else
    echo "   ⚠️  r-forecast-credentials not found (optional)"
fi

if kubectl -n $NAMESPACE get secret seedtest-db-credentials &>/dev/null; then
    echo "   ✅ seedtest-db-credentials exists"
else
    echo "   ❌ seedtest-db-credentials not found (required)"
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 3. Check CronJobs
# ============================================================================
echo "📦 [3/7] Checking CronJobs..."
CRONJOBS=("fit-bayesian-growth" "forecast-prophet" "fit-survival-churn" "compute-daily-kpis")
for cron in "${CRONJOBS[@]}"; do
    if kubectl -n $NAMESPACE get cronjob $cron &>/dev/null; then
        SUSPENDED=$(kubectl -n $NAMESPACE get cronjob $cron -o jsonpath='{.spec.suspend}')
        if [[ "$SUSPENDED" == "true" ]]; then
            echo "   ⚠️  $cron exists but is SUSPENDED"
        else
            echo "   ✅ $cron exists and is active"
        fi
    else
        echo "   ❌ $cron not found"
        FAILED=$((FAILED + 1))
    fi
done
echo ""

# ============================================================================
# 4. Check METRICS_USE_BAYESIAN flag
# ============================================================================
echo "📦 [4/7] Checking METRICS_USE_BAYESIAN flag..."
BAYESIAN_FLAG=$(kubectl -n $NAMESPACE get cronjob compute-daily-kpis -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].env[?(@.name=="METRICS_USE_BAYESIAN")].value}' 2>/dev/null)
if [[ "$BAYESIAN_FLAG" == "true" ]]; then
    echo "   ✅ METRICS_USE_BAYESIAN=true"
else
    echo "   ⚠️  METRICS_USE_BAYESIAN=$BAYESIAN_FLAG (expected: true)"
fi
echo ""

# ============================================================================
# 5. Health Check R Services
# ============================================================================
echo "📦 [5/7] Health checking R services..."

# r-brms-plumber
echo "   Testing r-brms-plumber..."
if kubectl -n $NAMESPACE run curl-brms-verify --rm -it --image=curlimages/curl --restart=Never -- \
    curl -sf http://r-brms-plumber.seedtest.svc.cluster.local:80/healthz &>/dev/null; then
    echo "   ✅ r-brms-plumber /healthz returned 200"
else
    echo "   ❌ r-brms-plumber /healthz failed"
    FAILED=$((FAILED + 1))
fi

# r-forecast-plumber
echo "   Testing r-forecast-plumber..."
if kubectl -n $NAMESPACE run curl-forecast-verify --rm -it --image=curlimages/curl --restart=Never -- \
    curl -sf http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz &>/dev/null; then
    echo "   ✅ r-forecast-plumber /healthz returned 200"
else
    echo "   ❌ r-forecast-plumber /healthz failed"
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 6. Check Database Tables
# ============================================================================
echo "📦 [6/7] Checking database tables..."
DATABASE_URL=$(kubectl -n $NAMESPACE get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' 2>/dev/null | base64 -d)

if [[ -n "$DATABASE_URL" ]]; then
    TABLES=$(kubectl -n $NAMESPACE run psql-verify-tables --rm -it --image=postgres:15 --restart=Never \
        --env="DATABASE_URL=$DATABASE_URL" \
        -- psql "$DATABASE_URL" -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename ~ 'prophet|survival' ORDER BY tablename;" 2>/dev/null | tr -d ' ')
    
    if echo "$TABLES" | grep -q "prophet_anomalies"; then
        echo "   ✅ prophet_anomalies exists"
    else
        echo "   ❌ prophet_anomalies not found"
        FAILED=$((FAILED + 1))
    fi
    
    if echo "$TABLES" | grep -q "prophet_fit_meta"; then
        echo "   ✅ prophet_fit_meta exists"
    else
        echo "   ❌ prophet_fit_meta not found"
        FAILED=$((FAILED + 1))
    fi
    
    if echo "$TABLES" | grep -q "survival_fit_meta"; then
        echo "   ✅ survival_fit_meta exists"
    else
        echo "   ❌ survival_fit_meta not found"
        FAILED=$((FAILED + 1))
    fi
    
    if echo "$TABLES" | grep -q "survival_risk"; then
        echo "   ✅ survival_risk exists"
    else
        echo "   ❌ survival_risk not found"
        FAILED=$((FAILED + 1))
    fi
else
    echo "   ⚠️  Could not retrieve DATABASE_URL, skipping table checks"
fi
echo ""

# ============================================================================
# 7. Check Recent Jobs
# ============================================================================
echo "📦 [7/7] Checking recent job executions..."
RECENT_JOBS=$(kubectl -n $NAMESPACE get jobs --sort-by=.metadata.creationTimestamp --no-headers 2>/dev/null | tail -5)
if [[ -n "$RECENT_JOBS" ]]; then
    echo "   Recent jobs (last 5):"
    echo "$RECENT_JOBS" | awk '{printf "   - %s (Status: %s)\n", $1, $2}'
else
    echo "   ⚠️  No recent jobs found"
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $FAILED -eq 0 ]]; then
    echo "✅ Verification PASSED - All checks successful!"
    echo ""
    echo "🎉 Advanced Analytics Pipeline is ready for production!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Trigger smoke tests:"
    echo "      kubectl -n $NAMESPACE create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-now"
    echo "      kubectl -n $NAMESPACE create job --from=cronjob/forecast-prophet forecast-prophet-now"
    echo "      kubectl -n $NAMESPACE create job --from=cronjob/fit-survival-churn fit-survival-churn-now"
    echo ""
    echo "   2. Monitor job logs:"
    echo "      kubectl -n $NAMESPACE logs -f job/<job-name>"
    echo ""
    echo "   3. Verify results in database:"
    echo "      kubectl -n $NAMESPACE run psql-check --rm -it --image=postgres:15 --restart=Never -- psql \$DATABASE_URL"
    exit 0
else
    echo "❌ Verification FAILED - $FAILED check(s) failed"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check pod status:"
    echo "      kubectl -n $NAMESPACE get pods -l 'app in (r-brms-plumber,r-forecast-plumber)'"
    echo ""
    echo "   2. Check pod logs:"
    echo "      kubectl -n $NAMESPACE logs -l app=r-brms-plumber --tail=50"
    echo "      kubectl -n $NAMESPACE logs -l app=r-forecast-plumber --tail=50"
    echo ""
    echo "   3. Re-run deployment:"
    echo "      ./portal_front/ops/k8s/deploy-advanced-analytics.sh"
    echo ""
    echo "   4. Check documentation:"
    echo "      apps/seedtest_api/docs/DEPLOYMENT_CHECKLIST_ADVANCED_ANALYTICS.md"
    exit 1
fi
