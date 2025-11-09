#!/usr/bin/env bash
#
# 주간 리스크 리포트 전체 파이프라인 실행 (DreamSeedAI)
#
set -euo pipefail

BASE="$(cd "$(dirname "$0")/.."; pwd)"
D=$(date +%F)
OUT="$BASE/reports/$D"
mkdir -p "$OUT"

echo "=== DreamSeedAI Weekly Risk Pipeline Started ==="
echo "Date: $D"
echo "Output: $OUT"

# 1) 데이터 스냅샷 추출
echo ""
echo "[1/6] Fetching snapshot from database..."
psql "${DSN:-postgresql://user:pass@localhost:5432/dreamseedai}" \
  < "$BASE/jobs/00_fetch_snapshots.sql" \
  > "/tmp/snapshot_${D}.csv"
echo "✓ Snapshot saved to /tmp/snapshot_${D}.csv"

# 2) 리스크 메트릭 계산 (IRT 확장 또는 기본)
echo ""
echo "[2/6] Computing risk metrics..."

# IRT 테이블 존재 여부 확인
if psql "${DSN}" -tAc "SELECT to_regclass('public.fact_assessment_item') IS NOT NULL" 2>/dev/null | grep -q t; then
  echo "  → Using IRT-based calculation..."
  Rscript "$BASE/jobs/10_compute_metrics_irt.R" \
    "$BASE/config/thresholds.yaml" \
    "/tmp/metrics_${D}.csv" || {
    echo "  [WARN] IRT calculation failed, falling back to simple metrics"
    Rscript "$BASE/jobs/10_compute_metrics.R" \
      "/tmp/snapshot_${D}.csv" \
      "$BASE/config/thresholds.yaml" \
      "/tmp/metrics_${D}.csv"
  }
else
  echo "  → Using simple calculation..."
  Rscript "$BASE/jobs/10_compute_metrics.R" \
    "/tmp/snapshot_${D}.csv" \
    "$BASE/config/thresholds.yaml" \
    "/tmp/metrics_${D}.csv"
fi
echo "✓ Metrics saved to /tmp/metrics_${D}.csv"

# 3) 테넌트별 집계 (Python)
echo ""
echo "[3/6] Aggregating by tenant..."
python3 "$BASE/jobs/20_aggregate.py" \
  "/tmp/metrics_${D}.csv" \
  "/tmp/summary_${D}.csv"
echo "✓ Summary saved to /tmp/summary_${D}.csv"

# 4) RMarkdown 리포트 렌더링
echo ""
echo "[4/6] Rendering reports..."
python3 "$BASE/jobs/run_render_all.py" \
  "/tmp/metrics_${D}.csv" \
  "$OUT"
echo "✓ Reports rendered to $OUT"

# 5) Shiny 준비 (선택사항)
echo ""
echo "[5/6] Preparing Shiny data..."
Rscript "$BASE/jobs/31_render_shiny_prep.R" \
  "/tmp/metrics_${D}.csv" \
  "$OUT/metrics_${D}.feather"
echo "✓ Shiny data saved to $OUT/metrics_${D}.feather"

# 6) 이메일 배포
echo ""
echo "[6/6] Sending reports..."
python3 "$BASE/jobs/send_reports.py" \
  "$OUT" \
  "/tmp/summary_${D}.csv"
echo "✓ Reports sent"

echo ""
echo "=== Weekly Risk Pipeline Completed ==="
echo "Output directory: $OUT"
