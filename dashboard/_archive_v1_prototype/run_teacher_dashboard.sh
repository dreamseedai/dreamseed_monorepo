#!/bin/bash
# ============================================================================
# 교사용 대시보드 실행 스크립트
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 기본 설정
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8081}"
DATASET_ROOT="${DATASET_ROOT:-$PROJECT_ROOT/data/datasets}"

# 개발 모드 환경변수 (프록시 없이 테스트)
export DEV_USER="${DEV_USER:-teacher01}"
export DEV_ORG_ID="${DEV_ORG_ID:-org_001}"
export DEV_ROLES="${DEV_ROLES:-teacher}"
export DATASET_ROOT="$DATASET_ROOT"

echo "=========================================="
echo "교사용 클래스 모니터링 대시보드"
echo "=========================================="
echo "Host: $HOST"
echo "Port: $PORT"
echo "Dataset: $DATASET_ROOT"
echo "User: $DEV_USER (org: $DEV_ORG_ID)"
echo "=========================================="
echo ""

# R 패키지 확인
echo "📦 R 패키지 확인 중..."
Rscript -e '
required_pkgs <- c("shiny", "shinydashboard", "DT", "arrow", "dplyr", 
                   "plotly", "lubridate", "stringr", "tidyr", "tibble")
missing_pkgs <- required_pkgs[!sapply(required_pkgs, requireNamespace, quietly = TRUE)]

if (length(missing_pkgs) > 0) {
  cat("⚠️  누락된 패키지:", paste(missing_pkgs, collapse = ", "), "\n")
  cat("설치 명령:\n")
  cat("  install.packages(c(\"", paste(missing_pkgs, collapse = "\", \""), "\"))\n", sep = "")
  quit(status = 1)
} else {
  cat("✓ 모든 패키지가 설치되어 있습니다.\n")
}
'

if [ $? -ne 0 ]; then
  echo ""
  echo "❌ 필수 R 패키지가 설치되지 않았습니다."
  echo "   위의 install.packages() 명령을 R 콘솔에서 실행하세요."
  exit 1
fi

echo ""
echo "🚀 대시보드 시작 중..."
echo "   브라우저에서 http://localhost:$PORT 접속"
echo ""

# Shiny 앱 실행
cd "$PROJECT_ROOT"
Rscript -e "shiny::runApp('dashboard/app_teacher.R', host='$HOST', port=$PORT)"
