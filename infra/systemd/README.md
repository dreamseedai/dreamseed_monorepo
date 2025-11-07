# SystemD Services for IRT Calibration

> TL;DR for Ops: See the deployment playbook — `shared/irt/docs/06_DEPLOYMENT_GUIDE.md`. This README focuses on SystemD specifics; the guide covers DB migrations, Docker/K8s, verification, rollback, and security.  
> 운영팀 요약: 전체 배포 절차는 `shared/irt/docs/06_DEPLOYMENT_GUIDE.md`를 우선 참조하세요. 본 문서는 SystemD 운영에 초점을 맞추고, 마이그레이션/쿠버네티스/검증/롤백/보안은 배포 가이드에 정리되어 있습니다.

Quick checklist / 빠른 체크리스트:
- [ ] DB 마이그레이션 완료: `alembic upgrade head`
- [ ] 환경파일 준비: `/etc/irt/irt.env` (권한 600)
- [ ] 서비스/타이머 설치: `irt-calibration.service` + `irt-calibration.timer`
- [ ] 리포트 타이머 설치(선택): `irt-report.timer`
- [ ] 수동 점검: `systemctl start irt-calibration.service` → `journalctl -u irt-calibration.service -f`
- [ ] 정기 실행 확인: `systemctl list-timers | grep irt`

Systemd service and timer units for automated monthly IRT calibration jobs.

## Files

- `irt-calibration.service.example` - PyMC Bayesian calibration (Python)
- `irt-calibration-mirt.service.example` - mirt baseline calibration (Python)
- `irt-calibration-brms.service.example` - brms Bayesian calibration (R/Stan)
- `irt-calibration.timer` - Monthly timer trigger

## Installation

### 1. Copy service files

```bash
# Copy and configure service files
sudo cp infra/systemd/irt-calibration.service.example \
    /etc/systemd/system/irt-calibration.service

sudo cp infra/systemd/irt-calibration-mirt.service.example \
    /etc/systemd/system/irt-calibration-mirt.service

sudo cp infra/systemd/irt-calibration-brms.service.example \
    /etc/systemd/system/irt-calibration-brms.service

sudo cp infra/systemd/irt-calibration.timer \
    /etc/systemd/system/irt-calibration.timer
```

### 2. Edit service files

```bash
# Edit PyMC service (update DATABASE_URL)
sudo vim /etc/systemd/system/irt-calibration.service

# Edit mirt service (update DATABASE_URL)
sudo vim /etc/systemd/system/irt-calibration-mirt.service

# Edit brms service (update PGHOST, PGUSER, PGPASSWORD)
sudo vim /etc/systemd/system/irt-calibration-brms.service
```

**Required changes:**
- Update `Environment="DATABASE_URL=..."` with actual credentials
- Update `WorkingDirectory=...` if different from `/opt/dreamseed`
- Update `User=` and `Group=` if service account is different
- Adjust paths in `ReadWritePaths=` for log directories

### 3. Set permissions

```bash
sudo chmod 600 /etc/systemd/system/irt-calibration*.service
sudo chmod 644 /etc/systemd/system/irt-calibration.timer
```

### 4. Reload systemd

```bash
sudo systemctl daemon-reload
```

### 5. Enable and start timer

```bash
# Enable timer (auto-start on boot)
sudo systemctl enable irt-calibration.timer

# Start timer immediately
sudo systemctl start irt-calibration.timer

# Check timer status
sudo systemctl status irt-calibration.timer
systemctl list-timers irt-calibration.timer
```

## Usage

### Manual Execution

Run calibration jobs manually (without waiting for timer):

```bash
# Run PyMC calibration
sudo systemctl start irt-calibration.service

# Run mirt baseline
sudo systemctl start irt-calibration-mirt.service

# Run brms Bayesian
sudo systemctl start irt-calibration-brms.service
```

### Check Status

```bash
# Service status
sudo systemctl status irt-calibration.service

# Timer status
sudo systemctl status irt-calibration.timer

# View logs
sudo journalctl -u irt-calibration.service -f
sudo journalctl -u irt-calibration-mirt.service --since "1 hour ago"
sudo journalctl -u irt-calibration-brms.service -n 100
```

### Timer Management

```bash
# List all timers
systemctl list-timers

# Show next trigger time
systemctl list-timers irt-calibration.timer

# Stop timer
sudo systemctl stop irt-calibration.timer

# Disable timer (prevent auto-start on boot)
sudo systemctl disable irt-calibration.timer
```

## Timer Schedule

Default schedule: **1st day of every month at 2:00 AM**

Edit timer file to customize:

```ini
[Timer]
# Run monthly
OnCalendar=monthly

# Or specific date/time
OnCalendar=*-*-01 02:00:00

# Or multiple times
OnCalendar=*-*-01 02:00:00
OnCalendar=*-*-15 02:00:00
```

Available calendar formats:
- `monthly` - 1st day of month at 00:00
- `weekly` - Monday at 00:00
- `daily` - Every day at 00:00
- `*-*-01 02:00:00` - 1st day at 2 AM
- `Mon *-*-* 12:00:00` - Every Monday at noon

After editing timer:
```bash
sudo systemctl daemon-reload
sudo systemctl restart irt-calibration.timer
```

## Running Multiple Methods

To run all three calibration methods sequentially:

### Option 1: Separate services with dependencies

Create `irt-calibration-all.service`:

```ini
[Unit]
Description=Run all IRT calibration methods
After=network.target postgresql.service

[Service]
Type=oneshot
ExecStart=/usr/bin/systemctl start irt-calibration-mirt.service
ExecStart=/usr/bin/systemctl start irt-calibration.service
ExecStart=/usr/bin/systemctl start irt-calibration-brms.service
User=root
Group=root
```

### Option 2: Shell script wrapper

Create `/opt/dreamseed/scripts/run_all_calibrations.sh`:

```bash
#!/bin/bash
set -e

echo "Starting mirt calibration..."
systemctl start irt-calibration-mirt.service
systemctl is-active --quiet irt-calibration-mirt.service || systemctl status irt-calibration-mirt.service

echo "Starting PyMC calibration..."
systemctl start irt-calibration.service
systemctl is-active --quiet irt-calibration.service || systemctl status irt-calibration.service

echo "Starting brms calibration..."
systemctl start irt-calibration-brms.service
systemctl is-active --quiet irt-calibration-brms.service || systemctl status irt-calibration-brms.service

echo "All calibrations completed successfully."
```

Then update timer to call script:

```ini
[Service]
ExecStart=/opt/dreamseed/scripts/run_all_calibrations.sh
```

## Monitoring

### Check last run

```bash
# View last execution logs
sudo journalctl -u irt-calibration.service -n 50

# Check exit status
systemctl show irt-calibration.service -p ExecMainStatus
```

### Email notifications on failure

Install `mailutils`:

```bash
sudo apt-get install mailutils
```

Add to service file:

```ini
[Service]
OnFailure=failure-email@%n.service
```

Create `/etc/systemd/system/failure-email@.service`:

```ini
[Unit]
Description=Send email on %i failure

[Service]
Type=oneshot
ExecStart=/usr/bin/mail -s "Service %i failed" admin@example.com
StandardInput=null
```

### Slack/Discord webhooks

Create notification script `/opt/dreamseed/scripts/notify_failure.sh`:

```bash
#!/bin/bash
SERVICE=$1
STATUS=$2

curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"IRT Calibration Service ${SERVICE} failed with status ${STATUS}\"}"
```

Add to service:

```ini
[Service]
ExecStopPost=/opt/dreamseed/scripts/notify_failure.sh %n %R
```

## Troubleshooting

### Service fails to start

```bash
# Check service status
sudo systemctl status irt-calibration.service

# View detailed logs
sudo journalctl -xe -u irt-calibration.service

# Check file permissions
ls -la /opt/dreamseed/shared/irt/
sudo -u svc_dreamseed python3 -m shared.irt.calibrate_monthly_pymc --help
```

### Database connection issues

```bash
# Test connection as service user
sudo -u svc_dreamseed psql "$DATABASE_URL" -c "SELECT 1;"

# Check environment variables
sudo systemctl show irt-calibration.service -p Environment
```

### Python module not found

```bash
# Verify PYTHONPATH
echo $PYTHONPATH

# Test import as service user
sudo -u svc_dreamseed python3 -c "import shared.irt.calibrate_monthly_pymc"

# Install missing packages
sudo -u svc_dreamseed pip3 install -r requirements.txt
```

### Timer not triggering

```bash
# Check timer is active
systemctl is-active irt-calibration.timer

# List upcoming triggers
systemctl list-timers --all

# Check timer logs
sudo journalctl -u irt-calibration.timer
```

## Security Considerations

### Service account

Create dedicated service account:

```bash
sudo useradd -r -s /bin/false -M -d /opt/dreamseed svc_dreamseed
sudo chown -R svc_dreamseed:svc_dreamseed /opt/dreamseed
```

### Database credentials

Store credentials securely:

```bash
# Use environment files
sudo mkdir -p /etc/dreamseed
sudo vim /etc/dreamseed/irt-calibration.env

# Add to service file:
[Service]
EnvironmentFile=/etc/dreamseed/irt-calibration.env

# Restrict permissions
sudo chmod 600 /etc/dreamseed/irt-calibration.env
sudo chown root:root /etc/dreamseed/irt-calibration.env
```

### Hardening options

Service includes:
- `NoNewPrivileges=true` - Prevent privilege escalation
- `PrivateTmp=true` - Isolate /tmp directory
- `ProtectSystem=strict` - Read-only filesystem
- `ProtectHome=true` - Hide home directories
- `ReadWritePaths=...` - Only specified paths writable

Additional options:

```ini
[Service]
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictNamespaces=true
RestrictRealtime=true
LockPersonality=true
```

## IRT Report Generation

### Report Service Files

- `irt-report.service.example` - Single window report
- `irt-report-batch.service.example` - Batch report for multiple windows
- `irt-report-script.service.example` - Shell script wrapper
- `irt-report.timer` - Monthly report generation timer
- `scripts/generate_reports.sh` - Standalone report generation script

### Installation

```bash
# Copy script and make executable
sudo cp infra/systemd/scripts/generate_reports.sh /opt/dreamseed/infra/systemd/scripts/
sudo chmod +x /opt/dreamseed/infra/systemd/scripts/generate_reports.sh

# Install service
sudo cp infra/systemd/irt-report-script.service.example \
    /etc/systemd/system/irt-report.service

# Edit configuration
sudo vim /etc/systemd/system/irt-report.service
# Update DATABASE_URL, REPORT_OUTPUT_DIR

# Install timer
sudo cp infra/systemd/irt-report.timer /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable --now irt-report.timer
```

### Manual Report Generation

```bash
# Generate reports for last 3 windows
sudo systemctl start irt-report.service

# Or run script directly
cd /opt/dreamseed
DATABASE_URL="postgresql://..." \
REPORT_OUTPUT_DIR="/opt/dreamseed/reports" \
./infra/systemd/scripts/generate_reports.sh 5
```

### Report Output

Reports are saved to `/opt/dreamseed/reports/`:
- `drift_window_1_20251105_140530.pdf`
- `drift_window_2_20251105_140545.pdf`
- `drift_window_3_20251105_140600.pdf`

### View Logs

```bash
# Service logs
sudo journalctl -u irt-report.service -f

# Last report generation
sudo journalctl -u irt-report.service -n 100 --no-pager
```

## Migration from Cron

If migrating from cron jobs:

```bash
# Remove old cron entries
sudo crontab -e -u svc_dreamseed
# Delete: 0 2 1 * * /opt/dreamseed/run_calibration.sh

# Install systemd timer
sudo systemctl enable --now irt-calibration.timer

# Verify migration
systemctl list-timers
```

Benefits over cron:
- Better logging (journalctl)
- Dependency management
- Resource limits
- Automatic retry on failure
- Email/webhook notifications

---

## 🔐 JWT Verifier Service

Nginx `auth_request`와 함께 사용하는 JWT 검증 마이크로서비스입니다.

### 설치

```bash
# 의존성 설치
pip install fastapi uvicorn python-jose[cryptography] httpx

# systemd 서비스 설정
sudo cp jwt-verifier.service.example /etc/systemd/system/jwt-verifier.service

# 환경변수 수정 (public key 경로 등)
sudo nano /etc/systemd/system/jwt-verifier.service

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable jwt-verifier
sudo systemctl start jwt-verifier
```

### 상태 확인

```bash
# 서비스 상태
sudo systemctl status jwt-verifier

# 로그 확인
sudo journalctl -u jwt-verifier -f

# Health check
curl http://127.0.0.1:9000/health
```

### nginx 연동

`infra/nginx/jwt_auth_simple.conf` 참고:
```nginx
location = /auth/verify {
    internal;
    proxy_pass http://127.0.0.1:9000/verify;
    proxy_set_header Authorization $http_authorization;
}

location /admin/ {
    auth_request /auth/verify;
    auth_request_set $auth_user $upstream_http_x_user;
    auth_request_set $auth_org_id $upstream_http_x_org_id;
    auth_request_set $auth_roles $upstream_http_x_roles;
    
    proxy_set_header X-User $auth_user;
    proxy_set_header X-Org-Id $auth_org_id;
    proxy_set_header X-Roles $auth_roles;
    proxy_pass http://127.0.0.1:8080/;
}
```

---

## 📊 Shiny Dashboard Service

R Shiny 관리자 대시보드를 systemd로 관리합니다.

### 설치

```bash
# R 패키지 설치 (root 또는 shiny 사용자)
Rscript -e 'install.packages(c("shiny", "shinydashboard", "DT", "arrow", "dplyr", "plotly"))'

# systemd 서비스 설정
sudo cp shiny-dashboard.service.example /etc/systemd/system/shiny-dashboard.service

# 경로 수정
sudo nano /etc/systemd/system/shiny-dashboard.service

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable shiny-dashboard
sudo systemctl start shiny-dashboard
```

### 상태 확인

```bash
sudo systemctl status shiny-dashboard
sudo journalctl -u shiny-dashboard -f
curl http://127.0.0.1:8080  # nginx 프록시 뒤에서만 접근 가능
```

### 리소스 모니터링

```bash
# 메모리 사용량
systemctl show shiny-dashboard | grep Memory

# CPU 사용률
systemctl status shiny-dashboard
```

---

## 📖 참고 문서

- [IRT Deployment Guide](../../shared/irt/docs/06_DEPLOYMENT_GUIDE.md)
- [Nginx JWT Authentication](../nginx/README.md)
- [Shiny Dashboard Guide](../../portal_front/dashboard/README.md)

````
