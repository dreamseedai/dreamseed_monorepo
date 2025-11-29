#!/usr/bin/env bash
#
# 리허설 실행 (샘플 데이터 사용)
#
set -euo pipefail

BASE="$(cd "$(dirname "$0")/.."; pwd)"
D=$(date +%F)
OUT="$BASE/reports/${D}_rehearsal"
mkdir -p "$OUT"

echo "=== Rehearsal Run Started ==="
echo "Date: $D"
echo "Output: $OUT"

# 1) 샘플 데이터 생성
echo ""
echo "[1/5] Generating sample data..."
python3 "$BASE/scripts/generate_sample_data.py" "/tmp/snapshot_${D}.csv"

# 2) 리스크 메트릭 계산
echo ""
echo "[2/5] Computing metrics..."
Rscript "$BASE/jobs/10_compute_metrics.R" \
  "/tmp/snapshot_${D}.csv" \
  "$BASE/config/thresholds.yaml" \
  "/tmp/metrics_${D}.csv"

# 3) 집계
echo ""
echo "[3/5] Aggregating..."
python3 "$BASE/jobs/20_aggregate.py" \
  "/tmp/metrics_${D}.csv" \
  "/tmp/summary_${D}.csv"

# 4) 렌더링
echo ""
echo "[4/5] Rendering reports..."
python3 "$BASE/jobs/run_render_all.py" \
  "/tmp/metrics_${D}.csv" \
  "$OUT"

# 5) Shiny 준비
echo ""
echo "[5/5] Preparing Shiny data..."
Rscript "$BASE/jobs/31_render_shiny_prep.R" \
  "/tmp/metrics_${D}.csv" \
  "$OUT/metrics_${D}.feather"

echo ""
echo "=== Rehearsal Completed ==="
echo "Output directory: $OUT"
echo ""
echo "Check the reports:"
ls -lh "$OUT"
