#!/bin/bash
# 네트워크 진단 로그 수집 스크립트
# 목적: "서버는 정상인데 외부에서 접속 불가" 문제 진단을 위한 로그 수집

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

# 출력 파일명
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/tmp/network_logs_${TIMESTAMP}"
OUTPUT_FILE="${OUTPUT_DIR}/network_diagnostics_${TIMESTAMP}.log"

log_info "=== 네트워크 진단 로그 수집 시작 ==="
log_info "출력 디렉토리: $OUTPUT_DIR"

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

# 로그 수집 함수
collect_log() {
    local title="$1"
    local command="$2"
    
    echo "==========================================" >> "$OUTPUT_FILE"
    echo "=== $title ===" >> "$OUTPUT_FILE"
    echo "시간: $(date)" >> "$OUTPUT_FILE"
    echo "명령어: $command" >> "$OUTPUT_FILE"
    echo "==========================================" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    eval "$command" >> "$OUTPUT_FILE" 2>&1 || echo "명령어 실행 실패: $command" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# 1. 시스템 정보
log_info "1. 시스템 정보 수집 중..."
collect_log "시스템 정보" "uname -a && hostname && whoami"

# 2. 네트워크 인터페이스
log_info "2. 네트워크 인터페이스 정보 수집 중..."
collect_log "네트워크 인터페이스" "ip addr show"
collect_log "라우팅 테이블" "ip route show"

# 3. 포트 상태
log_info "3. 포트 상태 수집 중..."
collect_log "LISTEN 포트 (ss)" "ss -lntp"
collect_log "LISTEN 포트 (netstat)" "netstat -lntp 2>/dev/null || echo 'netstat 사용 불가'"

# 4. 방화벽 상태
log_info "4. 방화벽 상태 수집 중..."
collect_log "UFW 상태" "ufw status verbose"
collect_log "iptables 규칙" "iptables -L -n -v 2>/dev/null || echo 'iptables 사용 불가'"

# 5. 실행 중인 프로세스
log_info "5. 네트워크 관련 프로세스 수집 중..."
collect_log "네트워크 프로세스" "ps aux | grep -E '(http|nginx|apache|python.*server)' | grep -v grep"

# 6. 시스템 로그
log_info "6. 시스템 로그 수집 중..."
collect_log "시스템 로그 (최근 50줄)" "journalctl -n 50 --no-pager 2>/dev/null || tail -50 /var/log/syslog 2>/dev/null || echo '시스템 로그 접근 불가'"

# 7. 네트워크 연결 테스트
log_info "7. 네트워크 연결 테스트 중..."
EXTERNAL_IP=$(hostname -I | awk '{print $1}')
collect_log "로컬 IP 정보" "hostname -I && echo '외부 IP: $EXTERNAL_IP'"

# 8. DNS 설정
log_info "8. DNS 설정 수집 중..."
collect_log "DNS 설정" "cat /etc/resolv.conf 2>/dev/null || echo 'DNS 설정 파일 접근 불가'"

# 9. 서비스 상태
log_info "9. 서비스 상태 수집 중..."
collect_log "네트워크 서비스 상태" "systemctl status networking 2>/dev/null || echo 'networking 서비스 상태 확인 불가'"

# 10. 추가 진단 정보
log_info "10. 추가 진단 정보 수집 중..."
collect_log "메모리 사용량" "free -h"
collect_log "디스크 사용량" "df -h"
collect_log "CPU 정보" "lscpu 2>/dev/null || cat /proc/cpuinfo | head -20"

# 11. 브라우저 호환성 체크
log_info "11. 브라우저 호환성 체크 중..."
{
    echo "=========================================="
    echo "=== 브라우저 호환성 체크 ==="
    echo "시간: $(date)"
    echo "=========================================="
    echo ""
    
    echo "브라우저 차단 포트 검사:"
    BLOCKED_PORTS=(6000 6665 6666 6667 6668 6669 10080)
    for port in "${BLOCKED_PORTS[@]}"; do
        if ss -lntp | grep -q ":$port "; then
            echo "❌ 브라우저 차단 포트 사용 중: $port"
        else
            echo "✅ 포트 $port 사용 안 함"
        fi
    done
    
    echo ""
    echo "안전한 포트 사용 현황:"
    SAFE_PORTS=(80 443 8000 8080 3000 5173 9000)
    for port in "${SAFE_PORTS[@]}"; do
        if ss -lntp | grep -q ":$port "; then
            echo "✅ 안전한 포트 사용 중: $port"
        fi
    done
    
} >> "$OUTPUT_FILE"

# 12. Windows 클라이언트 진단 가이드 생성
log_info "12. Windows 클라이언트 진단 가이드 생성 중..."
WINDOWS_GUIDE="${OUTPUT_DIR}/windows_client_diagnosis.md"

cat > "$WINDOWS_GUIDE" << EOF
# Windows 클라이언트 진단 가이드

## 서버 정보
- 서버 IP: $EXTERNAL_IP
- 진단 시간: $(date)

## 1단계: 기본 연결 확인

### ping 테스트
\`\`\`cmd
ping $EXTERNAL_IP
\`\`\`

### telnet 테스트 (포트별)
\`\`\`cmd
telnet $EXTERNAL_IP 80
telnet $EXTERNAL_IP 443
telnet $EXTERNAL_IP 8080
\`\`\`

## 2단계: HTTP 연결 확인

### curl 테스트
\`\`\`cmd
curl -I http://$EXTERNAL_IP:8080
curl -I https://$EXTERNAL_IP:443
\`\`\`

### PowerShell 테스트
\`\`\`powershell
Test-NetConnection -ComputerName $EXTERNAL_IP -Port 8080
Invoke-WebRequest -Uri "http://$EXTERNAL_IP:8080" -Method Head
\`\`\`

## 3단계: 브라우저 테스트

### URL 테스트
- http://$EXTERNAL_IP:8080
- https://$EXTERNAL_IP:443

### 브라우저 설정 확인
1. 캐시 삭제 (Ctrl+Shift+Delete)
2. 시크릿 모드로 테스트 (Ctrl+Shift+N)
3. 프록시 설정 확인
4. 확장 프로그램 비활성화

## 4단계: Windows 방화벽 확인

### 방화벽 상태 확인
\`\`\`cmd
netsh advfirewall show allprofiles
\`\`\`

### 방화벽 규칙 확인
\`\`\`cmd
netsh advfirewall firewall show rule name=all
\`\`\`

## 문제 해결

### 일반적인 문제들
1. **Windows 방화벽**: 임시로 비활성화 후 테스트
2. **바이러스 백신**: 실시간 보호 임시 비활성화
3. **프록시 설정**: 프록시 사용 안 함으로 설정
4. **네트워크 어댑터**: 네트워크 어댑터 재시작

### 네트워크 진단 명령어
\`\`\`cmd
ipconfig /all
nslookup $EXTERNAL_IP
tracert $EXTERNAL_IP
\`\`\`

EOF

# 13. 네트워크/방화벽 스냅샷 수집
log_info "13. 네트워크/방화벽 스냅샷 수집 중..."
TMPDIR=$(mktemp -d)

# 네트워크 및 방화벽 스냅샷
ss -lntp > "$TMPDIR/ss_lntp.txt" 2>&1 || true
ufw status verbose > "$TMPDIR/ufw_status.txt" 2>&1 || true
ip addr show > "$TMPDIR/ip_addr.txt" 2>&1 || true
ip route show > "$TMPDIR/ip_route.txt" 2>&1 || true

# nginx 설정 덤프 (nginx가 설치된 경우)
if command -v nginx >/dev/null 2>&1; then
    nginx -T > "$TMPDIR/nginx_T.txt" 2>&1 || true
fi

# 네트워크 관리자 정보 (NetworkManager 사용 시)
if command -v nmcli >/dev/null 2>&1; then
    nmcli dev show | sed -n '1,120p' > "$TMPDIR/nmcli_dev_show.txt" 2>&1 || true
fi

# DNS 설정 및 해석 정보
cat /etc/resolv.conf > "$TMPDIR/resolv_conf.txt" 2>&1 || true
dig +short $(hostname) > "$TMPDIR/dns_resolution.txt" 2>&1 || true

# 시간 동기화 상태
timedatectl > "$TMPDIR/timedatectl.txt" 2>&1 || true

# 14. 압축 파일 생성 (네트워크 스냅샷 포함)
log_info "14. 로그 파일 압축 중..."
cd /tmp
tar -czf "network_logs_${TIMESTAMP}.tar.gz" "network_logs_${TIMESTAMP}/" "$TMPDIR" 2>/dev/null || {
    log_warning "압축 실패, 개별 파일로 저장"
}

# 임시 디렉토리 정리
rm -rf "$TMPDIR"

# 결과 출력
log_success "네트워크 진단 로그 수집 완료!"

cat << EOF

${GREEN}=== 수집된 로그 파일 ===${NC}
- 메인 로그: $OUTPUT_FILE
- Windows 가이드: $WINDOWS_GUIDE
- 압축 파일: /tmp/network_logs_${TIMESTAMP}.tar.gz

${BLUE}=== 로그 내용 ===${NC}
- 시스템 정보 및 네트워크 설정
- 포트 상태 및 방화벽 규칙
- 실행 중인 서비스 및 프로세스
- 브라우저 호환성 체크
- Windows 클라이언트 진단 가이드

${YELLOW}=== 사용 방법 ===${NC}
1. 로그 파일을 확인하여 문제 원인 파악
2. Windows 가이드를 따라 클라이언트 측 진단
3. 필요시 로그 파일을 개발팀에 전달

EOF

# 로그 파일 크기 확인
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    log_info "로그 파일 크기: $FILE_SIZE"
fi

log_success "네트워크 진단 완료!"
