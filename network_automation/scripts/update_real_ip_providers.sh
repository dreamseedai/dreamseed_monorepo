#!/bin/bash
# 멀티 클라우드 CIDR 자동 동기화 스크립트
# 목적: Cloudflare, AWS ELB, GCP LB IP 범위를 자동으로 다운로드하여 nginx real_ip 설정에 적용

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

# 설정
OUT_DIR="/etc/nginx/conf.d"
OUT_FILE="$OUT_DIR/real_ip_providers.conf"
TMP_DIR=$(mktemp -d)
TMP_FILE="$TMP_DIR/real_ip_providers.conf.tmp"
LOCK_FILE="/var/run/update_real_ip_providers.lock"

# 환경 변수 (기본값: Cloudflare만 활성화)
CF_ENABLE="${CF_ENABLE:-yes}"
AWS_ENABLE="${AWS_ENABLE:-no}"
AWS_VPC_SUBNETS="${AWS_VPC_SUBNETS:-no}"
GCP_ENABLE="${GCP_ENABLE:-no}"
KEEP_LOCAL="${KEEP_LOCAL:-yes}"

# GCP 스코프 설정 (기본값: global)
GCP_SCOPE="${GCP_SCOPE:-global}"

# AWS VPC 설정 (자동 감지 또는 수동 지정)
AWS_REGION="${AWS_REGION:-}"
AWS_VPC_ID="${AWS_VPC_ID:-}"

# API URL들
CF_V4_URL="https://www.cloudflare.com/ips-v4"
CF_V6_URL="https://www.cloudflare.com/ips-v6"
AWS_URL="https://ip-ranges.amazonaws.com/ip-ranges.json"
GCP_URL="https://www.gstatic.com/ipranges/cloud.json"

log_info "=== 멀티 클라우드 CIDR 자동 동기화 시작 ==="
log_info "Cloudflare: $CF_ENABLE"
log_info "AWS ELB: $AWS_ENABLE"
log_info "AWS VPC Subnets: $AWS_VPC_SUBNETS"
log_info "GCP LB: $GCP_ENABLE (scope: $GCP_SCOPE)"
log_info "출력 파일: $OUT_FILE"

# 락 파일로 중복 실행 방지
exec 9>"$LOCK_FILE" || true
if ! flock -n 9; then
    log_warning "다른 업데이트가 진행 중입니다. 종료합니다."
    exit 0
fi

# 출력 디렉토리 생성
mkdir -p "$OUT_DIR"

# IP 목록 가져오기 함수
fetch_ips() {
    local url="$1"
    local name="$2"
    
    log_info "$name IP 목록 가져오는 중..."
    if curl -fsSL "$url" | awk 'NF {print $0}'; then
        log_success "$name IP 목록 가져오기 성공"
    else
        log_error "$name IP 목록 가져오기 실패"
        return 1
    fi
}

# CIDR 유효성 검사
validate_cidr() {
    grep -E -i '^(([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}|[0-9a-f:]+/[0-9]{1,3})$' || true
}

# set_real_ip_from 라인 생성 함수
append_set_lines() {
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            echo "set_real_ip_from $line;"
        fi
    done
}

# AWS VPC 메타데이터 자동 감지 함수
detect_aws_metadata() {
    log_info "AWS VPC 메타데이터 자동 감지 중..."
    
    # AWS CLI 설치 확인
    if ! command -v aws >/dev/null 2>&1; then
        log_warning "AWS CLI가 설치되지 않았습니다. VPC 서브넷 감지를 건너뜁니다."
        return 1
    fi
    
    # AWS 자격 증명 확인
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_warning "AWS 자격 증명이 설정되지 않았습니다. VPC 서브넷 감지를 건너뜁니다."
        return 1
    fi
    
    # 리전 자동 감지
    if [ -z "$AWS_REGION" ]; then
        log_info "AWS 리전 자동 감지 중..."
        if AWS_REGION=$(curl -s --max-time 5 http://169.254.169.254/latest/dynamic/instance-identity/document 2>/dev/null | jq -r .region 2>/dev/null); then
            log_success "AWS 리전 감지됨: $AWS_REGION"
        else
            log_warning "AWS 리전 자동 감지 실패. 기본값 사용"
            AWS_REGION="us-east-1"
        fi
    else
        log_info "AWS 리전 (수동 설정): $AWS_REGION"
    fi
    
    # VPC ID 자동 감지
    if [ -z "$AWS_VPC_ID" ]; then
        log_info "AWS VPC ID 자동 감지 중..."
        if AWS_VPC_ID=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/network/interfaces/macs/ 2>/dev/null | head -n1 | xargs -I{} curl -s --max-time 5 http://169.254.169.254/latest/meta-data/network/interfaces/macs/{}/vpc-id 2>/dev/null); then
            log_success "AWS VPC ID 감지됨: $AWS_VPC_ID"
        else
            log_warning "AWS VPC ID 자동 감지 실패"
            return 1
        fi
    else
        log_info "AWS VPC ID (수동 설정): $AWS_VPC_ID"
    fi
    
    return 0
}

# AWS VPC 서브넷 CIDR 가져오기 함수
fetch_aws_vpc_subnets() {
    local region="$1"
    local vpc_id="$2"
    
    log_info "AWS VPC 서브넷 CIDR 가져오는 중... (VPC: $vpc_id, Region: $region)"
    
    # IPv4 서브넷 CIDR
    local v4_subnets
    if v4_subnets=$(aws ec2 describe-subnets --region "$region" --filters "Name=vpc-id,Values=$vpc_id" --query 'Subnets[].CidrBlock' --output text 2>/dev/null); then
        if [ -n "$v4_subnets" ]; then
            log_success "IPv4 서브넷 CIDR 가져오기 성공"
            echo "$v4_subnets" | tr '\t' '\n' | validate_cidr
        fi
    else
        log_warning "IPv4 서브넷 CIDR 가져오기 실패 (권한 부족 또는 네트워크 오류)"
    fi
    
    # IPv6 서브넷 CIDR (선택사항)
    local v6_subnets
    if v6_subnets=$(aws ec2 describe-subnets --region "$region" --filters "Name=vpc-id,Values=$vpc_id" --query 'Subnets[].Ipv6CidrBlockAssociationSet[].Ipv6CidrBlock' --output text 2>/dev/null); then
        if [ -n "$v6_subnets" ]; then
            log_success "IPv6 서브넷 CIDR 가져오기 성공"
            echo "$v6_subnets" | tr '\t' '\n' | validate_cidr
        fi
    else
        log_info "IPv6 서브넷 CIDR 없음 또는 권한 부족"
    fi
}

# jq 설치 확인
if ! command -v jq >/dev/null 2>&1; then
    log_warning "jq가 설치되지 않았습니다. Python으로 JSON 파싱합니다."
    JQ_MISSING=1
else
    JQ_MISSING=""
fi

# nginx 설정 파일 생성 시작
log_info "1. nginx 설정 파일 생성 중..."
{
    echo "# Auto-generated by update_real_ip_providers.sh on $(date -u +%FT%TZ)"
    echo "# Providers: Cloudflare=$CF_ENABLE, AWS=$AWS_ENABLE, GCP=$GCP_ENABLE"
    echo "# GCP Scope: $GCP_SCOPE"
    echo ""
    
    # 로컬 프록시 설정
    if [ "$KEEP_LOCAL" = "yes" ]; then
        echo "# Local proxy (keep existing)"
        echo "set_real_ip_from 127.0.0.1;"
        echo ""
    fi
    
    # Cloudflare 처리
    if [ "$CF_ENABLE" = "yes" ]; then
        log_info "2. Cloudflare IP 범위 처리 중..."
        V4=$(fetch_ips "$CF_V4_URL" "Cloudflare IPv4" | validate_cidr)
        V6=$(fetch_ips "$CF_V6_URL" "Cloudflare IPv6" | validate_cidr)
        
        if [ -n "$V4" ] || [ -n "$V6" ]; then
            echo "# Cloudflare ranges"
            if [ -n "$V4" ]; then
                echo "$V4" | append_set_lines
            fi
            if [ -n "$V6" ]; then
                echo "$V6" | append_set_lines
            fi
            echo ""
        fi
    fi
    
    # AWS ELB 처리
    if [ "$AWS_ENABLE" = "yes" ]; then
        log_info "3. AWS ELB IP 범위 처리 중..."
        if [ -z "$JQ_MISSING" ]; then
            # jq 사용
            AWS_IPS=$(curl -fsSL "$AWS_URL" | jq -r '.prefixes[] | select(.service=="ELB") | .ip_prefix' | validate_cidr)
            AWS_IPS_V6=$(curl -fsSL "$AWS_URL" | jq -r '.ipv6_prefixes[] | select(.service=="ELB") | .ipv6_prefix' | validate_cidr)
        else
            # Python 사용
            AWS_IPS=$(python3 - "$AWS_URL" <<'PY'
import json, sys, urllib.request
url = sys.argv[1]
with urllib.request.urlopen(url) as r:
    data = json.load(r)
for p in data.get('prefixes', []):
    if p.get('service') == 'ELB' and 'ip_prefix' in p:
        print(p['ip_prefix'])
PY
)
            AWS_IPS_V6=$(python3 - "$AWS_URL" <<'PY'
import json, sys, urllib.request
url = sys.argv[1]
with urllib.request.urlopen(url) as r:
    data = json.load(r)
for p in data.get('ipv6_prefixes', []):
    if p.get('service') == 'ELB' and 'ipv6_prefix' in p:
        print(p['ipv6_prefix'])
PY
)
        fi
        
        if [ -n "$AWS_IPS" ] || [ -n "$AWS_IPS_V6" ]; then
            echo "# AWS ELB ranges (service=ELB)"
            if [ -n "$AWS_IPS" ]; then
                echo "$AWS_IPS" | append_set_lines
            fi
            if [ -n "$AWS_IPS_V6" ]; then
                echo "$AWS_IPS_V6" | append_set_lines
            fi
            echo "# NOTE: For ALB/NLB, prefer trusting your VPC subnet CIDRs instead of ip-ranges.json"
            echo ""
        fi
    fi
    
    # AWS VPC 서브넷 처리 (ALB/NLB용)
    if [ "$AWS_VPC_SUBNETS" = "yes" ]; then
        log_info "4. AWS VPC 서브넷 CIDR 처리 중..."
        if detect_aws_metadata; then
            VPC_SUBNETS=$(fetch_aws_vpc_subnets "$AWS_REGION" "$AWS_VPC_ID")
            if [ -n "$VPC_SUBNETS" ]; then
                echo "# AWS VPC Subnets (for ALB/NLB trust)"
                echo "# VPC ID: $AWS_VPC_ID, Region: $AWS_REGION"
                echo "$VPC_SUBNETS" | append_set_lines
                echo "# NOTE: These are your VPC subnet CIDRs for ALB/NLB trust"
                echo ""
            else
                log_warning "VPC 서브넷 CIDR을 가져올 수 없습니다"
            fi
        else
            log_warning "AWS VPC 메타데이터 감지 실패. VPC 서브넷 처리를 건너뜁니다"
        fi
    fi
    
    # GCP LB 처리
    if [ "$GCP_ENABLE" = "yes" ]; then
        log_info "5. GCP LB IP 범위 처리 중... (scope: $GCP_SCOPE)"
        if [ -z "$JQ_MISSING" ]; then
            # jq 사용
            GCP_IPS=$(curl -fsSL "$GCP_URL" | jq -r --arg S "$GCP_SCOPE" '.prefixes[] | select((.scope==$S) and (.ipv4Prefix or .ipv6Prefix)) | (.ipv4Prefix // .ipv6Prefix)' | validate_cidr)
        else
            # Python 사용
            GCP_IPS=$(python3 - "$GCP_URL" "$GCP_SCOPE" <<'PY'
import json, sys, urllib.request
url, scope = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(url) as r:
    data = json.load(r)
for p in data.get('prefixes', []):
    if p.get('scope') == scope:
        cidr = p.get('ipv4Prefix') or p.get('ipv6Prefix')
        if cidr:
            print(cidr)
PY
)
        fi
        
        if [ -n "$GCP_IPS" ]; then
            echo "# GCP LB ranges (scope=$GCP_SCOPE)"
            echo "$GCP_IPS" | append_set_lines
            echo ""
        fi
    fi
    
} > "$TMP_FILE"

# 파일 내용이 변경되었는지 확인
log_info "5. 변경 사항 확인 중..."
NEED_UPDATE=1
if [ -f "$OUT_FILE" ]; then
    if sha256sum "$OUT_FILE" "$TMP_FILE" | awk '{print $1}' | uniq -d | grep -q .; then
        NEED_UPDATE=0
        log_info "변경 사항이 없습니다"
    else
        log_info "변경 사항이 감지되었습니다"
    fi
else
    log_info "기존 파일이 없습니다. 새로 생성합니다"
fi

# nginx 설정 업데이트
if [ "$NEED_UPDATE" -eq 1 ]; then
    log_info "6. nginx 설정 업데이트 중..."
    
    # 원자적으로 파일 교체
    cp -af "$TMP_FILE" "$OUT_FILE"
    
    # nginx 설정 검증
    if nginx -t; then
        systemctl reload nginx
        log_success "✅ nginx 설정 업데이트 및 재로드 완료"
        log_success "   파일: $OUT_FILE"
        
        # 통계 출력
        V4_COUNT=$(grep -c "set_real_ip_from.*[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+" "$OUT_FILE" || echo "0")
        V6_COUNT=$(grep -c "set_real_ip_from.*:" "$OUT_FILE" || echo "0")
        LOCAL_COUNT=$(grep -c "set_real_ip_from 127.0.0.1" "$OUT_FILE" || echo "0")
        
        log_success "   IPv4 범위: $V4_COUNT개"
        log_success "   IPv6 범위: $V6_COUNT개"
        log_success "   로컬 범위: $LOCAL_COUNT개"
        log_success "   총 범위: $((V4_COUNT + V6_COUNT + LOCAL_COUNT))개"
    else
        log_error "❌ nginx 설정 검증 실패. 변경사항을 되돌립니다"
        # 이전 파일이 있다면 복원
        if [ -f "${OUT_FILE}.bak" ]; then
            cp -af "${OUT_FILE}.bak" "$OUT_FILE"
            log_info "이전 설정으로 복원됨"
        fi
        exit 1
    fi
else
    log_info "프로바이더 CIDR 변경사항이 없습니다. nginx 재로드가 필요하지 않습니다"
fi

# 백업 파일 생성
if [ "$NEED_UPDATE" -eq 1 ]; then
    cp -af "$OUT_FILE" "${OUT_FILE}.bak"
    log_info "백업 파일 생성: ${OUT_FILE}.bak"
fi

# 임시 파일 정리
rm -rf "$TMP_DIR" || true

# 보안 경고
echo ""
log_warning "🔒 보안 주의사항:"
echo "   • set_real_ip_from에 외부 CIDR을 추가하면 X-Forwarded-For 신뢰 범위가 넓어집니다"
echo "   • 해당 L7 프록시 뒤에 100% 위치한 서버에서만 사용하세요"
echo "   • 직접 접속이 가능한 환경이면 방화벽으로 원 서버 접근을 차단하세요"
echo "   • real_ip_recursive on과 함께 신뢰 범위를 최소화하세요"
echo "   • ALB/NLB 사용 시에는 VPC 서브넷 CIDR을 직접 지정하는 것을 권장합니다"

log_success "멀티 클라우드 CIDR 자동 동기화 완료!"
