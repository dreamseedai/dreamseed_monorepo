# Alert Threader 포트 분리 및 멀티 인스턴스 가이드

이 문서는 Alert Threader 서비스들을 개별 포트로 분리하고 멀티 인스턴스를 운영하는 방법을 설명합니다.

## 📋 개요

### 기본 포트 설정
- **Python**: 9009
- **Node.js**: 9010  
- **Go**: 9011

### 멀티 인스턴스 지원
- 템플릿 유닛(`alert-threader@.service`) 사용
- 인스턴스별 독립적인 포트 및 디렉터리
- 언어별 자동 감지 및 실행

## 🚀 사용법

### 1. 기본 포트 분리 배포

```bash
# 모든 서비스를 기본 포트로 배포
./scripts/deploy_threader_ports.sh

# 커스텀 포트로 배포
./scripts/deploy_threader_ports.sh \
  --python-port=8009 \
  --node-port=8010 \
  --go-port=8011

# Python만 특정 포트로 배포
./scripts/deploy_threader_ports.sh \
  --impl=python \
  --python-port=8009
```

### 2. 멀티 인스턴스 배포

```bash
# 멀티 인스턴스 플레이북 실행
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader_multi_instance.yaml

# 커스텀 인스턴스 설정으로 배포
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader_multi_instance.yaml \
  --extra-vars '{
    "threader_instances": [
      {"name": "py-primary", "impl": "python", "port": 9009},
      {"name": "py-backup", "impl": "python", "port": 9008},
      {"name": "node-primary", "impl": "node", "port": 9010},
      {"name": "go-primary", "impl": "go", "port": 9011}
    ]
  }'
```

### 3. Ansible 변수 설정

#### 포트 분리 설정
```yaml
# inventory/group_vars/all.yml
threader_impl: multi
threader_python_port: 9009
threader_node_port: 9010
threader_go_port: 9011
```

#### 멀티 인스턴스 설정
```yaml
# inventory/group_vars/all.yml
threader_instances:
  - name: py-primary
    impl: python
    port: 9009
  - name: py-backup
    impl: python
    port: 9008
  - name: node-primary
    impl: node
    port: 9010
  - name: go-primary
    impl: go
    port: 9011
```

## 🔧 고급 설정

### 1. 인스턴스별 환경 변수

각 인스턴스는 독립적인 환경 파일을 가질 수 있습니다:

```bash
# 인스턴스별 환경 파일
/etc/alert-threader.d/py-primary.env
/etc/alert-threader.d/py-backup.env
/etc/alert-threader.d/node-primary.env
/etc/alert-threader.d/go-primary.env
```

예시 내용:
```bash
# /etc/alert-threader.d/py-primary.env
PORT=9009
HOST=0.0.0.0
SLACK_CHANNEL=C0123456789
```

### 2. 서비스 관리

#### 기본 서비스 (단일 인스턴스)
```bash
# Python 서비스
sudo systemctl status alert-threader-python
sudo systemctl restart alert-threader-python

# Node.js 서비스
sudo systemctl status alert-threader-node
sudo systemctl restart alert-threader-node

# Go 서비스
sudo systemctl status alert-threader-go
sudo systemctl restart alert-threader-go
```

#### 멀티 인스턴스 서비스
```bash
# 특정 인스턴스 관리
sudo systemctl status alert-threader@py-primary
sudo systemctl restart alert-threader@py-primary

# 모든 인스턴스 관리
sudo systemctl status alert-threader@*
sudo systemctl restart alert-threader@*
```

### 3. 로그 모니터링

```bash
# 모든 서비스 로그
sudo journalctl -u alert-threader-* -f

# 특정 서비스 로그
sudo journalctl -u alert-threader-python -f
sudo journalctl -u alert-threader-node -f
sudo journalctl -u alert-threader-go -f

# 멀티 인스턴스 로그
sudo journalctl -u alert-threader@py-primary -f
sudo journalctl -u alert-threader@node-primary -f
```

## 📊 모니터링 및 헬스체크

### 1. 서비스별 헬스체크

```bash
# Python (포트 9009)
curl http://localhost:9009/health
curl http://localhost:9009/stats

# Node.js (포트 9010)
curl http://localhost:9010/health
curl http://localhost:9010/stats

# Go (포트 9011)
curl http://localhost:9011/health
curl http://localhost:9011/stats
```

### 2. 멀티 인스턴스 헬스체크

```bash
# 모든 인스턴스 헬스체크
for port in 9009 9008 9010 9011; do
  echo "Testing port $port..."
  curl -s http://localhost:$port/health || echo "Port $port failed"
done
```

### 3. Alertmanager 설정

#### 단일 서비스 사용
```yaml
# alertmanager.yml
receivers:
  - name: threader-python
    webhook_configs:
      - url: http://127.0.0.1:9009/alert
        send_resolved: true
```

#### 멀티 인스턴스 사용 (로드밸런싱)
```yaml
# alertmanager.yml
receivers:
  - name: threader-multi
    webhook_configs:
      - url: http://127.0.0.1:9009/alert  # Python primary
        send_resolved: true
      - url: http://127.0.0.1:9010/alert  # Node.js primary
        send_resolved: true
      - url: http://127.0.0.1:9011/alert  # Go primary
        send_resolved: true
```

## 🔄 업데이트 및 유지보수

### 1. 코드 업데이트

```bash
# 단일 서비스 업데이트
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader_ports.yaml \
  --extra-vars "threader_code_mode=copy"

# 멀티 인스턴스 업데이트
ansible-playbook -i inventory/hosts.yaml playbooks/deploy_threader_multi_instance.yaml \
  --extra-vars "threader_code_mode=copy"
```

### 2. 포트 변경

```bash
# 포트 변경 후 재배포
./scripts/deploy_threader_ports.sh \
  --python-port=8009 \
  --node-port=8010 \
  --go-port=8011
```

### 3. 인스턴스 추가/제거

```yaml
# inventory/group_vars/all.yml에 인스턴스 추가
threader_instances:
  - name: py-primary
    impl: python
    port: 9009
  - name: py-backup
    impl: python
    port: 9008
  - name: node-primary
    impl: node
    port: 9010
  - name: go-primary
    impl: go
    port: 9011
  - name: py-test  # 새 인스턴스 추가
    impl: python
    port: 9007
```

## 🚨 문제 해결

### 1. 포트 충돌

```bash
# 포트 사용 확인
sudo netstat -tlnp | grep -E ":(9009|9010|9011|9008|9007)"

# 프로세스 확인
sudo lsof -i :9009
sudo lsof -i :9010
sudo lsof -i :9011
```

### 2. 서비스 시작 실패

```bash
# 서비스 상태 확인
sudo systemctl status alert-threader-python
sudo systemctl status alert-threader-node
sudo systemctl status alert-threader-go

# 로그 확인
sudo journalctl -u alert-threader-python -n 50
sudo journalctl -u alert-threader-node -n 50
sudo journalctl -u alert-threader-go -n 50
```

### 3. 멀티 인스턴스 문제

```bash
# 인스턴스 상태 확인
sudo systemctl status alert-threader@*

# 특정 인스턴스 로그
sudo journalctl -u alert-threader@py-primary -n 50

# 인스턴스 디렉터리 확인
ls -la /opt/alert-threader-*
```

## 📈 성능 최적화

### 1. 리소스 제한

```yaml
# inventory/group_vars/all.yml
threader_security:
  limit_nofile: 65535
  limit_nproc: 4096
  memory_limit: "512M"
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

### 1. 포트 보안

```bash
# UFW 방화벽 설정
sudo ufw allow 9009/tcp
sudo ufw allow 9010/tcp
sudo ufw allow 9011/tcp
sudo ufw status
```

### 2. 서비스 계정

- `www-data` 계정 사용
- 최소 권한 원칙 적용
- 시스템 디렉터리 접근 제한

### 3. 네트워크 보안

- 로컬 바인딩 (0.0.0.0)
- 방화벽 규칙 설정
- SSL/TLS 암호화

## 📚 추가 자료

- [Alert Threader 메인 문서](../README.md)
- [Ansible 기본 설정](README.md)
- [멀티 인스턴스 템플릿](templates/alert-threader@.service.j2)
- [포트 기반 배포 스크립트](scripts/deploy_threader_ports.sh)
