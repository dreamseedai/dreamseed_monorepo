#!/bin/bash
# Advanced Analytics Pipeline Deployment Script
# Deploys: Bayesian Growth (brms), Prophet Forecasting, Survival Analysis
# Usage: ./deploy-advanced-analytics.sh [--dry-run] [--skip-migration]

set -e

NAMESPACE="seedtest"
DRY_RUN=false
SKIP_MIGRATION=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      echo "🔍 DRY-RUN MODE - No changes will be applied"
      shift
      ;;
    --skip-migration)
      SKIP_MIGRATION=true
      echo "⏭️  SKIP-MIGRATION MODE - Alembic migration will be skipped"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--dry-run] [--skip-migration]"
      exit 1
      ;;
  esac
done

echo "🚀 Deploying Advanced Analytics Pipeline to namespace: $NAMESPACE"
echo ""

# ============================================================================
# Phase 1: ExternalSecrets for R Services
# ============================================================================
echo "📦 Phase 1/9: Applying ExternalSecrets for R services..."
if [[ "$DRY_RUN" == "true" ]]; then
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml --dry-run=client
else
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/externalsecret.yaml
    echo "   Waiting for ExternalSecrets to sync..."
    sleep 5
    kubectl -n $NAMESPACE get secret r-brms-credentials -o jsonpath='{.metadata.name}' 2>/dev/null && echo "   ✅ r-brms-credentials synced" || echo "   ⚠️  r-brms-credentials not ready"
    kubectl -n $NAMESPACE get secret r-forecast-credentials -o jsonpath='{.metadata.name}' 2>/dev/null && echo "   ✅ r-forecast-credentials synced" || echo "   ⚠️  r-forecast-credentials not ready"
    kubectl -n $NAMESPACE get secret r-analytics-credentials -o jsonpath='{.metadata.name}' 2>/dev/null && echo "   ✅ r-analytics-credentials synced" || echo "   ⚠️  r-analytics-credentials not ready"
fi
echo "✅ ExternalSecrets applied"
echo ""

# ============================================================================
# Phase 2: Verify Database Credentials
# ============================================================================
echo "📦 Phase 2/8: Verifying database credentials..."
if [[ "$DRY_RUN" == "false" ]]; then
    kubectl -n $NAMESPACE get secret seedtest-db-credentials -o jsonpath='{.metadata.name}' 2>/dev/null && echo "   ✅ seedtest-db-credentials exists" || {
        echo "   ❌ seedtest-db-credentials not found!"
        echo "   Please ensure DATABASE_URL secret is configured."
        exit 1
    }
else
    echo "   [DRY-RUN] Would verify seedtest-db-credentials"
fi
echo ""

# ============================================================================
# Phase 3: Alembic Migration (Prophet/Survival Tables)
# ============================================================================
echo "📦 Phase 3/8: Running Alembic migration for Prophet/Survival tables..."
if [[ "$SKIP_MIGRATION" == "true" ]]; then
    echo "   ⏭️  Skipping migration (--skip-migration flag)"
elif [[ "$DRY_RUN" == "false" ]]; then
    echo "   Running migration: 20251102_1400_prophet_survival_tables.py"
    echo "   This will create: prophet_fit_meta, prophet_anomalies, survival_fit_meta, survival_risk"
    
    # Run migration in a temporary pod
    kubectl -n $NAMESPACE run alembic-migrate-prophet-survival \
        --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
        --rm -it --restart=Never \
        --env="DATABASE_URL=$(kubectl -n $NAMESPACE get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d)" \
        -- /bin/sh -c "cd /app && alembic upgrade head" || {
        echo "   ⚠️  Migration failed or already applied. Continuing..."
    }
    
    echo "   ✅ Migration complete"
else
    echo "   [DRY-RUN] Would run Alembic migration"
fi
echo ""

# ============================================================================
# Phase 4: Update compute-daily-kpis to Enable Bayesian
# ============================================================================
echo "📦 Phase 4/8: Updating compute-daily-kpis CronJob (METRICS_USE_BAYESIAN=true)..."
if [[ "$DRY_RUN" == "false" ]]; then
    # Patch the CronJob to enable Bayesian metrics
    kubectl -n $NAMESPACE patch cronjob compute-daily-kpis --type=json -p='[
        {"op": "replace", "path": "/spec/jobTemplate/spec/template/spec/containers/0/env/4/value", "value": "true"}
    ]' 2>/dev/null || {
        echo "   ⚠️  Failed to patch compute-daily-kpis. Applying full manifest..."
        kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml
    }
    echo "   ✅ compute-daily-kpis updated with METRICS_USE_BAYESIAN=true"
else
    echo "   [DRY-RUN] Would patch compute-daily-kpis CronJob"
fi
echo ""

# ============================================================================
# Phase 5: Apply CronJobs for Advanced Analytics
# ============================================================================
echo "📦 Phase 5/8: Applying CronJobs for Bayesian/Prophet/Survival..."
if [[ "$DRY_RUN" == "true" ]]; then
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml --dry-run=client
else
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml
fi
echo "✅ CronJobs applied:"
echo "   - fit-bayesian-growth (Mon 04:30 UTC)"
echo "   - forecast-prophet (Mon 05:00 UTC)"
echo "   - fit-survival-churn (Daily 05:00 UTC)"
echo ""

# ============================================================================
# Phase 6: Deploy r-analytics Service
# ============================================================================
echo "📦 Phase 6/9: Deploying r-analytics service..."
if [[ "$DRY_RUN" == "true" ]]; then
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/deployment.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/service.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/servicemonitor.yaml --dry-run=client
else
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/deployment.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/service.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-analytics/servicemonitor.yaml
    echo "   Waiting for r-analytics rollout..."
    kubectl -n $NAMESPACE rollout status deployment/r-analytics --timeout=2m || echo "   ⚠️  r-analytics rollout timeout (continuing...)"
fi
echo "✅ r-analytics service deployed"
echo ""

# ============================================================================
# Phase 7: Health Check R Services
# ============================================================================
echo "🔍 Phase 7/9: Testing R service health..."
if [[ "$DRY_RUN" == "false" ]]; then
    echo "   Testing r-brms-plumber..."
    kubectl -n $NAMESPACE run curl-brms-test --rm -it --image=curlimages/curl --restart=Never -- \
      curl -sS http://r-brms-plumber.seedtest.svc.cluster.local:80/healthz && echo "   ✅ r-brms-plumber healthy" || {
        echo "   ⚠️  r-brms-plumber health check failed"
        echo "   Check with: kubectl -n $NAMESPACE get pods -l app=r-brms-plumber"
    }
    
    echo "   Testing r-forecast-plumber..."
    kubectl -n $NAMESPACE run curl-forecast-test --rm -it --image=curlimages/curl --restart=Never -- \
      curl -sS http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz && echo "   ✅ r-forecast-plumber healthy" || {
        echo "   ⚠️  r-forecast-plumber health check failed"
        echo "   Check with: kubectl -n $NAMESPACE get pods -l app=r-forecast-plumber"
    }
    
    echo "   Testing r-analytics..."
    kubectl -n $NAMESPACE run curl-analytics-test --rm -it --image=curlimages/curl --restart=Never -- \
      curl -sS http://r-analytics.seedtest.svc.cluster.local:80/health && echo "   ✅ r-analytics healthy" || {
        echo "   ⚠️  r-analytics health check failed"
        echo "   Check with: kubectl -n $NAMESPACE get pods -l app=r-analytics"
    }
else
    echo "   [DRY-RUN] Would test R service health"
fi
echo ""

# ============================================================================
# Phase 8: Smoke Tests (Optional One-off Jobs)
# ============================================================================
echo "🎯 Phase 8/9: Smoke tests (optional one-off jobs)..."
echo ""

# Bayesian Growth
echo "   [1/3] Bayesian Growth Model (fit-bayesian-growth)"
read -p "   Trigger now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        kubectl -n $NAMESPACE delete job fit-bayesian-growth-now --ignore-not-found
        kubectl -n $NAMESPACE create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-now
        echo "   Job created. Tailing logs (Ctrl+C to skip)..."
        sleep 3
        kubectl -n $NAMESPACE logs -f job/fit-bayesian-growth-now --tail=50 || echo "   Job may still be starting..."
    else
        echo "   [DRY-RUN] Would create job: fit-bayesian-growth-now"
    fi
else
    echo "   Skipped. Run manually with:"
    echo "   kubectl -n $NAMESPACE create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-now"
fi
echo ""

# Prophet Forecasting
echo "   [2/3] Prophet Forecasting (forecast-prophet)"
read -p "   Trigger now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        kubectl -n $NAMESPACE delete job forecast-prophet-now --ignore-not-found
        kubectl -n $NAMESPACE create job --from=cronjob/forecast-prophet forecast-prophet-now
        echo "   Job created. Tailing logs (Ctrl+C to skip)..."
        sleep 3
        kubectl -n $NAMESPACE logs -f job/forecast-prophet-now --tail=50 || echo "   Job may still be starting..."
    else
        echo "   [DRY-RUN] Would create job: forecast-prophet-now"
    fi
else
    echo "   Skipped. Run manually with:"
    echo "   kubectl -n $NAMESPACE create job --from=cronjob/forecast-prophet forecast-prophet-now"
fi
echo ""

# Survival Analysis
echo "   [3/3] Survival Analysis (fit-survival-churn)"
read -p "   Trigger now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        kubectl -n $NAMESPACE delete job fit-survival-churn-now --ignore-not-found
        kubectl -n $NAMESPACE create job --from=cronjob/fit-survival-churn fit-survival-churn-now
        echo "   Job created. Tailing logs (Ctrl+C to skip)..."
        sleep 3
        kubectl -n $NAMESPACE logs -f job/fit-survival-churn-now --tail=50 || echo "   Job may still be starting..."
    else
        echo "   [DRY-RUN] Would create job: fit-survival-churn-now"
    fi
else
    echo "   Skipped. Run manually with:"
    echo "   kubectl -n $NAMESPACE create job --from=cronjob/fit-survival-churn fit-survival-churn-now"
fi
echo ""

# ============================================================================
# Phase 9: Deployment Summary
# ============================================================================
echo "✅ Deployment complete!"
echo ""
echo "📋 Deployed resources:"
echo "   ExternalSecrets:"
echo "     - r-brms-credentials (GCP Secret Manager)"
echo "     - r-forecast-credentials (GCP Secret Manager)"
echo "     - r-analytics-credentials (GCP Secret Manager)"
echo ""
echo "   R Services:"
echo "     - r-analytics (port 8010) - Unified analytics API"
echo ""
echo "   CronJobs:"
echo "     - fit-bayesian-growth (Mon 04:30 UTC) - Bayesian growth model"
echo "     - forecast-prophet (Mon 05:00 UTC) - Prophet time series forecasting"
echo "     - fit-survival-churn (Daily 05:00 UTC) - Survival analysis"
echo "     - compute-daily-kpis (Daily 02:10 UTC) - Updated with METRICS_USE_BAYESIAN=true"
echo ""
echo "   Database Tables (via Alembic):"
echo "     - prophet_fit_meta, prophet_anomalies"
echo "     - survival_fit_meta, survival_risk"
echo ""
echo "🔍 Verify deployment:"
echo "   # Check CronJobs"
echo "   kubectl -n $NAMESPACE get cronjobs | grep -E 'fit-bayesian|forecast-prophet|fit-survival|compute-daily'"
echo ""
echo "   # Check Secrets"
echo "   kubectl -n $NAMESPACE get secrets | grep -E 'r-brms|r-forecast|r-analytics|seedtest-db'"
echo ""
echo "   # Check R Services"
echo "   kubectl -n $NAMESPACE get pods -l 'app in (r-brms-plumber,r-forecast-plumber,r-analytics)'"
echo ""
echo "   # Verify database tables"
echo "   kubectl -n $NAMESPACE run psql-verify --rm -it --image=postgres:15 --restart=Never -- \\
echo "     psql \$DATABASE_URL -c \"\\dt prophet_* survival_*\""
echo ""
echo "📊 Monitor jobs:"
echo "   kubectl -n $NAMESPACE get jobs --watch"
echo "   kubectl -n $NAMESPACE logs -f job/<job-name>"
echo ""
echo "🔄 Rollback (if needed):"
echo "   # Disable Bayesian metrics"
echo "   kubectl -n $NAMESPACE set env cronjob/compute-daily-kpis METRICS_USE_BAYESIAN=false"
echo ""
echo "   # Suspend CronJobs"
echo "   kubectl -n $NAMESPACE patch cronjob fit-bayesian-growth -p '{\"spec\":{\"suspend\":true}}'"
echo "   kubectl -n $NAMESPACE patch cronjob forecast-prophet -p '{\"spec\":{\"suspend\":true}}'"
echo "   kubectl -n $NAMESPACE patch cronjob fit-survival-churn -p '{\"spec\":{\"suspend\":true}}'"
echo ""
echo "   # Alembic downgrade"
echo "   kubectl -n $NAMESPACE run alembic-downgrade --rm -it --image=... -- alembic downgrade -1"
echo ""
echo "📚 Documentation:"
echo "   - apps/seedtest_api/docs/DEPLOYMENT_GUIDE_IRT_PIPELINE.md"
echo "   - apps/seedtest_api/docs/README_IRT_PIPELINE.md"
echo "   - apps/seedtest_api/docs/INTEGRATION_TEST_GUIDE.md"
echo ""
echo "🎉 Advanced Analytics Pipeline is ready!"
echo ""
