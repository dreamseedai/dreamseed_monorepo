#!/bin/bash
# DreamSeed Monorepo 구조화 실행 스크립트
# 작성일: 2024-11-09
# 사용법: ./RESTRUCTURE_EXECUTE.sh [--dry-run]

set -e  # 에러 발생 시 중단
set -u  # 미정의 변수 사용 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
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

# Dry-run 모드 확인
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    log_warning "DRY-RUN 모드: 실제 변경 없이 시뮬레이션만 수행합니다."
fi

# 실행 함수
execute() {
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY-RUN] $*"
    else
        eval "$@"
    fi
}

# 현재 디렉토리 확인
if [[ ! -f "package.json" ]] || [[ ! -f "pnpm-workspace.yaml" ]]; then
    log_error "dreamseed_monorepo 루트 디렉토리에서 실행해주세요."
    exit 1
fi

log_info "DreamSeed Monorepo 구조화를 시작합니다..."
echo ""

# =============================================================================
# Phase 1: 준비
# =============================================================================
log_info "Phase 1: 준비 단계"

# 현재 상태 스냅샷
SNAPSHOT_FILE="monorepo_snapshot_$(date +%Y%m%d_%H%M%S).txt"
log_info "현재 상태 스냅샷 생성: $SNAPSHOT_FILE"
execute "find . -maxdepth 2 -type d | sort > $SNAPSHOT_FILE"

# 아카이브 디렉토리 생성
log_info "아카이브 디렉토리 생성"
execute "mkdir -p _archive"

# 아카이브 README 생성
if [ "$DRY_RUN" = false ]; then
    cat > _archive/README.md << 'EOF'
# 아카이브 디렉토리

이 디렉토리는 모노레포 구조화 과정에서 이동된 고립된/사용하지 않는 디렉토리를 보관합니다.

## 아카이브 날짜: 2024-11-09

### 아카이브된 디렉토리 목록

| 디렉토리 | 이유 | 복원 방법 |
|---------|------|----------|
| adaptive_engine | 빈 디렉토리 | `mv _archive/2024-11-09_adaptive_engine ./adaptive_engine` |
| admin_front | 1개 파일만 존재 | `mv _archive/2024-11-09_admin_front ./admin_front` |
| dreamseed | 빈 디렉토리 | `mv _archive/2024-11-09_dreamseed ./dreamseed` |
| dsadmin | 빈 디렉토리 | `mv _archive/2024-11-09_dsadmin ./dsadmin` |
| examples | 빈 디렉토리 | `mv _archive/2024-11-09_examples ./examples` |
| frontend | npm 캐시만 존재 | `mv _archive/2024-11-09_frontend ./frontend` |
| htmlcov | 빈 디렉토리 | `mv _archive/2024-11-09_htmlcov ./htmlcov` |
| mathml_env | 빈 가상환경 | `mv _archive/2024-11-09_mathml_env ./mathml_env` |
| migrations | 빈 디렉토리 | `mv _archive/2024-11-09_migrations ./migrations` |
| monitoring | 빈 디렉토리 | `mv _archive/2024-11-09_monitoring ./monitoring` |
| r-plumber | 빈 디렉토리 | `mv _archive/2024-11-09_r-plumber ./r-plumber` |
| shiny-admin | 빈 디렉토리 | `mv _archive/2024-11-09_shiny-admin ./shiny-admin` |
| tests | 빈 디렉토리 | `mv _archive/2024-11-09_tests ./tests` |
| webtests | 빈 디렉토리 | `mv _archive/2024-11-09_webtests ./webtests` |

## 주의사항

- 아카이브된 디렉토리는 30일 후 삭제 예정
- 필요한 경우 위 복원 명령어 사용
- Git 히스토리는 보존됨
EOF
    log_success "아카이브 README 생성 완료"
fi

log_success "Phase 1 완료"
echo ""

# =============================================================================
# Phase 2: 아카이브
# =============================================================================
log_info "Phase 2: 고립된 디렉토리 아카이브"

ARCHIVE_DIRS=(
    "adaptive_engine"
    "admin_front"
    "dreamseed"
    "dsadmin"
    "examples"
    "frontend"
    "htmlcov"
    "mathml_env"
    "migrations"
    "monitoring"
    "r-plumber"
    "shiny-admin"
    "tests"
    "webtests"
    "translator.py"
    "Caddyfile"
    "alembic"
)

for dir in "${ARCHIVE_DIRS[@]}"; do
    if [ -e "$dir" ]; then
        log_info "아카이브: $dir → _archive/2024-11-09_$dir"
        execute "git mv '$dir' '_archive/2024-11-09_$dir' 2>/dev/null || mv '$dir' '_archive/2024-11-09_$dir'"
    else
        log_warning "존재하지 않음: $dir (건너뜀)"
    fi
done

# 오염 파일 정리
log_info "최상위 오염 파일 정리"
CLEANUP_FILES=(
    "backend.log"
    "server.log"
    "batch_conversion.log"
    "mathml_conversion.log"
    "dummy.db"
    "server.pid"
    "question_editor_quill.html"
)

for file in "${CLEANUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_info "삭제: $file"
        execute "rm -f '$file'"
    fi
done

log_success "Phase 2 완료"
echo ""

# =============================================================================
# Phase 3: 구조 재정리
# =============================================================================
log_info "Phase 3: 디렉토리 구조 재정리"

# 3.1 Apps 디렉토리 정리
log_info "3.1 Apps 디렉토리 정리"

if [ -d "portal_front" ]; then
    log_info "portal_front → apps/portal"
    execute "mkdir -p apps/portal"
    execute "git mv portal_front/* apps/portal/ 2>/dev/null || mv portal_front/* apps/portal/"
    execute "rmdir portal_front 2>/dev/null || true"
    
    # 교사용 대시보드 분리
    if [ -d "apps/portal/dashboard" ]; then
        log_info "교사용 대시보드 분리: apps/portal/dashboard → apps/teacher-dashboard"
        execute "mkdir -p apps/teacher-dashboard"
        execute "git mv apps/portal/dashboard/* apps/teacher-dashboard/ 2>/dev/null || mv apps/portal/dashboard/* apps/teacher-dashboard/"
        execute "rmdir apps/portal/dashboard 2>/dev/null || true"
    fi
fi

# 3.2 Services 디렉토리 생성
log_info "3.2 Services 디렉토리 생성"
execute "mkdir -p services"

if [ -d "backend" ]; then
    log_info "backend → services/governance"
    execute "git mv backend services/governance 2>/dev/null || mv backend services/governance"
fi

if [ -d "apps/seedtest_api" ]; then
    log_info "apps/seedtest_api → services/seedtest-api"
    execute "git mv apps/seedtest_api services/seedtest-api 2>/dev/null || mv apps/seedtest_api services/seedtest-api"
fi

# 3.3 Packages 통합
log_info "3.3 Packages 디렉토리 처리"
if [ -d "packages" ]; then
    # packages 내용 확인
    PACKAGE_COUNT=$(find packages -mindepth 1 -maxdepth 1 | wc -l)
    if [ "$PACKAGE_COUNT" -eq 0 ]; then
        log_info "packages/ 빈 디렉토리 → 아카이브"
        execute "git mv packages _archive/2024-11-09_packages 2>/dev/null || mv packages _archive/2024-11-09_packages"
    else
        log_warning "packages/ 디렉토리에 파일이 있습니다. 수동 확인 필요."
    fi
fi

# 3.4 Shared-analytics-ui 처리
log_info "3.4 Shared-analytics-ui 처리"
if [ -d "shared-analytics-ui" ]; then
    log_info "shared-analytics-ui → 아카이브"
    execute "git mv shared-analytics-ui _archive/2024-11-09_shared-analytics-ui 2>/dev/null || mv shared-analytics-ui _archive/2024-11-09_shared-analytics-ui"
fi

log_success "Phase 3 완료"
echo ""

# =============================================================================
# Phase 4: 설정 파일 업데이트
# =============================================================================
log_info "Phase 4: 설정 파일 업데이트"

if [ "$DRY_RUN" = false ]; then
    # 4.1 pnpm-workspace.yaml 업데이트
    log_info "pnpm-workspace.yaml 업데이트"
    cat > pnpm-workspace.yaml << 'EOF'
packages:
  - "apps/*"
  - "services/*"
  - "shared/*"
EOF
    
    # 4.2 package.json 업데이트
    log_info "package.json 업데이트"
    # 기존 package.json 백업
    cp package.json package.json.backup
    
    # workspaces 섹션 업데이트 (jq 사용)
    if command -v jq &> /dev/null; then
        jq '.workspaces = ["apps/*", "services/*", "shared/*"]' package.json.backup > package.json
        log_success "package.json 업데이트 완료"
    else
        log_warning "jq가 설치되지 않음. package.json 수동 업데이트 필요."
    fi
else
    log_info "[DRY-RUN] pnpm-workspace.yaml 업데이트 (건너뜀)"
    log_info "[DRY-RUN] package.json 업데이트 (건너뜀)"
fi

log_success "Phase 4 완료"
echo ""

# =============================================================================
# Phase 5: 검증
# =============================================================================
log_info "Phase 5: 검증"

if [ "$DRY_RUN" = false ]; then
    # pnpm 워크스페이스 검증
    log_info "pnpm 워크스페이스 검증"
    if command -v pnpm &> /dev/null; then
        pnpm list --depth 0 || log_warning "pnpm 워크스페이스 검증 실패"
    else
        log_warning "pnpm이 설치되지 않음"
    fi
    
    # TypeScript 검증
    log_info "TypeScript 설정 검증"
    if [ -f "tsconfig.base.json" ]; then
        log_success "tsconfig.base.json 존재"
    else
        log_warning "tsconfig.base.json 없음"
    fi
else
    log_info "[DRY-RUN] 검증 단계 (건너뜀)"
fi

log_success "Phase 5 완료"
echo ""

# =============================================================================
# 완료
# =============================================================================
log_success "✅ 모노레포 구조화 완료!"
echo ""
log_info "다음 단계:"
echo "  1. 변경사항 확인: git status"
echo "  2. 빌드 테스트: pnpm build:all"
echo "  3. 커밋: git add . && git commit -m 'refactor: 모노레포 구조화'"
echo "  4. 문서 업데이트: README.md 수정"
echo ""
log_info "롤백이 필요한 경우:"
echo "  cp .gitignore.backup .gitignore"
echo "  git reset --hard HEAD"
echo ""
log_info "상세 계획: MONOREPO_RESTRUCTURE_PLAN.md 참조"
