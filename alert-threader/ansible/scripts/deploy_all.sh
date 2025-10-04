#!/usr/bin/env bash
set -euo pipefail

# =============================
# Alert Threader 전체 배포 스크립트
# =============================
# SOPS 또는 Vault 모드로 전체 시스템을 배포합니다.

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
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

# 사용법 표시
usage() {
    echo "사용법: $0 [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  -m, --mode MODE        배포 모드 (sops|vault|auto)"
    echo "  -h, --host HOST        특정 호스트만 배포"
    echo "  -t, --test             테스트 모드 (실제 배포하지 않음)"
    echo "  -v, --verbose          상세 출력"
    echo "  --help                 이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 --mode sops                    # SOPS 모드로 배포"
    echo "  $0 --mode vault --host threader-1 # Vault 모드로 threader-1에만 배포"
    echo "  $0 --test                         # 테스트 모드로 실행"
}

# 기본값 설정
MODE="auto"
HOST=""
TEST_MODE=false
VERBOSE=false

# 명령행 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -t|--test)
            TEST_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            usage
            exit 1
            ;;
    esac
done

# 모드 검증
if [[ "$MODE" != "sops" && "$MODE" != "vault" && "$MODE" != "auto" ]]; then
    log_error "잘못된 모드: $MODE. sops, vault, 또는 auto를 사용하세요."
    exit 1
fi

# Ansible 디렉터리로 이동
cd "$(dirname "$0")/.."

log_info "Alert Threader 배포 시작..."
log_info "모드: $MODE"
log_info "호스트: ${HOST:-all}"
log_info "테스트 모드: $TEST_MODE"

# 1. 연결 테스트
log_info "1단계: 연결 테스트 중..."
if ! ./scripts/test_connection.sh; then
    log_error "연결 테스트 실패. 배포를 중단합니다."
    exit 1
fi
log_success "연결 테스트 완료"

# 2. 모드별 배포
case $MODE in
    "sops")
        log_info "2단계: SOPS 모드로 배포 중..."
        if $TEST_MODE; then
            ansible-playbook playbooks/deploy_sops.yaml --check ${HOST:+-l $HOST} ${VERBOSE:+-vvv}
        else
            ansible-playbook playbooks/deploy_sops.yaml ${HOST:+-l $HOST} ${VERBOSE:+-vvv}
        fi
        ;;
    "vault")
        log_info "2단계: Vault 모드로 배포 중..."
        if $TEST_MODE; then
            ansible-playbook playbooks/deploy_vault.yaml --check ${HOST:+-l $HOST} ${VERBOSE:+-vvv}
        else
            ansible-playbook playbooks/deploy_vault.yaml ${HOST:+-l $HOST} ${VERBOSE:+-vvv}
        fi
        ;;
    "auto")
        log_info "2단계: 자동 모드로 배포 중..."
        if $TEST_MODE; then
            ansible-playbook playbooks/deploy_env.yaml --check ${HOST:+-l $HOST} ${VERBOSE:+-vvv}
        else
            ansible-playbook playbooks/deploy_env.yaml ${HOST:+-l $HOST} ${VERBOSE:+-vvv}
        fi
        ;;
esac

if [ $? -eq 0 ]; then
    log_success "배포 완료!"
else
    log_error "배포 실패!"
    exit 1
fi

# 3. 배포 검증
log_info "3단계: 배포 검증 중..."
if $TEST_MODE; then
    log_warning "테스트 모드이므로 검증을 건너뜁니다."
else
    ansible-playbook playbooks/test_deployment.yaml ${HOST:+-l $HOST} ${VERBOSE:+-vvv}
    if [ $? -eq 0 ]; then
        log_success "검증 완료!"
    else
        log_warning "검증에서 일부 문제가 발견되었습니다."
    fi
fi

# 4. 다음 단계 안내
log_info "4단계: 다음 단계 안내"
echo ""
echo "🎉 배포가 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
if [[ "$MODE" == "sops" || "$MODE" == "auto" ]]; then
    echo "1. SOPS 비밀 업데이트: sops /opt/alert-threader-sec/alert-threader.env.enc"
    echo "2. 서비스 재시작: systemctl restart alert-threader-*"
    echo "3. 로그 확인: journalctl -u alert-threader-python -f"
elif [[ "$MODE" == "vault" ]]; then
    echo "1. Vault 비밀 업데이트: vault kv put kv/data/alert-threader key=value"
    echo "2. 서비스 재시작: systemctl restart alert-threader-*"
    echo "3. Vault Agent 로그: journalctl -u vault-agent-alert-threader -f"
fi
echo "4. 헬스체크: curl http://localhost:9009/health"
echo "5. 통계 확인: curl http://localhost:9009/stats"
echo ""
echo "🔧 유용한 명령어:"
echo "- 연결 테스트: ./scripts/test_connection.sh"
echo "- 배포 테스트: $0 --test"
echo "- 특정 호스트: $0 --host threader-1"
echo "- 상세 출력: $0 --verbose"
