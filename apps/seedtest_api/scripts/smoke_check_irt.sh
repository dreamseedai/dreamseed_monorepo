#!/bin/bash
set -euo pipefail

# r-irt-plumber 스모크 체크 스크립트

NAMESPACE="${NAMESPACE:-seedtest}"
SERVICE_NAME="${SERVICE_NAME:-r-irt-plumber}"
LOCAL_PORT="${LOCAL_PORT:-8001}"

echo "=== r-irt-plumber Smoke Checks ==="
echo ""

# 1. Deployment 확인
echo "1. Checking deployment..."
if kubectl get deployment -n "$NAMESPACE" "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "✓ Deployment '$SERVICE_NAME' exists in namespace '$NAMESPACE'"
    kubectl get deployment -n "$NAMESPACE" "$SERVICE_NAME"
else
    echo "⚠ Deployment '$SERVICE_NAME' not found in namespace '$NAMESPACE'"
    echo "  Available deployments:"
    kubectl get deployment -n "$NAMESPACE" 2>&1 | tail -n +2 || echo "  (none)"
    exit 1
fi
echo ""

# 2. Service 확인
echo "2. Checking service..."
if kubectl get svc -n "$NAMESPACE" "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "✓ Service '$SERVICE_NAME' exists"
    kubectl get svc -n "$NAMESPACE" "$SERVICE_NAME"
else
    echo "⚠ Service '$SERVICE_NAME' not found"
fi
echo ""

# 3. Pod 상태 확인
echo "3. Checking pods..."
pods=$(kubectl get pods -n "$NAMESPACE" -l app="$SERVICE_NAME" -o name 2>/dev/null || echo "")
if [ -n "$pods" ]; then
    echo "✓ Pods found:"
    kubectl get pods -n "$NAMESPACE" -l app="$SERVICE_NAME"
else
    echo "⚠ No pods found for app=$SERVICE_NAME"
    echo "  All pods in namespace:"
    kubectl get pods -n "$NAMESPACE" 2>&1 | head -5 || echo "  (none)"
fi
echo ""

# 4. Port-forward 및 Health Check
echo "4. Setting up port-forward..."
echo "  Forwarding $SERVICE_NAME:8000 -> localhost:$LOCAL_PORT"

# 기존 포트포워드가 있으면 종료
pkill -f "kubectl.*port-forward.*$LOCAL_PORT" || true
sleep 1

# 백그라운드로 포트포워드 시작
kubectl port-forward -n "$NAMESPACE" deploy/"$SERVICE_NAME" "$LOCAL_PORT:8000" >/dev/null 2>&1 &
PF_PID=$!
sleep 2

# 포트포워드가 실행 중인지 확인
if kill -0 $PF_PID 2>/dev/null; then
    echo "✓ Port-forward active (PID: $PF_PID)"
    
    # Health check
    echo "5. Health check..."
    if curl -sf "http://127.0.0.1:$LOCAL_PORT/healthz" >/dev/null; then
        echo "✓ Health check passed"
        curl -s "http://127.0.0.1:$LOCAL_PORT/healthz" | head -1
    else
        echo "⚠ Health check failed"
        echo "  Response:"
        curl -s "http://127.0.0.1:$LOCAL_PORT/healthz" || echo "  (no response)"
    fi
    
    # 포트포워드 종료
    kill $PF_PID 2>/dev/null || true
else
    echo "⚠ Port-forward failed"
    exit 1
fi
echo ""

# 6. CronJob 확인
echo "6. Checking CronJob..."
cronjobs=$(kubectl get cronjob -n "$NAMESPACE" 2>/dev/null | grep -i "irt\|calibrate" | awk '{print $1}' || echo "")
if [ -n "$cronjobs" ]; then
    echo "✓ IRT calibration CronJobs found:"
    echo "$cronjobs" | while read cj; do
        echo "  - $cj"
        schedule=$(kubectl get cronjob -n "$NAMESPACE" "$cj" -o jsonpath='{.spec.schedule}' 2>/dev/null || echo "unknown")
        echo "    Schedule: $schedule"
    done
else
    echo "⚠ No IRT calibration CronJob found"
    echo "  Available CronJobs:"
    kubectl get cronjob -n "$NAMESPACE" 2>&1 | head -5 || echo "  (none)"
fi
echo ""

# 7. 최근 Job 실행 확인
echo "7. Recent calibration jobs..."
recent_jobs=$(kubectl get jobs -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp 2>/dev/null | grep -i "irt\|calibrate" | tail -3 || echo "")
if [ -n "$recent_jobs" ]; then
    echo "✓ Recent jobs:"
    echo "$recent_jobs"
else
    echo "  (no recent jobs found)"
fi
echo ""

echo "=== Smoke checks complete ==="

