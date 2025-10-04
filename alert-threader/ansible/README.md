# DreamSeed Alert Threader - Ansible 자동화

SOPS 또는 Vault를 사용하여 Alert Threader 환경변수를 안전하게 배포하는 Ansible 플레이북과 역할입니다.

## 🎯 **주요 기능**

### **1. SOPS 모드**
- **Git에 암호화 상태로 저장**: 평문 비밀을 Git에 커밋하지 않음
- **age/PGP 지원**: 하드웨어 보안 저장소와 연계 가능
- **자동 복호화**: 런타임에 자동으로 환경변수 생성
- **원자적 교체**: 임시 파일을 사용한 안전한 교체

### **2. Vault 모드**
- **중앙 비밀저장소**: 모든 비밀을 중앙에서 관리
- **Agent Template**: 자동으로 환경변수 파일 생성
- **동적 갱신**: 비밀 변경 시 자동으로 서비스에 반영
- **감사 로그**: 모든 비밀 접근 기록

### **3. 통합 관리**
- **단일 플레이북**: SOPS/Vault/자동 모드 선택 가능
- **자동 설정**: age 키 생성, Vault Agent 설정 자동화
- **보안 강화**: 파일 권한 및 systemd 하드닝
- **마이그레이션 지원**: 평문 → SOPS → Vault 전환

## 📁 **파일 구조**

```
ansible/
├── inventory/
│   ├── hosts.yaml                    # 인벤토리 파일
│   └── group_vars/
│       └── all.yml                   # 그룹 변수
├── roles/
│   └── alert_threader_env/
│       ├── defaults/main.yml         # 기본 변수
│       ├── tasks/main.yml            # 메인 태스크
│       ├── handlers/main.yml         # 핸들러
│       ├── templates/
│       │   ├── sops.env.enc.j2       # SOPS 암호화 파일 템플릿
│       │   ├── sops.yaml.j2          # SOPS 설정 템플릿
│       │   ├── sops-decrypt.sh.j2    # SOPS 복호화 스크립트
│       │   ├── vault.tpl.j2          # Vault 템플릿
│       │   ├── vault.hcl.j2          # Vault Agent 설정
│       │   └── alert-threader.env.sample.j2  # 샘플 환경 파일
│       └── files/
│           └── vault-agent.service   # Vault Agent 서비스 유닛
├── playbooks/
│   ├── deploy_env.yaml               # 통합 배포 플레이북
│   ├── deploy_sops.yaml              # SOPS 전용 배포
│   ├── deploy_vault.yaml             # Vault 전용 배포
│   └── test_deployment.yaml          # 배포 테스트
├── scripts/
│   ├── install_ansible.sh            # Ansible 설치 스크립트
│   ├── test_connection.sh            # 연결 테스트
│   └── deploy_all.sh                 # 전체 배포 스크립트
├── ansible.cfg                       # Ansible 설정
├── requirements.yml                  # 의존성 정의
└── README.md                         # 이 문서
```

## 🚀 **빠른 시작**

### **1. Ansible 설치**
```bash
cd ansible
chmod +x scripts/install_ansible.sh
./scripts/install_ansible.sh
```

### **2. 인벤토리 설정**
```bash
# inventory/hosts.yaml 수정
vim inventory/hosts.yaml
```

### **3. 변수 설정**
```bash
# inventory/group_vars/all.yml 수정
vim inventory/group_vars/all.yml
```

### **4. 배포 실행**
```bash
# 자동 모드 (group_vars의 threader_mode 사용)
./scripts/deploy_all.sh

# SOPS 모드
./scripts/deploy_all.sh --mode sops

# Vault 모드
./scripts/deploy_all.sh --mode vault

# 테스트 모드
./scripts/deploy_all.sh --test
```

## ⚙️ **설정**

### **인벤토리 설정 (inventory/hosts.yaml)**
```yaml
all:
  hosts:
    threader-1:
      ansible_host: 192.168.68.116
      ansible_user: won
      ansible_ssh_private_key_file: ~/.ssh/id_rsa
    threader-2:
      ansible_host: 192.168.68.117
      ansible_user: won
      ansible_ssh_private_key_file: ~/.ssh/id_rsa
  children:
    staging:
      hosts:
        - threader-1
    production:
      hosts:
        - threader-2
```

### **그룹 변수 설정 (inventory/group_vars/all.yml)**
```yaml
# 비밀 관리 방식 선택
threader_mode: sops  # sops | vault

# 공통 설정
threader_env_path: /run/alert-threader.env
threader_env_keys:
  SLACK_BOT_TOKEN: "xoxb-REDACTED"
  SLACK_CHANNEL: "C0123456789"
  ENVIRONMENT: "staging"
  THREAD_STORE: "file"
  THREAD_STORE_FILE: "/var/lib/alert-threader/threads.json"
  REDIS_URL: "redis://127.0.0.1:6379/0"
  REDIS_KEY_PREFIX: "threader:ts"

# SOPS 설정
sops_age_key: "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqs5p"

# Vault 설정
vault_addr: https://vault.mycorp.local:8200
vault_kv_path: kv/data/alert-threader
```

## 🔧 **사용법**

### **1. 연결 테스트**
```bash
# 모든 호스트 연결 테스트
./scripts/test_connection.sh

# Ansible 직접 사용
ansible all -m ping
```

### **2. 배포 실행**
```bash
# 통합 배포 (자동 모드)
ansible-playbook playbooks/deploy_env.yaml

# SOPS 모드
ansible-playbook playbooks/deploy_sops.yaml

# Vault 모드
ansible-playbook playbooks/deploy_vault.yaml

# 특정 호스트만
ansible-playbook playbooks/deploy_env.yaml --limit threader-1

# 테스트 모드
ansible-playbook playbooks/deploy_env.yaml --check

# 상세 출력
ansible-playbook playbooks/deploy_env.yaml -vvv
```

### **3. 배포 테스트**
```bash
# 배포 검증
ansible-playbook playbooks/test_deployment.yaml

# 특정 호스트만 테스트
ansible-playbook playbooks/test_deployment.yaml --limit threader-1
```

### **4. 스크립트 사용**
```bash
# 전체 배포
./scripts/deploy_all.sh

# SOPS 모드로 배포
./scripts/deploy_all.sh --mode sops

# Vault 모드로 배포
./scripts/deploy_all.sh --mode vault

# 특정 호스트만 배포
./scripts/deploy_all.sh --host threader-1

# 테스트 모드
./scripts/deploy_all.sh --test

# 상세 출력
./scripts/deploy_all.sh --verbose
```

## 🔐 **SOPS 모드**

### **설정**
```yaml
# inventory/group_vars/all.yml
threader_mode: sops
sops_age_key: "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqs5p"
```

### **배포**
```bash
# SOPS 모드로 배포
ansible-playbook playbooks/deploy_sops.yaml

# 또는 스크립트 사용
./scripts/deploy_all.sh --mode sops
```

### **비밀 관리**
```bash
# 비밀 수정
sops /opt/alert-threader-sec/alert-threader.env.enc

# 비밀 확인
sops -d /opt/alert-threader-sec/alert-threader.env.enc

# 서비스 재시작
systemctl restart alert-threader-python
```

## 🔐 **Vault 모드**

### **설정**
```yaml
# inventory/group_vars/all.yml
threader_mode: vault
vault_addr: https://vault.mycorp.local:8200
vault_kv_path: kv/data/alert-threader
```

### **배포**
```bash
# Vault 모드로 배포
ansible-playbook playbooks/deploy_vault.yaml

# 또는 스크립트 사용
./scripts/deploy_all.sh --mode vault
```

### **비밀 관리**
```bash
# Vault에 비밀 저장
vault kv put kv/data/alert-threader \
  SLACK_BOT_TOKEN="xoxb-your-token" \
  SLACK_CHANNEL="C0123456789" \
  ENVIRONMENT="production"

# 비밀 확인
vault kv get kv/data/alert-threader

# 자동으로 /run/alert-threader.env가 업데이트됨
```

## 🧪 **테스트**

### **1. 연결 테스트**
```bash
./scripts/test_connection.sh
```

### **2. 배포 테스트**
```bash
# 테스트 모드로 실행
ansible-playbook playbooks/deploy_env.yaml --check

# 또는 스크립트 사용
./scripts/deploy_all.sh --test
```

### **3. 배포 검증**
```bash
# 배포 후 검증
ansible-playbook playbooks/test_deployment.yaml
```

## 🔄 **마이그레이션**

### **평문 → SOPS**
```bash
# 1. SOPS 모드로 배포
ansible-playbook playbooks/deploy_sops.yaml

# 2. 기존 환경 파일을 SOPS로 암호화
sops -e -i /etc/alert-threader.env
mv /etc/alert-threader.env /opt/alert-threader-sec/alert-threader.env.enc

# 3. 서비스 재시작
systemctl restart alert-threader-python
```

### **평문 → Vault**
```bash
# 1. Vault에 비밀 저장
vault kv put kv/data/alert-threader @/etc/alert-threader.env

# 2. Vault 모드로 배포
ansible-playbook playbooks/deploy_vault.yaml

# 3. 서비스 재시작
systemctl restart alert-threader-python
```

### **SOPS → Vault**
```bash
# 1. SOPS에서 비밀 추출
sops -d /opt/alert-threader-sec/alert-threader.env.enc > /tmp/alert-threader.env

# 2. Vault에 비밀 저장
vault kv put kv/data/alert-threader @/tmp/alert-threader.env

# 3. Vault 모드로 배포
ansible-playbook playbooks/deploy_vault.yaml

# 4. 임시 파일 삭제
rm -f /tmp/alert-threader.env
```

## 🚨 **문제 해결**

### **1. 연결 문제**
```bash
# SSH 연결 테스트
ssh user@target-server

# SSH 키 확인
ssh-keygen -l -f ~/.ssh/id_rsa.pub

# SSH 키 복사
ssh-copy-id user@target-server
```

### **2. SOPS 문제**
```bash
# SOPS 설치 확인
sops --version

# age 키 확인
ls -la ~/.config/sops/age/keys.txt

# 복호화 테스트
sops -d /opt/alert-threader-sec/alert-threader.env.enc
```

### **3. Vault 문제**
```bash
# Vault 연결 확인
vault status

# Vault Agent 상태 확인
systemctl status vault-agent-alert-threader

# Vault Agent 로그 확인
journalctl -u vault-agent-alert-threader -f
```

### **4. 환경변수 문제**
```bash
# 환경변수 파일 확인
cat /run/alert-threader.env

# 권한 확인
ls -la /run/alert-threader.env

# 서비스 상태 확인
systemctl status alert-threader-python
```

## 📊 **성능 비교**

| 방식 | 보안성 | 복잡성 | 자동화 | Git 호환성 | 중앙 관리 |
|------|--------|--------|--------|------------|-----------|
| **SOPS** | 높음 | 낮음 | 중간 | 높음 | 낮음 |
| **Vault** | 매우 높음 | 높음 | 높음 | 중간 | 높음 |

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
6. **✅ 통합 배포**: 원클릭 배포 및 설정
7. **✅ 마이그레이션**: 평문 → SOPS → Vault 전환 지원
8. **✅ 문제 해결**: 상세한 디버깅 가이드
9. **✅ 성능 비교**: 각 방식의 장단점 분석
10. **✅ 포괄적인 문서화**: 설치부터 문제해결까지 완전한 가이드

이제 **엔터프라이즈급 보안**을 갖춘 **Ansible 자동화 시스템**이 완성되었습니다! 🎉

**사용자는 이제 다음 명령어 하나로 전체 시스템을 배포할 수 있습니다:**

```bash
./scripts/deploy_all.sh
```
