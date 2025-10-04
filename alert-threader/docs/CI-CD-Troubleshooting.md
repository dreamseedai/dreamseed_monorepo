# CI/CD Troubleshooting Guide

이 문서는 Alert Threader CI/CD 파이프라인에서 발생할 수 있는 일반적인 문제들과 해결 방법을 제공합니다.

## 📋 목차

- [일반적인 문제](#일반적인-문제)
- [GitHub Actions 문제](#github-actions-문제)
- [GitLab CI 문제](#gitlab-ci-문제)
- [배포 문제](#배포-문제)
- [모니터링 문제](#모니터링-문제)
- [보안 문제](#보안-문제)
- [성능 문제](#성능-문제)
- [디버깅 도구](#디버깅-도구)

## 🚨 일반적인 문제

### 1. 파이프라인 실행 실패

**증상**: 파이프라인이 시작되지 않거나 중간에 실패

**원인**:
- 잘못된 YAML 문법
- 누락된 시크릿 또는 변수
- 권한 문제

**해결 방법**:
```bash
# YAML 문법 검사
yamllint .github/workflows/*.yml
yamllint .gitlab-ci.yml

# 시크릿 확인
gh secret list
gitlab-ci-multi-runner exec shell --job build

# 권한 확인
ls -la ~/.ssh/
chmod 600 ~/.ssh/id_rsa
```

### 2. 의존성 설치 실패

**증상**: 패키지 설치 중 오류 발생

**원인**:
- 네트워크 연결 문제
- 패키지 저장소 문제
- 버전 충돌

**해결 방법**:
```bash
# Python 의존성
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# Node.js 의존성
npm cache clean --force
npm install --no-optional

# Go 모듈
go mod tidy
go mod download
```

## 🔧 GitHub Actions 문제

### 1. 워크플로우 실행 실패

**증상**: GitHub Actions 워크플로우가 실행되지 않음

**해결 방법**:
```bash
# 워크플로우 문법 검사
actionlint .github/workflows/*.yml

# 로컬에서 테스트
act -j build-and-test

# 시크릿 확인
gh secret list
```

### 2. 시크릿 접근 실패

**증상**: 시크릿을 읽을 수 없음

**해결 방법**:
```bash
# 시크릿 재설정
gh secret set SLACK_BOT_TOKEN --body "your_token"

# 권한 확인
gh auth status
```

### 3. 아티팩트 업로드 실패

**증상**: 빌드 아티팩트를 업로드할 수 없음

**해결 방법**:
```yaml
# 아티팩트 크기 제한 확인
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: build-artifacts
    path: dist/
    retention-days: 7
```

## 🚀 GitLab CI 문제

### 1. 파이프라인 실행 실패

**증상**: GitLab CI 파이프라인이 실행되지 않음

**해결 방법**:
```bash
# 파이프라인 문법 검사
gitlab-ci-multi-runner exec shell --job build

# 변수 확인
echo $CI_PROJECT_ID
echo $CI_COMMIT_SHA
```

### 2. Docker 이미지 빌드 실패

**증상**: Docker 이미지를 빌드할 수 없음

**해결 방법**:
```bash
# Docker 데몬 상태 확인
systemctl status docker

# 이미지 빌드 테스트
docker build -t test-image .

# 레지스트리 로그인
docker login registry.gitlab.com
```

### 3. SSH 연결 실패

**증상**: 배포 시 SSH 연결이 실패

**해결 방법**:
```bash
# SSH 키 확인
ssh-keygen -l -f ~/.ssh/id_rsa.pub

# 호스트 키 확인
ssh-keyscan -H target-host >> ~/.ssh/known_hosts

# 연결 테스트
ssh -i ~/.ssh/id_rsa user@target-host
```

## 🚀 배포 문제

### 1. Ansible 배포 실패

**증상**: Ansible 플레이북 실행 실패

**해결 방법**:
```bash
# 플레이북 문법 검사
ansible-playbook --syntax-check playbook.yaml

# 디버그 모드로 실행
ansible-playbook -i inventory/hosts.yaml playbook.yaml -vvv

# 특정 호스트만 실행
ansible-playbook -i inventory/hosts.yaml playbook.yaml -l target-host
```

### 2. 서비스 시작 실패

**증상**: 배포된 서비스가 시작되지 않음

**해결 방법**:
```bash
# 서비스 상태 확인
systemctl status alert-threader-python

# 로그 확인
journalctl -u alert-threader-python -f

# 서비스 재시작
systemctl restart alert-threader-python
```

### 3. 포트 충돌

**증상**: 포트가 이미 사용 중

**해결 방법**:
```bash
# 포트 사용 확인
netstat -tlnp | grep :9009

# 프로세스 종료
kill -9 $(lsof -t -i:9009)

# 포트 변경
# playbook.yaml에서 port 변수 수정
```

## 📊 모니터링 문제

### 1. Prometheus 연결 실패

**증상**: Prometheus가 메트릭을 수집할 수 없음

**해결 방법**:
```bash
# Prometheus 상태 확인
curl http://localhost:9090/-/healthy

# 설정 파일 검증
promtool check config prometheus.yml

# 서비스 재시작
systemctl restart prometheus
```

### 2. Grafana 대시보드 문제

**증상**: Grafana 대시보드가 표시되지 않음

**해결 방법**:
```bash
# Grafana 상태 확인
curl http://localhost:3000/api/health

# 데이터소스 확인
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  http://localhost:3000/api/datasources
```

### 3. Alertmanager 알림 실패

**증상**: 알림이 전송되지 않음

**해결 방법**:
```bash
# Alertmanager 상태 확인
curl http://localhost:9093/-/healthy

# 설정 파일 검증
amtool check-config alertmanager.yml

# 알림 규칙 확인
amtool alert query
```

## 🔒 보안 문제

### 1. 보안 스캔 실패

**증상**: 보안 스캔이 실패하거나 취약점 발견

**해결 방법**:
```bash
# Bandit 실행
bandit -r . -f json -o bandit-results.json

# Safety 실행
safety check --json --output safety-results.json

# Trivy 실행
trivy fs --format json --output trivy-results.json .
```

### 2. 시크릿 노출

**증상**: 시크릿이 로그에 노출됨

**해결 방법**:
```bash
# 로그에서 시크릿 검색
grep -r "password\|token\|key" logs/

# 시크릿 재생성
# 모든 노출된 시크릿 재생성

# 로그 정리
# 민감한 정보가 포함된 로그 삭제
```

### 3. SSL/TLS 인증서 문제

**증상**: SSL 인증서 오류

**해결 방법**:
```bash
# 인증서 유효성 확인
openssl x509 -in certificate.crt -text -noout

# 인증서 갱신
certbot renew --dry-run

# 인증서 설치
certbot --nginx -d example.com
```

## ⚡ 성능 문제

### 1. 빌드 시간 과다

**증상**: 빌드가 너무 오래 걸림

**해결 방법**:
```yaml
# 캐시 사용
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# 병렬 빌드
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
```

### 2. 테스트 실행 시간 과다

**증상**: 테스트가 너무 오래 걸림

**해결 방법**:
```bash
# 테스트 병렬 실행
pytest -n auto

# 특정 테스트만 실행
pytest tests/unit/

# 테스트 타임아웃 설정
pytest --timeout=300
```

### 3. 메모리 사용량 과다

**증상**: 메모리 부족으로 빌드 실패

**해결 방법**:
```yaml
# 메모리 제한 설정
- name: Build with memory limit
  run: |
    ulimit -v 2097152  # 2GB limit
    make build
```

## 🛠️ 디버깅 도구

### 1. 로그 분석

```bash
# GitHub Actions 로그
gh run view --log

# GitLab CI 로그
gitlab-ci-multi-runner exec shell --job build

# 시스템 로그
journalctl -u service-name -f
```

### 2. 네트워크 디버깅

```bash
# 네트워크 연결 확인
netstat -tlnp
ss -tlnp

# DNS 확인
nslookup example.com
dig example.com

# 포트 스캔
nmap -p 9009-9011 localhost
```

### 3. 성능 프로파일링

```bash
# CPU 사용량
top -p $(pgrep python)

# 메모리 사용량
ps aux --sort=-%mem | head

# 디스크 I/O
iotop
```

### 4. 컨테이너 디버깅

```bash
# 컨테이너 상태 확인
docker ps -a

# 컨테이너 로그
docker logs container-name

# 컨테이너 내부 접근
docker exec -it container-name /bin/bash
```

## 📞 지원 및 문의

문제가 해결되지 않으면:

1. **로그 수집**: 관련 로그 파일 수집
2. **환경 정보**: OS, 버전, 설정 정보 수집
3. **재현 단계**: 문제 재현 방법 문서화
4. **이슈 생성**: GitHub/GitLab에 이슈 생성

## 📚 추가 리소스

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [GitLab CI/CD 문서](https://docs.gitlab.com/ee/ci/)
- [Ansible 문서](https://docs.ansible.com/)
- [Docker 문서](https://docs.docker.com/)
- [Prometheus 문서](https://prometheus.io/docs/)