#!/bin/bash
# 포트 정책 강화 스크립트
# 목적: 브라우저 차단 포트 탐지 및 안전 포트 강제 사용

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 브라우저 차단 포트 목록
BLOCKED_PORTS=(6000 6665 6666 6667 6668 6669 10080)

# 안전한 포트 목록
SAFE_PORTS=(80 443 8000 8080 3000 5173 9000 4000 5000 5500)

# 검사할 디렉토리 (기본값: 현재 디렉토리)
SEARCH_DIR=${1:-.}

log_info "=== 포트 정책 검사 시작 ==="
log_info "검사 디렉토리: $SEARCH_DIR"

# 1. 차단된 포트 검사
log_info "1. 브라우저 차단 포트 검사 중..."

BLOCKED_FOUND=false
for port in "${BLOCKED_PORTS[@]}"; do
    if grep -r --line-number -E ":(6000|6665|6666|6667|6668|6669|10080)" "$SEARCH_DIR" 2>/dev/null; then
        log_error "브라우저 차단 포트 발견: $port"
        BLOCKED_FOUND=true
    fi
done

if [ "$BLOCKED_FOUND" = true ]; then
    log_error "❌ 브라우저가 차단하는 포트가 발견되었습니다!"
    log_error "다음 포트는 사용할 수 없습니다: ${BLOCKED_PORTS[*]}"
    log_error "안전한 포트를 사용하세요: ${SAFE_PORTS[*]}"
    exit 1
fi

log_success "브라우저 차단 포트 검사 통과"

# 2. 안전하지 않은 포트 경고
log_info "2. 안전하지 않은 포트 검사 중..."

# 포트 패턴 검색 (숫자:숫자 또는 포트=숫자)
PORT_PATTERNS=$(grep -r --line-number -E ":(6[0-9]{3}|7[0-9]{3}|8[0-9]{3}|9[0-9]{3}|[1-9][0-9]{4})" "$SEARCH_DIR" 2>/dev/null || true)

if [ -n "$PORT_PATTERNS" ]; then
    log_warning "다음 포트들이 발견되었습니다:"
    echo "$PORT_PATTERNS"
    
    # 각 포트가 안전한지 확인
    while IFS= read -r line; do
        if [[ $line =~ :([0-9]+) ]]; then
            port="${BASH_REMATCH[1]}"
            if [[ ! " ${SAFE_PORTS[@]} " =~ " ${port} " ]]; then
                log_warning "권장하지 않는 포트: $port"
            fi
        fi
    done <<< "$PORT_PATTERNS"
fi

# 3. 현재 실행 중인 서비스 포트 검사
log_info "3. 실행 중인 서비스 포트 검사 중..."

if command -v ss >/dev/null 2>&1; then
    LISTENING_PORTS=$(ss -lntp | grep LISTEN | awk '{print $4}' | sed 's/.*://' | sort -u)
    
    for port in $LISTENING_PORTS; do
        if [[ " ${BLOCKED_PORTS[@]} " =~ " ${port} " ]]; then
            log_error "실행 중인 서비스가 브라우저 차단 포트를 사용 중: $port"
            exit 1
        elif [[ ! " ${SAFE_PORTS[@]} " =~ " ${port} " ]]; then
            log_warning "실행 중인 서비스가 권장하지 않는 포트 사용: $port"
        fi
    done
    
    log_success "실행 중인 서비스 포트 검사 완료"
else
    log_warning "ss 명령어를 사용할 수 없습니다. netstat으로 대체 시도..."
    if command -v netstat >/dev/null 2>&1; then
        netstat -lntp | grep LISTEN || log_warning "netstat 결과 없음"
    else
        log_warning "netstat도 사용할 수 없습니다."
    fi
fi

# 4. 포트 정책 요약
log_info "4. 포트 정책 요약"

cat << EOF

${GREEN}=== 포트 정책 요약 ===${NC}

${RED}❌ 브라우저 차단 포트 (사용 금지):${NC}
${BLOCKED_PORTS[*]}

${GREEN}✅ 안전한 포트 (권장):${NC}
${SAFE_PORTS[*]}

${YELLOW}📋 포트 선택 가이드:${NC}
- 개발 서버: 3000, 5173, 8000
- 프로덕션: 80, 443
- 내부 서비스: 8080, 9000
- 테스트: 4000, 5000, 5500

${BLUE}💡 팁:${NC}
- 포트 6000-6999 범위는 브라우저에서 차단될 수 있습니다
- 10000 이상의 포트는 일반적으로 안전합니다
- HTTPS는 443 포트를 사용하세요

EOF

# 5. 허용 목록 외 포트 경고
log_info "5. 허용 목록 외 포트 검사 중..."

ALLOWLIST=':80|:443|:8000|:8080|:3000|:5173|:9000|:4000|:5000|:5500'
NON_RECOMMENDED_PORTS=$(grep -r -E ":[0-9]{2,5}" "$SEARCH_DIR" 2>/dev/null | grep -Ev "$ALLOWLIST" | grep -vE "(6000|6665|6666|6667|6668|6669|10080)" || true)

if [ -n "$NON_RECOMMENDED_PORTS" ]; then
    log_warning "권장하지 않는 포트가 발견되었습니다 (차단되지는 않지만 검토 필요):"
    echo "$NON_RECOMMENDED_PORTS"
    log_warning "권장 포트: 80, 443, 8000, 8080, 3000, 5173, 9000, 4000, 5000, 5500"
fi

log_success "포트 정책 검사 완료!"
