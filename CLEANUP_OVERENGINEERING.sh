#!/bin/bash
# 오버 엔지니어링 정리 스크립트
# 작성일: 2024-11-09

set -e
set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Dry-run 모드
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    log_warning "DRY-RUN 모드: 실제 변경 없이 시뮬레이션만 수행합니다."
fi

execute() {
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY-RUN] $*"
    else
        eval "$@"
    fi
}

log_info "오버 엔지니어링 정리를 시작합니다..."
echo ""

# =============================================================================
# 1. mock_api.py 확인
# =============================================================================
log_info "1. mock_api.py 파일 확인"

if [ -f "backend/app/api/mock_api.py" ]; then
    FILE_SIZE=$(du -h backend/app/api/mock_api.py | cut -f1)
    LINE_COUNT=$(wc -l < backend/app/api/mock_api.py)
    
    log_warning "mock_api.py 발견:"
    echo "  - 크기: $FILE_SIZE"
    echo "  - 줄 수: $LINE_COUNT"
    
    if [ "$LINE_COUNT" -gt 10000 ]; then
        log_error "❌ 이 파일은 ${LINE_COUNT}줄입니다!"
        log_error "❌ 데이터와 코드가 혼재되어 있습니다."
        echo ""
        log_info "해결 방법:"
        echo "  1. MOCK_API_MIGRATION_PLAN.md 읽기"
        echo "  2. 데이터를 JSON 파일로 분리"
        echo "  3. API 코드만 남기기"
        echo ""
        log_warning "이 파일은 수동으로 처리해야 합니다."
        echo ""
    fi
else
    log_success "mock_api.py 없음 (정상)"
fi

# =============================================================================
# 2. 빈 __init__.py 파일 확인
# =============================================================================
log_info "2. 빈 __init__.py 파일 확인"

EMPTY_INIT_FILES=$(find backend shared -name "__init__.py" -type f -size -10c 2>/dev/null | grep -v ".venv" || true)

if [ -z "$EMPTY_INIT_FILES" ]; then
    log_success "빈 __init__.py 파일 없음"
else
    log_warning "빈 __init__.py 파일 발견:"
    echo "$EMPTY_INIT_FILES" | while read -r file; do
        echo "  - $file"
    done
    
    if [ "$DRY_RUN" = false ]; then
        read -p "삭제하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "$EMPTY_INIT_FILES" | while read -r file; do
                rm -f "$file"
                log_success "삭제: $file"
            done
        fi
    fi
fi

echo ""

# =============================================================================
# 3. 사용하지 않는 Utils/Helper 클래스 확인
# =============================================================================
log_info "3. Utils/Helper 패턴 확인"

UTIL_FILES=$(find backend shared -type f -name "*util*.py" -o -name "*helper*.py" -o -name "*manager*.py" 2>/dev/null | grep -v ".venv" | grep -v "test" || true)

if [ -z "$UTIL_FILES" ]; then
    log_success "Utils/Helper 파일 없음"
else
    log_warning "Utils/Helper 파일 발견:"
    echo "$UTIL_FILES" | while read -r file; do
        if [ -f "$file" ]; then
            lines=$(wc -l < "$file")
            echo "  - $file ($lines줄)"
        fi
    done
    echo ""
    log_info "권장: 클래스 → 독립 함수로 변경"
fi

echo ""

# =============================================================================
# 4. 테스트 없는 복잡한 코드 확인
# =============================================================================
log_info "4. 테스트 없는 복잡한 코드 확인"

COMPLEX_FILES=$(find backend shared -type f -name "*.py" -exec wc -l {} \; 2>/dev/null | \
    grep -v ".venv" | \
    awk '$1 > 200 {print $2}' | \
    grep -v "test" | \
    head -10 || true)

if [ -z "$COMPLEX_FILES" ]; then
    log_success "복잡한 파일 없음"
else
    log_warning "200줄 이상 파일 (테스트 확인 필요):"
    echo "$COMPLEX_FILES" | while read -r file; do
        if [ -f "$file" ]; then
            lines=$(wc -l < "$file")
            test_file="${file%.*}_test.py"
            if [ -f "$test_file" ]; then
                echo "  - $file ($lines줄) ✅ 테스트 있음"
            else
                echo "  - $file ($lines줄) ❌ 테스트 없음"
            fi
        fi
    done
    echo ""
    log_info "권장: 테스트 추가 또는 코드 단순화"
fi

echo ""

# =============================================================================
# 5. 중복 설정 파일 확인
# =============================================================================
log_info "5. 중복 설정 파일 확인"

CONFIG_FILES=$(find backend shared -type f \( -name "config.py" -o -name "settings.py" -o -name "conf.py" \) 2>/dev/null | grep -v ".venv" || true)

CONFIG_COUNT=$(echo "$CONFIG_FILES" | grep -c . || echo "0")

if [ "$CONFIG_COUNT" -le 1 ]; then
    log_success "중복 설정 파일 없음"
else
    log_warning "설정 파일 여러 개 발견:"
    echo "$CONFIG_FILES" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    log_info "권장: 하나의 설정 파일로 통합"
fi

echo ""

# =============================================================================
# 6. 요약
# =============================================================================
log_info "📊 정리 요약"
echo ""

echo "✅ 완료된 항목:"
echo "  - 빈 __init__.py 확인"
echo "  - Utils/Helper 패턴 확인"
echo "  - 테스트 없는 코드 확인"
echo "  - 중복 설정 파일 확인"
echo ""

echo "⚠️ 수동 처리 필요:"
echo "  1. mock_api.py (49MB) → MOCK_API_MIGRATION_PLAN.md 참조"
echo "  2. 복잡한 코드 → 테스트 추가 또는 단순화"
echo "  3. Utils/Helper 클래스 → 독립 함수로 변경"
echo ""

echo "📚 참고 문서:"
echo "  - over-engineering-report-20251109.md"
echo "  - MOCK_API_MIGRATION_PLAN.md"
echo ""

log_success "✅ 오버 엔지니어링 정리 완료!"
