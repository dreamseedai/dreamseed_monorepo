#!/bin/bash
# IRT Analytics Pipeline Deployment Script
# Usage: ./deploy-irt-pipeline.sh [--dry-run]

set -e

NAMESPACE="seedtest"
DRY_RUN=false

# Parse arguments
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY-RUN MODE - No changes will be applied"
fi

echo "🚀 Deploying IRT Analytics Pipeline to namespace: $NAMESPACE"
echo ""

# Step 1: Apply ExternalSecret for R IRT token
echo "📦 Step 1/6: Applying ExternalSecret for R IRT credentials..."
if [[ "$DRY_RUN" == "true" ]]; then
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-irt-plumber/externalsecret.yaml --dry-run=client
else
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/r-irt-plumber/externalsecret.yaml
fi
echo "✅ ExternalSecret applied"
echo ""

# Step 2: Apply IRT Calibration CronJob
echo "📦 Step 2/6: Applying IRT Calibration CronJob..."
if [[ "$DRY_RUN" == "true" ]]; then
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml --dry-run=client
else
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
fi
echo "✅ IRT Calibration CronJob applied (schedule: daily 03:00 UTC)"
echo ""

# Step 3: Apply GLMM helper manifests
echo "📦 Step 3/6: Applying GLMM manifests..."
if [[ "$DRY_RUN" == "true" ]]; then
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-scripts.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-now.yaml --dry-run=client
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/glmm-fit-progress.yaml --dry-run=client
else
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-scripts.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-now.yaml
    kubectl -n $NAMESPACE apply -f portal_front/ops/k8s/cron/glmm-fit-progress.yaml
fi
echo "✅ GLMM manifests applied"
echo ""

# Step 4: Smoke test R IRT service
echo "🔍 Step 4/6: Testing R IRT Plumber service health..."
if [[ "$DRY_RUN" == "false" ]]; then
    kubectl -n $NAMESPACE run curl-irt --rm -it --image=curlimages/curl --restart=Never -- \
      curl -sS http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz || {
        echo "⚠️  R IRT service health check failed - service may not be ready"
        echo "   Check with: kubectl -n $NAMESPACE get pods -l app=r-irt-plumber"
    }
else
    echo "   [DRY-RUN] Would test R IRT service health"
fi
echo ""

# Step 5: Trigger one-off IRT calibration (optional)
echo "🎯 Step 5/6: One-off IRT Calibration Job (optional)..."
read -p "   Trigger IRT calibration now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        kubectl -n $NAMESPACE delete job calibrate-irt-now --ignore-not-found
        kubectl -n $NAMESPACE create -f portal_front/ops/k8s/jobs/calibrate-irt-now.yaml
        echo "   Job created. Tailing logs..."
        sleep 2
        kubectl -n $NAMESPACE logs -f job/calibrate-irt-now || echo "   Job may still be starting..."
    else
        echo "   [DRY-RUN] Would create job: calibrate-irt-now"
    fi
else
    echo "   Skipped. Run manually with:"
    echo "   kubectl -n $NAMESPACE create -f portal_front/ops/k8s/jobs/calibrate-irt-now.yaml"
fi
echo ""

# Step 6: Trigger one-off GLMM fit (optional)
echo "🎯 Step 6/6: One-off GLMM Fit Job (optional)..."
read -p "   Trigger GLMM fit now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        kubectl -n $NAMESPACE delete job glmm-fit-progress-now --ignore-not-found
        kubectl -n $NAMESPACE create -f portal_front/ops/k8s/jobs/glmm-fit-progress-now.yaml
        echo "   Job created. Tailing logs..."
        sleep 2
        kubectl -n $NAMESPACE logs -f job/glmm-fit-progress-now || echo "   Job may still be starting..."
    else
        echo "   [DRY-RUN] Would create job: glmm-fit-progress-now"
    fi
else
    echo "   Skipped. Run manually with:"
    echo "   kubectl -n $NAMESPACE create -f portal_front/ops/k8s/jobs/glmm-fit-progress-now.yaml"
fi
echo ""

# Summary
echo "✅ Deployment complete!"
echo ""
echo "📋 Deployed resources:"
echo "   - ExternalSecret: r-irt-credentials"
echo "   - CronJob: mirt-calibrate (daily 03:00 UTC)"
echo "   - CronJob: glmm-fit-progress (weekly Monday 03:30 UTC)"
echo "   - Job templates: calibrate-irt-now, glmm-fit-progress-now"
echo ""
echo "🔍 Verify deployment:"
echo "   kubectl -n $NAMESPACE get cronjobs"
echo "   kubectl -n $NAMESPACE get secrets r-irt-credentials"
echo "   kubectl -n $NAMESPACE get pods -l app=r-irt-plumber"
echo ""
echo "📊 Monitor jobs:"
echo "   kubectl -n $NAMESPACE get jobs --watch"
echo "   kubectl -n $NAMESPACE logs -f job/<job-name>"
echo ""
echo "📚 Documentation:"
echo "   - apps/seedtest_api/docs/DEPLOYMENT_GUIDE_IRT_PIPELINE.md"
echo "   - apps/seedtest_api/docs/IRT_CALIBRATION_GUIDE.md"
echo ""
