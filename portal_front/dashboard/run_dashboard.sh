#!/bin/bash
# ============================================================================
# 교사용 대시보드 실행 스크립트 (프로덕션 v2.0)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 기본 설정
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8081}"
DATASET_ROOT="${DATASET_ROOT:-$PROJECT_ROOT/data/datasets}"

# 개발 모드 환경변수 (프록시 없이 테스트)
export DEV_USER="${DEV_USER:-teacher01}"
export DEV_ORG_ID="${DEV_ORG_ID:-org_001}"
export DEV_ROLES="${DEV_ROLES:-teacher}"
export DATASET_ROOT="$DATASET_ROOT"

# 리스크 임계값 (선택)
export RISK_THETA_DELTA="${RISK_THETA_DELTA:-0.02}"
export RISK_ATTENDANCE="${RISK_ATTENDANCE:-0.25}"
export RISK_GUESS="${RISK_GUESS:-0.15}"
export RISK_OMIT="${RISK_OMIT:-0.12}"

# 과제 배정 API
export ASSIGNMENT_API_URL="${ASSIGNMENT_API_URL:-http://localhost:8000/api/assignments}"
export ASSIGNMENT_API_BEARER="${ASSIGNMENT_API_BEARER:-}"

echo "=========================================="
echo "교사용 클래스 모니터링 대시보드 v2.0"
echo "=========================================="
echo "Host: $HOST"
echo "Port: $PORT"
echo "Dataset: $DATASET_ROOT"
echo "User: $DEV_USER (org: $DEV_ORG_ID)"
echo "Roles: $DEV_ROLES"
echo ""
echo "리스크 임계값:"
echo "  - Theta Delta: $RISK_THETA_DELTA"
echo "  - Attendance: $RISK_ATTENDANCE"
echo "  - Guess Rate: $RISK_GUESS"
echo "  - Omit Rate: $RISK_OMIT"
echo ""
echo "API Endpoint: $ASSIGNMENT_API_URL"
echo "=========================================="
echo ""

# R 패키지 확인
echo "📦 R 패키지 확인 중..."
Rscript -e '
required_pkgs <- c("shiny", "shinydashboard", "DT", "arrow", "dplyr", 
                   "plotly", "lubridate", "stringr", "tidyr", "tibble",
                   "httr", "yaml")
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

# 설정 파일 확인
if [ ! -f "$SCRIPT_DIR/config/assignment_templates.yaml" ]; then
  echo ""
  echo "⚠️  설정 파일이 없습니다: config/assignment_templates.yaml"
  echo "   샘플 설정 파일을 생성하시겠습니까? (y/n)"
  read -r response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    mkdir -p "$SCRIPT_DIR/config"
    cat > "$SCRIPT_DIR/config/assignment_templates.yaml" << 'EOF'
# Assignment Template Configuration
templates:
  very_low:
    id: "remedial_basics"
    title: "기본 개념 보정 과제"
  low:
    id: "supplementary_review"
    title: "보충 복습 과제"
  mid:
    id: "core_practice"
    title: "핵심 연습 과제"
  high:
    id: "challenge_advanced"
    title: "상향 도전 과제"
  very_high:
    id: "enrichment_extension"
    title: "심화 확장 과제"

permissions:
  admin:
    can_assign: true
    can_view_all_classes: true
  teacher:
    can_assign: true
    can_view_all_classes: false
  viewer:
    can_assign: false
    can_view_all_classes: false
EOF
    echo "✓ 샘플 설정 파일이 생성되었습니다."
  fi
fi

echo ""
echo "🚀 대시보드 시작 중..."
echo "   브라우저에서 http://localhost:$PORT 접속"
echo ""
echo "💡 팁:"
echo "   - 설정 변경: vim $SCRIPT_DIR/config/assignment_templates.yaml"
echo "   - 핫리로드: 30초 이내 자동 반영 (재시작 불필요)"
echo "   - 퀵스타트: cat $SCRIPT_DIR/QUICKSTART_v2.md"
echo ""

# Shiny 앱 실행
cd "$SCRIPT_DIR"
Rscript -e "shiny::runApp('app_teacher.R', host='$HOST', port=$PORT)"
