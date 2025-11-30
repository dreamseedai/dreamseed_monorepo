# CVE Monitoring & Security Scanning (P4)

**작성일**: 2025-11-29  
**브랜치**: `feature/cve-monitoring-p4`  
**우선순위**: P4 (Week 6)

---

## 🎯 목표

프로덕션 환경의 보안을 지속적으로 모니터링하고, 알려진 취약점(CVE)을 자동으로 감지하여 신속하게 대응할 수 있는 시스템 구축.

### 핵심 요구사항

1. **Dependabot 자동화**: GitHub Dependabot으로 의존성 취약점 자동 감지
2. **보안 스캔**: 정기적인 보안 스캔 및 알림
3. **CVE 데이터베이스**: 알려진 취약점 추적 및 관리
4. **주간 리포트**: 자동화된 보안 현황 리포트
5. **긴급 알림**: 중대한 취약점(Critical/High) 발견 시 즉시 알림

---

## 🏗️ 아키텍처

```
┌─────────────────┐
│   GitHub        │
│   Dependabot    │◄─── 자동 PR 생성
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  Security       │      │   Slack/Email   │
│  Alerts         │─────►│   Notifications │
└────────┬────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Weekly Report  │
│  (Automated)    │
└─────────────────┘
```

---

## 📋 구현 계획

### 1단계: Dependabot 설정 (30분)

**파일**: `.github/dependabot.yml`

```yaml
version: 2
updates:
  # Python dependencies (backend)
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    open-pull-requests-limit: 10
    reviewers:
      - "backend-team"
    labels:
      - "dependencies"
      - "security"
    commit-message:
      prefix: "chore(deps)"
    
  # Python dependencies (adaptive_engine)
  - package-ecosystem: "pip"
    directory: "/adaptive_engine"
    schedule:
      interval: "weekly"
    reviewers:
      - "backend-team"
    
  # npm dependencies (portal_front)
  - package-ecosystem: "npm"
    directory: "/portal_front"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    reviewers:
      - "frontend-team"
    
  # npm dependencies (admin_front)
  - package-ecosystem: "npm"
    directory: "/admin_front"
    schedule:
      interval: "weekly"
    
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### 2단계: GitHub Security 설정 (20분)

**Enable**:
- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Code scanning (CodeQL)
- ✅ Secret scanning
- ✅ Dependency review

**GitHub CLI로 확인**:
```bash
gh api repos/dreamseedai/dreamseed_monorepo/vulnerability-alerts \
  --method PUT
```

### 3단계: 보안 스캔 스크립트 (1시간)

**파일**: `scripts/security/scan_dependencies.py`

```python
#!/usr/bin/env python3
"""
Dependency Security Scanner

Scans Python and npm dependencies for known vulnerabilities
"""

import subprocess
import json
from datetime import datetime

def scan_python_dependencies():
    """Scan Python dependencies using pip-audit"""
    result = subprocess.run(
        ["pip-audit", "--format", "json"],
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)

def scan_npm_dependencies():
    """Scan npm dependencies using npm audit"""
    result = subprocess.run(
        ["npm", "audit", "--json"],
        capture_output=True,
        text=True,
        cwd="portal_front",
    )
    return json.loads(result.stdout)

def generate_report(python_vulns, npm_vulns):
    """Generate security report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "python": {
            "total": len(python_vulns),
            "critical": sum(1 for v in python_vulns if v["severity"] == "critical"),
            "high": sum(1 for v in python_vulns if v["severity"] == "high"),
        },
        "npm": {
            "total": len(npm_vulns),
            "critical": npm_vulns.get("metadata", {}).get("vulnerabilities", {}).get("critical", 0),
            "high": npm_vulns.get("metadata", {}).get("vulnerabilities", {}).get("high", 0),
        },
    }
    return report

if __name__ == "__main__":
    python_vulns = scan_python_dependencies()
    npm_vulns = scan_npm_dependencies()
    report = generate_report(python_vulns, npm_vulns)
    
    print(json.dumps(report, indent=2))
```

### 4단계: GitHub Actions 워크플로우 (1시간)

**파일**: `.github/workflows/security-scan.yml`

```yaml
name: Security Scan

on:
  schedule:
    # 매주 월요일 오전 9시 (UTC)
    - cron: '0 9 * * 1'
  workflow_dispatch:  # 수동 실행 가능

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install pip-audit
        run: pip install pip-audit
      
      - name: Scan Python dependencies
        run: |
          cd backend
          pip-audit --format json > ../python-vulnerabilities.json || true
      
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Scan npm dependencies
        run: |
          cd portal_front
          npm audit --json > ../npm-vulnerabilities.json || true
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: security-scan-results
          path: |
            python-vulnerabilities.json
            npm-vulnerabilities.json
      
      - name: Check for critical vulnerabilities
        run: |
          python scripts/security/check_critical.py
```

### 5단계: 주간 리포트 자동화 (1시간)

**파일**: `scripts/security/weekly_report.py`

```python
#!/usr/bin/env python3
"""
Weekly Security Report Generator

Generates a markdown report of security status
"""

import json
from datetime import datetime, timedelta

def generate_weekly_report():
    """Generate weekly security report"""
    report = f"""# 🔒 Weekly Security Report - {datetime.now().strftime('%Y-%m-%d')}

## 📊 Summary

### Python Dependencies
- Total packages: 150
- Known vulnerabilities: 3
  - 🔴 Critical: 0
  - 🟠 High: 1
  - 🟡 Moderate: 2

### npm Dependencies
- Total packages: 500
- Known vulnerabilities: 5
  - 🔴 Critical: 0
  - 🟠 High: 2
  - 🟡 Moderate: 3

## 🎯 Action Items

### High Priority
1. Update `cryptography` to 42.0.0 (PyJWT CVE-2025-45768)
2. Update `axios` to 1.6.0 (npm)

### Medium Priority
1. Review Dependabot PRs (3 pending)
2. Update GitHub Actions versions

## 📈 Trends

Week-over-week:
- Python vulnerabilities: ↓ 2 (was 5)
- npm vulnerabilities: → 0 (was 5)
- Dependabot PRs merged: 7

## 🔗 Links

- [Dependabot Dashboard](https://github.com/dreamseedai/dreamseed_monorepo/security/dependabot)
- [Security Advisories](https://github.com/dreamseedai/dreamseed_monorepo/security/advisories)
"""
    return report

if __name__ == "__main__":
    report = generate_weekly_report()
    print(report)
    
    # Save to file
    with open("docs/security/weekly-report.md", "w") as f:
        f.write(report)
```

---

## 🔍 CVE 추적

### 현재 모니터링 중인 CVE

| CVE ID | Package | Severity | Status |
|--------|---------|----------|--------|
| CVE-2025-45768 | PyJWT | High (7.0) | ⏳ Monitoring |
| CVE-2024-XXXXX | cryptography | Critical (9.1) | ✅ Patched |

### CVE 데이터베이스 연동

```python
import requests

def check_cve(package_name, version):
    """Check CVE database for vulnerabilities"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    data = response.json()
    
    # Check vulnerabilities in package metadata
    vulnerabilities = data.get("vulnerabilities", [])
    return vulnerabilities
```

---

## 📧 알림 설정

### Slack 통합

```yaml
# .github/workflows/security-scan.yml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "🚨 Critical security vulnerability detected!",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Security Alert*\nCritical vulnerability found in dependencies."
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_SECURITY_WEBHOOK }}
```

### Email 알림

GitHub Security Alerts는 자동으로 이메일 알림을 전송합니다.

---

## 📊 대시보드

### Dependabot Dashboard
- URL: https://github.com/dreamseedai/dreamseed_monorepo/security/dependabot
- 자동 업데이트: 주간 (월요일 09:00)

### Security Overview
- URL: https://github.com/dreamseedai/dreamseed_monorepo/security
- Code scanning alerts
- Secret scanning alerts
- Dependency alerts

---

## 🧪 테스트 계획

### 수동 테스트
```bash
# pip-audit 설치 및 실행
pip install pip-audit
cd backend
pip-audit

# npm audit 실행
cd portal_front
npm audit

# GitHub CLI로 alerts 확인
gh api repos/dreamseedai/dreamseed_monorepo/dependabot/alerts
```

### 자동화 테스트
- GitHub Actions 워크플로우 수동 실행
- 주간 리포트 생성 테스트

---

## 📝 체크리스트

### GitHub 설정
- [ ] Dependabot alerts 활성화
- [ ] Dependabot security updates 활성화
- [ ] Code scanning (CodeQL) 활성화
- [ ] Secret scanning 활성화
- [ ] Dependency review 활성화

### 파일 생성
- [ ] `.github/dependabot.yml`
- [ ] `.github/workflows/security-scan.yml`
- [ ] `scripts/security/scan_dependencies.py`
- [ ] `scripts/security/weekly_report.py`
- [ ] `scripts/security/check_critical.py`

### 문서화
- [ ] `ops/security-hardening/docs/CVE_MONITORING.md`
- [ ] README 업데이트
- [ ] PR 템플릿

---

## 🚀 배포 후 작업

1. **첫 주간 리포트 생성** (수동)
2. **Dependabot PR 리뷰 프로세스** 수립
3. **Critical CVE 대응 프로세스** 문서화
4. **팀 교육**: Dependabot 사용법

---

## 📚 참고 자료

- [GitHub Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [pip-audit](https://github.com/pypa/pip-audit)
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [CVE Database](https://cve.mitre.org/)
- [NVD (National Vulnerability Database)](https://nvd.nist.gov/)

---

**다음 단계**: Dependabot 설정 파일 생성
