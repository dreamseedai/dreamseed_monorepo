#!/usr/bin/env bash
set -euo pipefail

# Monitor Kyverno cleanup CronJobs and view the latest job logs
# Usage:
#   ./check_cleanup_jobs.sh            # list matching jobs and show latest status
#   ./check_cleanup_jobs.sh -f         # follow logs from the latest cleanup job's pod
#   ./check_cleanup_jobs.sh -w         # watch for next cleanup job and print when created
#   NAMESPACE=kyverno ./check_cleanup_jobs.sh -f

NS="${NAMESPACE:-kyverno}"
FOLLOW=false
WATCH=false

while (( "$#" )); do
    case "$1" in
        -f|--follow) FOLLOW=true; shift ;;
        -w|--watch)  WATCH=true;  shift ;;
        -n|--namespace) NS="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 2 ;;
    esac
done

say() { echo "[check_cleanup_jobs] $*"; }

say "Namespace: $NS"

say "Listing cleanup jobs (name contains 'cleanup')"
if ! kubectl get jobs -n "$NS" 2>/dev/null | grep -i cleanup || true; then
    say "(none yet)"
fi

# Find latest cleanup job by creationTimestamp
LATEST_JOB=$(kubectl get jobs -n "$NS" -o json \
    | jq -r '.items[] | select(.metadata.name|test("cleanup";"i")) | [.metadata.name,.metadata.creationTimestamp] | @tsv' \
    | sort -k2 | tail -1 | cut -f1)

if [[ -z "${LATEST_JOB:-}" ]]; then
    say "No cleanup job found yet."
    if [[ "$WATCH" == true ]]; then
        say "Watching for new cleanup jobs... (Ctrl-C to stop)"
        kubectl get jobs -n "$NS" -w | grep --line-buffered -i cleanup || true
    fi
    exit 0
fi

say "Latest cleanup job: $LATEST_JOB"

say "Job details:"
kubectl get job -n "$NS" "$LATEST_JOB" -o wide || true

say "Pods for job:"
kubectl get pods -n "$NS" -l job-name="$LATEST_JOB" -o wide || true

if [[ "$FOLLOW" == true ]]; then
    POD=$(kubectl get pods -n "$NS" -l job-name="$LATEST_JOB" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$POD" ]]; then
        say "Following logs for pod: $POD"
        kubectl logs -n "$NS" "$POD" -f || true
    else
        say "No pod found yet for job $LATEST_JOB (it may be pending)."
    fi
fi

if [[ "$WATCH" == true ]]; then
    say "Watching for next cleanup jobs... (Ctrl-C to stop)"
    kubectl get jobs -n "$NS" -w | grep --line-buffered -i cleanup || true
fi

