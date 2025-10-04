# Alert Threader 통합 Ansible Role

이 문서는 Alert Threader 서비스들을 통합적으로 설치하고 관리하는 Ansible Role에 대한 설명입니다.

## 📋 개요

`threader_install` Role은 Python, Node.js, Go로 구현된 Alert Threader 서비스들을 자동으로 설치하고 관리합니다.

## 🏗️ 구조

```
ansible/roles/threader_install/
├── defaults/main.yml          # 기본 변수
├── tasks/main.yml             # 메인 태스크
├── templates/                 # systemd 서비스 템플릿
│   ├── alert-threader-python.service.j2
│   ├── alert-threader-node.service.j2
│   └── alert-threader-go.service.j2
├── files/                     # 소스 코드 파일
│   ├── python/
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── node/
│   │   └── index.js
│   └── go/
│       ├── main.go
│       └── go.mod
└── handlers/main.yml          # 핸들러
```

## ⚙️ 설정 변수

### 기본 변수 (defaults/main.yml)

```yaml
# 어떤 구현을 설치할지: python | node | go | multi
threader_impl: python

# 서비스 공통
threader_workdir_base: /opt
threader_envfile: /run/alert-threader.env
threader_user: www-data
threader_group: www-data
threader_port: 9009

# 구현별 디렉터리
threader_python_dir: "{{ threader_workdir_base }}/alert-threader-python"
threader_node_dir: "{{ threader_workdir_base }}/alert-threader-node"
threader_go_dir: "{{ threader_workdir_base }}/alert-threader-go"

# 코드 배포 방식: copy | skip
threader_code_mode: copy
```

## 🚀 사용법

### 1. 기본 사용법

```bash
# Python 구현만 설치
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml

# Node.js 구현만 설치
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml --extra-vars "threader_impl=node"

# Go 구현만 설치
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml --extra-vars "threader_impl=go"

# 모든 구현 설치
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader_multi.yaml
```

### 2. 통합 스크립트 사용

```bash
# Python 구현 (기본)
./scripts/deploy_threader.sh

# Node.js 구현
./scripts/deploy_threader.sh --impl=node

# Go 구현
./scripts/deploy_threader.sh --impl=go

# 모든 구현
./scripts/deploy_threader.sh --impl=multi

# SOPS 모드로 Python 설치
./scripts/deploy_threader.sh --mode=SOPS --impl=python

# Vault 모드로 Node.js 설치
./scripts/deploy_threader.sh --mode=VAULT --impl=node

# 테스트 모드
./scripts/deploy_threader.sh --impl=multi --test

# 상세 출력
./scripts/deploy_threader.sh --impl=python --verbose
```

### 3. 개별 서비스 관리

```bash
# 서비스 상태 확인
sudo systemctl status alert-threader-python
sudo systemctl status alert-threader-node
sudo systemctl status alert-threader-go

# 서비스 시작/중지
sudo systemctl start alert-threader-python
sudo systemctl stop alert-threader-python

# 서비스 재시작
sudo systemctl restart alert-threader-python

# 로그 확인
sudo journalctl -u alert-threader-python -f
```

## 🔧 기능

### 1. 자동 의존성 설치

- **Python**: fastapi, uvicorn, httpx, redis
- **Node.js**: express, node-fetch, redis
- **Go**: go-redis/v9

### 2. systemd 서비스 관리

- 자동 시작 설정
- 서비스 재시작 정책
- 보안 강화 옵션
- 환경 변수 파일 사용

### 3. 코드 배포

- 소스 코드 자동 복사
- 의존성 자동 설치
- 빌드 자동화 (Go)

### 4. 포트 설정

- Python: 9009
- Node.js: 9010
- Go: 9011

## 📊 모니터링

### 1. 헬스 체크

```bash
# Python
curl http://localhost:9009/health

# Node.js
curl http://localhost:9010/health

# Go
curl http://localhost:9011/health
```

### 2. 통계 확인

```bash
# Python
curl http://localhost:9009/stats

# Node.js
curl http://localhost:9010/stats

# Go
curl http://localhost:9011/stats
```

### 3. 로그 모니터링

```bash
# 모든 서비스 로그
sudo journalctl -u alert-threader-* -f

# 특정 서비스 로그
sudo journalctl -u alert-threader-python -f
```

## 🔄 업데이트

### 1. 코드 업데이트

```bash
# 코드만 업데이트 (서비스 재시작 없음)
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml --extra-vars "threader_code_mode=copy" --tags "code"

# 코드 업데이트 후 서비스 재시작
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml --extra-vars "threader_code_mode=copy"
```

### 2. 설정 업데이트

```bash
# 환경 변수 업데이트
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_env.yaml

# 서비스 설정 업데이트
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader.yaml
```

## 🧪 테스트

### 1. 배포 테스트

```bash
# 테스트 모드로 실행
./scripts/deploy_threader.sh --impl=multi --test

# 테스트 플레이북 실행
ansible-playbook -i inventory/hosts.yaml playbooks/test_threader.yaml
```

### 2. 기능 테스트

```bash
# Alert 전송 테스트
curl -X POST http://localhost:9009/alert \
  -H "Content-Type: application/json" \
  -d '{
    "status": "firing",
    "alerts": [{
      "labels": {
        "alertname": "TestAlert",
        "severity": "warning"
      },
      "annotations": {
        "summary": "Test Alert Summary",
        "description": "This is a test alert"
      }
    }]
  }'
```

## 🚨 문제 해결

### 1. 서비스 시작 실패

```bash
# 서비스 상태 확인
sudo systemctl status alert-threader-python

# 로그 확인
sudo journalctl -u alert-threader-python -n 50

# 환경 변수 확인
sudo cat /run/alert-threader.env
```

### 2. 의존성 문제

```bash
# Python 의존성 재설치
sudo -u www-data pip3 install -r /opt/alert-threader-python/requirements.txt

# Node.js 의존성 재설치
cd /opt/alert-threader-node && sudo -u www-data npm install

# Go 모듈 재설치
cd /opt/alert-threader-go && sudo -u www-data go mod tidy
```

### 3. 권한 문제

```bash
# 디렉터리 권한 수정
sudo chown -R www-data:www-data /opt/alert-threader-*
sudo chown -R www-data:www-data /var/lib/alert-threader

# 파일 권한 수정
sudo chmod 755 /opt/alert-threader-*
sudo chmod 644 /opt/alert-threader-*/*.py
sudo chmod 644 /opt/alert-threader-*/*.js
sudo chmod 644 /opt/alert-threader-*/*.go
```

## 📈 성능 최적화

### 1. 리소스 제한

```yaml
# systemd 서비스에 추가
LimitNOFILE=65535
LimitNPROC=4096
```

### 2. 로그 로테이션

```bash
# systemd 로그 설정
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/alert-threader.conf << EOF
[Journal]
SystemMaxUse=100M
SystemMaxFileSize=10M
SystemMaxFiles=10
EOF
```

### 3. 모니터링 설정

```bash
# Prometheus 메트릭 수집
curl http://localhost:9009/metrics
curl http://localhost:9010/metrics
curl http://localhost:9011/metrics
```

## 🔐 보안 고려사항

### 1. 서비스 계정

- `www-data` 계정 사용
- 최소 권한 원칙 적용
- 시스템 디렉터리 접근 제한

### 2. 네트워크 보안

- 로컬 바인딩 (0.0.0.0)
- 방화벽 규칙 설정
- SSL/TLS 암호화

### 3. 데이터 보안

- 환경 변수 암호화
- 로그 파일 권한 설정
- 민감한 정보 마스킹

## 📚 추가 자료

- [Alert Threader 메인 문서](../README.md)
- [SOPS 통합 문서](README-secrets-management.md)
- [Ansible 기본 설정](README.md)
- [systemd 서비스 관리](https://systemd.io/)
