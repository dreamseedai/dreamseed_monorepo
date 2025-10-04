# Windows → Linux 서버 연결 문제 해결 가이드

## 🚨 문제 상황
- **증상**: "사이트에 연결할 수 없음" 또는 "응답하는 데 시간이 너무 오래 걸립니다"
- **서버 상태**: Linux 서버는 정상 실행 중 (로컬 접속 가능)
- **클라이언트**: Windows에서 브라우저 접속 실패

## 🔍 원인 분석

### 1. 방화벽 문제 (가장 흔함)
- **Linux 서버**: UFW/iptables가 외부 접속 차단
- **Windows 클라이언트**: Windows 방화벽이 차단

### 2. 포트 정책 문제
- **브라우저 차단 포트**: 6000, 6665-6669, 10080
- **권장 포트**: 80, 443, 8000, 8080, 3000, 5173

### 3. 네트워크 설정 문제
- **바인딩 주소**: 127.0.0.1만 바인딩 (외부 접속 불가)
- **프록시 설정**: Windows 프록시가 차단
- **DNS 문제**: IP 주소 해석 실패

## 🛠️ 해결 방법

### 1단계: 서버 측 확인

#### 포트 정책 검사
```bash
# 포트 정책 스크립트 실행
./network_automation/scripts/ports_policy.sh

# 브라우저 차단 포트 확인
ss -lntp | grep -E ":(6000|6665|6666|6667|6668|6669|10080)"
```

#### 방화벽 설정
```bash
# UFW 상태 확인
sudo ufw status

# 포트 허용 (예: 8080)
sudo ufw allow 8080/tcp
sudo ufw reload

# iptables 확인 (UFW 사용 안 할 경우)
sudo iptables -L -n -v
```

#### 서버 바인딩 확인
```bash
# 올바른 바인딩 (외부 접속 가능)
python3 -m http.server 8080 --bind 0.0.0.0

# 잘못된 바인딩 (로컬만 접속 가능)
python3 -m http.server 8080 --bind 127.0.0.1
```

### 2단계: Windows 클라이언트 확인

#### 기본 연결 테스트
```cmd
# ping 테스트
ping 192.168.68.116

# telnet 테스트
telnet 192.168.68.116 8080

# curl 테스트 (PowerShell)
curl -I http://192.168.68.116:8080
```

#### Windows 방화벽 확인
```cmd
# 방화벽 상태 확인
netsh advfirewall show allprofiles

# 방화벽 임시 비활성화 (테스트용)
netsh advfirewall set allprofiles state off

# 방화벽 재활성화
netsh advfirewall set allprofiles state on
```

#### 브라우저 설정 확인
1. **캐시 삭제**: Ctrl+Shift+Delete
2. **시크릿 모드**: Ctrl+Shift+N
3. **프록시 설정**: 설정 → 고급 → 프록시
4. **확장 프로그램**: 비활성화 후 테스트

### 3단계: 네트워크 진단

#### 자동 진단 스크립트 실행
```bash
# 네트워크 진단 로그 수집
./network_automation/scripts/gather_network_logs.sh

# 자동 배포 및 검증
./network_automation/scripts/deploy_with_network_check.sh 8080
```

#### 수동 진단
```bash
# 서버 IP 확인
hostname -I

# 포트 상태 확인
ss -lntp | grep :8080

# 외부 접속 테스트
curl -I http://$(hostname -I | awk '{print $1}'):8080
```

## 🚀 자동화 솔루션

### 1. 자동 배포 스크립트
```bash
# 네트워크 검증이 포함된 배포
./network_automation/scripts/deploy_with_network_check.sh 8080 web-service
```

**기능**:
- 포트 정책 자동 검사
- UFW 방화벽 자동 설정
- 로컬/외부 연결성 자동 테스트
- Windows 클라이언트 가이드 자동 출력

### 2. 포트 정책 강화
```bash
# 포트 정책 검사
./network_automation/scripts/ports_policy.sh
```

**기능**:
- 브라우저 차단 포트 탐지
- 안전한 포트 권장
- 실행 중인 서비스 포트 검사

### 3. 네트워크 진단 로그
```bash
# 종합 네트워크 진단
./network_automation/scripts/gather_network_logs.sh
```

**수집 정보**:
- 시스템 및 네트워크 설정
- 포트 상태 및 방화벽 규칙
- Windows 클라이언트 진단 가이드
- 브라우저 호환성 체크

## 📋 체크리스트

### 배포 전 확인사항
- [ ] 포트가 브라우저 차단 목록에 없음
- [ ] 안전한 포트 사용 (8000, 8080, 3000, 5173)
- [ ] 0.0.0.0으로 바인딩 설정
- [ ] UFW 방화벽 포트 허용

### 배포 후 확인사항
- [ ] 로컬 접속 테스트 통과
- [ ] 외부 IP 접속 테스트 통과
- [ ] Windows 클라이언트 가이드 제공
- [ ] 네트워크 진단 로그 생성

### 문제 발생 시 확인사항
- [ ] 서버 로그 확인
- [ ] 방화벽 상태 확인
- [ ] 네트워크 진단 로그 분석
- [ ] Windows 클라이언트 진단 가이드 실행

## 🎯 예방 조치

### 1. 표준 포트 사용
```bash
# 권장 포트 목록
DEVELOPMENT_PORTS=(3000 5173 8000)
PRODUCTION_PORTS=(80 443)
INTERNAL_PORTS=(8080 9000)
```

### 2. 자동화된 배포 파이프라인
- 모든 배포 스크립트에 네트워크 검증 포함
- 포트 정책 자동 검사
- 방화벽 자동 설정
- 클라이언트 가이드 자동 생성

### 3. 모니터링 및 알림
- 외부 접속 불가 시 자동 알림
- 포트 정책 위반 시 배포 중단
- 네트워크 진단 로그 자동 수집

## 📞 지원 및 문의

### 문제 보고 시 포함할 정보
1. 네트워크 진단 로그 (`gather_network_logs.sh` 결과)
2. 서버 IP 및 포트 정보
3. Windows 클라이언트 진단 결과
4. 오류 메시지 스크린샷

### 자주 묻는 질문 (FAQ)

**Q: 서버는 정상인데 Windows에서 접속이 안 됩니다.**
A: 방화벽 설정을 확인하세요. `sudo ufw allow [포트]/tcp` 명령어로 포트를 허용하세요.

**Q: 어떤 포트를 사용해야 하나요?**
A: 8000, 8080, 3000, 5173 등 안전한 포트를 사용하세요. 6000, 6665-6669는 브라우저에서 차단됩니다.

**Q: Windows 방화벽을 어떻게 확인하나요?**
A: `netsh advfirewall show allprofiles` 명령어로 확인하거나, 임시로 비활성화하여 테스트하세요.

---

**💡 팁**: 이 가이드의 자동화 스크립트를 사용하면 대부분의 연결 문제를 사전에 방지할 수 있습니다.
