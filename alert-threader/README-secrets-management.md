# DreamSeed Alert Threader - 비밀 관리 시스템 가이드

`/etc/alert-threader.env`를 SOPS/Vault로 암호화 관리하는 엔터프라이즈급 보안 시스템입니다.

## 🎯 **지원하는 비밀 관리 방식**

### **1. SOPS (Secrets OPerationS)**
- **Git에 암호화 상태로 저장**: 평문 비밀을 Git에 커밋하지 않음
- **age/PGP 지원**: 하드웨어 보안 저장소와 연계 가능
- **런타임 복호화**: 서비스 시작 시 자동으로 복호화
- **원자적 교체**: 임시 파일을 사용한 안전한 교체

### **2. HashiCorp Vault**
- **중앙 비밀저장소**: 모든 비밀을 중앙에서 관리
- **Agent Template**: 자동으로 환경변수 파일 생성
- **동적 갱신**: 비밀 변경 시 자동으로 서비스에 반영
- **감사 로그**: 모든 비밀 접근 기록

## 🚀 **빠른 시작**

### **통합 설치 (권장)**
```bash
cd alert-threader
chmod +x install-secrets-management.sh
sudo ./install-secrets-management.sh
```

설치 과정에서 다음을 선택할 수 있습니다:
- 비밀 관리 방식 (SOPS/Vault/둘 다)
- Slack Bot Token
- Slack Channel ID
- 환경 설정

## 📁 **파일 구조**

```
alert-threader/
├── ops-secrets-sops/
│   ├── .sops.yaml                           # SOPS 설정 규칙
│   ├── alert-threader.env.enc               # 암호화된 환경 파일
│   └── alert-threader-sops-decrypt.sh       # 복호화 스크립트
├── ops-secrets-vault/
│   ├── alert-threader.tpl                   # Vault 템플릿
│   └── alert-threader.hcl                   # Vault Agent 설정
├── ops-services-alert-threader-python-sops.service    # SOPS 서비스 유닛
├── ops-services-alert-threader-python-vault.service   # Vault 서비스 유닛
├── ops-services-vault-agent-alert-threader.service    # Vault Agent 유닛
├── install-secrets-management.sh            # 통합 설치 스크립트
└── README-secrets-management.md             # 이 문서
```

## 🔐 **SOPS 방식**

### **설치 및 설정**
```bash
# 1. SOPS 설치
curl -sSL https://github.com/getsops/sops/releases/latest/download/sops-v3.8.1.linux.amd64 -o /tmp/sops
sudo mv /tmp/sops /usr/local/bin/sops
sudo chmod +x /usr/local/bin/sops

# 2. age 키 생성
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt

# 3. 설정 파일 복사
sudo mkdir -p /opt/alert-threader-sec
sudo cp ops-secrets-sops/.sops.yaml /opt/alert-threader-sec/
sudo cp ops-secrets-sops/alert-threader.env.enc /opt/alert-threader-sec/
sudo chown -R root:root /opt/alert-threader-sec
sudo chmod 0640 /opt/alert-threader-sec/alert-threader.env.enc

# 4. 복호화 스크립트 설치
sudo cp ops-secrets-sops/alert-threader-sops-decrypt.sh /usr/local/sbin/alert-threader-sops-decrypt
sudo chmod +x /usr/local/sbin/alert-threader-sops-decrypt

# 5. 서비스 파일 복사
sudo cp ops-services-alert-threader-python-sops.service /etc/systemd/system/alert-threader-python.service
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader-python
```

### **비밀 관리**
```bash
# 비밀 수정
sudo sops /opt/alert-threader-sec/alert-threader.env.enc

# 비밀 확인
sudo sops -d /opt/alert-threader-sec/alert-threader.env.enc

# 서비스 재시작
sudo systemctl restart alert-threader-python
```

### **SOPS 설정 파일**
```yaml
# .sops.yaml
creation_rules:
  - path_regex: .*\.env\.enc$
    age: ["age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqs5p"]
    encrypted_regex: '^(SLACK_BOT_TOKEN|SLACK_CHANNEL|ENVIRONMENT|THREAD_STORE|THREAD_STORE_FILE|REDIS_URL|REDIS_KEY_PREFIX)$'
    key_groups:
      - age: ["age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqs5p"]
```

## 🔐 **Vault 방식**

### **설치 및 설정**
```bash
# 1. Vault 설치
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt update
sudo apt install -y vault

# 2. Vault Agent 설정 디렉터리 생성
sudo mkdir -p /etc/vault-agent.d
sudo mkdir -p /run/vault

# 3. 설정 파일 복사
sudo cp ops-secrets-vault/alert-threader.tpl /etc/vault-agent.d/
sudo cp ops-secrets-vault/alert-threader.hcl /etc/vault-agent.d/
sudo chown -R root:root /etc/vault-agent.d
sudo chmod 0640 /etc/vault-agent.d/alert-threader.tpl
sudo chmod 0640 /etc/vault-agent.d/alert-threader.hcl

# 4. 서비스 파일 복사
sudo cp ops-services-vault-agent-alert-threader.service /etc/systemd/system/
sudo cp ops-services-alert-threader-python-vault.service /etc/systemd/system/alert-threader-python.service
sudo systemctl daemon-reload

# 5. Vault Agent 시작
sudo systemctl enable --now vault-agent-alert-threader
sleep 5
sudo systemctl enable --now alert-threader-python
```

### **비밀 관리**
```bash
# Vault에 비밀 저장
vault kv put kv/alert-threader \
  SLACK_BOT_TOKEN="xoxb-your-token" \
  SLACK_CHANNEL="C0123456789" \
  ENVIRONMENT="production" \
  THREAD_STORE="redis" \
  THREAD_STORE_FILE="/var/lib/alert-threader/threads.json" \
  REDIS_URL="redis://127.0.0.1:6379/0" \
  REDIS_KEY_PREFIX="threader:ts"

# 비밀 확인
vault kv get kv/alert-threader

# 자동으로 /run/alert-threader.env가 업데이트됨
```

### **Vault Agent 설정**
```hcl
# alert-threader.hcl
exit_after_auth = false
pid_file = "/run/vault-agent-alert-threader.pid"

vault {
  address = "https://vault.mycorp.local:8200"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/etc/vault-agent.d/role_id"
      secret_id_file_path = "/etc/vault-agent.d/secret_id"
    }
  }

  sink "file" {
    config = {
      path = "/run/vault/.token"
    }
  }
}

template {
  source      = "/etc/vault-agent.d/alert-threader.tpl"
  destination = "/run/alert-threader.env"
  perms       = 0640
  user        = "root"
  group       = "root"
  create_dest_dirs = true
}
```

## 🧪 **테스트**

### **SOPS 테스트**
```bash
# 복호화 테스트
sudo /usr/local/sbin/alert-threader-sops-decrypt /opt/alert-threader-sec/alert-threader.env.enc

# 환경변수 확인
sudo cat /run/alert-threader.env

# 서비스 상태 확인
sudo systemctl status alert-threader-python
```

### **Vault 테스트**
```bash
# Vault Agent 상태 확인
sudo systemctl status vault-agent-alert-threader

# 템플릿 렌더링 확인
sudo cat /run/alert-threader.env

# 서비스 상태 확인
sudo systemctl status alert-threader-python
```

### **통합 테스트**
```bash
# 헬스체크
curl http://localhost:9009/health | jq .

# 통계 확인
curl http://localhost:9009/stats | jq .

# 비밀 변경 테스트
# SOPS: sudo sops /opt/alert-threader-sec/alert-threader.env.enc
# Vault: vault kv put kv/alert-threader SLACK_BOT_TOKEN="new_token"
```

## 🔧 **서비스 관리**

### **SOPS 방식**
```bash
# 서비스 시작/중지
sudo systemctl start alert-threader-python
sudo systemctl stop alert-threader-python
sudo systemctl restart alert-threader-python

# 로그 확인
sudo journalctl -u alert-threader-python -f

# 비밀 업데이트
sudo sops /opt/alert-threader-sec/alert-threader.env.enc
sudo systemctl restart alert-threader-python
```

### **Vault 방식**
```bash
# Vault Agent 시작/중지
sudo systemctl start vault-agent-alert-threader
sudo systemctl stop vault-agent-alert-threader
sudo systemctl restart vault-agent-alert-threader

# 서비스 시작/중지
sudo systemctl start alert-threader-python
sudo systemctl stop alert-threader-python
sudo systemctl restart alert-threader-python

# 로그 확인
sudo journalctl -u vault-agent-alert-threader -f
sudo journalctl -u alert-threader-python -f

# 비밀 업데이트 (자동 반영)
vault kv put kv/alert-threader SLACK_BOT_TOKEN="new_token"
```

## 📊 **성능 비교**

| 방식 | 보안성 | 복잡성 | 자동화 | Git 호환성 | 중앙 관리 |
|------|--------|--------|--------|------------|-----------|
| **SOPS** | 높음 | 낮음 | 중간 | 높음 | 낮음 |
| **Vault** | 매우 높음 | 높음 | 높음 | 중간 | 높음 |

## 🚨 **문제 해결**

### **1. SOPS 문제**
```bash
# age 키 확인
ls -la ~/.config/sops/age/keys.txt

# SOPS 버전 확인
sops --version

# 복호화 테스트
sops -d /opt/alert-threader-sec/alert-threader.env.enc

# 권한 확인
ls -la /opt/alert-threader-sec/alert-threader.env.enc
```

### **2. Vault 문제**
```bash
# Vault Agent 상태 확인
sudo systemctl status vault-agent-alert-threader

# Vault 연결 확인
vault status

# 템플릿 렌더링 확인
sudo cat /run/alert-threader.env

# 로그 확인
sudo journalctl -u vault-agent-alert-threader -f
```

### **3. 공통 문제**
```bash
# 환경변수 파일 확인
sudo cat /run/alert-threader.env

# 서비스 상태 확인
sudo systemctl status alert-threader-python

# 포트 확인
netstat -tlnp | grep :9009

# 헬스체크
curl http://localhost:9009/health
```

## 🔄 **마이그레이션**

### **평문 → SOPS**
```bash
# 1. 기존 환경 파일 백업
sudo cp /etc/alert-threader.env /etc/alert-threader.env.backup

# 2. SOPS 설정
sudo mkdir -p /opt/alert-threader-sec
sudo cp /etc/alert-threader.env /opt/alert-threader-sec/alert-threader.env.enc
sudo sops -e -i /opt/alert-threader-sec/alert-threader.env.enc

# 3. 서비스 파일 교체
sudo cp ops-services-alert-threader-python-sops.service /etc/systemd/system/alert-threader-python.service
sudo systemctl daemon-reload
sudo systemctl restart alert-threader-python
```

### **평문 → Vault**
```bash
# 1. 기존 환경 파일 백업
sudo cp /etc/alert-threader.env /etc/alert-threader.env.backup

# 2. Vault에 비밀 저장
vault kv put kv/alert-threader @/etc/alert-threader.env

# 3. 서비스 파일 교체
sudo cp ops-services-alert-threader-python-vault.service /etc/systemd/system/alert-threader-python.service
sudo cp ops-services-vault-agent-alert-threader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start vault-agent-alert-threader
sudo systemctl restart alert-threader-python
```

### **SOPS → Vault**
```bash
# 1. SOPS에서 비밀 추출
sudo sops -d /opt/alert-threader-sec/alert-threader.env.enc > /tmp/alert-threader.env

# 2. Vault에 비밀 저장
vault kv put kv/alert-threader @/tmp/alert-threader.env

# 3. 서비스 파일 교체
sudo cp ops-services-alert-threader-python-vault.service /etc/systemd/system/alert-threader-python.service
sudo cp ops-services-vault-agent-alert-threader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start vault-agent-alert-threader
sudo systemctl restart alert-threader-python

# 4. 임시 파일 삭제
rm -f /tmp/alert-threader.env
```

## 🗑️ **제거**

### **SOPS 제거**
```bash
# 서비스 중지
sudo systemctl stop alert-threader-python
sudo systemctl disable alert-threader-python

# 파일 제거
sudo rm -rf /opt/alert-threader-sec
sudo rm /usr/local/sbin/alert-threader-sops-decrypt
sudo rm /etc/systemd/system/alert-threader-python.service

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

### **Vault 제거**
```bash
# 서비스 중지
sudo systemctl stop alert-threader-python
sudo systemctl stop vault-agent-alert-threader
sudo systemctl disable alert-threader-python
sudo systemctl disable vault-agent-alert-threader

# 파일 제거
sudo rm -rf /etc/vault-agent.d
sudo rm /etc/systemd/system/alert-threader-python.service
sudo rm /etc/systemd/system/vault-agent-alert-threader.service

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

## 🎯 **사용 시나리오**

### **1. 개발 환경**
- **SOPS**: 빠른 설정, Git 호환성
- **age 키**: 로컬 개발용

### **2. 스테이징 환경**
- **SOPS**: Git 기반 배포
- **age 키**: 팀 공유

### **3. 프로덕션 환경**
- **Vault**: 중앙 관리, 감사 로그
- **AppRole**: 자동 인증

### **4. 하이브리드 환경**
- **SOPS**: 개발/스테이징
- **Vault**: 프로덕션

## 📄 **라이선스**

MIT License

---

## 🎉 **완성된 기능**

1. **✅ SOPS 지원**: age/PGP 키로 암호화, Git 호환성
2. **✅ Vault 지원**: 중앙 비밀저장소, Agent Template
3. **✅ 자동 복호화**: 런타임에 자동으로 환경변수 생성
4. **✅ 원자적 교체**: 임시 파일을 사용한 안전한 교체
5. **✅ 보안 강화**: 파일 권한 및 systemd 하드닝
6. **✅ 통합 설치**: 원클릭 설치 및 설정
7. **✅ 마이그레이션**: 평문 → SOPS → Vault 전환 지원
8. **✅ 문제 해결**: 상세한 디버깅 가이드
9. **✅ 성능 비교**: 각 방식의 장단점 분석
10. **✅ 포괄적인 문서화**: 설치부터 문제해결까지 완전한 가이드

이제 **엔터프라이즈급 보안**을 갖춘 **비밀 관리 시스템**이 완성되었습니다! 🎉

**사용자는 이제 다음 명령어 하나로 전체 시스템을 배포할 수 있습니다:**

```bash
sudo ./install-secrets-management.sh
```
